"""Tests for SearxNG search integration."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
from aiohttp import ClientSession
import json
from datetime import datetime
import asyncio

from crs_thoughts.search.searxng import SearchService
from crs_thoughts.exceptions import SearchError

@pytest.fixture
def mock_config():
    """Mock configuration for search service."""
    with patch('crs_thoughts.search.searxng.ConfigManager') as mock:
        mock.return_value.settings.search.enabled = True
        mock.return_value.settings.search.url = "http://test-searx"
        yield mock

@pytest.fixture
def mock_session():
    """Create mock aiohttp session."""
    session = AsyncMock(spec=ClientSession)
    return session

@pytest.mark.asyncio
async def test_search_disabled(mock_config):
    """Test search when service is disabled."""
    mock_config.return_value.settings.search.enabled = False
    with pytest.raises(SearchError, match="Search service is disabled"):
        SearchService()

@pytest.mark.asyncio
async def test_search_no_url(mock_config):
    """Test search with no URL configured."""
    mock_config.return_value.settings.search.url = None
    with pytest.raises(SearchError, match="Search URL not configured"):
        SearchService()

@pytest.mark.asyncio
async def test_search_success(mock_config, mock_session):
    """Test successful search operation."""
    mock_response = {
        'results': [
            {
                'title': 'Test Result',
                'url': 'http://test.com',
                'content': 'Test content',
                'engine': 'test_engine',
                'score': 1.0,
                'published_date': '2024-01-01'
            }
        ]
    }
    
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aenter__.return_value = mock_response_obj
    
    async with SearchService() as service:
        service.session = mock_session
        results = await service.search("test query")
        
        assert len(results) == 1
        assert results[0]['title'] == 'Test Result'
        assert results[0]['url'] == 'http://test.com'
        assert results[0]['snippet'] == 'Test content'
        assert results[0]['source'] == 'test_engine'
        assert results[0]['published_date'] == '2024-01-01'

@pytest.mark.asyncio
async def test_search_no_results(mock_config, mock_session):
    """Test search with no results."""
    mock_response = {'results': []}
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aenter__.return_value = mock_response_obj
    
    async with SearchService() as service:
        service.session = mock_session
        results = await service.search("test query")
        assert len(results) == 0

@pytest.mark.asyncio
async def test_search_timeout(mock_config, mock_session):
    """Test search with timeout."""
    mock_session.get.side_effect = asyncio.TimeoutError()
    
    async with SearchService() as service:
        service.session = mock_session
        with pytest.raises(SearchError, match="Search request timed out"):
            await service.search("test query")

@pytest.mark.asyncio
async def test_search_retry_success(mock_config, mock_session):
    """Test search retry logic."""
    # First response fails with network error
    mock_session.get.side_effect = [
        aiohttp.ClientError("Network error"),  # First attempt fails
        AsyncMock(  # Second attempt succeeds
            __aenter__=AsyncMock(return_value=AsyncMock(
                status=200,
                json=AsyncMock(return_value={
                    'results': [{'title': 'Test', 'url': 'http://test.com'}]
                })
            ))
        )
    ]
    
    async with SearchService() as service:
        service.session = mock_session
        results = await service.search("test query")
        
        # Verify results
        assert len(results) == 1
        assert results[0]['title'] == 'Test'
        
        # Verify retry happened
        assert mock_session.get.call_count == 2

@pytest.mark.asyncio
async def test_process_results_sorting(mock_config):
    """Test search results sorting."""
    raw_results = [
        {'title': 'Low Score', 'url': 'http://test1.com', 'score': 0.5},
        {'title': 'High Score', 'url': 'http://test2.com', 'score': 0.9},
        {'title': 'Mid Score', 'url': 'http://test3.com', 'score': 0.7}
    ]
    
    async with SearchService() as service:
        processed = service._process_results(raw_results)
        assert len(processed) == 3
        assert processed[0]['title'] == 'High Score'
        assert processed[1]['title'] == 'Mid Score'
        assert processed[2]['title'] == 'Low Score'

@pytest.mark.asyncio
async def test_process_results_filtering(mock_config):
    """Test search results filtering."""
    raw_results = [
        {'title': 'Valid', 'url': 'http://test.com'},
        {'title': '', 'url': 'http://empty.com'},  # Should be filtered out
        {'title': 'No URL', 'url': ''},  # Should be filtered out
    ]
    
    async with SearchService() as service:
        processed = service._process_results(raw_results)
        assert len(processed) == 1
        assert processed[0]['title'] == 'Valid'

@pytest.mark.asyncio
async def test_search_with_custom_params(mock_config, mock_session):
    """Test search with custom parameters."""
    mock_response = {'results': []}
    mock_response_obj = AsyncMock()
    mock_response_obj.status = 200
    mock_response_obj.json = AsyncMock(return_value=mock_response)
    mock_session.get.return_value.__aenter__.return_value = mock_response_obj
    
    async with SearchService() as service:
        service.session = mock_session
        await service.search("test", num_results=10, timeout=60)
        
        # Verify correct parameters were used
        call_args = mock_session.get.call_args
        params = call_args[1]['params']
        assert params['num_results'] == 10
        assert call_args[1]['timeout'] == 60