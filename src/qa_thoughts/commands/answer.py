"""Handler for the answer command."""

from datetime import datetime
import uuid
from typing import Optional

from ..models.entry import Answer
from ..utils.storage import Storage

def handle_answer(
    storage: Storage,
    content: str,
    username: str,
    timestamp: datetime,
    entry_uuid: uuid.UUID,
    question_uuid: Optional[str] = None
) -> None:
    """Handle the answer command."""
    question_uuid_obj = uuid.UUID(question_uuid) if question_uuid else None
    answer = Answer(
        uuid=entry_uuid,
        timestamp=timestamp,
        username=username,
        content=content,
        question_uuid=question_uuid_obj
    )
    storage.save_entry(answer)
    print(f"Answer recorded with UUID: {entry_uuid}") 