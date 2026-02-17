from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    MOOD_CHANGED = "mood_changed"
    MEMORY_ADDED = "memory_added"
    RELATIONSHIP_CHANGED = "relationship_changed"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    WORLD_EVENT = "world_event"
    REFLECTION = "reflection"
    DIALOGUE = "dialogue"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"
    ACTION_EXECUTED = "action_executed"
    SYSTEM = "system"


class Log(Document):
    level: LogLevel = LogLevel.INFO
    category: LogCategory
    message: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    details: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "logs"
