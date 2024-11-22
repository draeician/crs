"""Test fixtures for crs_thoughts."""

import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime
import uuid
from typing import Generator, Any
from unittest.mock import Mock, MagicMock, AsyncMock

from crs_thoughts.utils.storage import Storage
from crs_thoughts.models.entry import Question, Answer, Thought

@pytest.fixture
def temp_storage_dir() -> Generator[Path, Any, None]:
    """Create a temporary directory for test storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_storage_dir = os.environ.get('CRS_THOUGHTS_DIR')
        os.environ['CRS_THOUGHTS_DIR'] = tmpdir
        yield Path(tmpdir)
        if old_storage_dir:
            os.environ['CRS_THOUGHTS_DIR'] = old_storage_dir
        else:
            del os.environ['CRS_THOUGHTS_DIR']

@pytest.fixture
def storage(temp_storage_dir: Path) -> Storage:
    """Create a Storage instance with temporary directory."""
    return Storage()

@pytest.fixture
def mock_storage():
    """Mock storage instance with all required methods."""
    storage = Mock(spec=Storage)
    storage.store_thought = Mock()
    storage.store_question = Mock()
    storage.store_answer = Mock()
    storage.get_question = Mock()
    storage.get_thought = Mock()
    return storage

@pytest.fixture
def sample_entry_data() -> dict:
    """Create sample entry data for tests."""
    return {
        'content': 'Test content',
        'username': 'test_user',
        'timestamp': datetime.now(),
        'entry_uuid': uuid.uuid4(),
        'session_uuid': None
    }

@pytest.fixture
def sample_models(sample_entry_data: dict) -> dict:
    """Create sample model instances."""
    return {
        'question': Question(
            uuid=sample_entry_data['entry_uuid'],
            timestamp=sample_entry_data['timestamp'],
            username=sample_entry_data['username'],
            content=sample_entry_data['content']
        ),
        'answer': Answer(
            uuid=sample_entry_data['entry_uuid'],
            timestamp=sample_entry_data['timestamp'],
            username=sample_entry_data['username'],
            content=sample_entry_data['content']
        ),
        'thought': Thought(
            uuid=sample_entry_data['entry_uuid'],
            timestamp=sample_entry_data['timestamp'],
            username=sample_entry_data['username'],
            content=sample_entry_data['content']
        )
    }

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = MagicMock()
    config.settings.ai.enabled = True
    config.settings.ai.url = "http://test-url"
    config.settings.ai.model = "test-model"
    return config

@pytest.fixture
def mock_session():
    """Mock aiohttp session with proper async context."""
    session = AsyncMock()
    session.post.return_value.__aenter__.return_value = AsyncMock(
        status=200,
        json=AsyncMock(return_value={
            'response': 'Test response',
            'total_duration': 123456789,
            'eval_count': 20
        })
    )
    return session

@pytest.fixture
def mock_ollama_response():
    """Standard Ollama API response fixture."""
    return {
        'response': 'Test response',
        'total_duration': 123456789,
        'load_duration': 12345678,
        'prompt_eval_count': 10,
        'eval_count': 20,
        'eval_duration': 123456
    }

@pytest.fixture
def mock_ollama_error():
    """Standard Ollama API error response fixture."""
    return {
        'error': 'Test error message'
    }

@pytest.fixture
def standard_ollama_request():
    """Standard Ollama API request parameters."""
    return {
        'model': 'test-model',
        'prompt': 'Test prompt',
        'system': '',
        'template': '',
        'stream': False,
        'raw': False,
        'options': {
            'temperature': 0.7,
            'num_predict': 150,
            'top_k': 40,
            'top_p': 0.9,
            'stop': []
        }
    } 