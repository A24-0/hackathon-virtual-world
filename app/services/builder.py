"""
Паттерн Билдер — собираем сложные объекты пошагово
вместо передачи кучи параметров в конструктор.

Пример:
    agent = (AgentBuilder()
        .set_name("Алиса")
        .set_bio("Исследовательница")
        .set_personality(openness=0.9)
        .set_mood(Mood.HAPPY)
        .build())
"""

from app.models.agent import Agent, PersonalityTraits, EmotionState, Mood, Memory
from app.models.event import Event, EventType
from app.models.log import Log, LogLevel, LogCategory
from typing import Optional


class AgentBuilder:

    def __init__(self):
        self._name = "Безымянный"
        self._bio = ""
        self._avatar_url = None
        self._personality = PersonalityTraits()
        self._emotion = EmotionState()
        self._system_prompt = None
        self._memories = []
        self._current_goal = None

    def set_name(self, name: str):
        self._name = name
        return self

    def set_bio(self, bio: str):
        self._bio = bio
        return self

    def set_avatar(self, url: str):
        self._avatar_url = url
        return self

    def set_personality(self, openness=0.5, conscientiousness=0.5,
                        extraversion=0.5, agreeableness=0.5, neuroticism=0.5):
        self._personality = PersonalityTraits(
            openness=openness, conscientiousness=conscientiousness,
            extraversion=extraversion, agreeableness=agreeableness,
            neuroticism=neuroticism,
        )
        return self

    def set_mood(self, mood: Mood, energy=0.7, stress=0.3, happiness=0.5):
        self._emotion = EmotionState(
            mood=mood, energy=energy, stress=stress, happiness=happiness,
        )
        return self

    def set_system_prompt(self, prompt: str):
        self._system_prompt = prompt
        return self

    def add_memory(self, content: str, importance=0.5):
        self._memories.append(Memory(content=content, importance=importance))
        return self

    def set_goal(self, goal: str):
        self._current_goal = goal
        return self

    def build(self) -> Agent:
        return Agent(
            name=self._name, bio=self._bio, avatar_url=self._avatar_url,
            personality=self._personality, emotion=self._emotion,
            system_prompt=self._system_prompt, memories=self._memories,
            current_goal=self._current_goal,
        )


class EventBuilder:

    def __init__(self):
        self._event_type = EventType.ACTION
        self._description = ""
        self._agent_id = None
        self._agent_name = None
        self._target_agent_id = None
        self._target_agent_name = None
        self._content = None
        self._metadata = {}

    def set_type(self, t: EventType):
        self._event_type = t
        return self

    def set_description(self, desc: str):
        self._description = desc
        return self

    def set_source(self, agent_id: str, name: str):
        self._agent_id = agent_id
        self._agent_name = name
        return self

    def set_target(self, agent_id: str, name: str):
        self._target_agent_id = agent_id
        self._target_agent_name = name
        return self

    def set_content(self, content: str):
        self._content = content
        return self

    def add_meta(self, key: str, value):
        self._metadata[key] = value
        return self

    def build(self) -> Event:
        return Event(
            event_type=self._event_type, description=self._description,
            agent_id=self._agent_id, agent_name=self._agent_name,
            target_agent_id=self._target_agent_id,
            target_agent_name=self._target_agent_name,
            content=self._content, metadata=self._metadata,
        )


class LogBuilder:

    def __init__(self):
        self._level = LogLevel.INFO
        self._category = LogCategory.SYSTEM
        self._message = ""
        self._agent_id = None
        self._agent_name = None
        self._details = {}

    def level(self, lvl: LogLevel):
        self._level = lvl
        return self

    def category(self, cat: LogCategory):
        self._category = cat
        return self

    def message(self, msg: str):
        self._message = msg
        return self

    def agent(self, agent_id: str, name: str):
        self._agent_id = agent_id
        self._agent_name = name
        return self

    def detail(self, key: str, value):
        self._details[key] = value
        return self

    def build(self) -> Log:
        return Log(
            level=self._level, category=self._category,
            message=self._message, agent_id=self._agent_id,
            agent_name=self._agent_name, details=self._details,
        )
