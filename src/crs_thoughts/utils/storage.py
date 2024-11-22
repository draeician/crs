"""Storage utilities for managing entries."""

import csv
import os
from pathlib import Path
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, Union

from ..models.entry import Question, Answer, Thought
from ..exceptions import StorageError, ValidationError

class Storage:
    """Handles storage operations for entries."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize storage with base directory.
        
        Args:
            base_dir: Optional base directory path. Defaults to ~/.crs_thoughts
        """
        self.base_dir = Path(base_dir) if base_dir else Path.home() / '.crs_thoughts'
        self.questions_dir = self.base_dir / 'questions'
        self.answers_dir = self.base_dir / 'answers'
        self.thoughts_dir = self.base_dir / 'thoughts'
        
        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.questions_dir, self.answers_dir, self.thoughts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Initialize CSV files with headers if they don't exist
        self._initialize_csv_file(self.questions_dir / 'questions.csv', 
                                ['uuid', 'timestamp', 'username', 'content', 'session_uuid'])
        self._initialize_csv_file(self.answers_dir / 'answers.csv',
                                ['uuid', 'question_uuid', 'timestamp', 'username', 'content', 'session_uuid'])
        self._initialize_csv_file(self.thoughts_dir / 'thoughts.csv',
                                ['uuid', 'timestamp', 'username', 'content', 'session_uuid', 'tags'])

    def _initialize_csv_file(self, file_path: Path, headers: list[str]) -> None:
        """Initialize a CSV file with headers if it doesn't exist.
        
        Args:
            file_path: Path to the CSV file
            headers: List of column headers
        """
        if not file_path.exists():
            with file_path.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def store_question(self, content: str, username: str, timestamp: datetime,
                      entry_uuid: uuid.UUID, session_uuid: Optional[uuid.UUID] = None) -> None:
        """Store a question entry.
        
        Args:
            content: The question text
            username: Username of the author
            timestamp: Time of creation
            entry_uuid: UUID for the entry
            session_uuid: Optional session UUID
            
        Raises:
            StorageError: If there's an error writing to storage
            ValidationError: If the input data is invalid
        """
        if not content.strip():
            raise ValidationError("Question content cannot be empty")

        question = Question(
            uuid=entry_uuid,
            timestamp=timestamp,
            username=username,
            content=content,
            session_uuid=session_uuid
        )

        try:
            with (self.questions_dir / 'questions.csv').open('a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    str(question.uuid),
                    question.timestamp.isoformat(),
                    question.username,
                    question.content,
                    str(question.session_uuid) if question.session_uuid else ''
                ])
        except Exception as e:
            raise StorageError(f"Failed to store question: {str(e)}") from e

    # Similar implementations for store_answer and store_thought... 