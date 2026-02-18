from fastapi import APIRouter, HTTPException
from beanie import PydanticObjectId
from datetime import datetime

from app.models.agent import Agent, Memory, Relationship
from app.models.event import EventType
from app.models.log import LogLevel, LogCategory
from app.services.builder import EventBuilder, LogBuilder
from app.services.gigachat_service import chat, reflect, dialogue
from app.schemas.schemas import SendMessage, ChatResponse, ReflectionResponse, DialogueResponse

router = APIRouter(prefix="/text", tags=["Text"])


async def update_relationship_after_interaction(agent: Agent, target_agent_id: str, message: str, is_positive: bool = True):
    """Автоматически обновляет отношения между агентами после взаимодействия"""
    if not target_agent_id:
        return None
    
    # Расширенный анализ тона сообщения
    positive_words = ['спасибо', 'благодарю', 'отлично', 'хорошо', 'рад', 'нравится', 'люблю', 'друг', 'помощь', 'приятно', 'замечательно', 'прекрасно', 'весело', 'интересно', 'классно']
    negative_words = ['ненавижу', 'плохо', 'злой', 'разозлился', 'обижен', 'не нравится', 'уходи', 'неприятно', 'скучно', 'уныло', 'надоел', 'достал']
    
    # Агрессивные слова и фразы
    aggressive_words = ['ненавижу', 'презираю', 'злой', 'злюсь', 'бесит', 'раздражает', 'достал', 'надоел', 'уйди', 'отстань', 'заткнись', 'тупой', 'идиот', 'дурак']
    offended_words = ['обижен', 'обидно', 'обиделся', 'несправедливо', 'нечестно', 'предал', 'обманул', 'разочарован', 'расстроен']
    rude_words = ['тупой', 'идиот', 'дурак', 'болван', 'кретин', 'заткнись', 'замолчи', 'уйди', 'отстань', 'пошел вон']
    
    message_lower = message.lower()
    positive_count = sum(1 for word in positive_words if word in message_lower)
    negative_count = sum(1 for word in negative_words if word in message_lower)
    aggressive_count = sum(1 for word in aggressive_words if word in message_lower)
    offended_count = sum(1 for word in offended_words if word in message_lower)
    rude_count = sum(1 for word in rude_words if word in message_lower)
    
    # Определяем изменение симпатии на основе тона
    if aggressive_count > 0 or rude_count > 0:
        # Агрессивное или грубое взаимодействие - сильное негативное изменение
        sympathy_delta = -0.2 - (aggressive_count * 0.1) - (rude_count * 0.15)
        is_positive = False
    elif offended_count > 0:
        # Обиженное взаимодействие - среднее негативное изменение
        sympathy_delta = -0.15 - (offended_count * 0.08)
        is_positive = False
    elif negative_count > positive_count:
        # Негативное взаимодействие
        sympathy_delta = -0.1 - (negative_count * 0.05)
        is_positive = False
    elif positive_count > negative_count:
        # Позитивное взаимодействие
        sympathy_delta = 0.1 + (positive_count * 0.05)
        is_positive = True
    else:
        # Нейтральное взаимодействие
        sympathy_delta = 0.05 if is_positive else -0.02
    
    # Учитываем текущие отношения - если отношения плохие, легче их ухудшить
    rel = next((r for r in agent.relationships if r.agent_id == target_agent_id), None)
    if rel and rel.sympathy < -0.3:
        # Если отношения уже плохие, негативные взаимодействия сильнее влияют
        if sympathy_delta < 0:
            sympathy_delta *= 1.3
    
    # Ограничиваем изменение
    sympathy_delta = max(-0.4, min(0.3, sympathy_delta))
    
    # Получаем целевого агента
    target = await Agent.get(PydanticObjectId(target_agent_id))
    if not target:
        return None
    
    # Обновляем или создаем отношение
    rel = next((r for r in agent.relationships if r.agent_id == target_agent_id), None)
    if rel:
        rel.sympathy = max(-1.0, min(1.0, rel.sympathy + sympathy_delta))
        rel.last_interaction = datetime.utcnow()
    else:
        agent.relationships.append(Relationship(
            agent_id=target_agent_id,
            agent_name=target.name,
            sympathy=max(-1.0, min(1.0, sympathy_delta)),
            description="",
            last_interaction=datetime.utcnow()
        ))
    
    # Обновляем отношения в ОБОИХ направлениях
    # Также обновляем отношение целевого агента к исходному
    target_rel = next((r for r in target.relationships if r.agent_id == str(agent.id)), None)
    if target_rel:
        # Взаимное изменение (обычно меньше, чем прямое)
        mutual_delta = sympathy_delta * 0.5  # Взаимное изменение в 2 раза меньше
        target_rel.sympathy = max(-1.0, min(1.0, target_rel.sympathy + mutual_delta))
        target_rel.last_interaction = datetime.utcnow()
    else:
        # Создаем обратное отношение
        mutual_delta = sympathy_delta * 0.5
        target.relationships.append(Relationship(
            agent_id=str(agent.id),
            agent_name=agent.name,
            sympathy=max(-1.0, min(1.0, mutual_delta)),
            description="",
            last_interaction=datetime.utcnow()
        ))
    await target.save()
    
    # Создаем событие об изменении отношений, если изменение значительное
    if abs(sympathy_delta) > 0.05:
        ev = EventBuilder().set_type(EventType.RELATIONSHIP).set_description(
            f"{agent.name} ↔ {target.name}: {sympathy_delta:+.2f}"
        ).set_source(str(agent.id), agent.name).set_target(str(target.id), target.name).build()
        await ev.insert()
        await _log(LogCategory.RELATIONSHIP_CHANGED, f"{agent.name} ↔ {target.name}: {sympathy_delta:+.2f}", agent)
    
    return sympathy_delta


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

    # Структурированное воспоминание о полученном сообщении
    memory_content = f"[Сообщение] От {from_name}: \"{data.content[:150]}\""
    agent.memories.append(Memory(
        content=memory_content,
        importance=0.6,
        related_agent_id=data.from_agent_id,
        timestamp=datetime.utcnow()
    ))

    try:
        reply = await chat(agent, data.content)
    except Exception as e:
        await _log(LogCategory.LLM_ERROR, f"Ошибка: {e}", agent, lvl=LogLevel.ERROR)
        reply = f"[Ошибка GigaChat: {e}]"

    ev_out = EventBuilder().set_type(EventType.CHAT).set_description(f"{agent.name} → {from_name}").set_source(str(agent.id), agent.name).set_content(reply).build()
    await ev_out.insert()

    # Структурированное воспоминание о ответе
    memory_content = f"[Ответ] Ответил {from_name}: \"{reply[:150]}\""
    agent.memories.append(Memory(
        content=memory_content,
        importance=0.5,
        timestamp=datetime.utcnow()
    ))
    
    # Улучшенное динамическое изменение настроения на основе ответа
    from app.models.agent import Mood
    old_mood = agent.emotion.mood
    reply_lower = reply.lower()
    
    # Расширенный анализ эмоциональных слов
    positive_words = ['рад', 'хорошо', 'отлично', 'спасибо', 'нравится', 'замечательно', 'прекрасно', 'весело']
    negative_words = ['плохо', 'грустно', 'злой', 'не нравится', 'обижен', 'уныло', 'скучно']
    excited_words = ['восторг', 'взволнован', 'энергичн', 'интересно', 'классно', 'супер']
    angry_words = ['злой', 'раздражен', 'сердит', 'недоволен', 'бесит']
    
    positive_count = sum(1 for word in positive_words if word in reply_lower)
    negative_count = sum(1 for word in negative_words if word in reply_lower)
    excited_count = sum(1 for word in excited_words if word in reply_lower)
    angry_count = sum(1 for word in angry_words if word in reply_lower)
    
    # Анализируем также само сообщение пользователя на негатив
    message_lower = data.content.lower()
    user_aggressive = any(word in message_lower for word in ['ненавижу', 'презираю', 'злой', 'тупой', 'идиот', 'дурак', 'заткнись', 'уйди', 'отстань', 'бесит'])
    user_offensive = any(word in message_lower for word in ['обидел', 'несправедливо', 'предал', 'обманул'])
    user_negative = any(word in message_lower for word in ['плохо', 'грустно', 'не нравится', 'неприятно'])
    
    # Определяем изменение настроения - УСИЛЕНО для более заметных изменений
    if user_aggressive or user_offensive:
        # Если пользователь агрессивен или обижает - агент должен отреагировать негативно
        agent.emotion.mood = Mood.ANGRY
        agent.emotion.stress = min(1.0, agent.emotion.stress + 0.15)
        agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.12)
    elif excited_count > 0:
        agent.emotion.mood = Mood.EXCITED
        agent.emotion.energy = min(1.0, agent.emotion.energy + 0.12)
        agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.08)
    elif angry_count > 0:
        agent.emotion.mood = Mood.ANGRY
        agent.emotion.stress = min(1.0, agent.emotion.stress + 0.12)
        agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.1)
    elif positive_count > negative_count and not user_negative:
        agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.06)
        agent.emotion.stress = max(0.0, agent.emotion.stress - 0.04)
        if agent.emotion.happiness > 0.7:
            agent.emotion.mood = Mood.HAPPY
    elif negative_count > positive_count or user_negative:
        agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.08)
        agent.emotion.stress = min(1.0, agent.emotion.stress + 0.1)
        if agent.emotion.happiness < 0.3:
            agent.emotion.mood = Mood.SAD
    
    # Сохраняем изменения настроения СРАЗУ после изменения
    if old_mood != agent.emotion.mood:
        print(f"[TEXT_CONTROLLER] {agent.name} изменил настроение: {old_mood} -> {agent.emotion.mood}")
        agent.updated_at = datetime.utcnow()
        await agent.save()
    
    # Обновляем отношения, если сообщение от другого агента
    if not data.from_user and data.from_agent_id:
        await update_relationship_after_interaction(agent, data.from_agent_id, reply, is_positive=True)
    
    # Автоматическая суммаризация памяти при превышении лимита
    MAX_MEMORIES = 50
    if len(agent.memories) > MAX_MEMORIES:
        agent.memories.sort(key=lambda m: m.importance)
        old = agent.memories[:len(agent.memories) - MAX_MEMORIES]
        summary = Memory(
            content="[Сводка] " + "; ".join(m.content[:60] for m in old[:5]),
            importance=0.3,
            timestamp=datetime.utcnow()
        )
        agent.memories = [summary] + agent.memories[len(old):]
    
    agent.updated_at = datetime.utcnow()
    await agent.save()
    print(f"[TEXT_CONTROLLER] {agent.name} сохранен: настроение={agent.emotion.mood}, счастье={agent.emotion.happiness:.2f}, доброжелательность={agent.personality.agreeableness:.2f}")

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
        # Структурированное воспоминание о диалоге
        memory_content = f"[Диалог] Общался с {target.name}: \"{reply[:150]}\""
        agent.memories.append(Memory(
            content=memory_content,
            importance=0.6,
            related_agent_id=str(target.id),
            timestamp=datetime.utcnow()
        ))
        
        # Определяем, было ли взаимодействие позитивным или негативным
        reply_lower = reply.lower()
        aggressive_words = ['ненавижу', 'презираю', 'злой', 'злюсь', 'бесит', 'раздражает', 'достал', 'надоел', 'уйди', 'отстань', 'заткнись', 'тупой', 'идиот', 'дурак']
        offended_words = ['обижен', 'обидно', 'обиделся', 'несправедливо', 'нечестно', 'предал', 'обманул', 'разочарован', 'расстроен']
        negative_words = ['плохо', 'грустно', 'не нравится', 'неприятно', 'скучно', 'уныло']
        
        is_positive_interaction = not (any(word in reply_lower for word in aggressive_words + offended_words + negative_words))
        
        # Обновляем отношения между агентами после диалога (двусторонне)
        await update_relationship_after_interaction(agent, str(target.id), reply, is_positive=is_positive_interaction)
        
        # Автоматическая суммаризация памяти при превышении лимита
        MAX_MEMORIES = 50
        if len(agent.memories) > MAX_MEMORIES:
            agent.memories.sort(key=lambda m: m.importance)
            old = agent.memories[:len(agent.memories) - MAX_MEMORIES]
            summary = Memory(content="[Сводка] " + "; ".join(m.content[:60] for m in old[:5]), importance=0.3)
            agent.memories = [summary] + agent.memories[len(old):]
        
        await agent.save()
    
    # Обновляем данные обоих агентов после диалога
    await a1.save()
    await a2.save()
    print(f"[TEXT_CONTROLLER] Диалог сохранен: {a1.name} (настроение={a1.emotion.mood}, счастье={a1.emotion.happiness:.2f}), {a2.name} (настроение={a2.emotion.mood}, счастье={a2.emotion.happiness:.2f})")

    await _log(LogCategory.DIALOGUE, f"{a1.name} ↔ {a2.name}")
    return DialogueResponse(
        agent1={"id": str(a1.id), "name": a1.name, "says": r1},
        agent2={"id": str(a2.id), "name": a2.name, "says": r2},
    )
