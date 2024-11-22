"""Tests for AI enrichment functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import uuid
from typing import Dict, Any

from crs_thoughts.ai.enrichment import EnrichmentService
from crs_thoughts.exceptions import AIError, ValidationError
from crs_thoughts.models.entry import Thought

@pytest.fixture
def mock_storage():
    """Mock storage instance."""
    with patch('crs_thoughts.ai.enrichment.Storage') as mock:
        storage_instance = MagicMock()
        storage_instance.get_thought.return_value = Thought(
            uuid=uuid.uuid4(),
            content="Test thought content",
            username="test_user"
        )
        yield storage_instance

@pytest.fixture
def mock_ai_response() -> Dict[str, Any]:
    """Create mock AI response."""
    return {
        'response': 'Key topics:\n1. Testing\n2. Python\nTags: testing, python, automation'
    }

@pytest.fixture
async def enrichment_service(mock_storage):
    """Create enrichment service with mocked dependencies."""
    with patch('crs_thoughts.ai.enrichment.SearchService') as mock_search:
        service = EnrichmentService()
        service.storage = mock_storage
        service.search_enabled = False  # Disable search for basic tests
        yield service

@pytest.mark.asyncio
async def test_enrich_thought_success(enrichment_service, mock_ai_response):
    """Test successful thought enrichment."""
    enrichment_service.generate_completion = AsyncMock(
        return_value=mock_ai_response['response']
    )

    result = await enrichment_service.enrich_thought(uuid.uuid4())
    
    assert 'generated_tags' in result
    assert isinstance(result['generated_tags'], list)
    assert len(result['generated_tags']) > 0
    assert any('python' in tag.lower() for tag in result['generated_tags'])
    assert any('testing' in tag.lower() for tag in result['generated_tags'])

@pytest.mark.asyncio
async def test_enrich_thought_with_search(enrichment_service, mock_ai_response):
    """Test enrichment with search results."""
    enrichment_service.search_enabled = True
    enrichment_service.generate_completion = AsyncMock(
        return_value=mock_ai_response['response']
    )
    
    # Mock search results
    mock_search_results = [{'title': 'Test Result', 'url': 'http://test.com'}]
    mock_search = AsyncMock()
    mock_search.search = AsyncMock(return_value=mock_search_results)
    mock_search.__aenter__.return_value = mock_search
    enrichment_service.search = mock_search
    
    result = await enrichment_service.enrich_thought(uuid.uuid4())
    
    assert 'search_results' in result
    assert len(result['search_results']) > 0
    assert result['search_results'][0]['title'] == 'Test Result'

@pytest.mark.asyncio
async def test_enrich_nonexistent_thought(enrichment_service):
    """Test enriching a nonexistent thought."""
    enrichment_service.storage.get_thought.return_value = None
    
    with pytest.raises(ValidationError, match="Thought not found"):
        await enrichment_service.enrich_thought(uuid.uuid4())

@pytest.mark.asyncio
async def test_enrich_thought_ai_error(mock_storage):
    """Test enrichment with AI error."""
    service = EnrichmentService()
    service.storage = mock_storage
    service.generate_completion = AsyncMock(
        side_effect=AIError("AI failed")
    )
    
    with pytest.raises(AIError, match="Failed to enrich thought"):
        await service.enrich_thought(uuid.uuid4()) 