"""Main CLI interface for qa_thoughts."""

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

def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(description='Record questions, answers, and thoughts')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Question command
    question_parser = subparsers.add_parser('question', help='Record a question')
    question_parser.add_argument('content', help='The question text')

    # Answer command
    answer_parser = subparsers.add_parser('answer', help='Record an answer')
    answer_parser.add_argument('content', help='The answer text')
    answer_parser.add_argument('-q', '--question-uuid', help='UUID of the question being answered')

    # Thought command
    thought_parser = subparsers.add_parser('thought', help='Record a thought')
    thought_parser.add_argument('content', help='The thought text')

    return parser

def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    storage = Storage()
    username = get_current_username()
    timestamp = datetime.now()
    entry_uuid = uuid.uuid4()

    try:
        if args.command == 'question':
            question.handle_question(
                storage=storage,
                content=escape_content(args.content),
                username=username,
                timestamp=timestamp,
                entry_uuid=entry_uuid
            )
        elif args.command == 'answer':
            if args.question_uuid and not validate_uuid(args.question_uuid):
                print("Error: Invalid question UUID format", file=sys.stderr)
                sys.exit(1)
            
            answer.handle_answer(
                storage=storage,
                content=escape_content(args.content),
                username=username,
                timestamp=timestamp,
                entry_uuid=entry_uuid,
                question_uuid=args.question_uuid
            )
        elif args.command == 'thought':
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

if __name__ == '__main__':
    main() 