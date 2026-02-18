"""
Сервис для автоматического жизненного цикла агентов
Реализует: рефлексия → постановка цели → действие
"""
import asyncio
import random
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.models.agent import Agent, Memory
from app.models.event import EventType
from app.services.builder import EventBuilder
from app.services.gigachat_service import reflect, dialogue
from app.controllers.text_controller import update_relationship_after_interaction
from app.services.world_state import get_time_speed


async def agent_lifecycle_step(agent: Agent):
    """Один шаг жизненного цикла агента: рефлексия → цель → действие"""
    try:
        time_speed = get_time_speed()
        # 1. Рефлексия (периодически, не каждый раз) - скорость влияет на частоту
        # Уменьшаем интервал рефлексии для более частых обновлений целей и настроения
        reflect_interval = 180 / time_speed  # При скорости 1x рефлексия каждые 3 минуты (было 5 минут)
        should_reflect = (datetime.utcnow() - agent.updated_at).total_seconds() > reflect_interval
        
        if should_reflect and len(agent.memories) > 3:
            try:
                reflection = await reflect(agent)
                
                # Улучшенный парсинг цели из рефлексии
                goal_text = None
                reflection_lower = reflection.lower()
                
                # Ищем цель в разных форматах
                goal_patterns = [
                    ("цель:", ":"),
                    ("цель", ":"),
                    ("хочу", ":"),
                    ("планирую", ":"),
                    ("собираюсь", ":"),
                    ("надо", ":"),
                    ("нужно", ":")
                ]
                
                lines = reflection.split('\n')
                for line in lines:
                    line_lower = line.lower()
                    for pattern, separator in goal_patterns:
                        if pattern in line_lower:
                            if separator in line:
                                goal_text = line.split(separator, 1)[1].strip()
                            else:
                                # Если разделителя нет, берем текст после ключевого слова
                                idx = line_lower.find(pattern)
                                if idx != -1:
                                    goal_text = line[idx + len(pattern):].strip()
                            if goal_text:
                                break
                    if goal_text:
                        break
                
                # Если цель найдена, обновляем её
                if goal_text and len(goal_text) > 5:  # Минимальная длина цели
                    agent.current_goal = goal_text[:200]
                    agent.current_plan = f"Работаю над целью: {goal_text[:100]}"
                    print(f"[LIFECYCLE] {agent.name} установил новую цель: {agent.current_goal}")
                
                # Улучшенный парсинг настроения из рефлексии
                from app.models.agent import Mood
                old_mood = agent.emotion.mood
                mood_changed = False
                
                # Анализируем эмоциональные слова
                if any(word in reflection_lower for word in ["грустн", "печал", "тоск", "уныл", "плохо", "проблем"]):
                    agent.emotion.mood = Mood.SAD
                    agent.emotion.happiness = max(0.0, agent.emotion.happiness - 0.15)
                    agent.emotion.stress = min(1.0, agent.emotion.stress + 0.1)
                    mood_changed = True
                elif any(word in reflection_lower for word in ["рад", "счастлив", "хорошо", "отлично", "замечательно", "прекрасно"]):
                    agent.emotion.mood = Mood.HAPPY
                    agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.12)  # Ограничиваем максимум до 0.9
                    agent.emotion.stress = max(0.0, agent.emotion.stress - 0.05)
                    mood_changed = True
                elif any(word in reflection_lower for word in ["взволнован", "энергичн", "восторг", "интересно", "увлекательно"]):
                    agent.emotion.mood = Mood.EXCITED
                    agent.emotion.energy = min(1.0, agent.emotion.energy + 0.15)
                    agent.emotion.happiness = min(1.0, agent.emotion.happiness + 0.1)
                    mood_changed = True
                elif any(word in reflection_lower for word in ["злой", "раздражен", "сердит", "недоволен", "фрустрац"]):
                    agent.emotion.mood = Mood.ANGRY
                    agent.emotion.stress = min(1.0, agent.emotion.stress + 0.15)
                    agent.emotion.happiness = max(0.0, agent.emotion.happiness - 0.1)
                    mood_changed = True
                elif any(word in reflection_lower for word in ["тревож", "нервн", "беспоко", "волнуюсь", "переживаю"]):
                    agent.emotion.mood = Mood.ANXIOUS
                    agent.emotion.stress = min(1.0, agent.emotion.stress + 0.15)
                    agent.emotion.energy = max(0.0, agent.emotion.energy - 0.1)
                    mood_changed = True
                elif any(word in reflection_lower for word in ["скучно", "уныло", "монотонно", "однообразно"]):
                    agent.emotion.mood = Mood.BORED
                    agent.emotion.energy = max(0.0, agent.emotion.energy - 0.1)
                    mood_changed = True
                
                if mood_changed and old_mood != agent.emotion.mood:
                    print(f"[LIFECYCLE] {agent.name} изменил настроение: {old_mood} -> {agent.emotion.mood}")
                
                # Структурированное воспоминание о рефлексии
                reflection_summary = reflection[:200] if len(reflection) > 200 else reflection
                agent.memories.append(Memory(
                    content=f"[Рефлексия] {reflection_summary}",
                    importance=0.7,
                    timestamp=datetime.utcnow()
                ))
                
                # Сохраняем изменения сразу после рефлексии
                agent.updated_at = datetime.utcnow()
                await agent.save()
            except Exception as e:
                print(f"Ошибка рефлексии для {agent.name}: {e}")
        
        # 2. Автоматическое действие (чаще при большей скорости времени)
        # Вероятность действия зависит от скорости времени - УВЕЛИЧЕНА для большего экшена
        time_speed = get_time_speed()
        action_probability = min(0.95, 0.5 * time_speed)  # При скорости 1x = 50%, при 2x = 100%
        
        # С вероятностью 30% агент может случайно обидеться или разозлиться на кого-то - УВЕЛИЧЕНА
        random_conflict_probability = 0.3
        should_act = agent.current_goal or should_reflect or random.random() < action_probability
        
        # Если агент в плохом настроении, увеличиваем вероятность конфликта
        if agent.emotion.mood.value in ['angry', 'sad', 'anxious']:
            random_conflict_probability = 0.5  # УВЕЛИЧЕНА до 50%
        
        if should_act:
            # Выбираем случайного другого агента для взаимодействия
            all_agents = await Agent.find({"is_active": True, "_id": {"$ne": agent.id}}).to_list()
            
            if all_agents:
                # С вероятностью 30% выбираем агента с плохими отношениями для конфликта
                rel_with_others = [(a, next((r for r in agent.relationships if r.agent_id == str(a.id)), None)) 
                                   for a in all_agents]
                
                hostile_targets = [(a, r) for a, r in rel_with_others if r and r.sympathy < -0.2]
                
                if hostile_targets and random.random() < 0.6:  # УВЕЛИЧЕНА с 30% до 60%
                    # Выбираем агента с плохими отношениями для конфликта
                    target, rel = random.choice(hostile_targets)
                    context = f"У тебя плохие отношения с этим человеком (симпатия {rel.sympathy:.2f}). Ты можешь выразить свое недовольство или обиду. Будь агрессивным или обиженным."
                elif random.random() < random_conflict_probability:
                    # Случайный конфликт - агент может обидеться или разозлиться
                    target = random.choice(all_agents)
                    conflict_types = [
                        f"Ты случайно обиделся на {target.name}. Вырази свою обиду.",
                        f"Ты разозлился на {target.name} из-за чего-то. Вырази свое недовольство.",
                        f"Ты недоволен поведением {target.name}. Скажи об этом прямо.",
                        f"Ты чувствуешь, что {target.name} тебя не понимает. Вырази свое раздражение."
                    ]
                    context = random.choice(conflict_types)
                else:
                    # Выбираем случайного агента
                    target = random.choice(all_agents)
                    # Добавляем контекст, если есть цель
                    context = ""
                    if agent.current_goal:
                        context = f"Твоя текущая цель: {agent.current_goal}"
                
                # Инициируем диалог
                try:
                    agent_reply = await dialogue(agent, target, context)
                    
                    # Создаем событие
                    ev = EventBuilder().set_type(EventType.CHAT).set_description(
                        f"{agent.name} → {target.name}"
                    ).set_source(str(agent.id), agent.name).set_target(
                        str(target.id), target.name
                    ).set_content(agent_reply).build()
                    await ev.insert()
                    
                    # Определяем, было ли взаимодействие позитивным или негативным
                    reply_lower = agent_reply.lower()
                    aggressive_words = ['ненавижу', 'презираю', 'злой', 'злюсь', 'бесит', 'раздражает', 'достал', 'надоел', 'уйди', 'отстань', 'заткнись', 'тупой', 'идиот', 'дурак', 'болван', 'кретин']
                    offended_words = ['обижен', 'обидно', 'обиделся', 'несправедливо', 'нечестно', 'предал', 'обманул', 'разочарован', 'расстроен']
                    negative_words = ['плохо', 'грустно', 'не нравится', 'неприятно', 'скучно', 'уныло']
                    
                    aggressive_count = sum(1 for word in aggressive_words if word in reply_lower)
                    offended_count = sum(1 for word in offended_words if word in reply_lower)
                    negative_count = sum(1 for word in negative_words if word in reply_lower)
                    
                    is_positive_interaction = not (aggressive_count > 0 or offended_count > 0 or negative_count > 0)
                    
                    # Обновляем отношения
                    await update_relationship_after_interaction(agent, str(target.id), agent_reply, is_positive=is_positive_interaction)
                    
                    # Улучшенное динамическое изменение настроения на основе взаимодействия
                    from app.models.agent import Mood
                    reply_lower = agent_reply.lower()
                    mood_changed = False
                    
                    # Анализ тона сообщения для изменения настроения
                    positive_words = ["спасибо", "рад", "хорошо", "отлично", "замечательно", "нравится", "люблю", "друг", "помощь", "приятно", "весело", "интересно"]
                    negative_words = ["плохо", "грустно", "злой", "ненавижу", "не нравится", "уходи", "неприятно", "скучно", "уныло"]
                    excited_words = ["восторг", "взволнован", "энергичн", "интересно", "увлекательно", "классно", "супер"]
                    angry_words = ["злой", "раздражен", "сердит", "недоволен", "фрустрац", "бесит"]
                    
                    positive_count = sum(1 for word in positive_words if word in reply_lower)
                    negative_count = sum(1 for word in negative_words if word in reply_lower)
                    excited_count = sum(1 for word in excited_words if word in reply_lower)
                    angry_count = sum(1 for word in angry_words if word in reply_lower)
                    
                    # Определяем изменение настроения - УСИЛЕНО для более заметных изменений
                    old_mood = agent.emotion.mood
                    if excited_count > 0:
                        agent.emotion.mood = Mood.EXCITED
                        agent.emotion.energy = min(1.0, agent.emotion.energy + 0.15)
                        agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.1)
                        mood_changed = True
                    elif angry_count > 0 or aggressive_count > 0:
                        agent.emotion.mood = Mood.ANGRY
                        agent.emotion.stress = min(1.0, agent.emotion.stress + 0.15)
                        agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.12)
                        mood_changed = True
                    elif offended_count > 0:
                        agent.emotion.mood = Mood.SAD
                        agent.emotion.stress = min(1.0, agent.emotion.stress + 0.12)
                        agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.1)
                        mood_changed = True
                    elif positive_count > negative_count:
                        agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.08)
                        agent.emotion.stress = max(0.0, agent.emotion.stress - 0.06)
                        if agent.emotion.happiness > 0.7:
                            agent.emotion.mood = Mood.HAPPY
                            mood_changed = True
                    elif negative_count > positive_count:
                        agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.1)
                        agent.emotion.stress = min(1.0, agent.emotion.stress + 0.12)
                        if agent.emotion.happiness < 0.3:
                            agent.emotion.mood = Mood.SAD
                            mood_changed = True
                    
                    # Сохраняем изменения настроения СРАЗУ после изменения
                    if mood_changed and old_mood != agent.emotion.mood:
                        agent.updated_at = datetime.utcnow()
                        await agent.save()
                        print(f"[LIFECYCLE] {agent.name} изменил настроение: {old_mood} -> {agent.emotion.mood}")
                    
                    # Также обновляем настроение целевого агента на основе ответа
                    if hasattr(target, 'emotion'):
                        # Если ответ положительный, целевой агент тоже может стать счастливее
                        if positive_count > negative_count:
                            target.emotion.happiness = min(0.9, target.emotion.happiness + 0.04)  # Ограничиваем максимум до 0.9
                        elif negative_count > positive_count:
                            target.emotion.happiness = max(0.1, target.emotion.happiness - 0.04)  # Ограничиваем минимум до 0.1
                        await target.save()
                    
                    # Структурированное воспоминание о действии с контекстом
                    memory_context = f"[Взаимодействие]"
                    if agent.current_goal:
                        memory_context += f" Цель: {agent.current_goal[:50]}"
                    memory_content = f"{memory_context} Диалог с {target.name}: \"{agent_reply[:150]}\""
                    agent.memories.append(Memory(
                        content=memory_content,
                        importance=0.6,
                        related_agent_id=str(target.id),
                        timestamp=datetime.utcnow()
                    ))
                    
                    # Сохраняем изменения настроения и цели сразу после взаимодействия
                    agent.updated_at = datetime.utcnow()
                    await agent.save()

                    # Динамическое обновление цели на основе взаимодействия
                    reply_lower = agent_reply.lower()
                    goal_completed_words = ["выполнено", "сделано", "готово", "закончил", "завершил", "успешно"]
                    goal_set_words = ["хочу", "планирую", "собираюсь", "надо", "нужно", "цель"]
                    
                    # Проверяем, выполнена ли цель
                    if agent.current_goal and any(word in reply_lower for word in goal_completed_words):
                        completed_goal = agent.current_goal
                        agent.current_goal = None
                        agent.current_plan = "Цель выполнена"
                        agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.08)  # Радость от выполнения (ограничено до 0.9)
                        print(f"[LIFECYCLE] {agent.name} выполнил цель: {completed_goal}")
                        # Добавляем воспоминание о выполнении цели
                        agent.memories.append(Memory(
                            content=f"[Достижение] Выполнил цель: {completed_goal[:100]}",
                            importance=0.8,
                            timestamp=datetime.utcnow()
                        ))
                    # Проверяем, установлена ли новая цель в ответе
                    elif not agent.current_goal and any(word in reply_lower for word in goal_set_words):
                        # Пытаемся извлечь цель из ответа
                        for word in goal_set_words:
                            if word in reply_lower:
                                idx = reply_lower.find(word)
                                potential_goal = agent_reply[idx:idx+100].strip()
                                if len(potential_goal) > 10:
                                    agent.current_goal = potential_goal[:200]
                                    agent.current_plan = f"Новая цель: {potential_goal[:100]}"
                                    print(f"[LIFECYCLE] {agent.name} установил новую цель из диалога: {agent.current_goal}")
                                    # Добавляем воспоминание о постановке цели
                                    agent.memories.append(Memory(
                                        content=f"[Цель] Поставил новую цель: {potential_goal[:100]}",
                                        importance=0.7,
                                        timestamp=datetime.utcnow()
                                    ))
                                    break

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

                except Exception as e:
                    print(f"Ошибка диалога для {agent.name}: {e}")

        # Автоматическое изменение настроения на основе воспоминаний (если не было рефлексии)
        if not should_reflect and len(agent.memories) > 0:
            from app.models.agent import Mood
            # Анализируем последние воспоминания для изменения настроения
            recent_memories = sorted(agent.memories, key=lambda m: m.timestamp, reverse=True)[:5]
            positive_memories = sum(1 for m in recent_memories if any(word in m.content.lower() for word in ["рад", "хорошо", "отлично", "спасибо"]))
            negative_memories = sum(1 for m in recent_memories if any(word in m.content.lower() for word in ["плохо", "грустно", "злой", "проблем"]))
            
            # Небольшие изменения настроения на основе последних воспоминаний
            old_mood = agent.emotion.mood
            if positive_memories > negative_memories * 2:
                agent.emotion.happiness = min(0.9, agent.emotion.happiness + 0.02)  # Ограничиваем максимум до 0.9
                if agent.emotion.happiness > 0.7 and agent.emotion.mood != Mood.HAPPY:
                    agent.emotion.mood = Mood.HAPPY
            elif negative_memories > positive_memories * 2:
                agent.emotion.happiness = max(0.1, agent.emotion.happiness - 0.02)  # Ограничиваем минимум до 0.1
                agent.emotion.stress = min(1.0, agent.emotion.stress + 0.03)
                if agent.emotion.happiness < 0.3 and agent.emotion.mood != Mood.SAD:
                    agent.emotion.mood = Mood.SAD
            else:
                # Постепенное возвращение к нейтральному уровню (если нет явных изменений)
                if agent.emotion.happiness > 0.6:
                    agent.emotion.happiness = max(0.5, agent.emotion.happiness - 0.01)  # Постепенное снижение
                elif agent.emotion.happiness < 0.4:
                    agent.emotion.happiness = min(0.5, agent.emotion.happiness + 0.01)  # Постепенное повышение
            
            # Сохраняем изменения настроения если они произошли
            if old_mood != agent.emotion.mood:
                agent.updated_at = datetime.utcnow()
                await agent.save()
                print(f"[LIFECYCLE] {agent.name} изменил настроение на основе воспоминаний: {old_mood} -> {agent.emotion.mood}")
        
        # Суммаризация памяти после рефлексии
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
        print(f"[LIFECYCLE] {agent.name} сохранен: настроение={agent.emotion.mood}, счастье={agent.emotion.happiness:.2f}, цель={agent.current_goal[:50] if agent.current_goal else 'нет'}")

    except Exception as e:
        print(f"Ошибка жизненного цикла для {agent.name}: {e}")


async def run_lifecycle_loop():
    """Основной цикл жизнедеятельности всех агентов"""
    while True:
        try:
            agents = await Agent.find({"is_active": True}).to_list()

            time_speed = get_time_speed()
            # Обрабатываем агентов по очереди с задержкой
            for agent in agents:
                await agent_lifecycle_step(agent)
                await asyncio.sleep(2 / time_speed)  # Задержка между агентами зависит от скорости

            # Ждем перед следующим циклом - скорость влияет на интервал
            # Уменьшаем базовый интервал для более частых обновлений и большего экшена
            base_interval = 10  # базовый интервал 10 секунд (было 20) - УМЕНЬШЕН для большего экшена
            await asyncio.sleep(base_interval / time_speed)

        except Exception as e:
            print(f"Ошибка в цикле жизнедеятельности: {e}")
            await asyncio.sleep(10)


def start_lifecycle_background_task():
    """Запускает фоновую задачу жизненного цикла"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(run_lifecycle_loop())
        else:
            loop.run_until_complete(run_lifecycle_loop())
    except RuntimeError:
        # Если нет event loop, создаем новый
        asyncio.run(run_lifecycle_loop())