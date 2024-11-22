"""Test script for basic Ollama prompt."""

import asyncio
import structlog
from crs_thoughts.ai.base import AIService

logger = structlog.get_logger(__name__)

async def test_prompt():
    """Test basic prompt to Ollama."""
    async with AIService() as service:
        try:
            prompt = "Say 'Hello, World!' and nothing else."
            response = await service.generate_completion(prompt)
            print(f"Prompt: {prompt}")
            print(f"Response: {response}")
            return True
        except Exception as e:
            logger.error("prompt_test_failed", error=str(e))
            print(f"Error: {str(e)}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_prompt())
    exit(0 if success else 1) 