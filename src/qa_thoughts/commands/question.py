"""Handler for the question command."""

from datetime import datetime
import uuid

from ..models.entry import Question
from ..utils.storage import Storage

def handle_question(
    storage: Storage,
    content: str,
    username: str,
    timestamp: datetime,
    entry_uuid: uuid.UUID
) -> None:
    """Handle the question command."""
    question = Question(
        uuid=entry_uuid,
        timestamp=timestamp,
        username=username,
        content=content
    )
    storage.save_entry(question)
    print(f"Question recorded with UUID: {entry_uuid}") 