from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from app.models.agent import Agent, Mood
import os
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")


def get_client():
    return GigaChat(credentials=CREDENTIALS, scope=SCOPE, verify_ssl_certs=False)


def make_prompt(agent: Agent) -> str:
    moods = {
        Mood.HAPPY: "Ты в хорошем настроении.",
        Mood.SAD: "Тебе грустно.",
        Mood.ANGRY: "Ты раздражён.",
        Mood.NEUTRAL: "Ты спокоен.",
        Mood.EXCITED: "Ты взволнован!",
        Mood.ANXIOUS: "Ты нервничаешь.",
        Mood.BORED: "Тебе скучно.",
    }

    top_mem = sorted(agent.memories, key=lambda m: m.importance, reverse=True)[:5]
    mem_block = ""
    if top_mem:
        mem_block = "\n\nВоспоминания:\n" + "\n".join(f"- {m.content}" for m in top_mem)

    rel_block = ""
    if agent.relationships:
        lines = []
        for r in agent.relationships:
            tone = "хорошо" if r.sympathy > 0.3 else "плохо" if r.sympathy < -0.3 else "нейтрально"
            lines.append(f"- {r.agent_name}: {tone}")
        rel_block = "\n\nОтношения:\n" + "\n".join(lines)

    goal = f"\n\nЦель: {agent.current_goal}" if agent.current_goal else ""

    prompt = (
        f"Ты — {agent.name}. {agent.bio}\n\n"
        f"Характер: открытость {agent.personality.openness}, "
        f"экстраверсия {agent.personality.extraversion}, "
        f"доброжелательность {agent.personality.agreeableness}.\n\n"
        f"{moods.get(agent.emotion.mood, 'Ты спокоен.')}"
        f"{mem_block}{rel_block}{goal}\n\n"
        f"Говори от первого лица, кратко, 1-3 предложения."
    )

    if agent.system_prompt:
        prompt += f"\n\n{agent.system_prompt}"
    return prompt


async def chat(agent: Agent, message: str) -> str:
    prompt = make_prompt(agent)
    with get_client() as c:
        resp = c.chat(Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=prompt),
                Messages(role=MessagesRole.USER, content=message),
            ],
            temperature=0.8, max_tokens=300,
        ))
    return resp.choices[0].message.content


async def reflect(agent: Agent) -> str:
    prompt = make_prompt(agent)
    recent = sorted(agent.memories, key=lambda m: m.timestamp, reverse=True)[:10]
    mem_text = "\n".join(f"- {m.content}" for m in recent) if recent else "Нет воспоминаний."

    with get_client() as c:
        resp = c.chat(Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=prompt),
                Messages(role=MessagesRole.USER,
                         content=f"Проанализируй события:\n{mem_text}\n\nОтветь:\nМЫСЛИ: ...\nНАСТРОЕНИЕ: ...\nЦЕЛЬ: ..."),
            ],
            temperature=0.9, max_tokens=400,
        ))
    return resp.choices[0].message.content


async def dialogue(agent1: Agent, agent2: Agent, context: str = "") -> str:
    prompt = make_prompt(agent1)
    rel = next((r for r in agent1.relationships if r.agent_id == str(agent2.id)), None)
    rel_text = f"симпатия {rel.sympathy:+.1f}" if rel else "не знакомы"

    msg = f"Ты общаешься с {agent2.name} ({agent2.bio}). Отношения: {rel_text}."
    if context:
        msg += f"\nКонтекст: {context}"
    msg += "\nСкажи что-нибудь, 1-2 предложения."

    with get_client() as c:
        resp = c.chat(Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=prompt),
                Messages(role=MessagesRole.USER, content=msg),
            ],
            temperature=0.85, max_tokens=200,
        ))
    return resp.choices[0].message.content
