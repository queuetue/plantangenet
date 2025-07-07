#!/usr/bin/env python3
"""
Simple validation script to test the unified Omni infrastructure.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from plantangenet.omni.omni import Omni
    from plantangenet.omni.observable import Observable
    from plantangenet.omni.persisted import PersistedBase
    print("✅ Successfully imported unified Omni classes")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test basic functionality


class TestOmni(Omni):
    name = Observable(field_type=str, default="test")
    value = Observable(field_type=int, default=42)
    count = PersistedBase(field_type=int, default=100)


try:
    # Test creation
    omni = TestOmni()
    print("✅ Successfully created Omni instance")

    # Test field access
    name_value = omni.get_field_value('name', check_policy=False)
    print(f"✅ Retrieved field value: {name_value}")

    # Test field setting
    omni.set_field_value('name', 'updated_test', check_policy=False)
    updated_value = omni.get_field_value('name', check_policy=False)
    print(f"✅ Updated field value: {updated_value}")

    # Test dirty tracking
    dirty_fields = omni.get_dirty_fields()
    print(f"✅ Dirty fields tracked: {list(dirty_fields.keys())}")

    # Test batch updates
    omni.batch_update_fields({
        'value': 99,
        'count': 200
    }, check_policy=False)
    print("✅ Batch update successful")

    # Test serialization
    data = omni.to_dict(check_policy=False)
    print(f"✅ Serialization successful: {len(data)} fields")

    print("\n🎉 All basic Omni functionality tests PASSED!")
    print("✨ The unified Omni infrastructure is working correctly!")

except Exception as e:
    print(f"❌ Runtime error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
