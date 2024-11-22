"""Script to run tests and manage test output."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import re

def run_tests() -> tuple[str, int]:
    """Run pytest and capture output.
    
    Returns:
        Tuple of (output string, return code)
    """
    result = subprocess.run(
        ["pytest", "-v"],
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr, result.returncode

def extract_errors(output: str) -> str:
    """Extract error messages from pytest output.
    
    Args:
        output: Raw pytest output
        
    Returns:
        String containing only error messages
    """
    # Split output into lines
    lines = output.split('\n')
    error_lines = []
    in_error_block = False
    
    for line in lines:
        # Start of error section
        if line.startswith('=') and 'ERROR' in line:
            in_error_block = True
            error_lines.append(line)
        # End of error section
        elif line.startswith('=') and in_error_block:
            in_error_block = False
            error_lines.append(line)
        # Coverage failure
        elif 'Coverage failure:' in line:
            error_lines.append(line)
        # Lines within error block
        elif in_error_block:
            error_lines.append(line)
    
    return '\n'.join(error_lines)

def save_output(errors: str) -> None:
    """Save error output to log file.
    
    Args:
        errors: Error messages to save
    """
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'test_errors_{timestamp}.log'
    
    # Save latest errors
    log_file.write_text(errors)
    
    # Create/update latest link
    latest_link = log_dir / 'latest_errors.log'
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(log_file.name)

def main() -> None:
    """Main entry point."""
    print("Running tests...")
    output, return_code = run_tests()
    
    if return_code != 0:
        errors = extract_errors(output)
        save_output(errors)
        print("\nErrors found! See logs/latest_errors.log for details.")
        print("\nLatest errors:")
        print("=" * 80)
        print(errors)
    else:
        print("\nAll tests passed!")
    
    sys.exit(return_code)

if __name__ == '__main__':
    main() 