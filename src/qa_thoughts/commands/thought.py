"""Handler for the thought command."""

from datetime import datetime
import uuid

from ..models.entry import Thought
from ..utils.storage import Storage

def handle_thought(
    storage: Storage,
    content: str,
    username: str,
    timestamp: datetime,
    entry_uuid: uuid.UUID
) -> None:
    """Handle the thought command."""
    thought = Thought(
        uuid=entry_uuid,
        timestamp=timestamp,
        username=username,
        content=content
    )
    storage.save_entry(thought)
    print(f"Thought recorded with UUID: {entry_uuid}") 