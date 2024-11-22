"""Base models for entries in the system."""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class EntryBase(BaseModel):
    """Base model for all entries."""
    id: UUID = Field(default_factory=uuid4, alias='uuid')
    timestamp: datetime = Field(default_factory=datetime.now)
    username: str
    content: str
    session_uuid: Optional[UUID] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str
        },
        arbitrary_types_allowed=True,
        populate_by_name=True,
        allow_population_by_field_name=True
    )

class Question(EntryBase):
    """Model for question entries."""
    pass

class Answer(EntryBase):
    """Model for answer entries."""
    question_uuid: Optional[UUID] = None

class Thought(EntryBase):
    """Model for thought entries."""
    tags: List[str] = Field(default_factory=list) 