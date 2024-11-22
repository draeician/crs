"""Base AI service functionality."""

import os
from typing import Any, Optional
import structlog
import aiohttp
import json
import re
import backoff
from urllib.parse import urljoin

from ..config.settings import ConfigManager
from ..exceptions import AIError

logger = structlog.get_logger(__name__)

class AIService:
    """Base service for AI functionality."""
    
    def __init__(self):
        """Initialize AI service with configuration."""
        self.config = ConfigManager()
        self.ai_config = self.config.settings.ai
        
        if not self.ai_config.enabled:
            logger.warning("ai_service_disabled")
            return
            
        if not self.ai_config.url:
            logger.error("ai_url_missing")
            raise AIError("AI service URL not configured")
        
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, AIError),
        max_tries=3
    )
    async def generate_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 150,
        system: str = "",
        template: str = "",
    ) -> str:
        """Generate completion from prompt using Ollama.
        
        Args:
            prompt: The prompt text
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system: Optional system message
            template: Optional prompt template
            
        Returns:
            Generated completion text
            
        Raises:
            AIError: If generation fails
        """
        if not self.ai_config.enabled:
            raise AIError("AI service is disabled")
            
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            payload = {
                "model": self.ai_config.model,
                "prompt": prompt,
                "system": system,
                "template": template,
                "stream": False,
                "raw": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                    "stop": []
                }
            }
            
            logger.debug("sending_ollama_request", 
                        model=self.ai_config.model,
                        temperature=temperature,
                        max_tokens=max_tokens)
            
            async with self.session.post(
                f"{self.ai_config.url}/api/generate",
                json=payload,
                timeout=30
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("completion_request_failed",
                               status=response.status,
                               error=error_text)
                    raise AIError(f"AI request failed with status: {response.status}")
                
                data = await response.json()
                if 'error' in data:
                    raise AIError(f"Ollama error: {data['error']}")
                    
                if 'response' not in data:
                    raise AIError("Invalid response format from Ollama")
                    
                logger.debug("completion_success", 
                           response_length=len(data['response']),
                           total_duration=data.get('total_duration', 0),
                           eval_count=data.get('eval_count', 0))
                return data['response']
                
        except aiohttp.ClientError as e:
            logger.error("completion_failed", error=str(e))
            raise AIError(f"Failed to generate completion: {str(e)}") from e
        except Exception as e:
            logger.error("completion_failed", error=str(e))
            raise AIError(f"Failed to generate completion: {str(e)}") from e

    def format_prompt(self, template: str, **kwargs: Any) -> str:
        """Format prompt template with variables.
        
        Args:
            template: Prompt template string
            **kwargs: Variables for template
            
        Returns:
            Formatted prompt string
            
        Raises:
            AIError: If template is invalid or empty
        """
        if not template:
            logger.error("empty_prompt_template")
            raise AIError("Empty prompt template")
            
        try:
            # First validate that all required variables are present
            required_vars = {
                name.group(1)
                for name in re.finditer(r'\{(\w+)\}', template)
            }
            
            missing_vars = required_vars - set(kwargs.keys())
            if missing_vars:
                missing_list = ', '.join(missing_vars)
                logger.error("prompt_format_failed", missing_variables=missing_list)
                raise AIError(f"Invalid prompt template: missing variable(s): {missing_list}")
                
            return template.format(**kwargs)
        except KeyError as e:
            logger.error("prompt_format_failed", error=str(e))
            raise AIError(f"Invalid prompt template: missing variable {str(e)}") from e
        except Exception as e:
            logger.error("prompt_format_failed", error=str(e))
            raise AIError(f"Invalid prompt template: {str(e)}") from e

    async def _verify_ollama(self) -> bool:
        """Verify Ollama is running and configured correctly."""
        try:
            async with self.session.get(f"{self.ai_config.url}/api/version") as response:
                if response.status != 200:
                    raise AIError("Ollama service is not healthy")
                version_data = await response.json()
                logger.info("ollama_running", version=version_data.get('version'))
                
                # Check for required models
                async with self.session.get(f"{self.ai_config.url}/api/tags") as model_response:
                    if model_response.status != 200:
                        raise AIError("Failed to get model list")
                        
                    data = await model_response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    
                    required_models = [self.ai_config.model]  # Only check for main model
                    missing = [m for m in required_models if m not in models]
                    
                    if missing:
                        raise AIError(f"Missing required models: {', '.join(missing)}")
                        
                    return True
        except aiohttp.ClientError as e:
            raise AIError(f"Failed to connect to Ollama: {str(e)}") from e
        except Exception as e:
            raise AIError(f"Failed to verify Ollama: {str(e)}") from e