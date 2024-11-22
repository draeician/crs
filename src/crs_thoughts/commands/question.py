"""Handler for question commands."""

from datetime import datetime
import uuid
from typing import Optional

from ..utils.storage import Storage
from ..exceptions import ValidationError, StorageError
import structlog

logger = structlog.get_logger(__name__)

def handle_question(
    storage: Storage,
    content: str,
    username: str,
    timestamp: datetime,
    entry_uuid: uuid.UUID,
    session_uuid: Optional[uuid.UUID] = None
) -> None:
    """Handle the creation of a new question.
    
    Args:
        storage: Storage instance for persistence
        content: The question text
        username: Author of the question
        timestamp: Time of creation
        entry_uuid: UUID for the entry
        session_uuid: Optional session UUID
        
    Raises:
        ValidationError: If the input data is invalid
        StorageError: If there's an error storing the question
    """
    logger.info("handling_question", 
                username=username, 
                entry_uuid=str(entry_uuid),
                session_uuid=str(session_uuid) if session_uuid else None)
    
    if not content.strip():
        logger.error("empty_question_content")
        raise ValidationError("Question content cannot be empty")
        
    try:
        storage.store_question(
            content=content,
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid,
            session_uuid=session_uuid
        )
        logger.info("question_stored_successfully", entry_uuid=str(entry_uuid))
    except Exception as e:
        logger.error("question_storage_failed", error=str(e))
        raise StorageError(f"Failed to store question: {str(e)}") from e 