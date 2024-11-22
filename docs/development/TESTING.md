# Testing Guide for crs_thoughts

## Setup Development Environment

1. Clone the repository and create a virtual environment:
```bash
git clone https://github.com/yourusername/crs_thoughts.git
cd crs_thoughts
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Running Tests

### Basic Test Execution
Run all tests with:
```bash
pytest
```

### Common Test Commands

1. Run tests with coverage report:
```bash
pytest --cov=crs_thoughts --cov-report=term-missing
```

2. Run specific test file:
```bash
pytest tests/utils/test_backup.py
```

3. Run tests by marker:
```bash
pytest -v -m "integration"  # Run integration tests
pytest -v -m "slow"        # Run slow tests
pytest -v -m "security"    # Run security tests
```

4. Run tests in parallel:
```bash
pytest -n auto  # Uses all available CPU cores
```

5. Generate HTML coverage report:
```bash
pytest --cov=crs_thoughts --cov-report=html
# Report will be in ./coverage_html/index.html
```

### Test Categories

- **Unit Tests**: Located in `tests/` directory
- **Integration Tests**: Marked with `@pytest.mark.integration`
- **Security Tests**: Marked with `@pytest.mark.security`
- **Performance Tests**: Located in `tests/performance/`

### Test Configuration

Test settings are defined in `pyproject.toml`:
- Minimum coverage: 80%
- Test discovery paths: `tests/`
- Strict mode enabled
- Custom markers defined

## Writing Tests

### Test Structure
```python
# tests/test_example.py

import pytest
from crs_thoughts.module import function

def test_function_name():
    """Test description."""
    # Arrange
    input_data = "test"
    
    # Act
    result = function(input_data)
    
    # Assert
    assert result == expected_result

@pytest.mark.integration
def test_integration_feature():
    """Integration test description."""
    # Test implementation
```

### Using Fixtures
```python
# tests/conftest.py

@pytest.fixture
def mock_service():
    """Provide a mock service."""
    # Setup
    service = create_mock_service()
    yield service
    # Teardown
    service.cleanup()
```

### Test Best Practices

1. **Naming Conventions**
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`

2. **Documentation**
   - Each test should have a clear docstring
   - Document test assumptions
   - Explain complex test setups

3. **Isolation**
   - Tests should be independent
   - Use fixtures for common setup
   - Clean up resources after tests

4. **Coverage**
   - Aim for 80% minimum coverage
   - Cover edge cases
   - Include error scenarios

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Pushes to main branch
- Nightly builds

### CI Pipeline Stages
1. Lint check (ruff)
2. Type check (mypy)
3. Unit tests
4. Integration tests
5. Coverage report

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Test Discovery Issues**
   ```bash
   pytest --collect-only
   ```

3. **Coverage Issues**
   ```bash
   pytest --cov=crs_thoughts --cov-report=term-missing -v
   ```

### Debug Tools

1. Print debug information:
```bash
pytest -vv --debug
```

2. Drop into debugger on failures:
```bash
pytest --pdb
```

3. Show local variables in tracebacks:
```bash
pytest --showlocals
```

## Adding New Tests

1. Create test file in appropriate directory
2. Import required modules
3. Write test functions/classes
4. Add necessary fixtures
5. Run tests and verify coverage
6. Update documentation if needed

## Test Maintenance

1. Regular review of test coverage
2. Update tests when features change
3. Remove obsolete tests
4. Keep test dependencies updated
5. Monitor test execution time

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/) 