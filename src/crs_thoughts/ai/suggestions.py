"""AI-powered suggestion functionality."""

import uuid
from typing import List, Optional
import click
import structlog

from .base import AIService
from ..utils.storage import Storage
from ..exceptions import AIError, ValidationError

logger = structlog.get_logger(__name__)

ANSWER_PROMPT_TEMPLATE = """
Given this question: {question}

Please provide a clear, concise, and accurate answer. Consider:
1. The specific context of the question
2. Any relevant technical details
3. Practical implications

Answer:
"""

QUESTIONS_PROMPT_TEMPLATE = """
Based on this topic or question: {content}

Generate 3-5 related follow-up questions that would help explore this topic further.
Consider:
1. Different aspects of the topic
2. Practical applications
3. Common misconceptions
4. Current developments

Questions:
"""

class SuggestionService(AIService):
    """Service for generating AI-powered suggestions."""
    
    def __init__(self):
        """Initialize suggestion service."""
        super().__init__()
        self.storage = Storage()

    async def suggest_answer(self, question_uuid: uuid.UUID) -> str:
        """Generate suggested answer for a question.
        
        Args:
            question_uuid: UUID of the question
            
        Returns:
            Generated answer suggestion
            
        Raises:
            AIError: If suggestion generation fails
            ValidationError: If question not found
        """
        question = self.storage.get_question(question_uuid)
        if not question:
            raise ValidationError(f"Question not found: {question_uuid}")
            
        prompt = self.format_prompt(
            ANSWER_PROMPT_TEMPLATE,
            question=question.content
        )
        
        return await self.generate_completion(prompt, temperature=0.7)

    async def suggest_questions(self, content: str) -> List[str]:
        """Generate related questions for a topic.
        
        Args:
            content: Topic or question text
            
        Returns:
            List of generated questions
            
        Raises:
            AIError: If suggestion generation fails
        """
        prompt = self.format_prompt(
            QUESTIONS_PROMPT_TEMPLATE,
            content=content
        )
        
        response = await self.generate_completion(prompt, temperature=0.8)
        return [q.strip() for q in response.split('\n') if q.strip()]

@click.command()
@click.option('--question-uuid', required=True, help='UUID of the question')
def suggest_answer_main(question_uuid: str) -> None:
    """CLI command for suggesting an answer."""
    try:
        service = SuggestionService()
        suggestion = service.suggest_answer(uuid.UUID(question_uuid))
        click.echo(suggestion)
    except Exception as e:
        logger.error("suggest_answer_failed", error=str(e))
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

@click.command()
@click.option('--content', required=True, help='Topic or question text')
def suggest_questions_main(content: str) -> None:
    """CLI command for suggesting related questions."""
    try:
        service = SuggestionService()
        suggestions = service.suggest_questions(content)
        for question in suggestions:
            click.echo(question)
    except Exception as e:
        logger.error("suggest_questions_failed", error=str(e))
        click.echo(f"Error: {str(e)}", err=True)
        exit(1) 