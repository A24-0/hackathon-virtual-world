from fastapi import APIRouter, HTTPException, Query
from beanie import PydanticObjectId
from datetime import datetime

from app.models.agent import Agent, Memory
from app.models.event import Event, EventType
from app.models.log import LogCategory
from app.services.builder import EventBuilder, LogBuilder
from app.schemas.schemas import (
    WorldEventCreate, AgentEventCreate, EventResponse,
    EventListResponse, EventFeedResponse,
)

router = APIRouter(prefix="/action", tags=["Action"])


def to_resp(e: Event) -> EventResponse:
    return EventResponse(
        id=str(e.id), event_type=e.event_type, description=e.description,
        agent_id=e.agent_id, agent_name=e.agent_name,
        target_agent_id=e.target_agent_id, target_agent_name=e.target_agent_name,
        content=e.content, metadata=e.metadata, timestamp=e.timestamp,
    )


@router.get("/feed", response_model=EventFeedResponse)
async def feed(limit: int = Query(20, ge=1, le=100), cursor: str | None = None,
               event_type: EventType | None = None, agent_id: str | None = None):
    q = {}
    if cursor:
        try:
            ce = await Event.get(PydanticObjectId(cursor))
            if ce: q["timestamp"] = {"$lt": ce.timestamp}
        except: pass
    if event_type: q["event_type"] = event_type.value
    if agent_id: q["$or"] = [{"agent_id": agent_id}, {"target_agent_id": agent_id}]

    events = await Event.find(q).sort("-timestamp").limit(limit + 1).to_list()
    has_more = len(events) > limit
    events = events[:limit]
    return EventFeedResponse(events=[to_resp(e) for e in events], has_more=has_more,
                             next_cursor=str(events[-1].id) if events and has_more else None)


@router.post("/world-event", response_model=EventResponse, status_code=201)
async def world_event(data: WorldEventCreate):
    from app.models.agent import Agent, Memory
    from app.models.event import EventType
    from app.services.gigachat_service import chat
    from app.models.log import LogCategory, LogLevel
    from app.services.builder import LogBuilder
    import random
    
    ev = EventBuilder().set_type(EventType.WORLD_EVENT).set_description(data.description).build()
    ev.metadata = data.metadata
    await ev.insert()

    await LogBuilder().category(LogCategory.WORLD_EVENT).message(f"Событие: {data.description}").build().insert()
    
    # Агенты реагируют на мировое событие
    agents = await Agent.find({"is_active": True}).to_list()
    if agents:
        # Выбираем случайных агентов для реакции (1-3 агента)
        reacting_agents = random.sample(agents, min(3, len(agents)))
        
        for agent in reacting_agents:
            try:
                # Агент комментирует событие
                reaction = await chat(agent, f"Произошло событие: {data.description}. Что ты об этом думаешь?")
                
                # Создаем событие реакции
                reaction_ev = EventBuilder().set_type(EventType.ACTION).set_description(
                    f"{agent.name} реагирует на событие"
                ).set_source(str(agent.id), agent.name).set_content(
                    reaction
                ).build()
                await reaction_ev.insert()
                
                # Добавляем в память агента
                agent.memories.append(Memory(
                    content=f"Событие в мире: {data.description}. Моя реакция: {reaction}",
                    importance=0.6
                ))
                
                # Изменяем настроение в зависимости от типа события
                from app.models.agent import Mood
                event_lower = data.description.lower()
                if any(word in event_lower for word in ['клад', 'найден', 'удача', 'победа', 'радость', 'хорошо']):
                    # Положительное событие
                    agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.15)  # Ограничиваем максимум до 0.9
                    if agent.emotion.mood in [Mood.SAD, Mood.BORED]:
                        agent.emotion.mood = Mood.HAPPY
                elif any(word in event_lower for word in ['катастрофа', 'проблема', 'опасность', 'угроза', 'плохо']):
                    # Отрицательное событие
                    agent.emotion.stress = min(1.0, agent.emotion.stress + 0.2)
                    agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.15)  # Ограничиваем минимум до 0.1
                    if agent.emotion.mood in [Mood.HAPPY, Mood.EXCITED]:
                        agent.emotion.mood = Mood.ANXIOUS
                
                # Суммаризация памяти
                MAX_MEMORIES = 50
                if len(agent.memories) > MAX_MEMORIES:
                    agent.memories.sort(key=lambda m: m.importance)
                    old = agent.memories[:len(agent.memories) - MAX_MEMORIES]
                    summary = Memory(content="[Сводка] " + "; ".join(m.content[:60] for m in old[:5]), importance=0.3)
                    agent.memories = [summary] + agent.memories[len(old):]
                
                agent.updated_at = datetime.utcnow()
                await agent.save()
                
            except Exception as e:
                print(f"Ошибка реакции агента {agent.name} на событие: {e}")
    
    return to_resp(ev)


@router.post("/agent-event", response_model=EventResponse, status_code=201)
async def agent_event(data: AgentEventCreate):
    agent = await Agent.get(PydanticObjectId(data.agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")

    b = EventBuilder().set_type(data.event_type).set_description(data.description).set_source(data.agent_id, agent.name)
    if data.target_agent_id:
        target = await Agent.get(PydanticObjectId(data.target_agent_id))
        if not target: raise HTTPException(404, "Целевой агент не найден")
        b.set_target(data.target_agent_id, target.name)
    if data.content:
        b.set_content(data.content)

    ev = b.build()
    ev.metadata = data.metadata
    await ev.insert()

    await LogBuilder().category(LogCategory.ACTION_EXECUTED).message(f"{agent.name}: {data.description}").agent(str(agent.id), agent.name).build().insert()
    return to_resp(ev)


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    ev = await Event.get(PydanticObjectId(event_id))
    if not ev: raise HTTPException(404, "Не найдено")
    return to_resp(ev)


@router.get("/events/agent/{agent_id}", response_model=EventListResponse)
async def agent_events(agent_id: str, skip: int = 0, limit: int = 50, event_type: EventType | None = None):
    q = {"$or": [{"agent_id": agent_id}, {"target_agent_id": agent_id}]}
    if event_type: q["event_type"] = event_type.value
    events = await Event.find(q).sort("-timestamp").skip(skip).limit(limit).to_list()
    total = await Event.find(q).count()
    return EventListResponse(events=[to_resp(e) for e in events], total=total)


@router.get("/events/between/{a1}/{a2}", response_model=EventListResponse)
async def between(a1: str, a2: str, skip: int = 0, limit: int = 50):
    q = {"$or": [{"agent_id": a1, "target_agent_id": a2}, {"agent_id": a2, "target_agent_id": a1}]}
    events = await Event.find(q).sort("-timestamp").skip(skip).limit(limit).to_list()
    total = await Event.find(q).count()
    return EventListResponse(events=[to_resp(e) for e in events], total=total)


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(event_id: str):
    ev = await Event.get(PydanticObjectId(event_id))
    if not ev: raise HTTPException(404, "Не найдено")
    await ev.delete()
