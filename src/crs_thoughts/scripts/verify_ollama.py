"""Script to verify Ollama installation and required models."""

import asyncio
import aiohttp
import sys
import click
import logging
from typing import List, Dict, Any
import structlog
import json

logger = structlog.get_logger(__name__)

REQUIRED_MODELS = [
    "llama3.2:latest",
    "nomic-embed-text:v1.5"
]

OLLAMA_BASE_URL = "http://localhost:11434"

async def check_ollama_health() -> Dict[str, Any]:
    """Check if Ollama is running.
    
    Returns:
        Dict containing version info if successful
    """
    try:
        async with aiohttp.ClientSession() as session:
            # First try /api/version which should always work if Ollama is running
            async with session.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5) as response:
                if response.status == 200:
                    version_data = await response.json()
                    logger.info("ollama_running", version=version_data.get('version'))
                    return version_data
                else:
                    error_text = await response.text()
                    logger.error("ollama_health_check_failed", 
                               status=response.status,
                               error=error_text)
                    return {}
    except aiohttp.ClientError as e:
        logger.error("ollama_connection_failed", error=str(e))
        return {}
    except Exception as e:
        logger.error("ollama_health_check_failed", error=str(e))
        return {}

async def list_installed_models() -> List[str]:
    """Get list of installed Ollama models."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    logger.info("models_found", count=len(models), models=models)
                    return models
                else:
                    error_text = await response.text()
                    logger.error("list_models_failed", 
                               status=response.status,
                               error=error_text)
    except Exception as e:
        logger.error("list_models_failed", error=str(e))
    return []

async def pull_model(model_name: str) -> bool:
    """Pull an Ollama model."""
    try:
        async with aiohttp.ClientSession() as session:
            click.echo(f"Pulling {model_name}... This may take a while.")
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name},
                timeout=600  # 10 minutes timeout for model pulling
            ) as response:
                if response.status == 200:
                    logger.info("model_pulled_successfully", model=model_name)
                    return True
                else:
                    error_text = await response.text()
                    logger.error("model_pull_failed", 
                               model=model_name, 
                               status=response.status,
                               error=error_text)
                    return False
    except Exception as e:
        logger.error("model_pull_failed", model=model_name, error=str(e))
        return False

@click.command()
@click.option('--install', is_flag=True, help='Install missing models')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--timeout', default=5, help='Connection timeout in seconds')
def main(install: bool, debug: bool, timeout: int) -> None:
    """Verify Ollama setup and models."""
    # Configure logging based on debug flag
    if debug:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        )
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )
    
    async def run():
        # Check if Ollama is running
        click.echo("Checking Ollama status...")
        version_info = await check_ollama_health()
        if not version_info:
            click.echo("\nError: Could not connect to Ollama. Please ensure:", err=True)
            click.echo("1. Ollama is installed (run: curl https://ollama.ai/install.sh | sh)")
            click.echo("2. Ollama service is running (run: ollama serve)")
            click.echo("3. Port 11434 is accessible (check: curl http://localhost:11434)")
            sys.exit(1)
        
        click.echo(f"✓ Ollama is running (version: {version_info.get('version')})")
        
        # Check installed models
        click.echo("\nChecking installed models...")
        installed_models = await list_installed_models()
        missing_models = [m for m in REQUIRED_MODELS if m not in installed_models]
        
        if not missing_models:
            click.echo("✓ All required models are installed")
            return
        
        click.echo("\nMissing required models:")
        for model in missing_models:
            click.echo(f"  - {model}")
        
        if install:
            click.echo("\nInstalling missing models...")
            for model in missing_models:
                if await pull_model(model):
                    click.echo(f"✓ Installed {model}")
                else:
                    click.echo(f"✗ Failed to install {model}", err=True)
        else:
            click.echo("\nTo install missing models, run:")
            for model in missing_models:
                click.echo(f"  ollama pull {model}")
            sys.exit(1)

    asyncio.run(run())

if __name__ == '__main__':
    main() 