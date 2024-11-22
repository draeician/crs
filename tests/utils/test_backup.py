"""Tests for backup functionality."""

import pytest
from pathlib import Path
import json
import zipfile
from datetime import datetime
import shutil
from unittest.mock import patch, Mock, ANY

from crs_thoughts.utils.backup import BackupService
from crs_thoughts.exceptions import BackupError

@pytest.fixture
def mock_config():
    """Mock configuration for backup service."""
    with patch('crs_thoughts.utils.backup.ConfigManager') as mock:
        mock.return_value.settings.storage_dir = Path('/test/storage')
        mock.return_value.settings.version = '0.1.0'
        yield mock

@pytest.fixture
def backup_service(mock_config, tmp_path):
    """Create backup service with temporary directory."""
    mock_config.return_value.settings.storage_dir = tmp_path
    service = BackupService()
    
    # Create test data structure
    for dir_name in ['questions', 'answers', 'thoughts', 'backups']:
        (tmp_path / dir_name).mkdir(exist_ok=True)
    
    # Create test files
    test_files = {
        'questions/questions.csv': 'test question data',
        'answers/answers.csv': 'test answer data',
        'thoughts/thoughts.csv': 'test thought data',
        'config.yaml': 'test config data'
    }
    
    for path, content in test_files.items():
        (tmp_path / path).write_text(content)
    
    return service

def test_create_backup(backup_service, tmp_path):
    """Test creating a backup."""
    backup_file = backup_service.create_backup('test_backup')
    
    assert backup_file.exists()
    assert backup_file.suffix == '.zip'
    
    with zipfile.ZipFile(backup_file, 'r') as zf:
        # Check metadata
        metadata = json.loads(zf.read('metadata.json'))
        assert metadata['name'] == 'test_backup'
        assert metadata['version'] == '0.1.0'
        
        # Check files
        assert 'config.yaml' in zf.namelist()
        assert 'questions/questions.csv' in zf.namelist()
        assert 'answers/answers.csv' in zf.namelist()
        assert 'thoughts/thoughts.csv' in zf.namelist()
        
        # Check content
        assert zf.read('questions/questions.csv').decode() == 'test question data'

def test_create_backup_with_timestamp(backup_service):
    """Test creating a backup with timestamp-based name."""
    backup_file = backup_service.create_backup()
    assert backup_file.exists()
    assert datetime.now().strftime('%Y%m%d') in backup_file.name

def test_restore_backup(backup_service, tmp_path):
    """Test restoring from a backup."""
    # Create initial backup
    backup_file = backup_service.create_backup('test_backup')
    
    # Modify original files
    (tmp_path / 'questions/questions.csv').write_text('modified data')
    
    # Restore backup
    backup_service.restore_backup(backup_file)
    
    # Verify restoration
    assert (tmp_path / 'questions/questions.csv').read_text() == 'test question data'

def test_restore_nonexistent_backup(backup_service):
    """Test restoring from a nonexistent backup."""
    with pytest.raises(BackupError, match="Backup file not found"):
        backup_service.restore_backup(Path('nonexistent.zip'))

def test_restore_invalid_backup(backup_service, tmp_path):
    """Test restoring from an invalid backup."""
    invalid_backup = tmp_path / 'invalid.zip'
    with zipfile.ZipFile(invalid_backup, 'w') as zf:
        zf.writestr('test.txt', 'invalid data')
    
    with pytest.raises(BackupError, match="Invalid backup file"):
        backup_service.restore_backup(invalid_backup)

def test_list_backups(backup_service):
    """Test listing available backups."""
    # Create test backups
    backup_service.create_backup('backup1')
    backup_service.create_backup('backup2')
    
    backups = backup_service.list_backups()
    assert len(backups) == 2
    assert backups[0]['name'] == 'backup2'  # Most recent first
    assert backups[1]['name'] == 'backup1'
    
    for backup in backups:
        assert 'timestamp' in backup
        assert 'version' in backup
        assert 'size' in backup
        assert 'path' in backup

def test_backup_error_handling(backup_service, tmp_path):
    """Test error handling during backup operations."""
    with patch('zipfile.ZipFile', side_effect=Exception('Test error')):
        with pytest.raises(BackupError, match="Failed to create backup"):
            backup_service.create_backup()

def test_create_backup_with_custom_name(backup_service, tmp_path):
    """Test creating a backup with custom name."""
    backup_file = backup_service.create_backup('custom_backup')
    assert backup_file.name == 'custom_backup.zip'
    assert backup_file.exists()

def test_create_backup_with_empty_directories(backup_service, tmp_path):
    """Test creating a backup with empty directories."""
    # Remove all test files
    for file in tmp_path.rglob('*.csv'):
        file.unlink()
    
    backup_file = backup_service.create_backup()
    assert backup_file.exists()
    
    with zipfile.ZipFile(backup_file, 'r') as zf:
        metadata = json.loads(zf.read('metadata.json'))
        assert 'timestamp' in metadata
        assert metadata['version'] == '0.1.0'

def test_restore_backup_with_missing_files(backup_service, tmp_path):
    """Test restoring from a backup with missing files."""
    # Create backup
    backup_file = backup_service.create_backup()
    
    # Delete original files
    for file in tmp_path.rglob('*.csv'):
        file.unlink()
    
    backup_service.restore_backup(backup_file)
    assert (tmp_path / 'questions/questions.csv').exists()
    assert (tmp_path / 'answers/answers.csv').exists()

def test_list_backups_with_invalid_files(backup_service, tmp_path):
    """Test listing backups with some invalid backup files."""
    # Create valid backup
    backup_service.create_backup('valid_backup')
    
    # Create invalid backup file
    invalid_backup = tmp_path / 'backups/invalid_backup.zip'
    invalid_backup.parent.mkdir(exist_ok=True)
    invalid_backup.write_bytes(b'invalid data')
    
    backups = backup_service.list_backups()
    assert len(backups) == 1
    assert backups[0]['name'] == 'valid_backup'

def test_backup_error_handling_with_permission_error(backup_service, tmp_path):
    """Test backup error handling with permission errors."""
    with patch('zipfile.ZipFile', side_effect=PermissionError('Access denied')):
        with pytest.raises(BackupError, match="Failed to create backup"):
            backup_service.create_backup()

def test_restore_backup_with_version_mismatch(backup_service, tmp_path):
    """Test restoring backup with version mismatch."""
    # Create backup with different version
    backup_file = tmp_path / 'backups/old_backup.zip'
    backup_file.parent.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(backup_file, 'w') as zf:
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'name': 'old_backup',
            'version': '0.0.1',
            'directories': ['questions', 'answers', 'thoughts']
        }
        zf.writestr('metadata.json', json.dumps(metadata))
    
    # Should still restore but log a warning
    backup_service.restore_backup(backup_file)
    
def test_backup_initialization(backup_service, tmp_path):
    """Test backup service initialization."""
    assert backup_service.backup_dir == tmp_path / 'backups'
    assert backup_service.backup_dir.exists()

def test_create_backup_with_missing_directory(backup_service, tmp_path):
    """Test creating backup when directory doesn't exist."""
    shutil.rmtree(tmp_path / 'backups')
    backup_file = backup_service.create_backup('test_backup')
    assert backup_file.exists()
    assert backup_file.parent == tmp_path / 'backups'

def test_create_backup_with_existing_name(backup_service):
    """Test creating backup with existing name."""
    backup_service.create_backup('test_backup')
    with pytest.raises(BackupError, match="Backup already exists"):
        backup_service.create_backup('test_backup')

def test_restore_backup_with_missing_directories(backup_service, tmp_path):
    """Test restoring backup when directories don't exist."""
    # Create backup
    backup_file = backup_service.create_backup('test_backup')
    
    # Remove all directories
    for dir_name in ['questions', 'answers', 'thoughts']:
        shutil.rmtree(tmp_path / dir_name)
    
    # Restore should recreate directories
    backup_service.restore_backup(backup_file)
    assert (tmp_path / 'questions').exists()
    assert (tmp_path / 'answers').exists()
    assert (tmp_path / 'thoughts').exists()

def test_restore_backup_with_corrupted_zip(backup_service, tmp_path):
    """Test restoring from corrupted backup."""
    backup_file = tmp_path / 'backups/corrupted.zip'
    backup_file.write_bytes(b'corrupted data')
    
    with pytest.raises(BackupError, match="Invalid backup file"):
        backup_service.restore_backup(backup_file)

def test_list_backups_with_empty_directory(backup_service):
    """Test listing backups with empty directory."""
    backups = backup_service.list_backups()
    assert len(backups) == 0

def test_list_backups_sorting(backup_service):
    """Test backup listing order."""
    # Create backups in reverse order
    backup_service.create_backup('backup2')
    backup_service.create_backup('backup1')
    backup_service.create_backup('backup3')
    
    backups = backup_service.list_backups()
    assert len(backups) == 3
    assert [b['name'] for b in backups] == ['backup3', 'backup1', 'backup2']

def test_backup_with_special_characters(backup_service, tmp_path):
    """Test backup with special characters in filenames."""
    special_file = tmp_path / 'thoughts/special#file.csv'
    special_file.write_text('special content')
    
    backup_file = backup_service.create_backup('test_backup')
    assert backup_file.exists()
    
    # Verify special file was backed up
    with zipfile.ZipFile(backup_file, 'r') as zf:
        assert 'thoughts/special#file.csv' in zf.namelist()

def test_backup_large_files(backup_service, tmp_path):
    """Test backup with large files."""
    large_file = tmp_path / 'thoughts/large.csv'
    large_file.write_text('x' * 1024 * 1024)  # 1MB file
    
    backup_file = backup_service.create_backup('test_backup')
    assert backup_file.exists()
    assert backup_file.stat().st_size > 1024 * 1024

def test_backup_with_readonly_files(backup_service, tmp_path):
    """Test backup with readonly files."""
    readonly_file = tmp_path / 'thoughts/readonly.csv'
    readonly_file.write_text('readonly content')
    readonly_file.chmod(0o444)
    
    backup_file = backup_service.create_backup('test_backup')
    assert backup_file.exists()
    
    with zipfile.ZipFile(backup_file, 'r') as zf:
        assert 'thoughts/readonly.csv' in zf.namelist()
    