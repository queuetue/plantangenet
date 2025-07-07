"""
Pytest configuration for the unified Omni test suite.
"""

import pytest
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import all fixtures from our fixtures modules
try:
    from tests.fixtures.omni_fixtures import *
except ImportError:
    # Fixtures not available yet, will be loaded later
    pass


@pytest.fixture(scope="session")
def config():
    return {"testing": True}


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location"""
    for item in items:
        # Add markers based on test location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add performance marker for performance tests
        if "performance" in str(item.fspath) or "performance" in item.name:
            item.add_marker(pytest.mark.performance)

        # Add slow marker for async tests and storage tests
        if item.get_closest_marker("asyncio") or "storage" in item.name:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test data and utilities
@pytest.fixture
def sample_field_data():
    """Provide sample field data for testing"""
    return {
        'name': 'test_entity',
        'value': 42,
        'count': 100,
        'is_active': True,
        'description': 'Test entity description'
    }


# Performance test configuration
@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        'iteration_count': 100,
        'timeout_seconds': 5.0,
        'memory_limit_mb': 100
    }
