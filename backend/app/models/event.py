from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    CHAT = "chat"
    ACTION = "action"
    MOOD_CHANGE = "mood_change"
    RELATIONSHIP = "relationship"
    WORLD_EVENT = "world_event"
    USER_MESSAGE = "user_message"
    REFLECTION = "reflection"
    GOAL_SET = "goal_set"


class Event(Document):
    event_type: EventType
    description: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    target_agent_id: Optional[str] = None
    target_agent_name: Optional[str] = None
    content: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "events"
