"""AI-powered thought enrichment functionality."""

import asyncio
import uuid
from typing import List, Dict, Any, Set
import click
import structlog
import re

from .base import AIService
from ..utils.storage import Storage
from ..exceptions import AIError, ValidationError
from ..search.searxng import SearchService, SearchError

logger = structlog.get_logger(__name__)

TAG_EXTRACTION_PROMPT = """
Analyze this text and extract relevant tags/keywords. 
Return only a comma-separated list of lowercase tags.
Text: {thought}

Tags:"""

class EnrichmentService(AIService):
    """Service for enriching thoughts with AI-generated metadata."""
    
    def __init__(self):
        """Initialize enrichment service."""
        super().__init__()
        self.storage = Storage()
        try:
            self.search = SearchService()
            self.search_enabled = True
        except SearchError:
            logger.warning("search_service_unavailable")
            self.search_enabled = False

    async def _extract_tags(self, content: str) -> Set[str]:
        """Extract tags using AI analysis.
        
        Args:
            content: Text to analyze
            
        Returns:
            Set of extracted tags
        """
        prompt = self.format_prompt(TAG_EXTRACTION_PROMPT, thought=content)
        response = await self.generate_completion(prompt)
        
        # Split response into tags and clean them
        tags = {
            tag.strip().lower()
            for tag in response.split(',')
            if len(tag.strip()) > 3
        }
        
        return tags

    def _generate_search_query(
        self,
        content: str,
        tags: Set[str],
        max_length: int = 100
    ) -> str:
        """Generate optimized search query from content and tags.
        
        Args:
            content: Original thought content
            tags: Generated tags
            max_length: Maximum query length
            
        Returns:
            Optimized search query
        """
        # Use first sentence of content
        first_sentence = re.split(r'[.!?]', content)[0].strip()
        
        # Combine with most relevant tags
        tag_string = ' '.join(list(tags)[:3])
        
        query = f"{first_sentence} {tag_string}"
        return query[:max_length]

    async def enrich_thought(
        self,
        thought_uuid: uuid.UUID,
        include_search: bool = True
    ) -> Dict[str, Any]:
        """Enrich a thought with AI-generated metadata and relevant search results.
        
        Args:
            thought_uuid: UUID of the thought to enrich
            include_search: Whether to include search results
            
        Returns:
            Dictionary containing enrichment data
            
        Raises:
            AIError: If enrichment fails
            ValidationError: If thought not found
        """
        thought = self.storage.get_thought(thought_uuid)
        if not thought:
            raise ValidationError(f"Thought not found: {thought_uuid}")
            
        logger.info("enriching_thought",
                   thought_uuid=str(thought_uuid),
                   content_length=len(thought.content))
        
        try:
            # Extract tags using AI
            tags = await self._extract_tags(thought.content)
            
            enrichment = {
                'generated_tags': list(tags),
                'search_results': []
            }
            
            # Get related search results if enabled
            if include_search and self.search_enabled:
                search_query = self._generate_search_query(
                    thought.content,
                    tags
                )
                try:
                    async with self.search as search_service:
                        enrichment['search_results'] = await search_service.search(
                            search_query,
                            num_results=3
                        )
                except SearchError as e:
                    logger.warning("search_failed", error=str(e))
            
            # Update thought with generated tags
            self.storage.update_thought_tags(
                thought_uuid,
                enrichment['generated_tags']
            )
            
            logger.info("thought_enriched_successfully",
                       thought_uuid=str(thought_uuid),
                       num_tags=len(enrichment['generated_tags']),
                       num_search_results=len(enrichment['search_results']))
            
            return enrichment
        except Exception as e:
            logger.error("thought_enrichment_failed", error=str(e))
            raise AIError(f"Failed to enrich thought: {str(e)}") from e

@click.command()
@click.option('--thought-uuid', required=True, help='UUID of the thought')
@click.option('--no-search', is_flag=True, help='Disable search results')
async def enrich_thought_main(thought_uuid: str, no_search: bool) -> None:
    """CLI command for enriching a thought."""
    try:
        service = EnrichmentService()
        enrichment = await service.enrich_thought(
            uuid.UUID(thought_uuid),
            include_search=not no_search
        )
        
        click.echo("\nGenerated Tags:")
        click.echo(", ".join(enrichment['generated_tags']))
        
        if enrichment['search_results']:
            click.echo("\nRelevant Resources:")
            for result in enrichment['search_results']:
                click.echo(f"\n- {result['title']}")
                click.echo(f"  {result['url']}")
    except Exception as e:
        logger.error("enrich_thought_failed", error=str(e))
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

if __name__ == '__main__':
    asyncio.run(enrich_thought_main()) 