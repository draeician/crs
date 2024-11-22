"""Backup utilities for crs_thoughts data."""

import shutil
from pathlib import Path
from datetime import datetime
import structlog
from typing import Optional
import zipfile
import json

from ..config.settings import ConfigManager
from ..exceptions import BackupError

logger = structlog.get_logger(__name__)

class BackupService:
    """Service for managing backups of crs_thoughts data."""
    
    def __init__(self):
        """Initialize backup service."""
        self.config = ConfigManager()
        self.storage_dir = self.config.settings.storage_dir
        self.backup_dir = self.storage_dir / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """Create a backup of the current data.
        
        Args:
            backup_name: Optional name for the backup
                       (defaults to timestamp-based name)
            
        Returns:
            Path to the created backup file
            
        Raises:
            BackupError: If backup creation fails
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = backup_name or f"backup_{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.zip"
        
        try:
            # Create metadata
            metadata = {
                'timestamp': timestamp,
                'name': backup_name,
                'version': self.config.settings.version,
                'directories': [
                    'questions',
                    'answers',
                    'thoughts',
                    'config.yaml'
                ]
            }
            
            # Create zip archive
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # Add config file
                config_file = self.storage_dir / 'config.yaml'
                if config_file.exists():
                    zf.write(config_file, 'config.yaml')
                
                # Add data directories
                for dir_name in ['questions', 'answers', 'thoughts']:
                    dir_path = self.storage_dir / dir_name
                    if dir_path.exists():
                        for file_path in dir_path.glob('**/*'):
                            if file_path.is_file():
                                zf.write(
                                    file_path,
                                    str(file_path.relative_to(self.storage_dir))
                                )
            
            logger.info("backup_created",
                       backup_file=str(backup_file),
                       size=backup_file.stat().st_size)
            return backup_file
            
        except Exception as e:
            logger.error("backup_failed", error=str(e))
            raise BackupError(f"Failed to create backup: {str(e)}") from e

    def restore_backup(self, backup_path: Path) -> None:
        """Restore data from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Raises:
            BackupError: If restoration fails
        """
        if not backup_path.exists():
            raise BackupError(f"Backup file not found: {backup_path}")
        
        try:
            # Create temporary directory for validation
            with zipfile.ZipFile(backup_path, 'r') as zf:
                # Verify metadata
                try:
                    metadata = json.loads(zf.read('metadata.json'))
                    logger.info("restoring_backup",
                              backup_name=metadata['name'],
                              timestamp=metadata['timestamp'])
                except Exception as e:
                    raise BackupError("Invalid backup file: missing or invalid metadata")
                
                # Create backup of current data before restoring
                current_backup = self.create_backup("pre_restore_backup")
                
                # Clear existing data
                for dir_name in ['questions', 'answers', 'thoughts']:
                    dir_path = self.storage_dir / dir_name
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                
                # Extract backup
                zf.extractall(self.storage_dir)
                
            logger.info("backup_restored",
                       backup_file=str(backup_path),
                       previous_backup=str(current_backup))
            
        except Exception as e:
            logger.error("restore_failed", error=str(e))
            raise BackupError(f"Failed to restore backup: {str(e)}") from e

    def list_backups(self) -> list[dict]:
        """List available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        for backup_file in self.backup_dir.glob('*.zip'):
            try:
                with zipfile.ZipFile(backup_file, 'r') as zf:
                    metadata = json.loads(zf.read('metadata.json'))
                    backups.append({
                        'name': metadata['name'],
                        'timestamp': metadata['timestamp'],
                        'version': metadata.get('version', 'unknown'),
                        'size': backup_file.stat().st_size,
                        'path': str(backup_file)
                    })
            except Exception:
                logger.warning(f"Invalid backup file: {backup_file}")
                
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True) 