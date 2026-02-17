from fastapi import APIRouter, HTTPException, Query
from beanie import PydanticObjectId
from datetime import datetime

from app.models.agent import Agent, Relationship, Memory
from app.models.event import EventType
from app.models.log import LogCategory
from app.services.builder import AgentBuilder, EventBuilder, LogBuilder
from app.schemas.schemas import (
    AgentCreate, AgentUpdate, AgentResponse, AgentDetailResponse,
    AgentListResponse, MoodUpdate, RelationshipUpdate, MemoryAdd,
    RelationshipGraphResponse, RelationshipGraphNode, RelationshipGraphEdge,
)

router = APIRouter(prefix="/system", tags=["System"])

MAX_MEMORIES = 50


def to_response(a: Agent) -> AgentResponse:
    return AgentResponse(
        id=str(a.id), name=a.name, bio=a.bio, avatar_url=a.avatar_url,
        personality=a.personality, emotion=a.emotion,
        relationships=a.relationships, memories_count=len(a.memories),
        current_plan=a.current_plan, current_goal=a.current_goal,
        is_active=a.is_active, created_at=a.created_at, updated_at=a.updated_at,
    )


def to_detail(a: Agent) -> AgentDetailResponse:
    return AgentDetailResponse(
        id=str(a.id), name=a.name, bio=a.bio, avatar_url=a.avatar_url,
        personality=a.personality, emotion=a.emotion,
        relationships=a.relationships, memories=a.memories,
        memories_count=len(a.memories), current_plan=a.current_plan,
        current_goal=a.current_goal, is_active=a.is_active,
        system_prompt=a.system_prompt, created_at=a.created_at,
        updated_at=a.updated_at,
    )


async def _log(cat, msg, agent=None, **details):
    b = LogBuilder().category(cat).message(msg)
    if agent:
        b.agent(str(agent.id), agent.name)
    for k, v in details.items():
        b.detail(k, v)
    await b.build().insert()


'''CRUD'''

@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(data: AgentCreate):
    builder = AgentBuilder().set_name(data.name).set_bio(data.bio)
    if data.avatar_url:
        builder.set_avatar(data.avatar_url)
    if data.personality:
        p = data.personality
        builder.set_personality(p.openness, p.conscientiousness, p.extraversion, p.agreeableness, p.neuroticism)
    if data.emotion:
        builder.set_mood(data.emotion.mood, data.emotion.energy, data.emotion.stress, data.emotion.happiness)
    if data.system_prompt:
        builder.set_system_prompt(data.system_prompt)

    agent = builder.build()
    await agent.insert()
    await _log(LogCategory.AGENT_CREATED, f"Создан: {agent.name}", agent)
    return to_response(agent)


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(active_only: bool = False, skip: int = 0, limit: int = 20):
    q = {"is_active": True} if active_only else {}
    agents = await Agent.find(q).skip(skip).limit(limit).to_list()
    total = await Agent.find(q).count()
    return AgentListResponse(agents=[to_response(a) for a in agents], total=total)


@router.get("/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")
    return to_detail(agent)


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, data: AgentUpdate):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")

    fields = data.model_dump(exclude_unset=True)
    fields["updated_at"] = datetime.utcnow()
    for k, v in fields.items():
        setattr(agent, k, v)
    await agent.save()

    await _log(LogCategory.AGENT_UPDATED, f"Обновлён: {agent.name}", agent, fields=list(fields.keys()))
    return to_response(agent)


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")
    await _log(LogCategory.AGENT_DELETED, f"Удалён: {agent.name}", agent)
    await agent.delete()


'''Настроение'''

@router.patch("/agents/{agent_id}/mood", response_model=AgentResponse)
async def update_mood(agent_id: str, data: MoodUpdate):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")

    old = agent.emotion.mood
    agent.emotion.mood = data.mood
    if data.energy is not None: agent.emotion.energy = data.energy
    if data.stress is not None: agent.emotion.stress = data.stress
    if data.happiness is not None: agent.emotion.happiness = data.happiness
    agent.updated_at = datetime.utcnow()
    await agent.save()

    event = (EventBuilder()
        .set_type(EventType.MOOD_CHANGE)
        .set_description(f"{agent.name}: {old.value} → {data.mood.value}")
        .set_source(str(agent.id), agent.name)
        .set_content(data.reason)
        .add_meta("old_mood", old.value)
        .add_meta("new_mood", data.mood.value)
        .build())
    await event.insert()
    await _log(LogCategory.MOOD_CHANGED, f"{agent.name}: {old.value} → {data.mood.value}", agent)
    return to_response(agent)


'''Отношения'''

@router.patch("/agents/{agent_id}/relationship", response_model=AgentResponse)
async def update_relationship(agent_id: str, data: RelationshipUpdate):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")
    target = await Agent.get(PydanticObjectId(data.target_agent_id))
    if not target:
        raise HTTPException(404, "Целевой агент не найден")

    rel = next((r for r in agent.relationships if r.agent_id == data.target_agent_id), None)
    if rel:
        rel.sympathy = max(-1.0, min(1.0, rel.sympathy + data.sympathy_delta))
        if data.description: rel.description = data.description
        rel.last_interaction = datetime.utcnow()
    else:
        agent.relationships.append(Relationship(
            agent_id=data.target_agent_id, agent_name=target.name,
            sympathy=max(-1.0, min(1.0, data.sympathy_delta)),
            description=data.description or "", last_interaction=datetime.utcnow(),
        ))

    agent.updated_at = datetime.utcnow()
    await agent.save()

    event = (EventBuilder()
        .set_type(EventType.RELATIONSHIP)
        .set_description(f"{agent.name} → {target.name} ({data.sympathy_delta:+.2f})")
        .set_source(str(agent.id), agent.name)
        .set_target(str(target.id), target.name)
        .build())
    await event.insert()
    await _log(LogCategory.RELATIONSHIP_CHANGED, f"{agent.name} → {target.name}", agent)
    return to_response(agent)

'''Память'''

@router.post("/agents/{agent_id}/memory", response_model=AgentDetailResponse)
async def add_memory(agent_id: str, data: MemoryAdd):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")

    agent.memories.append(Memory(content=data.content, importance=data.importance, related_agent_id=data.related_agent_id))

    if len(agent.memories) > MAX_MEMORIES:
        agent.memories.sort(key=lambda m: m.importance)
        old = agent.memories[:len(agent.memories) - MAX_MEMORIES]
        summary = Memory(content="[Сводка] " + "; ".join(m.content[:60] for m in old[:5]), importance=0.3)
        agent.memories = [summary] + agent.memories[len(old):]

    agent.updated_at = datetime.utcnow()
    await agent.save()
    await _log(LogCategory.MEMORY_ADDED, f"Память: {data.content[:50]}", agent)
    return to_detail(agent)


@router.get("/agents/{agent_id}/memories")
async def get_memories(agent_id: str, min_importance: float = Query(0.0, ge=0.0, le=1.0)):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")
    mems = sorted([m for m in agent.memories if m.importance >= min_importance], key=lambda m: m.timestamp, reverse=True)
    return {"memories": mems, "total": len(mems)}


'''Граф отношений'''

@router.get("/agents/graph/relationships", response_model=RelationshipGraphResponse)
async def get_graph():
    agents = await Agent.find({"is_active": True}).to_list()
    nodes = [RelationshipGraphNode(id=str(a.id), name=a.name, mood=a.emotion.mood, avatar_url=a.avatar_url) for a in agents]

    edges, seen = [], set()
    for a in agents:
        for r in a.relationships:
            key = tuple(sorted([str(a.id), r.agent_id]))
            if key not in seen:
                seen.add(key)
                edges.append(RelationshipGraphEdge(source=str(a.id), target=r.agent_id, sympathy=r.sympathy, description=r.description))

    return RelationshipGraphResponse(nodes=nodes, edges=edges)
