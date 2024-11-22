"""Tests for AI base functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
import json

from crs_thoughts.ai.base import AIService
from crs_thoughts.exceptions import AIError

@pytest.fixture
def mock_config():
    """Mock configuration for AI service."""
    with patch('crs_thoughts.ai.base.ConfigManager') as mock:
        mock.return_value.settings.ai.enabled = True
        mock.return_value.settings.ai.url = "http://test-url"
        mock.return_value.settings.ai.model = "test-model"
        yield mock

@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session

@pytest.mark.asyncio
async def test_generate_completion_success(mock_config, mock_session):
    """Test successful completion generation."""
    # Configure mock response
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {'response': 'Hello, World!'}
    mock_resp.__aenter__.return_value = mock_resp
    mock_session.post.return_value = mock_resp

    async with AIService() as service:
        service.ai_config = mock_config.return_value.settings.ai
        service.session = mock_session
        result = await service.generate_completion("Test prompt")
        assert "Hello, World!" in result

@pytest.mark.asyncio
async def test_generate_completion_disabled(mock_config):
    """Test completion generation when AI is disabled."""
    mock_config.return_value.settings.ai.enabled = False
    service = AIService()
    
    with pytest.raises(AIError, match="AI service is disabled"):
        await service.generate_completion("Test prompt")

@pytest.mark.asyncio
async def test_generate_completion_no_url(mock_config):
    """Test completion generation without URL."""
    mock_config.return_value.settings.ai.url = None
    
    with pytest.raises(AIError, match="AI service URL not configured"):
        AIService()

@pytest.mark.asyncio
async def test_generate_completion_api_error(mock_config, mock_session):
    """Test completion generation with API error."""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Server Error"
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    async with AIService() as service:
        service.session = mock_session
        with pytest.raises(AIError, match="AI request failed with status: 500"):
            await service.generate_completion("Test prompt")

@pytest.mark.asyncio
async def test_generate_completion_network_error(mock_config, mock_session):
    """Test completion generation with network error."""
    mock_session.post.side_effect = aiohttp.ClientError("Network Error")
    
    async with AIService() as service:
        service.session = mock_session
        with pytest.raises(AIError, match="Failed to generate completion"):
            await service.generate_completion("Test prompt")

def test_format_prompt_success(mock_config):
    """Test successful prompt formatting."""
    service = AIService()
    template = "Question: {question}\nContext: {context}"
    result = service.format_prompt(
        template,
        question="What is Python?",
        context="Programming languages"
    )
    assert result == "Question: What is Python?\nContext: Programming languages"

def test_format_prompt_missing_variable(mock_config):
    """Test prompt formatting with missing variable."""
    service = AIService()
    template = "Question: {question}\nContext: {context}"
    
    with pytest.raises(AIError, match="Invalid prompt template: missing variable"):
        service.format_prompt(template, question="What is Python?")

def test_format_prompt_invalid_template(mock_config):
    """Test prompt formatting with invalid template."""
    service = AIService()
    template = "Question: {invalid}"
    
    with pytest.raises(AIError, match="Invalid prompt template: missing variable"):
        service.format_prompt(template, question="What is Python?")

def test_format_prompt_empty_template(mock_config):
    """Test prompt formatting with empty template."""
    service = AIService()
    with pytest.raises(AIError, match="Empty prompt template"):
        service.format_prompt("", question="What is Python?")

def test_format_prompt_with_extra_vars(mock_config):
    """Test prompt formatting with extra variables."""
    service = AIService()
    template = "Question: {question}"
    result = service.format_prompt(
        template,
        question="What is Python?",
        extra="Ignored"
    )
    assert result == "Question: What is Python?"
    