from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.agent import Mood, PersonalityTraits, EmotionState, Relationship, Memory
from app.models.event import EventType
from app.models.log import LogLevel, LogCategory

class AgentCreate(BaseModel):
    name: str
    bio: str = ""
    avatar_url: Optional[str] = None
    personality: Optional[PersonalityTraits] = None
    emotion: Optional[EmotionState] = None
    system_prompt: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    personality: Optional[PersonalityTraits] = None
    emotion: Optional[EmotionState] = None
    current_plan: Optional[str] = None
    current_goal: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class MoodUpdate(BaseModel):
    mood: Mood
    energy: Optional[float] = None
    stress: Optional[float] = None
    happiness: Optional[float] = None
    reason: str = ""


class RelationshipUpdate(BaseModel):
    target_agent_id: str
    sympathy_delta: float = Field(ge=-1.0, le=1.0)
    description: Optional[str] = None


class MemoryAdd(BaseModel):
    content: str
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    related_agent_id: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    bio: str
    avatar_url: Optional[str]
    personality: PersonalityTraits
    emotion: EmotionState
    relationships: list[Relationship]
    memories_count: int
    current_plan: Optional[str]
    current_goal: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentDetailResponse(AgentResponse):
    memories: list[Memory]
    system_prompt: Optional[str]


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int


class RelationshipGraphNode(BaseModel):
    id: str
    name: str
    mood: Mood
    avatar_url: Optional[str]


class RelationshipGraphEdge(BaseModel):
    source: str
    target: str
    sympathy: float
    description: str


class RelationshipGraphResponse(BaseModel):
    nodes: list[RelationshipGraphNode]
    edges: list[RelationshipGraphEdge]

'''Текст'''

class SendMessage(BaseModel):
    content: str
    from_user: bool = True
    from_agent_id: Optional[str] = None


class ChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    user_message: str
    agent_reply: str
    event_id: str


class ReflectionResponse(BaseModel):
    agent_id: str
    agent_name: str
    reflection: str


class DialogueResponse(BaseModel):
    agent1: dict
    agent2: dict


'''Action'''

class WorldEventCreate(BaseModel):
    description: str
    metadata: dict = Field(default_factory=dict)


class AgentEventCreate(BaseModel):
    event_type: EventType
    description: str
    agent_id: str
    target_agent_id: Optional[str] = None
    content: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: str
    event_type: EventType
    description: str
    agent_id: Optional[str]
    agent_name: Optional[str]
    target_agent_id: Optional[str]
    target_agent_name: Optional[str]
    content: Optional[str]
    metadata: dict
    timestamp: datetime


class EventListResponse(BaseModel):
    events: list[EventResponse]
    total: int


class EventFeedResponse(BaseModel):
    events: list[EventResponse]
    has_more: bool
    next_cursor: Optional[str] = None


'''Логгер'''

class LogResponse(BaseModel):
    id: str
    level: LogLevel
    category: LogCategory
    message: str
    agent_id: Optional[str]
    agent_name: Optional[str]
    details: dict
    timestamp: datetime


class LogListResponse(BaseModel):
    logs: list[LogResponse]
    total: int


class LogStats(BaseModel):
    total_logs: int
    by_level: dict
    by_category: dict
    last_error: Optional[LogResponse] = None
