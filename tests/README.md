# Onscreen Menu Plugin - Test Suite

This directory contains unit and integration tests for the onscreen_menu plugin.

## Test Structure

```
tests/
├── __init__.py                    # Test package init
├── test_utils.py                  # Unit tests for utils module
├── test_toggle_deauth.py          # Unit tests for deauth toggle
├── test_scripts_integration.py    # Integration tests for scripts
└── README.md                      # This file
```

## Running Tests

### Run all tests:
```bash
cd /home/user/pwnagotchi
python3 -m pytest tests/ -v
```

Or with unittest:
```bash
python3 -m unittest discover tests/
```

### Run specific test file:
```bash
python3 -m pytest tests/test_utils.py -v
```

### Run specific test class:
```bash
python3 -m pytest tests/test_utils.py::TestAuditFunctions -v
```

### Run with coverage:
```bash
python3 -m pytest tests/ --cov=plugins/onscreen_menu --cov-report=html
```

## Test Categories

### Unit Tests
- **test_utils.py**: Tests for utility functions (audit, validation, state management)
- **test_toggle_deauth.py**: Tests for deauth toggle logic and state transitions

### Integration Tests
- **test_scripts_integration.py**: Tests that verify scripts can execute and produce output

## Requirements

Install test dependencies:
```bash
pip3 install pytest pytest-cov
```

## CI/CD Integration

These tests are designed to be run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r plugins/onscreen_menu/requirements.txt
      - run: pip install pytest pytest-cov
      - run: python3 -m pytest tests/ -v
```

## Adding New Tests

When adding new features:

1. Create unit tests in appropriate test file
2. Add integration tests if the feature has external interactions
3. Ensure tests are isolated and don't require actual hardware
4. Use mocks for file system and network operations
5. Follow existing test naming conventions

## Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names: `test_toggle_from_disabled_to_enabled`

## Mocking Strategy

- Use `unittest.mock` for mocking file operations, network calls, and subprocess execution
- Mock at the appropriate level (function vs. module)
- Avoid mocking the code under test
- Verify mock calls when testing side effects

## Coverage Goals

- Aim for >80% code coverage
- Critical paths (security, state management) should have 100% coverage
- Document any intentionally untested code
