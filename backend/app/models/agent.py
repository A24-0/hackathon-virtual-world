from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Mood(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    BORED = "bored"


class Relationship(BaseModel):
    agent_id: str
    agent_name: str
    sympathy: float = Field(default=0.0, ge=-1.0, le=1.0)
    description: str = ""
    last_interaction: Optional[datetime] = None


class Memory(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    related_agent_id: Optional[str] = None
    summary: Optional[str] = None


class PersonalityTraits(BaseModel):
    openness: float = Field(default=0.5, ge=0.0, le=1.0)
    conscientiousness: float = Field(default=0.5, ge=0.0, le=1.0)
    extraversion: float = Field(default=0.5, ge=0.0, le=1.0)
    agreeableness: float = Field(default=0.5, ge=0.0, le=1.0)
    neuroticism: float = Field(default=0.5, ge=0.0, le=1.0)


class EmotionState(BaseModel):
    mood: Mood = Mood.NEUTRAL
    energy: float = Field(default=0.7, ge=0.0, le=1.0)
    stress: float = Field(default=0.3, ge=0.0, le=1.0)
    happiness: float = Field(default=0.5, ge=0.0, le=1.0)


class Agent(Document):
    name: str
    avatar_url: Optional[str] = None
    bio: str = ""
    personality: PersonalityTraits = Field(default_factory=PersonalityTraits)
    emotion: EmotionState = Field(default_factory=EmotionState)
    relationships: list[Relationship] = Field(default_factory=list)
    memories: list[Memory] = Field(default_factory=list)
    current_plan: Optional[str] = None
    current_goal: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "agents"
