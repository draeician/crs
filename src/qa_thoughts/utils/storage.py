"""Storage utilities for saving and retrieving entries."""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from ..models.entry import Question, Answer, Thought

class Storage:
    """Handles storage and retrieval of entries."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize storage with optional base directory."""
        if base_dir is None:
            base_dir = os.path.expanduser("~/.qa_thoughts")
        self.base_dir = Path(base_dir)
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ['questions', 'answers', 'thoughts']:
            (self.base_dir / subdir).mkdir(exist_ok=True)
    
    def save_entry(self, entry: Union[Question, Answer, Thought]) -> None:
        """Save an entry to the appropriate file."""
        entry_type = entry.__class__.__name__.lower()
        file_path = self.base_dir / f"{entry_type}s" / f"{entry_type}s.csv"
        
        # Create file with headers if it doesn't exist
        if not file_path.exists():
            headers = ['uuid', 'timestamp', 'username', 'content']
            if isinstance(entry, Answer):
                headers.insert(1, 'question_uuid')
            
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        
        # Append entry
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(str(entry).split(',')) 