#!/usr/bin/env python3
"""
Demonstration of the enhanced OmniSquad architecture showing how Squad
inherits from both Omni and Agent for unified management capabilities.
"""

import asyncio
from plantangenet.squad.omni_squad import OmniSquad, ManagerMixin
from plantangenet.policy.identity import Identity
from plantangenet.policy.vanilla import Vanilla
from plantangenet.transport_operations import TransportOperationsManager
from plantangenet.storage_operations import StorageOperationsManager


class EnhancedTransportManager(TransportOperationsManager, ManagerMixin):
    """Enhanced transport manager with common interface."""

    def get_preview(self, action: str, **params) -> dict:
        """Get cost/feasibility preview for transport operations."""
        if action == "publish":
            return self.get_publish_preview(
                params.get('topic', 'default'),
                params.get('data', {})
            )
        elif action == "subscribe":
            return self.get_subscribe_preview(params.get('topic', 'default'))
        else:
            return {"error": f"Unknown action: {action}"}

    async def execute_with_cost(self, action: str, **params) -> dict:
        """Execute transport operation with cost tracking."""
        try:
            if action == "publish":
                result = await self.publish_with_cost(
                    params.get('topic', 'default'),
                    params.get('data', {})
                )
            else:
                result = {"error": f"Unsupported action: {action}"}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}


class EnhancedStorageManager(StorageOperationsManager, ManagerMixin):
    """Enhanced storage manager with common interface."""

    def get_preview(self, action: str, **params) -> dict:
        """Get cost/feasibility preview for storage operations."""
        if action == "save":
            return self.get_save_preview(
                params.get('omni'),
                params.get('incremental', True)
            )
        else:
            return {"error": f"Unknown action: {action}"}

    async def execute_with_cost(self, action: str, **params) -> dict:
        """Execute storage operation with cost tracking."""
        try:
            if action == "save":
                result = await self.save_omni_with_cost(
                    params.get('omni'),
                    params.get('incremental', True)
                )
            else:
                result = {"error": f"Unsupported action: {action}"}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}


class MockOmni:
    """Mock omni object for testing."""

    def __init__(self, omni_id: str = "test_omni"):
        self._omni_id = omni_id
        self._omni_all_fields = ["name", "value"]
        self._dirty_fields = {"name": "Test", "value": 42}

    def get_dirty_fields(self):
        return self._dirty_fields


async def demonstrate_omni_squad():
    """Demonstrate the OmniSquad capabilities."""
    print("🚀 Demonstrating OmniSquad Architecture")
    print("=" * 50)

    # 1. Create policy and identity
    policy = Vanilla(logger=None, namespace="demo")
    admin_identity = Identity(
        id="admin_001", nickname="admin", roles=["admin"])
    user_identity = Identity(id="user_001", nickname="user", roles=["user"])

    policy.add_identity(admin_identity)
    policy.add_identity(user_identity)

    # 2. Create OmniSquad with both Omni and Agent capabilities
    print("\n📋 Creating OmniSquad...")
    squad = OmniSquad(
        name="demo_squad",
        policy=policy,
        namespace="demo"
    )

    print(f"   Squad ID: {squad.id}")
    print(f"   Squad Name: {squad.squad_name}")
    print(f"   Squad Nickname: {squad.name}")
    print(f"   Ocean Ready: {squad.ocean_ready}")

    # 3. Demonstrate session management
    print("\n🎯 Session Management...")
    session1 = squad.create_session(admin_identity)
    session2 = squad.create_session(user_identity)

    print(f"   Created {len(squad.get_sessions())} sessions")
    print(f"   Session count property: {squad.session_count}")

    # 4. Demonstrate group management
    print("\n👥 Group Management...")

    # Create enhanced managers
    transport_mgr = EnhancedTransportManager(session1)
    storage_mgr = EnhancedStorageManager(session1)

    # Add managers to squad groups
    squad.add("transport_managers", transport_mgr)
    squad.add("storage_managers", storage_mgr)
    squad.add("mock_objects", MockOmni("obj1"))
    squad.add("mock_objects", MockOmni("obj2"))

    print(f"   Total groups: {len(squad.get_all_groups())}")
    print(f"   Member count: {squad.member_count}")
    print(
        f"   Transport managers: {len(squad.get_group('transport_managers'))}")
    print(f"   Storage managers: {len(squad.get_group('storage_managers'))}")
    print(f"   Mock objects: {len(squad.get_group('mock_objects'))}")

    # 5. Demonstrate policy-aware object creation
    print("\n🔐 Policy-Aware Object Creation...")
    try:
        mock_obj = squad.create_managed_object(
            MockOmni,
            admin_identity,
            omni_id="policy_test_obj"
        )
        print(f"   ✅ Created object with admin identity: {mock_obj._omni_id}")
    except PermissionError as e:
        print(f"   ❌ Permission denied: {e}")

    # 6. Demonstrate policy caching
    print("\n⚡ Policy Caching...")
    for i in range(3):
        allowed = squad.evaluate_policy_cached(
            admin_identity, "read", "test_resource")
        print(f"   Attempt {i+1}: {'✅ Allowed' if allowed else '❌ Denied'}")

    print(f"   Policy cache hits: {squad._policy_cache_hits}")

    # 7. Demonstrate manager interface uniformity
    print("\n🔧 Unified Manager Interface...")

    # Get previews from different manager types
    transport_preview = transport_mgr.get_preview(
        "publish", topic="test", data="hello")
    storage_preview = storage_mgr.get_preview(
        "save", omni=MockOmni(), incremental=True)
    squad_preview = squad.get_preview("create_session", identity=user_identity)

    print("   Transport preview:", transport_preview.get("action", "N/A"))
    print("   Storage preview:", storage_preview.get("action", "N/A"))
    print("   Squad preview:", squad_preview.get("action", "N/A"))

    # 8. Demonstrate Agent-style updates
    print("\n🔄 Agent-Style Updates...")
    update_success = await squad.update()
    print(f"   Squad update: {'✅ Success' if update_success else '❌ Failed'}")

    # 9. Show comprehensive status
    print("\n📊 Squad Status...")
    status = squad.get_squad_status()

    print(f"   Squad ID: {status['squad_id']}")
    print(f"   Squad Name: {status['squad_name']}")
    print(f"   Groups: {status['groups']}")
    print(f"   Sessions: {status['sessions']}")
    print(f"   Cache Entries: {status['cache_entries']}")
    print(f"   Member Count: {status['member_count']}")
    print(f"   Last Activity: {status['last_activity']}")

    # 10. Demonstrate persistence capabilities (if storage available)
    print("\n💾 Persistence Capabilities...")
    if hasattr(squad, 'save_to_storage'):
        print("   Squad has Omni persistence capabilities")
        # We won't actually save since we don't have storage configured
        print("   (Storage not configured for demo)")
    else:
        print("   Squad persistence would require storage configuration")

    print("\n✨ Demo Complete!")
    print("\nKey Benefits of OmniSquad Architecture:")
    print("• Unified identity and persistence (from Omni)")
    print("• Agent-like coordination capabilities (from Agent)")
    print("• Policy-aware access control")
    print("• Session and object lifecycle management")
    print("• Uniform manager interface")
    print("• Audit trail and performance tracking")
    print("• Distributed coordination ready")


if __name__ == "__main__":
    asyncio.run(demonstrate_omni_squad())
