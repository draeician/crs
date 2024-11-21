"""Entry models for questions, answers, and thoughts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Entry:
    """Base class for all entries."""
    
    uuid: uuid.UUID
    timestamp: datetime
    username: str
    content: str

@dataclass
class Question(Entry):
    """Question entry."""
    
    def __str__(self) -> str:
        return f"{self.uuid},{self.timestamp.isoformat()},{self.username},{self.content}"

@dataclass
class Answer(Entry):
    """Answer entry with optional reference to a question."""
    
    question_uuid: Optional[uuid.UUID] = None
    
    def __str__(self) -> str:
        quuid_str = str(self.question_uuid) if self.question_uuid else ""
        return f"{self.uuid},{quuid_str},{self.timestamp.isoformat()},{self.username},{self.content}"

@dataclass
class Thought(Entry):
    """Thought entry."""
    
    def __str__(self) -> str:
        return f"{self.uuid},{self.timestamp.isoformat()},{self.username},{self.content}" 