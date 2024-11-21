"""Main CLI interface for crs_thoughts."""

import argparse
import os
import sys
from datetime import datetime
import uuid
from typing import Optional

from .commands import question, answer, thought
from .utils.storage import Storage
from .utils.formatting import escape_content, validate_uuid

def get_current_username() -> str:
    """Get the current system username."""
    return os.getenv('USER', os.getenv('USERNAME', 'unknown'))

def question_main() -> None:
    """Entry point for the question command."""
    parser = argparse.ArgumentParser(description='Record a question')
    parser.add_argument('content', help='The question text')
    args = parser.parse_args()

    storage = Storage()
    username = get_current_username()
    timestamp = datetime.now()
    entry_uuid = uuid.uuid4()

    try:
        question.handle_question(
            storage=storage,
            content=escape_content(args.content),
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid
        )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def answer_main() -> None:
    """Entry point for the answer command."""
    parser = argparse.ArgumentParser(description='Record an answer')
    parser.add_argument('content', help='The answer text')
    parser.add_argument('-q', '--question-uuid', help='UUID of the question being answered')
    args = parser.parse_args()

    if args.question_uuid and not validate_uuid(args.question_uuid):
        print("Error: Invalid question UUID format", file=sys.stderr)
        sys.exit(1)

    storage = Storage()
    username = get_current_username()
    timestamp = datetime.now()
    entry_uuid = uuid.uuid4()

    try:
        answer.handle_answer(
            storage=storage,
            content=escape_content(args.content),
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid,
            question_uuid=args.question_uuid
        )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

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
        thought.handle_thought(
            storage=storage,
            content=escape_content(args.content),
            username=username,
            timestamp=timestamp,
            entry_uuid=entry_uuid
        )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1) 