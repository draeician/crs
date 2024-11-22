"""Script to test basic Ollama prompt functionality."""

import asyncio
import aiohttp
import click
import structlog
from urllib.parse import urljoin

logger = structlog.get_logger(__name__)

OLLAMA_URL = "http://localhost:11434"

async def test_prompt():
    """Test basic prompt to Ollama."""
    prompt = "Say 'Hello, World!' and nothing else."
    
    payload = {
        "model": "llama3.2:latest",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 150,
            "top_k": 40,
            "top_p": 0.9,
            "stop": []
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("sending_prompt", prompt=prompt)
            async with session.post(
                urljoin(OLLAMA_URL, "/api/generate"),
                json=payload,
                timeout=30
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("prompt_failed", 
                               status=response.status,
                               error=error_text)
                    return
                
                data = await response.json()
                if 'error' in data:
                    logger.error("ollama_error", error=data['error'])
                    return
                    
                logger.info("prompt_response", 
                          response=data.get('response', ''),
                          total_duration=data.get('total_duration', 0),
                          eval_count=data.get('eval_count', 0))
                print(f"\nSending prompt: {prompt}")
                print(f"Response: {data.get('response', '')}")
                
    except Exception as e:
        logger.error("prompt_test_failed", error=str(e))
        print(f"\nError: {str(e)}")

def main():
    """Main entry point."""
    asyncio.run(test_prompt())

if __name__ == '__main__':
    main() 