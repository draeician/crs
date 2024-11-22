"""Handler for thought commands."""

from datetime import datetime
import uuid
from typing import Optional, List

from ..utils.storage import Storage
from ..exceptions import ValidationError, StorageError
import structlog

logger = structlog.get_logger(__name__)

def handle_thought(
    storage: Storage,
    content: str,
    username: str,
    timestamp: datetime,
    entry_uuid: uuid.UUID,
    tags: Optional[List[str]] = None,
    session_uuid: Optional[uuid.UUID] = None
) -> None:
    """Handle the creation of a new thought.
    
    Args:
        storage: Storage instance for persistence
        content: The thought text
        username: Author of the thought
        timestamp: Time of creation
        entry_uuid: UUID for the entry
        tags: Optional list of tags for the thought
        session_uuid: Optional session UUID
        
    Raises:
        ValidationError: If the input data is invalid
        StorageError: If there's an error storing the thought
    """
    logger.info("handling_thought", 
                username=username,
                entry_uuid=str(entry_uuid),
                tags=tags,
                session_uuid=str(session_uuid) if session_uuid else None)
    
    if not content.strip():
        logger.error("empty_thought_content")
        raise ValidationError("Thought content cannot be empty")
    
    try:
        storage.store_thought(
            content=content,
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid,
            tags=tags or [],
            session_uuid=session_uuid
        )
        logger.info("thought_stored_successfully", 
                   entry_uuid=str(entry_uuid),
                   tags=tags)
    except Exception as e:
        logger.error("thought_storage_failed", error=str(e))
        raise StorageError(f"Failed to store thought: {str(e)}") from e 