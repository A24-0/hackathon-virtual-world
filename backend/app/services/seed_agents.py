"""
Скрипт для создания базовых агентов при первом запуске
"""
from app.models.agent import Agent, Mood
from app.services.builder import AgentBuilder


async def seed_initial_agents():
    """Создает базовых агентов, если их еще нет"""
    try:
        existing_count = await Agent.count()
        print(f"[SEED] Проверка агентов: найдено {existing_count}")
        
        if existing_count > 0:
            print(f"[SEED] Найдено {existing_count} агентов. Пропускаем создание базовых агентов.")
            return
        
        print("[SEED] Создание базовых агентов...")
        
        # Агент 1: Алекс - исследователь
        alex = (AgentBuilder()
            .set_name("Алекс")
            .set_bio("Любознательный исследователь, который любит изучать новое и открывать неизведанное. Всегда в поиске приключений и интересных открытий.")
            .set_avatar("A")
            .set_personality(openness=0.9, conscientiousness=0.7, extraversion=0.8, agreeableness=0.7, neuroticism=0.3)
            .set_mood(Mood.HAPPY, energy=0.8, stress=0.2, happiness=0.6)
            .set_system_prompt("Ты любознательный и энергичный исследователь. Ты всегда ищешь что-то новое и интересное.")
            .build())
        await alex.insert()
        print(f"[SEED] Создан агент: {alex.name}")
        
        # Агент 2: Мария - художник
        maria = (AgentBuilder()
            .set_name("Мария")
            .set_bio("Творческая художница, которая видит красоту во всем. Любит создавать произведения искусства и делиться своими эмоциями через творчество.")
            .set_avatar("M")
            .set_personality(openness=0.95, conscientiousness=0.6, extraversion=0.6, agreeableness=0.9, neuroticism=0.4)
            .set_mood(Mood.EXCITED, energy=0.7, stress=0.3, happiness=0.65)
            .set_system_prompt("Ты творческая и эмпатичная художница. Ты видишь красоту в простых вещах и выражаешь эмоции через искусство.")
            .build())
        await maria.insert()
        print(f"[SEED] Создан агент: {maria.name}")
        
        # Агент 3: Роберт - ученый
        robert = (AgentBuilder()
            .set_name("Роберт")
            .set_bio("Логичный и аналитичный ученый, который анализирует все вокруг. Любит систематизировать информацию и находить закономерности.")
            .set_avatar("R")
            .set_personality(openness=0.7, conscientiousness=0.95, extraversion=0.4, agreeableness=0.6, neuroticism=0.3)
            .set_mood(Mood.NEUTRAL, energy=0.6, stress=0.2, happiness=0.5)
            .set_system_prompt("Ты логичный и методичный ученый. Ты анализируешь все вокруг и ищешь закономерности.")
            .build())
        await robert.insert()
        print(f"[SEED] Создан агент: {robert.name}")
        
        print(f"[SEED] ✓ Успешно создано 3 базовых агента!")
    except Exception as e:
        print(f"[SEED] ОШИБКА при создании базовых агентов: {e}")
        import traceback
        traceback.print_exc()
