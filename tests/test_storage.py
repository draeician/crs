"""Tests for storage functionality."""

import pytest
from pathlib import Path
import csv
from datetime import datetime
import uuid
from typing import Dict, Any

from crs_thoughts.utils.storage import Storage
from crs_thoughts.exceptions import StorageError, ValidationError
from crs_thoughts.models.entry import Question, Answer, Thought

@pytest.fixture
def storage_with_data(temp_storage_dir: Path, sample_entry_data: Dict[str, Any]) -> Storage:
    """Create storage with test data."""
    storage = Storage()
    
    # Create test entries
    storage.store_question(**sample_entry_data)
    storage.store_answer(**sample_entry_data)
    storage.store_thought(**sample_entry_data)
    
    return storage

def test_storage_initialization(temp_storage_dir: Path):
    """Test storage directory creation."""
    storage = Storage()
    
    assert (temp_storage_dir / 'questions').exists()
    assert (temp_storage_dir / 'answers').exists()
    assert (temp_storage_dir / 'thoughts').exists()
    
    # Check CSV files
    assert (temp_storage_dir / 'questions/questions.csv').exists()
    assert (temp_storage_dir / 'answers/answers.csv').exists()
    assert (temp_storage_dir / 'thoughts/thoughts.csv').exists()

def test_store_question(storage: Storage, sample_entry_data: Dict[str, Any]):
    """Test storing a question."""
    storage.store_question(**sample_entry_data)
    
    csv_file = storage.questions_dir / 'questions.csv'
    with csv_file.open() as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row['content'] == sample_entry_data['content']
        assert row['username'] == sample_entry_data['username']

def test_store_answer(storage: Storage, sample_entry_data: Dict[str, Any]):
    """Test storing an answer."""
    storage.store_answer(**sample_entry_data)
    
    csv_file = storage.answers_dir / 'answers.csv'
    with csv_file.open() as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row['content'] == sample_entry_data['content']

def test_store_thought(storage: Storage, sample_entry_data: Dict[str, Any]):
    """Test storing a thought."""
    storage.store_thought(**sample_entry_data)
    
    csv_file = storage.thoughts_dir / 'thoughts.csv'
    with csv_file.open() as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert row['content'] == sample_entry_data['content']

def test_store_invalid_data(storage: Storage):
    """Test storing invalid data."""
    with pytest.raises(ValidationError):
        storage.store_question(
            content='',
            username='test',
            timestamp=datetime.now(),
            entry_uuid=uuid.uuid4()
        )

def test_get_question(storage_with_data: Storage, sample_entry_data: Dict[str, Any]):
    """Test retrieving a question."""
    question = storage_with_data.get_question(sample_entry_data['entry_uuid'])
    assert question is not None
    assert question.content == sample_entry_data['content']

def test_get_nonexistent_question(storage: Storage):
    """Test retrieving a nonexistent question."""
    result = storage.get_question(uuid.uuid4())
    assert result is None

def test_storage_error_handling(storage: Storage, sample_entry_data: Dict[str, Any]):
    """Test storage error handling."""
    # Make directory read-only
    storage.questions_dir.chmod(0o444)
    
    with pytest.raises(StorageError):
        storage.store_question(**sample_entry_data)