"""Handler for answer commands."""

from datetime import datetime
import uuid
from typing import Optional

from ..utils.storage import Storage
from ..exceptions import ValidationError, StorageError
import structlog

logger = structlog.get_logger(__name__)

def handle_answer(
    storage: Storage,
    content: str,
    username: str,
    timestamp: datetime,
    entry_uuid: uuid.UUID,
    question_uuid: Optional[str] = None,
    session_uuid: Optional[uuid.UUID] = None
) -> None:
    """Handle the creation of a new answer.
    
    Args:
        storage: Storage instance for persistence
        content: The answer text
        username: Author of the answer
        timestamp: Time of creation
        entry_uuid: UUID for the entry
        question_uuid: Optional UUID of the question being answered
        session_uuid: Optional session UUID
        
    Raises:
        ValidationError: If the input data is invalid
        StorageError: If there's an error storing the answer
    """
    logger.info("handling_answer", 
                username=username,
                entry_uuid=str(entry_uuid),
                question_uuid=question_uuid,
                session_uuid=str(session_uuid) if session_uuid else None)
    
    if not content.strip():
        logger.error("empty_answer_content")
        raise ValidationError("Answer content cannot be empty")
    
    try:
        storage.store_answer(
            content=content,
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid,
            question_uuid=uuid.UUID(question_uuid) if question_uuid else None,
            session_uuid=session_uuid
        )
        logger.info("answer_stored_successfully", entry_uuid=str(entry_uuid))
    except ValueError as e:
        logger.error("invalid_question_uuid", error=str(e))
        raise ValidationError(f"Invalid question UUID: {str(e)}") from e
    except Exception as e:
        logger.error("answer_storage_failed", error=str(e))
        raise StorageError(f"Failed to store answer: {str(e)}") from e 