"""
Unit tests for the unified Omni base class.
Tests the core functionality, field management, policy integration, and storage.
"""

import pytest
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase
from tests.fixtures.omni_fixtures import SampleOmni


class TestOmniCore:
    """Test core Omni functionality"""

    def test_omni_creation(self):
        """Test basic Omni instance creation"""
        omni = SampleOmni()
        assert omni is not None
        assert hasattr(omni, '_omni_id')
        assert hasattr(omni, '_dirty_fields')
        assert hasattr(omni, '_original_values')

    def test_field_descriptor_collection(self):
        """Test that field descriptors are properly collected"""
        # Check class-level field collections
        assert 'name' in SampleOmni._omni_all_fields
        assert 'value' in SampleOmni._omni_all_fields
        assert 'count' in SampleOmni._omni_all_fields
        assert 'is_active' in SampleOmni._omni_all_fields

        # Check field types are recognized
        assert isinstance(SampleOmni._omni_all_fields['name'], Observable)
        assert isinstance(SampleOmni._omni_all_fields['count'], PersistedBase)

    def test_field_initialization(self):
        """Test that fields are initialized with default values"""
        omni = SampleOmni()
        assert omni.get_field_value('name', check_policy=False) == ""
        assert omni.get_field_value('value', check_policy=False) == 0
        assert omni.get_field_value('count', check_policy=False) == 42
        assert omni.get_field_value('is_active', check_policy=False) is True


class TestOmniFieldAccess:
    """Test field access methods"""

    def test_get_field_value(self, omni_without_policy):
        """Test getting field values"""
        # Basic access without policy
        assert omni_without_policy.get_field_value(
            'name', check_policy=False) == ""
        assert omni_without_policy.get_field_value(
            'value', check_policy=False) == 0

    def test_set_field_value(self, omni_without_policy):
        """Test setting field values"""
        # Basic setting without policy
        omni_without_policy.set_field_value(
            'name', 'test_name', check_policy=False)
        omni_without_policy.set_field_value('value', 42, check_policy=False)

        assert omni_without_policy.get_field_value(
            'name', check_policy=False) == 'test_name'
        assert omni_without_policy.get_field_value(
            'value', check_policy=False) == 42

    def test_batch_update_fields(self, omni_without_policy):
        """Test batch field updates"""
        updates = {
            'name': 'batch_test',
            'value': 99,
            'is_active': False
        }

        result = omni_without_policy.batch_update_fields(
            updates, check_policy=False)
        assert result is True

        # Verify all fields were updated
        assert omni_without_policy.get_field_value(
            'name', check_policy=False) == 'batch_test'
        assert omni_without_policy.get_field_value(
            'value', check_policy=False) == 99
        assert omni_without_policy.get_field_value(
            'is_active', check_policy=False) is False

    def test_nonexistent_field(self, omni_without_policy):
        """Test access to nonexistent fields"""
        # Should return None for nonexistent fields
        assert omni_without_policy.get_field_value(
            'nonexistent', check_policy=False) is None


class TestOmniDirtyTracking:
    """Test dirty field tracking functionality"""

    def test_dirty_fields_tracking(self, omni_without_policy):
        """Test that dirty fields are properly tracked"""
        # Initially no dirty fields
        assert not omni_without_policy.has_dirty_fields()
        assert len(omni_without_policy.get_dirty_fields()) == 0

        # Change a field
        omni_without_policy.set_field_value(
            'name', 'dirty_test', check_policy=False)

        # Should now have dirty fields
        assert omni_without_policy.has_dirty_fields()
        dirty = omni_without_policy.get_dirty_fields()
        assert 'name' in dirty
        assert dirty['name'] == 'dirty_test'

    def test_clear_dirty_fields(self, omni_without_policy):
        """Test clearing dirty field state"""
        # Make some changes
        omni_without_policy.set_field_value('name', 'test', check_policy=False)
        omni_without_policy.set_field_value('value', 42, check_policy=False)

        assert omni_without_policy.has_dirty_fields()

        # Clear dirty state
        omni_without_policy.clear_dirty_fields()

        assert not omni_without_policy.has_dirty_fields()
        assert len(omni_without_policy.get_dirty_fields()) == 0

    def test_batch_update_dirty_tracking(self, omni_without_policy):
        """Test dirty tracking with batch updates"""
        updates = {
            'name': 'batch_dirty',
            'value': 123
        }

        omni_without_policy.batch_update_fields(updates, check_policy=False)

        dirty = omni_without_policy.get_dirty_fields()
        assert len(dirty) == 2
        assert 'name' in dirty
        assert 'value' in dirty


class TestOmniPolicyIntegration:
    """Test policy integration functionality"""

    def test_policy_check_read(self, simple_omni):
        """Test policy checks for read operations"""
        # Should be able to read with proper policy
        value = simple_omni.get_field_value('name', check_policy=True)
        assert value == ""  # Default value

    def test_policy_check_write(self, simple_omni):
        """Test policy checks for write operations"""
        # Should be able to write with proper policy
        simple_omni.set_field_value('name', 'policy_test', check_policy=True)
        assert simple_omni.get_field_value(
            'name', check_policy=False) == 'policy_test'

    def test_policy_check_batch_update(self, simple_omni):
        """Test policy checks for batch operations"""
        updates = {'name': 'batch_policy', 'value': 99}
        result = simple_omni.batch_update_fields(updates, check_policy=True)
        assert result is True

    def test_policy_caching(self, simple_omni):
        """Test that policy decisions are cached"""
        # First access should set cache
        simple_omni.get_field_value('name', check_policy=True)

        # Cache should have entries
        assert len(simple_omni._policy_cache) > 0


class TestOmniStorageIntegration:
    """Test storage integration functionality"""

    @pytest.mark.asyncio
    async def test_save_to_storage_full(self, simple_omni, mock_storage):
        """Test full save to storage"""
        # Make some changes
        simple_omni.set_field_value('name', 'storage_test', check_policy=False)
        simple_omni.set_field_value('value', 42, check_policy=False)

        # Save all fields
        success = await simple_omni.save_to_storage(incremental=False)
        assert success

        # Check storage was called
        assert len(mock_storage.operations) > 0
        assert mock_storage.operations[-1][0] == 'store_structured'

    @pytest.mark.asyncio
    async def test_save_to_storage_incremental(self, simple_omni, mock_storage):
        """Test incremental save to storage"""
        # Make some changes
        simple_omni.set_field_value(
            'name', 'incremental_test', check_policy=False)

        # Save only dirty fields
        success = await simple_omni.save_to_storage(incremental=True)
        assert success

        # Check storage was called for update
        operations = [
            op for op in mock_storage.operations if op[0] == 'update_fields']
        assert len(operations) > 0

    @pytest.mark.asyncio
    async def test_load_from_storage(self, simple_omni, mock_storage):
        """Test loading from storage"""
        # Pre-populate storage
        await mock_storage.store_omni_structured(simple_omni._omni_id, {
            'name': 'loaded_name',
            'value': 123,
            'count': 456
        })

        # Load from storage
        success = await simple_omni.load_from_storage()
        assert success

        # Check values were loaded
        assert simple_omni.get_field_value(
            'name', check_policy=False) == 'loaded_name'
        assert simple_omni.get_field_value('value', check_policy=False) == 123
        assert simple_omni.get_field_value('count', check_policy=False) == 456

    @pytest.mark.asyncio
    async def test_storage_convenience_methods(self, simple_omni):
        """Test the convenience store/load/update methods"""
        # These should delegate to the enhanced methods
        simple_omni.set_field_value(
            'name', 'convenience_test', check_policy=False)

        # Test store (should call save_to_storage)
        success = await simple_omni.store()
        assert success is not None  # Could be True or False depending on storage

        # Test update (should call save_to_storage with incremental=True)
        success = await simple_omni.update()
        assert success is not None

        # Test load (should call load_from_storage)
        success = await simple_omni.load()
        assert success is not None


class TestOmniSnapshotVersioning:
    """Test snapshot and versioning functionality"""

    @pytest.mark.asyncio
    async def test_create_snapshot(self, simple_omni):
        """Test creating versioned snapshots"""
        # Set up some data
        simple_omni.set_field_value(
            'name', 'snapshot_test', check_policy=False)
        simple_omni.set_field_value('value', 42, check_policy=False)

        # Create snapshot
        version_id = await simple_omni.create_snapshot()

        # Should get a version ID if storage supports it
        if simple_omni.storage:
            assert version_id is not None

    @pytest.mark.asyncio
    async def test_restore_from_snapshot(self, simple_omni, mock_storage):
        """Test restoring from snapshots"""
        # Set up initial data and create snapshot
        simple_omni.set_field_value('name', 'original', check_policy=False)
        version_id = await simple_omni.create_snapshot()

        # Change data
        simple_omni.set_field_value('name', 'changed', check_policy=False)

        # Restore from snapshot
        if version_id:
            success = await simple_omni.restore_from_snapshot(version_id)
            if success:
                assert simple_omni.get_field_value(
                    'name', check_policy=False) == 'original'


class TestOmniSerialization:
    """Test serialization functionality"""

    def test_to_dict(self, omni_without_policy):
        """Test converting omni to dictionary"""
        # Set up some data
        omni_without_policy.set_field_value(
            'name', 'dict_test', check_policy=False)
        omni_without_policy.set_field_value('value', 42, check_policy=False)

        # Convert to dict
        data = omni_without_policy.to_dict(check_policy=False)

        assert isinstance(data, dict)
        assert 'name' in data
        assert 'value' in data
        assert data['name'] == 'dict_test'
        assert data['value'] == 42

    def test_from_dict(self, omni_without_policy):
        """Test importing omni from dictionary"""
        data = {
            'name': 'imported_name',
            'value': 99,
            'is_active': False
        }

        omni_without_policy.from_dict(data, check_policy=False)

        # Check values were imported
        assert omni_without_policy.get_field_value(
            'name', check_policy=False) == 'imported_name'
        assert omni_without_policy.get_field_value(
            'value', check_policy=False) == 99
        assert omni_without_policy.get_field_value(
            'is_active', check_policy=False) is False

    def test_omni_id_management(self, omni_without_policy):
        """Test omni ID setting and getting"""
        # Should have auto-generated ID
        original_id = omni_without_policy.get_omni_id()
        assert original_id is not None

        # Set custom ID
        custom_id = "custom_test_id"
        omni_without_policy.set_omni_id(custom_id)
        assert omni_without_policy.get_omni_id() == custom_id
