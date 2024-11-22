"""Tests for CLI functionality."""

import pytest
from unittest.mock import patch, Mock
import uuid
from datetime import datetime
import sys

from crs_thoughts.cli import (
    get_current_username, handle_error,
    question_main, answer_main, thought_main
)
from crs_thoughts.exceptions import ValidationError, StorageError
from crs_thoughts.utils.storage import Storage
from crs_thoughts.commands import question, answer, thought

@pytest.fixture
def mock_storage():
    """Mock storage instance."""
    storage = Mock(spec=Storage)
    # Add required methods
    storage.store_thought = Mock()
    storage.store_question = Mock()
    storage.store_answer = Mock()
    storage.get_question = Mock()
    storage.get_thought = Mock()
    return storage

@pytest.fixture
def mock_handlers():
    """Mock command handlers."""
    with patch('crs_thoughts.commands.question.handle_question') as mock_q, \
         patch('crs_thoughts.commands.answer.handle_answer') as mock_a, \
         patch('crs_thoughts.commands.thought.handle_thought') as mock_t:
        yield {
            'question': mock_q,
            'answer': mock_a,
            'thought': mock_t
        }

def test_get_current_username():
    """Test username retrieval."""
    with patch.dict('os.environ', {'USER': 'test_user'}):
        assert get_current_username() == 'test_user'
    
    with patch.dict('os.environ', {'USERNAME': 'windows_user'}, clear=True):
        assert get_current_username() == 'windows_user'
    
    with patch.dict('os.environ', {}, clear=True):
        assert get_current_username() == 'unknown'

def test_handle_error():
    """Test error handling."""
    with pytest.raises(SystemExit) as exc_info:
        handle_error(ValueError("Test error"))
    assert exc_info.value.code == 1

    with pytest.raises(SystemExit) as exc_info:
        handle_error(Exception("Test error"), exit_code=2)
    assert exc_info.value.code == 2

@pytest.mark.parametrize("command,args,handler_name", [
    (question_main, ["Test question"], "question"),
    (thought_main, ["Test thought"], "thought"),
    (answer_main, ["Test answer"], "answer"),
])
def test_cli_commands(command, args, handler_name, mock_storage, mock_handlers):
    """Test CLI commands with various inputs."""
    with patch('sys.argv', [command.__name__] + args):
        with patch('crs_thoughts.cli.Storage', return_value=mock_storage):
            command()
            handler = mock_handlers[handler_name]
            handler.assert_called_once()
            assert handler.call_args[1]['storage'] == mock_storage

def test_question_main_with_validation_error(mock_storage, mock_handlers):
    """Test question command with validation error."""
    mock_handlers['question'].side_effect = ValidationError("Invalid input")
    
    with patch('sys.argv', ['question_main', 'test']):
        with patch('crs_thoughts.cli.Storage', return_value=mock_storage):
            with pytest.raises(SystemExit) as exc_info:
                question_main()
            assert exc_info.value.code == 1

def test_answer_main_with_invalid_uuid():
    """Test answer command with invalid UUID."""
    with patch('sys.argv', ['answer_main', 'test', '--question-uuid', 'invalid-uuid']):
        with pytest.raises(SystemExit) as exc_info:
            answer_main()
        assert exc_info.value.code == 1

def test_thought_main_with_storage_error(mock_storage, mock_handlers):
    """Test thought command with storage error."""
    mock_handlers['thought'].side_effect = StorageError("Storage failed")
    
    with patch('sys.argv', ['thought_main', 'test']):
        with patch('crs_thoughts.cli.Storage', return_value=mock_storage):
            with pytest.raises(SystemExit) as exc_info:
                thought_main()
            assert exc_info.value.code == 1

def test_answer_main_with_valid_uuid(mock_storage, mock_handlers):
    """Test answer command with valid UUID."""
    valid_uuid = str(uuid.uuid4())
    with patch('sys.argv', ['answer_main', 'test', '--question-uuid', valid_uuid]):
        with patch('crs_thoughts.cli.Storage', return_value=mock_storage):
            answer_main()
            mock_handlers['answer'].assert_called_once()

def test_thought_main_with_long_content(mock_storage, mock_handlers):
    """Test thought command with long content."""
    long_content = "x" * 1000
    with patch('sys.argv', ['thought_main', long_content]):
        with patch('crs_thoughts.cli.Storage', return_value=mock_storage):
            thought_main()
            mock_handlers['thought'].assert_called_once()
            args = mock_handlers['thought'].call_args[1]
            assert args['content'] == long_content
            assert args['storage'] == mock_storage