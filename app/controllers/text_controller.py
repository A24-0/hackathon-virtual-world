from fastapi import APIRouter, HTTPException
from beanie import PydanticObjectId
from datetime import datetime

from app.models.agent import Agent, Memory
from app.models.event import EventType
from app.models.log import LogLevel, LogCategory
from app.services.builder import EventBuilder, LogBuilder
from app.services.gigachat_service import chat, reflect, dialogue
from app.schemas.schemas import SendMessage, ChatResponse, ReflectionResponse, DialogueResponse

router = APIRouter(prefix="/text", tags=["Text"])


async def _log(cat, msg, agent=None, lvl=LogLevel.INFO, **details):
    b = LogBuilder().level(lvl).category(cat).message(msg)
    if agent:
        b.agent(str(agent.id), agent.name)
    for k, v in details.items():
        b.detail(k, v)
    await b.build().insert()


@router.post("/agents/{agent_id}/message", response_model=ChatResponse)
async def send_message(agent_id: str, data: SendMessage):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")

    from_name = "Пользователь"
    if not data.from_user and data.from_agent_id:
        sender = await Agent.get(PydanticObjectId(data.from_agent_id))
        from_name = sender.name if sender else "Неизвестный"

    await _log(LogCategory.LLM_REQUEST, f"Запрос к GigaChat: {agent.name}", agent, user_message=data.content)

    ev_type = EventType.USER_MESSAGE if data.from_user else EventType.CHAT
    ev_in = EventBuilder().set_type(ev_type).set_description(f"{from_name} → {agent.name}").set_target(str(agent.id), agent.name).set_content(data.content).build()
    if not data.from_user and data.from_agent_id:
        ev_in.agent_id = data.from_agent_id
        ev_in.agent_name = from_name
    await ev_in.insert()

    agent.memories.append(Memory(content=f"От {from_name}: {data.content}", importance=0.6, related_agent_id=data.from_agent_id))

    try:
        reply = await chat(agent, data.content)
    except Exception as e:
        await _log(LogCategory.LLM_ERROR, f"Ошибка: {e}", agent, lvl=LogLevel.ERROR)
        reply = f"[Ошибка GigaChat: {e}]"

    ev_out = EventBuilder().set_type(EventType.CHAT).set_description(f"{agent.name} → {from_name}").set_source(str(agent.id), agent.name).set_content(reply).build()
    await ev_out.insert()

    agent.memories.append(Memory(content=f"Ответил {from_name}: {reply}", importance=0.4))
    agent.updated_at = datetime.utcnow()
    await agent.save()

    await _log(LogCategory.LLM_RESPONSE, f"Ответ: {agent.name}", agent, reply=reply[:200])

    return ChatResponse(agent_id=str(agent.id), agent_name=agent.name, user_message=data.content, agent_reply=reply, event_id=str(ev_out.id))


@router.post("/agents/{agent_id}/reflect", response_model=ReflectionResponse)
async def do_reflect(agent_id: str):
    agent = await Agent.get(PydanticObjectId(agent_id))
    if not agent:
        raise HTTPException(404, "Агент не найден")

    try:
        result = await reflect(agent)
    except Exception as e:
        await _log(LogCategory.LLM_ERROR, f"Ошибка рефлексии: {e}", agent, lvl=LogLevel.ERROR)
        raise HTTPException(500, f"Ошибка GigaChat: {e}")

    ev = EventBuilder().set_type(EventType.REFLECTION).set_description(f"{agent.name}: рефлексия").set_source(str(agent.id), agent.name).set_content(result).build()
    await ev.insert()

    agent.memories.append(Memory(content=f"Рефлексия: {result}", importance=0.7))
    agent.updated_at = datetime.utcnow()
    await agent.save()

    await _log(LogCategory.REFLECTION, f"{agent.name}: рефлексия", agent)
    return ReflectionResponse(agent_id=str(agent.id), agent_name=agent.name, reflection=result)


@router.post("/dialogue/{agent1_id}/{agent2_id}", response_model=DialogueResponse)
async def do_dialogue(agent1_id: str, agent2_id: str, context: str = ""):
    a1 = await Agent.get(PydanticObjectId(agent1_id))
    a2 = await Agent.get(PydanticObjectId(agent2_id))
    if not a1 or not a2:
        raise HTTPException(404, "Агент не найден")

    try:
        r1 = await dialogue(a1, a2, context)
        r2 = await dialogue(a2, a1, f"{a1.name} сказал: {r1}")
    except Exception as e:
        await _log(LogCategory.LLM_ERROR, f"Ошибка диалога: {e}", lvl=LogLevel.ERROR)
        raise HTTPException(500, f"Ошибка GigaChat: {e}")

    for agent, reply, target in [(a1, r1, a2), (a2, r2, a1)]:
        ev = EventBuilder().set_type(EventType.CHAT).set_description(f"{agent.name} → {target.name}").set_source(str(agent.id), agent.name).set_target(str(target.id), target.name).set_content(reply).build()
        await ev.insert()
        agent.memories.append(Memory(content=f"Сказал {target.name}: '{reply}'", importance=0.5, related_agent_id=str(target.id)))
        await agent.save()

    await _log(LogCategory.DIALOGUE, f"{a1.name} ↔ {a2.name}")
    return DialogueResponse(
        agent1={"id": str(a1.id), "name": a1.name, "says": r1},
        agent2={"id": str(a2.id), "name": a2.name, "says": r2},
    )
