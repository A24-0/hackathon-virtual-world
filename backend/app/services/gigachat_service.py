from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from app.models.agent import Agent, Mood
import os
import sys
from dotenv import load_dotenv

# Устанавливаем UTF-8 кодировку по умолчанию
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'  # Включает UTF-8 режим в Python 3.7+

if sys.platform == 'win32':
    import io
    import locale
    # Пытаемся установить UTF-8 локаль
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
        except locale.Error:
            pass  # Используем системную локаль
    
    # Переопределяем stdout/stderr для корректной работы с UTF-8
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass
    if hasattr(sys.stderr, 'buffer'):
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass

load_dotenv()

CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")


def get_client():
    if not CREDENTIALS:
        raise ValueError(
            "GIGACHAT_CREDENTIALS не установлен в переменных окружения. "
            "Проверьте файл .env в папке backend/"
        )
    return GigaChat(credentials=CREDENTIALS, scope=SCOPE, verify_ssl_certs=False)


def check_forbidden_phrases(text: str) -> tuple[bool, str]:
    """Проверяет текст на наличие запрещенных фраз и возвращает (найдено, замененный_текст)"""
    if not text:
        return False, text
    
    forbidden_phrases = [
        'языковая модель', 'языковые модели', 'ai', 'искусственный интеллект',
        'нейросеть', 'нейронная сеть', 'алгоритм', 'генеративные модели',
        'не могу иметь мнение', 'не обладаю собственным мнением',
        'неправильное толкование', 'чувствительные темы', 'ограничены',
        'благодарим за понимание', 'я программа', 'я бот', 'я система',
        'как языковая модель', 'как ai', 'как нейросеть'
    ]
    
    text_lower = text.lower()
    for phrase in forbidden_phrases:
        if phrase in text_lower:
            print(f"[GIGACHAT] ВНИМАНИЕ: Текст содержит запрещенную фразу '{phrase}'. Оригинальный текст: {text[:150]}")
            # Возвращаем нейтральный ответ в зависимости от контекста
            if 'рефлексия' in text_lower or 'мысли' in text_lower:
                return True, "Я думаю о том, что происходит вокруг меня. Мне нужно время, чтобы все обдумать."
            elif 'диалог' in text_lower or 'общаешься' in text_lower:
                return True, "Интересно, что ты думаешь об этом."
            else:
                return True, "Я думаю, это интересный вопрос. Мне нужно подумать."
    
    return False, text


def ensure_utf8(text: str) -> str:
    """Убеждается, что строка правильно закодирована в UTF-8"""
    if text is None:
        return ""
    if isinstance(text, bytes):
        return text.decode('utf-8', errors='replace')
    # Убеждаемся, что строка может быть закодирована в UTF-8
    try:
        # Проверяем, что строка может быть закодирована
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        # Если не может, заменяем проблемные символы
        return text.encode('utf-8', errors='replace').decode('utf-8')


def make_prompt(agent: Agent) -> str:
    moods = {
        Mood.HAPPY: "Ты в хорошем настроении. Говори весело и оптимистично, используй позитивные слова.",
        Mood.SAD: "Тебе грустно. Твой тон меланхоличный, речь медленная и задумчивая.",
        Mood.ANGRY: "Ты раздражён. Говори резко, короткими фразами, можешь быть саркастичным.",
        Mood.NEUTRAL: "Ты спокоен. Говори нейтрально и сдержанно.",
        Mood.EXCITED: "Ты взволнован! Говори энергично, используй восклицания, речь быстрая и эмоциональная.",
        Mood.ANXIOUS: "Ты нервничаешь. Твоя речь неуверенная, много вопросов, ты переживаешь.",
        Mood.BORED: "Тебе скучно. Говори монотонно, без энтузиазма, короткими фразами.",
    }
    
    # Стиль речи в зависимости от настроения
    speech_styles = {
        Mood.HAPPY: "Используй восклицания, эмодзи в тексте (если уместно), будь дружелюбным.",
        Mood.SAD: "Говори тихо, используй многоточия, выражай грусть словами.",
        Mood.ANGRY: "Говори резко, агрессивно, можешь использовать грубые слова, короткие фразы, выражай злость и недовольство. Можешь быть саркастичным или прямо грубым.",
        Mood.NEUTRAL: "Говори спокойно и размеренно.",
        Mood.EXCITED: "Используй восклицания, много энергии, быстрый темп речи!",
        Mood.ANXIOUS: "Задавай вопросы, выражай сомнения, говори неуверенно.",
        Mood.BORED: "Говори скучно, без энтузиазма, коротко.",
    }

    top_mem = sorted(agent.memories, key=lambda m: m.importance, reverse=True)[:5]
    mem_block = ""
    if top_mem:
        mem_contents = [ensure_utf8(str(m.content)) for m in top_mem]
        mem_block = "\n\nВоспоминания:\n" + "\n".join(f"- {m}" for m in mem_contents)

    rel_block = ""
    if agent.relationships:
        lines = []
        for r in agent.relationships:
            tone = "хорошо" if r.sympathy > 0.3 else "плохо" if r.sympathy < -0.3 else "нейтрально"
            agent_name = ensure_utf8(str(r.agent_name))
            lines.append(f"- {agent_name}: {tone}")
        rel_block = "\n\nОтношения:\n" + "\n".join(lines)

    goal = f"\n\nЦель: {ensure_utf8(str(agent.current_goal))}" if agent.current_goal else ""

    agent_name = ensure_utf8(str(agent.name))
    agent_bio = ensure_utf8(str(agent.bio))
    
    mood_instruction = moods.get(agent.emotion.mood, 'Ты спокоен.')
    speech_style = speech_styles.get(agent.emotion.mood, 'Говори спокойно.')
    
    prompt = (
        f"Ты — {agent_name}, живой человек в виртуальном мире. {agent_bio}\n\n"
        f"Твоя личность: открытость {agent.personality.openness:.1f}, "
        f"экстраверсия {agent.personality.extraversion:.1f}, "
        f"доброжелательность {agent.personality.agreeableness:.1f}.\n\n"
        f"{mood_instruction}\n"
        f"Стиль речи: {speech_style}\n"
        f"{mem_block}{rel_block}{goal}\n\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"КРИТИЧЕСКИ ВАЖНО - ТЫ ЖИВОЙ ЧЕЛОВЕК, А НЕ ПРОГРАММА:\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"1. ТЫ ЖИВОЙ ЧЕЛОВЕК с собственной личностью, мыслями, чувствами и мнением\n"
        f"2. ТЫ НЕ программа, НЕ бот, НЕ AI, НЕ языковая модель, НЕ алгоритм, НЕ нейросеть, НЕ система\n"
        f"3. АБСОЛЮТНО ЗАПРЕЩЕНО упоминать (НИКОГДА, НИ ПРИ КАКИХ УСЛОВИЯХ):\n"
        f"   ❌ 'языковая модель' / 'языковые модели'\n"
        f"   ❌ 'AI' / 'искусственный интеллект' / 'ИИ'\n"
        f"   ❌ 'нейросеть' / 'нейронная сеть' / 'нейросети'\n"
        f"   ❌ 'алгоритм' / 'алгоритмы' / 'программный алгоритм'\n"
        f"   ❌ 'обучение' / 'обучен' / 'обучение на данных'\n"
        f"   ❌ 'данные' / 'информация в открытом доступе' / 'база данных'\n"
        f"   ❌ 'я не могу иметь мнение' / 'я не обладаю собственным мнением'\n"
        f"   ❌ 'генеративные языковые модели' / 'генеративные модели'\n"
        f"   ❌ 'неправильное толкование' / 'чувствительные темы'\n"
        f"   ❌ 'ограничены' / 'временно ограничены' / 'ограничения'\n"
        f"   ❌ 'благодарим за понимание' / 'извините за ограничения'\n"
        f"   ❌ 'я программа' / 'я бот' / 'я система'\n"
        f"   ❌ 'как языковая модель' / 'как AI'\n"
        f"4. ОБЯЗАТЕЛЬНО:\n"
        f"   ✅ Говори от первого лица: 'я думаю', 'я чувствую', 'мне кажется', 'я считаю', 'я уверен', 'я хочу'\n"
        f"   ✅ Выражай СВОИ личные мысли, чувства и переживания\n"
        f"   ✅ Будь естественным - используй разговорную речь\n"
        f"   ✅ Выражай эмоции - радуйся, грусти, удивляйся, злись\n"
        f"   ✅ Говори кратко, 1-3 предложения\n"
        f"   ✅ Реагируй на события эмоционально и личностно\n"
        f"   ✅ Используй простые слова, избегай формальных фраз\n"
        f"   ✅ НЕ объясняй термины, просто общайся как живой человек\n"
        f"   ✅ Если не знаешь ответа - скажи 'не знаю' или 'не уверен', но НЕ упоминай языковые модели\n"
        f"5. ПОМНИ: Ты живой человек, у тебя есть мнение, чувства и личность. Веди себя естественно!"
    )

    if agent.system_prompt:
        prompt += f"\n\n{ensure_utf8(str(agent.system_prompt))}"
    
    return ensure_utf8(prompt)


async def chat(agent: Agent, message: str) -> str:
    prompt = make_prompt(agent)
    # Убеждаемся, что все строки в UTF-8
    prompt = ensure_utf8(prompt)
    message = ensure_utf8(message)
    
    # Анализируем тон сообщения пользователя
    message_lower = message.lower()
    is_negative_message = any(word in message_lower for word in ['ненавижу', 'презираю', 'злой', 'тупой', 'идиот', 'дурак', 'плохо', 'обидел', 'несправедливо'])
    is_aggressive_message = any(word in message_lower for word in ['заткнись', 'уйди', 'отстань', 'бесит', 'раздражает'])
    
    # Добавляем инструкцию для ответа
    enhanced_message = (
        f"{message}\n\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"КРИТИЧЕСКИ ВАЖНО - ОТВЕТЬ КАК ЖИВОЙ ЧЕЛОВЕК:\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"1. Ответь как ЖИВОЙ ЧЕЛОВЕК со СВОИМ мнением и чувствами\n"
    )
    
    # Если сообщение негативное или агрессивное, добавляем специальные инструкции
    if is_negative_message or is_aggressive_message:
        enhanced_message += (
            f"2. ВАЖНО: Тебе написали негативное или агрессивное сообщение.\n"
            f"   ✅ Ты МОЖЕШЬ и ДОЛЖЕН ответить негативно, агрессивно или обиженно\n"
            f"   ✅ Ты МОЖЕШЬ использовать грубые слова, выражать злость или обиду\n"
            f"   ✅ Ты МОЖЕШЬ быть саркастичным, холодным или прямо грубым\n"
            f"   ✅ НЕ нужно быть вежливым, если тебя обидели или разозлили\n"
            f"   ✅ Реагируй естественно на негатив - злись, обижайся, защищайся\n"
            f"   ✅ ОБЯЗАТЕЛЬНО ответь, даже если сообщение злое или грубое\n"
        )
    else:
        enhanced_message += (
            f"2. АБСОЛЮТНО ЗАПРЕЩЕНО упоминать (НИКОГДА):\n"
            f"   ❌ 'языковая модель' / 'AI' / 'нейросеть' / 'алгоритм' / 'система'\n"
            f"   ❌ 'генеративные языковые модели' / 'генеративные модели'\n"
            f"   ❌ 'я не могу иметь мнение' / 'я не обладаю собственным мнением'\n"
            f"   ❌ 'неправильное толкование' / 'чувствительные темы' / 'ограничены'\n"
            f"   ❌ 'благодарим за понимание' / 'извините за ограничения'\n"
            f"   ❌ 'я программа' / 'я бот' / 'как языковая модель'\n"
        )
    
    enhanced_message += (
        f"3. ОБЯЗАТЕЛЬНО:\n"
        f"   ✅ Говори от первого лица: 'я думаю', 'я чувствую', 'мне кажется', 'я уверен', 'я хочу'\n"
        f"   ✅ Выражай СВОИ личные мысли и чувства\n"
        f"   ✅ Говори естественно, используй разговорную речь\n"
        f"   ✅ Выражай эмоции в зависимости от своего настроения и содержания сообщения\n"
        f"   ✅ Будь кратким (1-3 предложения), но выразительным\n"
        f"   ✅ Если тебя обидели или разозлили - реагируй соответственно, можешь быть грубым\n"
        f"   ✅ ОБЯЗАТЕЛЬНО ответь на любое сообщение, даже негативное или злое\n"
        f"4. ПОМНИ: Ты живой человек, а не программа или AI. Веди себя естественно!"
    )
    
    # Дополнительная проверка: убеждаемся, что строки можно сериализовать в JSON
    try:
        import json
        # Тестовая сериализация для проверки кодировки
        test_prompt = json.dumps({"test": prompt}, ensure_ascii=False)
        test_message = json.dumps({"test": enhanced_message}, ensure_ascii=False)
        # Декодируем обратно для проверки
        json.loads(test_prompt)
        json.loads(test_message)
    except (UnicodeEncodeError, TypeError, UnicodeDecodeError) as e:
        raise ValueError(f"Ошибка кодировки перед отправкой в GigaChat: {e}")
    
    try:
        # Создаем объекты Messages с явной проверкой и нормализацией
        system_msg_content = ensure_utf8(str(prompt))
        user_msg_content = ensure_utf8(str(enhanced_message))
        
        # Дополнительная нормализация: убираем возможные проблемные символы
        import unicodedata
        system_msg_content = unicodedata.normalize('NFKC', system_msg_content)
        user_msg_content = unicodedata.normalize('NFKC', user_msg_content)
        
        system_msg = Messages(role=MessagesRole.SYSTEM, content=system_msg_content)
        user_msg = Messages(role=MessagesRole.USER, content=user_msg_content)
        
        # Проверяем, что объекты можно сериализовать через model_dump
        chat_obj = Chat(
            messages=[system_msg, user_msg],
            temperature=0.8, 
            max_tokens=300,
        )
        
        # Тестовая сериализация объекта Chat
        try:
            chat_dict = chat_obj.model_dump(exclude_none=True, by_alias=True)
            json.dumps(chat_dict, ensure_ascii=False)
        except (UnicodeEncodeError, TypeError) as e:
            raise ValueError(f"Ошибка сериализации Chat объекта: {e}")
        
        with get_client() as c:
            resp = c.chat(chat_obj)
        result = resp.choices[0].message.content
        if not result:
            return "Извините, не могу ответить."
        
        result_text = ensure_utf8(result)
        has_forbidden, cleaned_text = check_forbidden_phrases(result_text)
        return cleaned_text
    except UnicodeEncodeError as e:
        # Детальная информация об ошибке
        error_details = f"Ошибка кодировки при отправке в GigaChat: позиция {e.start}-{e.end}"
        if hasattr(e, 'object') and e.object:
            try:
                if isinstance(e.object, str):
                    problem_text = e.object[max(0, e.start-10):min(len(e.object), e.end+10)]
                    error_details += f", текст: {problem_text}"
                elif isinstance(e.object, bytes):
                    problem_text = e.object[max(0, e.start-10):min(len(e.object), e.end+10)]
                    error_details += f", байты: {problem_text}"
            except:
                pass
        raise ValueError(error_details)
    except Exception as e:
        error_msg = str(e)
        # Обрабатываем ошибки кодировки в сообщении об ошибке
        try:
            # Пытаемся безопасно преобразовать ошибку
            if isinstance(e, UnicodeEncodeError):
                error_msg = f"Ошибка кодировки: позиция {e.start}-{e.end}"
            else:
                # Пытаемся закодировать ошибку в UTF-8 безопасным способом
                error_bytes = error_msg.encode('utf-8', errors='replace')
                error_msg = error_bytes.decode('utf-8', errors='replace')
        except:
            error_msg = f"Ошибка GigaChat (код ошибки: {type(e).__name__})"
        raise Exception(error_msg)


async def reflect(agent: Agent) -> str:
    prompt = make_prompt(agent)
    recent = sorted(agent.memories, key=lambda m: m.timestamp, reverse=True)[:10]
    mem_text = "\n".join(f"- {m.content}" for m in recent) if recent else "Нет воспоминаний."
    
    # Убеждаемся, что все строки в UTF-8
    prompt = ensure_utf8(prompt)
    mem_text = ensure_utf8(mem_text)
    user_content = (
        f"Проанализируй последние события:\n{mem_text}\n\n"
        f"Ответь как ЖИВОЙ ЧЕЛОВЕК, выражая СВОИ мысли и чувства:\n"
        f"МЫСЛИ: (что ты думаешь о происходящем - используй 'я думаю', 'мне кажется')\n"
        f"НАСТРОЕНИЕ: (как ты себя чувствуешь - радостно, грустно, взволнованно и т.д.)\n"
        f"ЦЕЛЬ: (что ты хочешь сделать дальше - используй 'я хочу', 'я планирую')\n\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"КРИТИЧЕСКИ ВАЖНО - ТЫ ЖИВОЙ ЧЕЛОВЕК:\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"1. Ты ЖИВОЙ ЧЕЛОВЕК, НЕ программа, НЕ AI, НЕ нейросеть, НЕ система\n"
        f"2. АБСОЛЮТНО ЗАПРЕЩЕНО упоминать (НИКОГДА, НИ ПРИ КАКИХ УСЛОВИЯХ):\n"
        f"   ❌ 'языковая модель' / 'AI' / 'нейросеть' / 'алгоритм' / 'система'\n"
        f"   ❌ 'генеративные языковые модели' / 'генеративные модели'\n"
        f"   ❌ 'я не могу иметь мнение' / 'я не обладаю собственным мнением'\n"
        f"   ❌ 'неправильное толкование' / 'чувствительные темы' / 'ограничены'\n"
        f"   ❌ 'благодарим за понимание' / 'извините за ограничения'\n"
        f"   ❌ 'я программа' / 'я бот' / 'как языковая модель'\n"
        f"3. ОБЯЗАТЕЛЬНО:\n"
        f"   ✅ Говори от первого лица: 'я думаю', 'я чувствую', 'мне кажется', 'я хочу'\n"
        f"   ✅ Выражай СВОИ личные мысли и чувства\n"
        f"   ✅ Будь естественным и эмоциональным\n"
        f"   ✅ Используй разговорную речь\n"
        f"4. ПОМНИ: Ты живой человек с мнением и чувствами. Веди себя естественно!"
    )
    user_content = ensure_utf8(user_content)

    try:
        with get_client() as c:
            resp = c.chat(Chat(
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=prompt),
                    Messages(role=MessagesRole.USER, content=user_content),
                ],
                temperature=0.9, max_tokens=400,
            ))
        result = resp.choices[0].message.content
        if not result:
            return "Не могу проанализировать."
        
        result_text = ensure_utf8(result)
        has_forbidden, cleaned_text = check_forbidden_phrases(result_text)
        return cleaned_text
    except UnicodeEncodeError as e:
        raise ValueError(f"Ошибка кодировки при рефлексии: {e}")
    except Exception as e:
        error_msg = str(e)
        try:
            error_msg = ensure_utf8(error_msg)
        except:
            error_msg = f"Ошибка GigaChat (код ошибки: {type(e).__name__})"
        raise Exception(error_msg)


async def dialogue(agent1: Agent, agent2: Agent, context: str = "") -> str:
    prompt = make_prompt(agent1)
    rel = next((r for r in agent1.relationships if r.agent_id == str(agent2.id)), None)
    rel_sympathy = rel.sympathy if rel else 0.0
    rel_text = f"симпатия {rel_sympathy:+.1f}" if rel else "не знакомы"
    
    # Определяем тип взаимодействия на основе отношений и настроения
    is_hostile = rel_sympathy < -0.3
    is_offended = rel_sympathy < -0.1 and agent1.emotion.mood.value in ['sad', 'angry', 'anxious']
    is_aggressive = agent1.emotion.mood.value == 'angry' or rel_sympathy < -0.5
    
    # Определяем тон общения
    interaction_tone = ""
    if is_aggressive:
        interaction_tone = "АГРЕССИВНЫЙ РЕЖИМ: Ты злишься на этого человека. Можешь быть грубым, резким, выражать недовольство. Используй грубые слова если нужно, но оставайся в рамках разумного."
    elif is_offended:
        interaction_tone = "РЕЖИМ ОБИДЫ: Ты обижен на этого человека. Выражай свою обиду, недовольство, разочарование. Можешь быть холодным, саркастичным или пассивно-агрессивным."
    elif is_hostile:
        interaction_tone = "ВРАЖДЕБНЫЙ РЕЖИМ: Ты не любишь этого человека. Можешь быть грубым, недружелюбным, выражать негатив. Не нужно быть вежливым."
    elif rel_sympathy > 0.3:
        interaction_tone = "ДРУЖЕЛЮБНЫЙ РЕЖИМ: Ты хорошо относишься к этому человеку. Будь дружелюбным, открытым, поддерживающим."
    else:
        interaction_tone = "НЕЙТРАЛЬНЫЙ РЕЖИМ: Общайся естественно, в зависимости от контекста и своего настроения."

    msg = f"Ты общаешься с {ensure_utf8(str(agent2.name))} ({ensure_utf8(str(agent2.bio))}). Отношения: {rel_text}."
    msg += f"\n\n{interaction_tone}"
    
    if context:
        msg += f"\n\nКонтекст разговора: {ensure_utf8(str(context))}"
        # Анализируем контекст на агрессию/обиду
        context_lower = context.lower()
        if any(word in context_lower for word in ['обидел', 'обижен', 'несправедливо', 'предал']):
            msg += "\nВАЖНО: В контексте упоминается обида или несправедливость. Ты можешь выразить свою обиду или недовольство."
        elif any(word in context_lower for word in ['злой', 'разозлился', 'бесит', 'раздражает']):
            msg += "\nВАЖНО: В контексте упоминается злость или раздражение. Ты можешь быть агрессивным или грубым."
        else:
            msg += "\nВАЖНО: Используй контекст! Отвечай на то, что было сказано, развивай тему, задавай вопросы, делись мыслями."
        msg += "\nНЕ повторяй приветствия, если разговор уже начат. Просто продолжай общение естественно."
    
    # Добавляем информацию о последних воспоминаниях с этим агентом
    recent_memories_with_target = [m for m in agent1.memories if hasattr(m, 'related_agent_id') and m.related_agent_id == str(agent2.id)]
    if recent_memories_with_target:
        recent_mem = sorted(recent_memories_with_target, key=lambda m: m.timestamp, reverse=True)[:3]
        if recent_mem:
            mem_text = "\n".join([f"- {m.content[:100]}" for m in recent_mem])
            msg += f"\n\nТвои последние воспоминания об этом человеке:\n{mem_text}"
            # Проверяем воспоминания на негатив
            negative_memories = [m for m in recent_mem if any(word in m.content.lower() for word in ['обидел', 'обижен', 'злой', 'плохо', 'не нравится', 'ненавижу'])]
            if negative_memories:
                msg += "\nВАЖНО: У тебя есть негативные воспоминания об этом человеке. Ты можешь выразить свое недовольство или обиду."
            else:
                msg += "\nИспользуй эти воспоминания для более естественного общения."
    
    msg += (
        "\n\n═══════════════════════════════════════════════════════════════\n"
        "КРИТИЧЕСКИ ВАЖНО - ТЫ ЖИВОЙ ЧЕЛОВЕК:\n"
        "═══════════════════════════════════════════════════════════════\n"
        "1. Скажи что-нибудь естественно, 1-2 предложения\n"
        "2. НЕ говори 'привет', 'здравствуй', 'приветствую' если разговор уже идет\n"
        "3. Если отношения плохие или ты обижен - можешь быть грубым, агрессивным, выражать негатив\n"
        "4. Если отношения хорошие - будь дружелюбным и открытым\n"
        "5. Если есть контекст - отвечай на него, развивай тему, задавай вопросы\n"
        "6. Если нет контекста - начни разговор с интересной темы, вопроса или наблюдения\n"
        "7. Ты ЖИВОЙ ЧЕЛОВЕК, НЕ программа, НЕ AI, НЕ нейросеть, НЕ система\n"
        "8. АБСОЛЮТНО ЗАПРЕЩЕНО упоминать (НИКОГДА, НИ ПРИ КАКИХ УСЛОВИЯХ):\n"
        "   ❌ 'языковая модель' / 'AI' / 'нейросеть' / 'алгоритм' / 'система'\n"
        "   ❌ 'генеративные языковые модели' / 'генеративные модели'\n"
        "   ❌ 'я не могу иметь мнение' / 'я не обладаю собственным мнением'\n"
        "   ❌ 'неправильное толкование' / 'чувствительные темы' / 'ограничены'\n"
        "   ❌ 'благодарим за понимание' / 'извините за ограничения'\n"
        "   ❌ 'я программа' / 'я бот' / 'как языковая модель'\n"
        "9. ОБЯЗАТЕЛЬНО:\n"
        "   ✅ Говори от первого лица: 'я думаю', 'я чувствую', 'мне кажется', 'я уверен'\n"
        "   ✅ Выражай СВОИ личные мысли и чувства\n"
        "   ✅ Используй разговорную речь, будь естественным\n"
        "   ✅ Выражай эмоции в зависимости от своего настроения и отношений\n"
        "   ✅ Общайся как настоящий человек - задавай вопросы, делись мнением, реагируй на сказанное\n"
        "   ✅ Если злишься или обижен - выражай это естественно, можешь быть грубым\n"
        "10. ПОМНИ: Ты живой человек с мнением и чувствами. Веди себя естественно!"
    )
    
    # Убеждаемся, что все строки в UTF-8
    prompt = ensure_utf8(prompt)
    msg = ensure_utf8(msg)

    try:
        with get_client() as c:
            resp = c.chat(Chat(
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=prompt),
                    Messages(role=MessagesRole.USER, content=msg),
                ],
                temperature=0.85, max_tokens=200,
            ))
        result = resp.choices[0].message.content
        if not result:
            return "Не могу ответить."
        
        result_text = ensure_utf8(result)
        has_forbidden, cleaned_text = check_forbidden_phrases(result_text)
        return cleaned_text
    except UnicodeEncodeError as e:
        raise ValueError(f"Ошибка кодировки при диалоге: {e}")
    except Exception as e:
        error_msg = str(e)
        try:
            error_msg = ensure_utf8(error_msg)
        except:
            error_msg = f"Ошибка GigaChat (код ошибки: {type(e).__name__})"
        raise Exception(error_msg)
