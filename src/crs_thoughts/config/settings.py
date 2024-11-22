"""Configuration management for crs_thoughts."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field, ConfigDict
import structlog

from ..exceptions import ConfigurationError

logger = structlog.get_logger(__name__)

class AISettings(BaseModel):
    """AI service configuration."""
    model_config = ConfigDict(
        extra='forbid',
        validate_assignment=True
    )
    
    enabled: bool = True
    url: str = "http://localhost:11434"
    model: str = "llama3.2:latest"

class SearchConfig(BaseModel):
    """Search integration configuration."""
    enabled: bool = True
    url: str = "http://nomnom:4000"

class Settings(BaseModel):
    """Global application settings."""
    username: str = Field(default_factory=lambda: os.getenv('USER', 'unknown'))
    current_session: Optional[str] = None
    datetime_format: str = "%Y-%m-%dT%H:%M:%S"
    storage_dir: Path = Field(default_factory=lambda: Path.home() / '.crs_thoughts')
    ai: AISettings = Field(default_factory=AISettings)
    search: SearchConfig = Field(default_factory=SearchConfig)

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = Path.home() / '.crs_thoughts'
        self.config_file = self.config_dir / 'config.yaml'
        self.settings = self._load_config()

    def _load_config(self) -> Settings:
        """Load configuration from file.
        
        Returns:
            Settings object with configuration values
            
        Raises:
            ConfigurationError: If configuration file is invalid
        """
        if not self.config_file.exists():
            logger.info("config_file_not_found_creating_default")
            return self._create_default_config()

        try:
            with self.config_file.open('r') as f:
                config_data = yaml.safe_load(f)
            return Settings(**config_data) if config_data else Settings()
        except Exception as e:
            logger.error("config_load_failed", error=str(e))
            raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e

    def _create_default_config(self) -> Settings:
        """Create default configuration file.
        
        Returns:
            Default Settings object
        """
        settings = Settings()
        self._save_config(settings)
        return settings

    def _save_config(self, settings: Settings) -> None:
        """Save configuration to file.
        
        Args:
            settings: Settings object to save
            
        Raises:
            ConfigurationError: If saving configuration fails
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with self.config_file.open('w') as f:
                yaml.safe_dump(settings.dict(), f)
        except Exception as e:
            logger.error("config_save_failed", error=str(e))
            raise ConfigurationError(f"Failed to save configuration: {str(e)}") from e

    def get_setting(self, key: str) -> Any:
        """Get a configuration setting.
        
        Args:
            key: Setting key to retrieve
            
        Returns:
            Setting value
            
        Raises:
            ConfigurationError: If setting doesn't exist
        """
        try:
            return getattr(self.settings, key)
        except AttributeError as e:
            logger.error("setting_not_found", key=key)
            raise ConfigurationError(f"Setting not found: {key}") from e

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting.
        
        Args:
            key: Setting key to set
            value: Value to set
            
        Raises:
            ConfigurationError: If setting is invalid
        """
        try:
            setattr(self.settings, key, value)
            self._save_config(self.settings)
            logger.info("setting_updated", key=key)
        except Exception as e:
            logger.error("setting_update_failed", key=key, error=str(e))
            raise ConfigurationError(f"Failed to update setting: {str(e)}") from e 