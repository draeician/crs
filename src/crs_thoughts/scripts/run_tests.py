"""Script to run tests and manage test output."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import re
import asyncio
import aiohttp
import structlog

logger = structlog.get_logger(__name__)

async def verify_ollama() -> bool:
    """Verify Ollama is running and models are available."""
    try:
        async with aiohttp.ClientSession() as session:
            # Check if Ollama is running
            async with session.get("http://localhost:11434/api/version") as response:
                if response.status != 200:
                    logger.error("ollama_not_running")
                    return False
                version_data = await response.json()
                logger.info("ollama_running", version=version_data.get('version'))

            # Check for required models
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status != 200:
                    logger.error("ollama_models_check_failed")
                    return False
                data = await response.json()
                models = [model['name'] for model in data.get('models', [])]
                required_models = ["llama3.2:latest", "nomic-embed-text:v1.5"]
                missing = [m for m in required_models if m not in models]
                
                if missing:
                    logger.error("missing_required_models", models=missing)
                    print("\nMissing required Ollama models:")
                    for model in missing:
                        print(f"  - {model}")
                    print("\nPlease install missing models with:")
                    for model in missing:
                        print(f"  ollama pull {model}")
                    return False
                
                logger.info("required_models_available")
                return True
                
    except Exception as e:
        logger.error("ollama_verification_failed", error=str(e))
        print("\nError: Failed to connect to Ollama. Is it running?")
        print("Start Ollama with: ollama serve")
        return False

def run_tests() -> tuple[str, int]:
    """Run pytest and capture output."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # First verify Ollama
    if not asyncio.run(verify_ollama()):
        return "Ollama verification failed", 1
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_log_file = log_dir / f'pytest_full_{timestamp}.log'
    
    # Run pytest and tee output to both console and file
    with full_log_file.open('w') as f:
        process = subprocess.Popen(
            ["pytest", "-v", "--full-trace"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )
        
        output = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # Write to file
                f.write(line)
                f.flush()  # Ensure it's written immediately
                
                # Write to console
                sys.stdout.write(line)
                sys.stdout.flush()
                
                output.append(line)
        
        return_code = process.wait()
    
    return ''.join(output), return_code

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
        if line.startswith('=') and ('ERROR' in line or 'FAIL' in line):
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
        print("\nFull test output saved to logs/pytest_full_*.log")
    else:
        print("\nAll tests passed!")
        print("\nFull test output saved to logs/pytest_full_*.log")
    
    sys.exit(return_code)

if __name__ == '__main__':
    main() 