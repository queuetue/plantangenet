# Plantangenet Test Infrastructure

This directory contains the unified test infrastructure for the modernized Plantangenet Omni system.

## Structure

```
tests/
├── conftest.py                 # Pytest configuration and global fixtures
├── run_tests.py               # Test runner script
├── fixtures/                  # Test fixtures and utilities
│   └── omni_fixtures.py      # Omni-specific test fixtures
├── helpers/                   # Test helper utilities
├── unit/                      # Unit tests
│   ├── omni/                 # Omni infrastructure tests
│   │   ├── test_omni_base.py        # Core Omni functionality
│   │   ├── test_omni_performance.py # Performance tests
│   │   └── test_omni_policy.py      # Policy integration tests
│   ├── policy/               # Policy system tests
│   └── session/              # Session tests
└── integration/              # Integration tests
```

## Test Organization

### Unit Tests (`tests/unit/`)

- **Omni Tests** (`tests/unit/omni/`): Test the core Omni infrastructure
  - `test_omni_base.py`: Core functionality, field management, storage
  - `test_omni_performance.py`: Performance characteristics and efficiency
  - `test_omni_policy.py`: Policy integration and enforcement

- **Policy Tests** (`tests/unit/policy/`): Test policy evaluation and management
- **Session Tests** (`tests/unit/session/`): Test session management

### Integration Tests (`tests/integration/`)

- End-to-end scenarios
- Cross-component interactions
- Real-world usage patterns

### Fixtures (`tests/fixtures/`)

- **`omni_fixtures.py`**: Common test objects and mock implementations
  - `MockStorage`: Mock storage backend for testing
  - `SampleOmni`: Simple test Omni class
  - `ComplexSampleOmni`: Advanced test Omni with various field types
  - Policy setup fixtures

## Running Tests

### Using the Test Runner

```bash
# Run all Omni tests (default)
python run_tests.py

# Run specific test categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --performance
python run_tests.py --all

# Run component-specific tests
python run_tests.py --omni
python run_tests.py --policy

# Run with coverage
python run_tests.py --coverage --verbose
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/unit/omni/test_omni_base.py

# Run with markers
pytest -m unit
pytest -m performance
pytest -m "not slow"

# Run with coverage
pytest --cov=plantangenet --cov-report=html
```

## Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests  
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Slow-running tests (async, storage)

## Key Test Features

### Comprehensive Fixtures

The test infrastructure provides comprehensive fixtures for testing all aspects of the Omni system:

- **Mock Storage**: Simulates storage operations without dependencies
- **Policy Setup**: Pre-configured policies with identities and roles
- **Test Omni Classes**: Ready-to-use Omni implementations for testing

### Performance Testing

Performance tests validate the efficiency improvements of the unified Omni infrastructure:

- Batch vs. individual operations
- Policy caching effectiveness
- Storage operation efficiency
- Memory usage patterns

### Policy Integration Testing

Policy tests ensure proper integration between Omni and the policy system:

- Permission enforcement
- Policy caching
- Error handling
- Resource identification

## Migration from Old Tests

The previous `test_efficiency_improvements.py` has been replaced with the organized test structure:

- Core functionality → `test_omni_base.py`
- Performance testing → `test_omni_performance.py`  
- Policy integration → `test_omni_policy.py`

Old tests have been backed up as `old_test_efficiency_improvements.py.bak`.

## Modernization Benefits

This unified test infrastructure supports the modernized Omni system by:

1. **Eliminating Legacy Dependencies**: No more EnhancedOmni, OmniDescriptor, etc.
2. **Comprehensive Coverage**: Tests all aspects of the unified system
3. **Performance Validation**: Ensures efficiency improvements are maintained
4. **Policy Integration**: Validates security and access control
5. **Maintainable Structure**: Organized, documented, and extensible

## Contributing

When adding new tests:

1. Use appropriate fixtures from `omni_fixtures.py`
2. Add tests to the correct category (unit/integration)
3. Use proper test markers
4. Follow the naming conventions
5. Update this README if adding new test categories
