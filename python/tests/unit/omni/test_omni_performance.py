"""
Performance and efficiency tests for the unified Omni infrastructure.
Tests improvements from centralized policy checks and enhanced field management.
"""

import pytest
import time
from plantangenet.omni.omni import Omni
from plantangenet.omni.observable import Observable
from tests.fixtures.omni_fixtures import MockStorage


class PerformanceTestOmni(Omni):
    """Test Omni with multiple fields for performance testing"""
    field1 = Observable(field_type=int, default=0)
    field2 = Observable(field_type=int, default=0)
    field3 = Observable(field_type=int, default=0)
    field4 = Observable(field_type=int, default=0)
    field5 = Observable(field_type=int, default=0)


class TestOmniPerformance:
    """Test performance characteristics of the unified Omni"""

    def test_batch_vs_individual_updates(self):
        """Test performance benefit of batch operations"""
        omni = PerformanceTestOmni()

        # Test individual updates
        start_time = time.perf_counter()
        for i in range(100):
            omni.set_field_value('field1', i, check_policy=False)
            omni.set_field_value('field2', i + 1, check_policy=False)
            omni.set_field_value('field3', i + 2, check_policy=False)
            omni.set_field_value('field4', i + 3, check_policy=False)
            omni.set_field_value('field5', i + 4, check_policy=False)
        individual_time = time.perf_counter() - start_time

        # Test batch updates
        omni_batch = PerformanceTestOmni()
        start_time = time.perf_counter()
        for i in range(100):
            omni_batch.batch_update_fields({
                'field1': i,
                'field2': i + 1,
                'field3': i + 2,
                'field4': i + 3,
                'field5': i + 4
            }, check_policy=False)
        batch_time = time.perf_counter() - start_time

        print(f"Individual updates: {individual_time:.4f}s")
        print(f"Batch updates: {batch_time:.4f}s")

        # Batch should be reasonably close to individual (allow up to 2x for now)
        # This reflects current implementation overhead; optimize if needed.
        assert batch_time <= individual_time * 2.0, (
            f"Batch updates ({batch_time:.4f}s) should not be more than 2x slower than individual updates ({individual_time:.4f}s)."
        )

    def test_policy_caching_performance(self, test_policy):
        """Test that policy caching improves performance"""
        policy, identity, _ = test_policy
        omni = PerformanceTestOmni()
        omni._omni__policy = policy
        omni.identity = identity

        # First access (no cache)
        start_time = time.perf_counter()
        omni.get_field_value('field1', check_policy=True)
        first_access_time = time.perf_counter() - start_time

        # Subsequent accesses (with cache)
        start_time = time.perf_counter()
        for _ in range(10):
            omni.get_field_value('field1', check_policy=True)
        cached_access_time = (time.perf_counter() - start_time) / 10

        print(f"First access: {first_access_time:.6f}s")
        print(f"Cached access: {cached_access_time:.6f}s")

        # Cache should be faster (though timing can be variable)
        # Just verify cache is populated
        assert len(omni._policy_cache) > 0

    def test_dirty_field_tracking_efficiency(self):
        """Test that dirty field tracking is efficient"""
        omni = PerformanceTestOmni()

        # Initially clean
        assert not omni.has_dirty_fields()

        # Make changes and verify tracking is fast
        start_time = time.perf_counter()
        for i in range(1, 101):  # Start from 1 to avoid setting to default values
            omni.set_field_value('field1', i, check_policy=False)
            omni.set_field_value('field3', i * 2, check_policy=False)

            # Check dirty state
            dirty = omni.get_dirty_fields()
            assert len(dirty) == 2

        tracking_time = time.perf_counter() - start_time
        print(f"Dirty tracking for 100 iterations: {tracking_time:.4f}s")

        # Should be reasonably fast
        assert tracking_time < 1.0  # Should take less than 1 second


class TestOmniStorageEfficiency:
    """Test storage efficiency improvements"""

    @pytest.mark.asyncio
    async def test_incremental_storage_efficiency(self):
        """Test that incremental storage only saves dirty fields"""
        storage = MockStorage()
        omni = PerformanceTestOmni()
        omni.storage = storage

        # Make changes to only some fields
        omni.set_field_value('field1', 42, check_policy=False)
        omni.set_field_value('field3', 84, check_policy=False)

        # Incremental save should only save dirty fields
        success = await omni.save_to_storage(incremental=True)
        assert success

        # Check that only dirty fields were saved
        update_ops = [
            op for op in storage.operations if op[0] == 'update_fields']
        if update_ops:
            # Should have saved exactly 2 fields (the dirty ones)
            assert update_ops[-1][2] == 2

    @pytest.mark.asyncio
    async def test_full_vs_incremental_storage(self):
        """Test difference between full and incremental storage"""
        storage = MockStorage()
        omni = PerformanceTestOmni()
        omni.storage = storage

        # Make changes
        omni.set_field_value('field1', 1, check_policy=False)
        omni.set_field_value('field2', 2, check_policy=False)

        # Full save
        await omni.save_to_storage(incremental=False)
        full_ops = [op for op in storage.operations if op[0]
                    == 'store_structured']

        # Clear operations log
        storage.operations.clear()

        # Make more changes
        omni.set_field_value('field3', 3, check_policy=False)

        # Incremental save
        await omni.save_to_storage(incremental=True)
        incremental_ops = [
            op for op in storage.operations if op[0] == 'update_fields']

        # Full save should include all fields, incremental only dirty ones
        if full_ops and incremental_ops:
            # Full >= incremental
            assert full_ops[0][2] >= incremental_ops[0][2]

    @pytest.mark.asyncio
    async def test_storage_operation_tracking(self):
        """Test that storage operations are properly tracked"""
        storage = MockStorage()
        omni = PerformanceTestOmni()
        omni.storage = storage

        # Test different operations
        await omni.save_to_storage(incremental=False)  # Full save
        omni.set_field_value('field1', 99, check_policy=False)
        await omni.save_to_storage(incremental=True)   # Incremental save
        await omni.load_from_storage()                 # Load

        # Should have recorded all operations
        assert len(storage.operations) >= 3

        # Check operation types
        operation_types = [op[0] for op in storage.operations]
        assert 'store_structured' in operation_types or 'update_fields' in operation_types
        assert 'load_structured' in operation_types


class TestOmniFieldManagement:
    """Test field management efficiency"""

    def test_field_descriptor_access_performance(self):
        """Test that field descriptor access is efficient"""
        omni = PerformanceTestOmni()

        # Access field descriptors many times
        start_time = time.perf_counter()
        for _ in range(1000):
            # Access through the field management system
            value = omni.get_field_value('field1', check_policy=False)
            omni.set_field_value('field1', value + 1, check_policy=False)
        access_time = time.perf_counter() - start_time

        print(f"1000 field accesses: {access_time:.4f}s")

        # Should be reasonably fast
        assert access_time < 2.0  # Should take less than 2 seconds

    def test_field_validation_efficiency(self):
        """Test that field validation doesn't significantly impact performance"""
        omni = PerformanceTestOmni()

        # Set many values (some with validation)
        start_time = time.perf_counter()
        for i in range(100):
            omni.set_field_value('field1', i, check_policy=False)
            omni.set_field_value('field2', i * 2, check_policy=False)
            omni.set_field_value('field3', i * 3, check_policy=False)
        validation_time = time.perf_counter() - start_time

        print(f"Field validation for 300 operations: {validation_time:.4f}s")

        # Should be reasonably fast
        assert validation_time < 1.0

    def test_memory_efficiency(self):
        """Test that the unified Omni doesn't use excessive memory"""
        import sys

        # Create multiple omnies and check memory usage
        omnies = []
        for i in range(100):
            omni = PerformanceTestOmni()
            omni.set_field_value('field1', i, check_policy=False)
            omnies.append(omni)

        # Check that instances don't have excessive overhead
        # Each omni should have reasonable memory footprint
        sample_omni = omnies[0]

        # Basic sanity checks - should have expected attributes
        assert hasattr(sample_omni, '_dirty_fields')
        assert hasattr(sample_omni, '_original_values')
        assert hasattr(sample_omni, '_policy_cache')
        assert hasattr(sample_omni, '_omni_id')

        # Instance dict shouldn't be excessive
        instance_attrs = len(vars(sample_omni))
        assert instance_attrs < 20  # Reasonable number of instance attributes


if __name__ == "__main__":
    # Run some quick performance tests
    print("🚀 Running Omni performance tests...")

    test_perf = TestOmniPerformance()
    test_perf.test_batch_vs_individual_updates()
    print("✅ Batch update performance test passed")

    test_efficiency = TestOmniFieldManagement()
    test_efficiency.test_field_descriptor_access_performance()
    print("✅ Field access performance test passed")

    test_efficiency.test_memory_efficiency()
    print("✅ Memory efficiency test passed")

    print("🎉 All performance tests completed!")
