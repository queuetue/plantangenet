#!/usr/bin/env python3
"""
Test the efficiency improvements from centralizing policy checks at the omni level.
"""

import time
import pytest
from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.base import Identity, Role

# Test both old and new approaches for comparison


def test_efficiency_comparison():
    """Compare old per-field vs new omni-level policy enforcement"""

    # Setup policy
    policy = Vanilla(logger=None, namespace="test")
    identity = Identity("user1", "Test User")
    admin_role = Role("admin_role", "admin", "Admin role")

    policy.add_identity(identity)
    policy.add_role(admin_role)
    policy.add_identity_to_role(identity, admin_role)
    policy.add_statement(["admin"], "allow", ["read", "write"], "*")

    print("🔬 Testing efficiency improvements...")

    # Test 1: Old approach (per-field policy checks)
    from plantangenet.omni.observable import Observable as OldObservable
    from plantangenet.omni.persisted import PersistedBase as OldPersistedBase
    from plantangenet.omni.omni import Omni as OldOmni

    class OldTestOmni(OldOmni):
        field1 = OldObservable(field_type=int, default=0)
        field2 = OldObservable(field_type=int, default=0)
        field3 = OldObservable(field_type=int, default=0)
        field4 = OldObservable(field_type=int, default=0)
        field5 = OldObservable(field_type=int, default=0)

        def __init__(self, session=None, policy=None):
            super().__init__()
            self.session = session
            self.policy = policy

    # Test 2: New approach (omni-level policy checks)
    from plantangenet.omni.enhanced_omni import EnhancedOmni
    from plantangenet.omni.efficient_descriptors import EfficientObservable

    class NewTestOmni(EnhancedOmni):
        field1 = EfficientObservable(field_type=int, default=0)
        field2 = EfficientObservable(field_type=int, default=0)
        field3 = EfficientObservable(field_type=int, default=0)
        field4 = EfficientObservable(field_type=int, default=0)
        field5 = EfficientObservable(field_type=int, default=0)

    # Benchmark old approach
    old_omni = OldTestOmni(session=identity, policy=policy)

    start_time = time.perf_counter()
    for i in range(100):
        # Each field access triggers individual policy check
        old_omni.field1 = i
        old_omni.field2 = i + 1
        old_omni.field3 = i + 2
        old_omni.field4 = i + 3
        old_omni.field5 = i + 4

        # Each read also triggers individual policy check
        _ = old_omni.field1
        _ = old_omni.field2
        _ = old_omni.field3
        _ = old_omni.field4
        _ = old_omni.field5
    old_time = time.perf_counter() - start_time

    # Benchmark new approach
    new_omni = NewTestOmni(identity=identity, policy=policy)

    start_time = time.perf_counter()
    for i in range(100):
        # Batch update with single policy check
        new_omni.batch_update_fields({
            'field1': i,
            'field2': i + 1,
            'field3': i + 2,
            'field4': i + 3,
            'field5': i + 4
        })

        # Reads use cached policy decision
        _ = new_omni.get_field_value('field1')
        _ = new_omni.get_field_value('field2')
        _ = new_omni.get_field_value('field3')
        _ = new_omni.get_field_value('field4')
        _ = new_omni.get_field_value('field5')
    new_time = time.perf_counter() - start_time

    # Results
    improvement = (old_time - new_time) / old_time * 100
    print(f"Old approach (per-field): {old_time:.4f}s")
    print(f"New approach (omni-level): {new_time:.4f}s")
    print(f"Improvement: {improvement:.1f}% faster")

    # Test dirty field tracking efficiency
    print("\n🔧 Testing dirty field tracking...")

    # New approach tracks dirty fields efficiently
    new_omni.clear_dirty_fields()
    assert not new_omni.has_dirty_fields()

    new_omni.batch_update_fields({
        'field1': 999,
        'field3': 888
    })

    dirty = new_omni.get_dirty_fields()
    assert 'field1' in dirty
    assert 'field3' in dirty
    assert 'field2' not in dirty
    assert dirty['field1'] == 999
    assert dirty['field3'] == 888

    print(f"✅ Dirty tracking: {len(dirty)} fields changed")

    # Test policy caching
    print("\n⚡ Testing policy caching...")

    # First access should check policy
    start_time = time.perf_counter()
    new_omni.get_field_value('field1')
    first_access_time = time.perf_counter() - start_time

    # Subsequent accesses should use cache
    start_time = time.perf_counter()
    for _ in range(10):
        new_omni.get_field_value('field1')
    cached_access_time = (time.perf_counter() - start_time) / 10

    cache_improvement = (first_access_time -
                         cached_access_time) / first_access_time * 100
    print(f"First access: {first_access_time:.6f}s")
    print(f"Cached access: {cached_access_time:.6f}s")
    print(f"Cache improvement: {cache_improvement:.1f}% faster")

    print("\n🎉 All efficiency tests passed!")


@pytest.mark.asyncio
async def test_storage_integration_efficiency():
    """Test efficient storage integration"""

    from plantangenet.omni.enhanced_omni import EnhancedOmni
    from plantangenet.omni.efficient_descriptors import EfficientObservable

    class StorageTestOmni(EnhancedOmni):
        name = EfficientObservable(field_type=str, default="")
        value = EfficientObservable(field_type=int, default=0)
        count = EfficientObservable(field_type=int, default=42)

    # Mock storage that tracks operations
    class MockStorage:
        def __init__(self):
            self.operations = []

        async def store_omni_structured(self, omni_id, fields, **kwargs):
            self.operations.append(('store_structured', omni_id, len(fields)))
            return True

        async def update_omni_fields(self, omni_id, dirty_fields, **kwargs):
            self.operations.append(
                ('update_fields', omni_id, len(dirty_fields)))
            return True

        async def load_omni_structured(self, omni_id, **kwargs):
            self.operations.append(('load_structured', omni_id))
            return {
                'name': 'loaded_name',
                'value': 123,
                'count': 456
            }

    storage = MockStorage()
    omni = StorageTestOmni(storage=storage)

    # Test incremental updates (only dirty fields)
    omni.batch_update_fields({
        'name': 'test_name',
        'value': 100
    })

    success = await omni.save_to_storage(incremental=True)
    assert success

    # Should have called update_fields with 2 dirty fields
    assert storage.operations[-1] == ('update_fields', omni._omni_id, 2)

    # Test full save
    success = await omni.save_to_storage(incremental=False)
    assert success

    # Should have called store_structured with all 3 fields
    assert storage.operations[-1] == ('store_structured', omni._omni_id, 3)

    # Test load
    success = await omni.load_from_storage()
    assert success
    assert omni.get_field_value('name', check_policy=False) == 'loaded_name'
    assert omni.get_field_value('value', check_policy=False) == 123

    print("✅ Storage integration efficiency tests passed!")


def test_constraint_enforcement():
    """Test that descriptors only work in EnhancedOmni classes"""

    from plantangenet.omni.efficient_descriptors import EfficientObservable

    # Should fail when used outside EnhancedOmni
    try:
        class InvalidClass:
            field = EfficientObservable(field_type=int, default=0)

        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "can only be used in EnhancedOmni subclasses" in str(e)
        print("✅ Constraint enforcement works - descriptors rejected outside EnhancedOmni")

    # Should work when used in EnhancedOmni
    from plantangenet.omni.enhanced_omni import EnhancedOmni

    class ValidClass(EnhancedOmni):
        field = EfficientObservable(field_type=int, default=0)

    omni = ValidClass()
    omni.set_field_value('field', 42, check_policy=False)
    assert omni.get_field_value('field', check_policy=False) == 42

    print("✅ Valid usage in EnhancedOmni works correctly")


if __name__ == "__main__":
    import asyncio

    async def main():
        test_efficiency_comparison()
        print()
        await test_storage_integration_efficiency()
        print()
        test_constraint_enforcement()
        print("\n🎉 All efficiency improvement tests passed!")

    asyncio.run(main())
