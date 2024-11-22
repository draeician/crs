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
from pathlib import Path

from .commands import question, answer, thought
from .utils.storage import Storage
from .utils.formatting import escape_content, validate_uuid
from .exceptions import ValidationError, StorageError
from .utils.backup import BackupService

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

def answer_main() -> None:
    """Entry point for the answer command."""
    parser = argparse.ArgumentParser(description='Record an answer')
    parser.add_argument('content', help='The answer text')
    parser.add_argument('-q', '--question-uuid', help='UUID of the question being answered')
    args = parser.parse_args()

    if args.question_uuid and not validate_uuid(args.question_uuid):
        logger.error("Invalid question UUID format")
        handle_error(ValidationError("Invalid question UUID format"))

    storage = Storage()
    username = get_current_username()
    timestamp = datetime.now()
    entry_uuid = uuid.uuid4()

    try:
        logger.info(f"Recording answer from user {username}")
        answer.handle_answer(
            storage=storage,
            content=escape_content(args.content),
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid,
            question_uuid=args.question_uuid
        )
        logger.info(f"Answer recorded successfully with UUID: {entry_uuid}")
        print(f"Answer recorded with UUID: {entry_uuid}")
    except (ValidationError, StorageError) as e:
        handle_error(e)
    except Exception as e:
        logger.error("Unexpected error occurred", exc_info=True)
        handle_error(e)

def thought_main() -> None:
    """Entry point for the thought command."""
    parser = argparse.ArgumentParser(description='Record a thought')
    parser.add_argument('content', help='The thought text')
    args = parser.parse_args()

    storage = Storage()
    username = get_current_username()
    timestamp = datetime.now()
    entry_uuid = uuid.uuid4()

    try:
        logger.info(f"Recording thought from user {username}")
        thought.handle_thought(
            storage=storage,
            content=escape_content(args.content),
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid
        )
        logger.info(f"Thought recorded successfully with UUID: {entry_uuid}")
        print(f"Thought recorded with UUID: {entry_uuid}")
    except (ValidationError, StorageError) as e:
        handle_error(e)
    except Exception as e:
        logger.error("Unexpected error occurred", exc_info=True)
        handle_error(e)

def backup_main() -> None:
    """Entry point for the crsbackup command."""
    parser = argparse.ArgumentParser(
        description='Manage crs_thoughts backups',
        prog='crsbackup'
    )
    subparsers = parser.add_subparsers(dest='command', help='Backup commands')
    
    # Create backup
    create_parser = subparsers.add_parser('create', help='Create a new backup')
    create_parser.add_argument('--name', help='Custom name for the backup')
    
    # List backups
    subparsers.add_parser('list', help='List available backups')
    
    # Restore backup
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_name', help='Name or path of backup to restore')
    
    args = parser.parse_args()
    
    try:
        backup_service = BackupService()
        
        if args.command == 'create':
            backup_file = backup_service.create_backup(args.name)
            print(f"Backup created: {backup_file}")
            
        elif args.command == 'list':
            backups = backup_service.list_backups()
            if not backups:
                print("No backups found")
                return
                
            print("\nAvailable backups:")
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                print(f"\nName: {backup['name']}")
                print(f"Created: {backup['timestamp']}")
                print(f"Version: {backup['version']}")
                print(f"Size: {size_mb:.2f} MB")
                
        elif args.command == 'restore':
            backup_path = Path(args.backup_name)
            if not backup_path.is_absolute():
                # Check in backups directory
                backup_service = BackupService()
                backup_path = backup_service.backup_dir / f"{args.backup_name}.zip"
            
            backup_service.restore_backup(backup_path)
            print(f"Backup restored successfully from: {backup_path}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

# Similar updates for answer_main() and thought_main()... 