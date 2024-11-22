"""Tests for Ollama connectivity and basic functionality."""

import pytest
import aiohttp
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
import structlog
from urllib.parse import urljoin
import backoff
from unittest.mock import patch, AsyncMock, MagicMock
import logging

from crs_thoughts.ai.base import AIService
from crs_thoughts.exceptions import AIError
from crs_thoughts.config.settings import ConfigManager

logger = structlog.get_logger(__name__)

OLLAMA_URL = "http://localhost:11434"

@pytest.fixture
async def mock_config():
    """Mock configuration for AI service."""
    with patch('crs_thoughts.ai.base.ConfigManager') as mock:
        mock.return_value.settings.ai.enabled = True
        mock.return_value.settings.ai.url = OLLAMA_URL
        mock.return_value.settings.ai.model = "llama3.2:latest"
        yield mock

@pytest.fixture
async def mock_response() -> Dict[str, Any]:
    """Create mock response data."""
    return {
        'response': 'Hello, World!',
        'model': 'llama3.2:latest',
        'created_at': '2024-01-01T00:00:00Z'
    }

@pytest.fixture
async def mock_session(mock_response):
    """Create mock aiohttp session."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = mock_response
    mock_resp.__aenter__.return_value = mock_resp
    session.post.return_value = mock_resp
    session.get.return_value = mock_resp
    return session

@pytest.fixture
async def ai_service(mock_config, mock_session) -> AsyncGenerator[AIService, None]:
    """Create AI service instance."""
    service = AIService()
    service.session = mock_session
    async with service:
        yield service

@pytest.mark.asyncio
async def test_ollama_health():
    """Test basic Ollama connectivity."""
    url = urljoin(OLLAMA_URL, "/api/version")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=5) as response:
            assert response.status == 200
            data = await response.json()
            assert 'version' in data
            logger.info("ollama_health_check_success", version=data['version'])

@pytest.mark.asyncio
async def test_basic_completion():
    """Test basic completion with 'Hello, World!'."""
    async with AIService() as service:
        response = await service.generate_completion(
            "Say 'Hello, World!' and nothing else."
        )
        assert any(word in response.lower() for word in ['hello', 'world'])
        logger.debug("basic_completion_success", response=response)

# Add more test cases to improve coverage
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in AIService."""
    async with AIService() as service:
        service.ai_config.enabled = False
        with pytest.raises(AIError):
            await service.generate_completion("")

@pytest.mark.asyncio
async def test_model_configuration():
    """Test model configuration and parameters."""
    url = urljoin(OLLAMA_URL, "/api/show")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"name": "llama3.2:latest"}) as response:
            assert response.status == 200
            data = await response.json()
            assert isinstance(data, dict)
            assert len(data) > 0