"""Main CLI interface for crs_thoughts.

This module provides the main entry points for the CLI commands: question, answer, and thought.
Each command handles user input, validates it, and stores the entry in the appropriate format.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
import uuid
from typing import Optional, NoReturn

from .commands import question, answer, thought
from .utils.storage import Storage
from .utils.formatting import escape_content, validate_uuid
from .exceptions import ValidationError, StorageError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_current_username() -> str:
    """Get the current system username.
    
    Returns:
        str: The current username from environment variables or 'unknown' if not found.
    """
    username = os.getenv('USER', os.getenv('USERNAME', 'unknown'))
    logger.debug(f"Current username: {username}")
    return username

def handle_error(error: Exception, exit_code: int = 1) -> NoReturn:
    """Handle errors uniformly across CLI commands.
    
    Args:
        error: The exception that occurred
        exit_code: The system exit code to use (default: 1)
    
    Raises:
        SystemExit: Always exits with the specified code
    """
    logger.error(f"Error occurred: {str(error)}", exc_info=True)
    print(f"Error: {str(error)}", file=sys.stderr)
    sys.exit(exit_code)

def question_main() -> None:
    """Entry point for the question command.
    
    Records a new question with timestamp, username, and UUID.
    
    Raises:
        ValidationError: If the input content is invalid
        StorageError: If there's an error storing the question
    """
    parser = argparse.ArgumentParser(description='Record a question')
    parser.add_argument('content', help='The question text')
    args = parser.parse_args()

    storage = Storage()
    username = get_current_username()
    timestamp = datetime.now()
    entry_uuid = uuid.uuid4()

    try:
        logger.info(f"Recording question from user {username}")
        question.handle_question(
            storage=storage,
            content=escape_content(args.content),
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid
        )
        logger.info(f"Question recorded successfully with UUID: {entry_uuid}")
        print(f"Question recorded with UUID: {entry_uuid}")
    except (ValidationError, StorageError) as e:
        handle_error(e)
    except Exception as e:
        logger.error("Unexpected error occurred", exc_info=True)
        handle_error(e)

# Similar updates for answer_main() and thought_main()... 