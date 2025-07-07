"""
Test fixtures for Omni-related tests.
Provides common test objects, mock implementations, and utilities.
"""

import pytest
from typing import Dict, Any, Optional
from plantangenet.omni.omni import Omni
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase
from plantangenet.policy import Policy
from plantangenet.policy.policy import Identity, Role


class MockStorage:
    """Mock storage backend for testing Omni storage operations"""

    def __init__(self):
        self.operations = []
        self.data = {}
        self.versions = {}

    async def store_omni_structured(self, omni_id: str, fields: Dict[str, Any], **kwargs) -> bool:
        """Store omni fields in mock storage"""
        self.operations.append(('store_structured', omni_id, len(fields)))
        self.data[omni_id] = fields.copy()
        return True

    async def update_omni_fields(self, omni_id: str, dirty_fields: Dict[str, Any], **kwargs) -> bool:
        """Update dirty fields in mock storage"""
        self.operations.append(('update_fields', omni_id, len(dirty_fields)))
        if omni_id not in self.data:
            self.data[omni_id] = {}
        self.data[omni_id].update(dirty_fields)
        return True

    async def load_omni_structured(self, omni_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Load omni from mock storage"""
        self.operations.append(('load_structured', omni_id))
        return self.data.get(omni_id)

    async def store_omni_version(self, omni_id: str, version_data: Dict[str, Any]) -> str:
        """Store a versioned snapshot"""
        version_id = f"{omni_id}_v{len(self.versions)}"
        self.versions[version_id] = version_data.copy()
        return version_id

    async def load_omni_version(self, omni_id: str, version_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load a versioned snapshot"""
        if version_id:
            return self.versions.get(version_id)
        # Return latest version
        for vid, data in reversed(self.versions.items()):
            if vid.startswith(omni_id):
                return data
        return None

    def clear(self):
        """Clear all mock data"""
        self.operations.clear()
        self.data.clear()
        self.versions.clear()


class SampleOmni(Omni):
    """Simple test Omni class with various field types"""

    name = Observable(field_type=str, default="")
    value = Observable(field_type=int, default=0)
    count = PersistedBase(field_type=int, default=42)
    is_active = Observable(field_type=bool, default=True)


class ComplexSampleOmni(Omni):
    """More complex test Omni for advanced testing"""

    # Basic fields
    name = Observable(field_type=str, default="test")
    value = Observable(field_type=int, default=0)

    # String field
    description = PersistedBase(field_type=str, default="")

    # Numeric field
    limited_value = Observable(field_type=int, default=0)

    # Boolean field
    internal_flag = Observable(field_type=bool, default=False)


@pytest.fixture
def mock_storage():
    """Provide a clean mock storage instance"""
    return MockStorage()


@pytest.fixture
def test_policy():
    """Provide a configured test policy"""
    policy = Policy()

    # Create test identity and role
    identity = Identity(
        id="test_user",
        nickname="Test User",
        metadata={},
        roles=["admin"]
    )

    admin_role = Role(
        id="admin",
        name="Admin Role",
        description="Test admin role",
        members=["test_user"]
    )

    # Set up policy
    policy.add_identity(identity)
    policy.add_role(admin_role)
    policy.add_identity_to_role(identity, admin_role)
    policy.add_statement(["admin"], "allow", ["read", "write"], "*")

    return policy, identity, admin_role


@pytest.fixture
def simple_omni(mock_storage, test_policy):
    """Provide a simple test omni instance"""
    policy, identity, _ = test_policy
    omni = SampleOmni()
    omni.storage = mock_storage
    omni._omni__policy = policy
    omni.identity = identity
    return omni


@pytest.fixture
def complex_omni(mock_storage, test_policy):
    """Provide a complex test omni instance"""
    policy, identity, _ = test_policy
    omni = ComplexSampleOmni()
    omni.storage = mock_storage
    omni._omni__policy = policy
    omni.identity = identity
    return omni


@pytest.fixture
def omni_without_policy():
    """Provide an omni without policy for basic testing"""
    return SampleOmni()


class MockSession:
    """Mock session for testing"""

    def __init__(self, storage=None, identity=None):
        self.storage = storage
        self.identity = identity

    async def get(self, key: str):
        if self.storage and hasattr(self.storage, 'data'):
            return self.storage.data.get(key)
        return None

    async def set(self, key: str, value):
        if self.storage and hasattr(self.storage, 'data'):
            self.storage.data[key] = value
            return True
        return False


@pytest.fixture
def mock_session(mock_storage, test_policy):
    """Provide a mock session with storage and identity"""
    _, identity, _ = test_policy
    return MockSession(storage=mock_storage, identity=identity)
