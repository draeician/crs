"""Tests for CLI backup functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock, ANY
import json

from crs_thoughts.cli import backup_main
from crs_thoughts.exceptions import BackupError

@pytest.fixture
def mock_backup_service():
    """Mock backup service."""
    with patch('crs_thoughts.cli.BackupService') as mock:
        yield mock.return_value

def test_backup_create(mock_backup_service, capsys):
    """Test backup create command."""
    mock_backup_service.create_backup.return_value = Path('/test/backup.zip')
    
    with patch('sys.argv', ['crsbackup', 'create']):
        backup_main()
        
    captured = capsys.readouterr()
    assert "Backup created: /test/backup.zip" in captured.out
    mock_backup_service.create_backup.assert_called_once_with(None)

def test_backup_create_with_name(mock_backup_service, capsys):
    """Test backup create command with custom name."""
    mock_backup_service.create_backup.return_value = Path('/test/custom_backup.zip')
    
    with patch('sys.argv', ['crsbackup', 'create', '--name', 'custom_backup']):
        backup_main()
        
    captured = capsys.readouterr()
    assert "Backup created: /test/custom_backup.zip" in captured.out
    mock_backup_service.create_backup.assert_called_once_with('custom_backup')

def test_backup_list_empty(mock_backup_service, capsys):
    """Test backup list command with no backups."""
    mock_backup_service.list_backups.return_value = []
    
    with patch('sys.argv', ['crsbackup', 'list']):
        backup_main()
        
    captured = capsys.readouterr()
    assert "No backups found" in captured.out

def test_backup_list(mock_backup_service, capsys):
    """Test backup list command."""
    mock_backups = [
        {
            'name': 'backup1',
            'timestamp': '20240101_120000',
            'version': '0.1.0',
            'size': 1024 * 1024,  # 1MB
            'path': '/test/backup1.zip'
        }
    ]
    mock_backup_service.list_backups.return_value = mock_backups
    
    with patch('sys.argv', ['crsbackup', 'list']):
        backup_main()
        
    captured = capsys.readouterr()
    assert "backup1" in captured.out
    assert "1.00 MB" in captured.out
    assert "0.1.0" in captured.out

def test_backup_restore(mock_backup_service, capsys):
    """Test backup restore command."""
    with patch('sys.argv', ['crsbackup', 'restore', 'backup1']):
        backup_main()
        
    captured = capsys.readouterr()
    assert "Backup restored successfully" in captured.out
    mock_backup_service.restore_backup.assert_called_once()

def test_backup_error_handling(mock_backup_service, capsys):
    """Test error handling in backup commands."""
    mock_backup_service.create_backup.side_effect = BackupError("Test error")
    
    with patch('sys.argv', ['crsbackup', 'create']):
        with pytest.raises(SystemExit):
            backup_main()
        
    captured = capsys.readouterr()
    assert "Error: Test error" in captured.err

def test_backup_invalid_command(capsys):
    """Test invalid backup command."""
    with patch('sys.argv', ['crsbackup']):
        backup_main()
        
    captured = capsys.readouterr()
    assert "usage:" in captured.out  # Help message should be displayed 

def test_backup_create_with_long_name(mock_backup_service, capsys):
    """Test backup create command with a long name."""
    long_name = "a" * 100
    mock_backup_service.create_backup.return_value = Path(f'/test/{long_name}.zip')
    
    with patch('sys.argv', ['crsbackup', 'create', '--name', long_name]):
        backup_main()
        
    captured = capsys.readouterr()
    assert long_name in captured.out

def test_backup_list_with_multiple_backups(mock_backup_service, capsys):
    """Test backup list command with multiple backups."""
    mock_backups = [
        {
            'name': f'backup{i}',
            'timestamp': f'2024010{i}_120000',
            'version': '0.1.0',
            'size': 1024 * 1024 * i  # i MB
        } for i in range(1, 4)
    ]
    mock_backup_service.list_backups.return_value = mock_backups
    
    with patch('sys.argv', ['crsbackup', 'list']):
        backup_main()
        
    captured = capsys.readouterr()
    for i in range(1, 4):
        assert f'backup{i}' in captured.out
        assert f'{i}.00 MB' in captured.out

def test_backup_restore_with_absolute_path(mock_backup_service, capsys, tmp_path):
    """Test backup restore command with absolute path."""
    backup_path = tmp_path / 'test_backup.zip'
    
    with patch('sys.argv', ['crsbackup', 'restore', str(backup_path)]):
        backup_main()
        
    mock_backup_service.restore_backup.assert_called_once_with(backup_path)

def test_backup_command_with_no_args(capsys):
    """Test backup command with no arguments."""
    with patch('sys.argv', ['crsbackup']):
        backup_main()
        
    captured = capsys.readouterr()
    assert 'usage:' in captured.out
    assert 'Backup commands' in captured.out

def test_backup_error_handling_with_keyboard_interrupt(mock_backup_service, capsys):
    """Test backup error handling with KeyboardInterrupt."""
    mock_backup_service.create_backup.side_effect = KeyboardInterrupt()
    
    with pytest.raises(SystemExit):
        with patch('sys.argv', ['crsbackup', 'create']):
            backup_main()
    
    captured = capsys.readouterr()
    assert "Error: " in captured.err