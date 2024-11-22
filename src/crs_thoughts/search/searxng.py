"""SearxNG search integration."""

import asyncio
import aiohttp
import click
from typing import List, Dict, Any, Optional
import structlog
from urllib.parse import urljoin
import backoff  # For retry logic

from ..config.settings import ConfigManager
from ..exceptions import SearchError

logger = structlog.get_logger(__name__)

class SearchService:
    """Service for performing web searches via SearxNG."""
    
    def __init__(self):
        """Initialize search service with configuration."""
        self.config = ConfigManager()
        self.search_config = self.config.settings.search
        
        if not self.search_config.enabled:
            logger.warning("search_service_disabled")
            raise SearchError("Search service is disabled")
            
        if not self.search_config.url:
            logger.error("search_url_missing")
            raise SearchError("Search URL not configured")
        
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, SearchError),
        max_tries=3,
        giveup=lambda e: isinstance(e, SearchError) and "timeout" in str(e).lower()
    )
    async def search(
        self,
        query: str,
        num_results: int = 5,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """Perform web search using SearxNG.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            timeout: Request timeout in seconds
            
        Returns:
            List of search results
            
        Raises:
            SearchError: If search fails
        """
        params = {
            'q': query,
            'format': 'json',
            'pageno': 1,
            'num_results': num_results,
            'categories': 'general',
            'language': 'en'
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(
                urljoin(self.search_config.url, '/search'),
                params=params,
                timeout=timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("search_request_failed",
                               status=response.status,
                               error=error_text)
                    raise SearchError(
                        f"Search failed with status: {response.status}"
                    )
                
                data = await response.json()
                if not data.get('results'):
                    logger.info("no_search_results", query=query)
                    return []
                
                return self._process_results(data['results'])
        except asyncio.TimeoutError:
            logger.error("search_timeout", query=query)
            raise SearchError("Search request timed out")
        except aiohttp.ClientError as e:
            logger.error("search_request_failed", error=str(e))
            raise SearchError(f"Failed to perform search: {str(e)}")
        except Exception as e:
            logger.error("unexpected_search_error", error=str(e))
            raise SearchError(f"Unexpected error during search: {str(e)}")

    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and format search results.
        
        Args:
            results: Raw search results
            
        Returns:
            Processed search results
        """
        processed = []
        for result in results:
            processed_result = {
                'title': result.get('title', '').strip(),
                'url': result.get('url', ''),
                'snippet': result.get('content', '').strip(),
                'source': result.get('engine', 'unknown'),
                'score': result.get('score', 0.0),
                'published_date': result.get('published_date', None)
            }
            
            # Only include results with actual content
            if processed_result['title'] and processed_result['url']:
                processed.append(processed_result)
        
        # Sort by score if available
        return sorted(
            processed,
            key=lambda x: float(x['score'] or 0),
            reverse=True
        )

@click.command()
@click.argument('query')
@click.option('--num-results', '-n', default=5,
              help='Number of results to return')
@click.option('--timeout', '-t', default=30,
              help='Search timeout in seconds')
async def web_search_main(query: str, num_results: int, timeout: int) -> None:
    """CLI command for web search."""
    try:
        async with SearchService() as service:
            results = await service.search(
                query,
                num_results=num_results,
                timeout=timeout
            )
            
            if not results:
                click.echo("No results found.")
                return
            
            for i, result in enumerate(results, 1):
                click.echo(f"\n{i}. {result['title']}")
                click.echo(f"URL: {result['url']}")
                if result['published_date']:
                    click.echo(f"Published: {result['published_date']}")
                click.echo(f"Source: {result['source']}")
                click.echo(f"\n{result['snippet']}\n")
                click.echo("-" * 80)
    except Exception as e:
        logger.error("web_search_failed", error=str(e))
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

if __name__ == '__main__':
    asyncio.run(web_search_main()) 