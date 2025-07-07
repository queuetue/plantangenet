"""
Demo of policy-enforced TicTacToe game.

This example shows how the new policy mixin allows games to be subject
to policy enforcement, enabling consistent governance across activities.
"""

import asyncio
from examples.tictactoe.game import TicTacToeGame
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role


async def demo_policy_enforced_game():
    """Demonstrate a TicTacToe game with policy enforcement."""

    # Create a policy
    policy = Policy()

    # Create roles with consistent IDs and names
    player_role = Role(
        id="player",  # Use same ID as name for consistency
        name="player",
        description="Can play games",
        members=[]
    )
    spectator_role = Role(
        id="spectator",  # Use same ID as name for consistency
        name="spectator",
        description="Can only view games",
        members=[]
    )
    admin_role = Role(
        id="admin",  # Use same ID as name for consistency
        name="admin",
        description="Can do anything",
        members=[]
    )

    # Add roles to policy
    policy.add_role(player_role)
    policy.add_role(spectator_role)
    policy.add_role(admin_role)

    # Create identities
    alice = Identity(id="alice", nickname="Alice")
    bob = Identity(id="bob", nickname="Bob")
    charlie = Identity(id="charlie", nickname="Charlie")
    admin = Identity(id="admin", nickname="Admin")

    # Add identities to policy
    policy.add_identity(alice)
    policy.add_identity(bob)
    policy.add_identity(charlie)
    policy.add_identity(admin)

    # Assign roles by adding identities to roles
    policy.add_identity_to_role(alice, player_role)
    policy.add_identity_to_role(bob, player_role)
    policy.add_identity_to_role(charlie, spectator_role)
    policy.add_identity_to_role(admin, admin_role)

    # Create policy statements using Role objects (which use role.id internally)
    # Allow players and admins to make moves and join
    policy.add_statement(
        roles=[player_role, admin_role],
        effect="allow",
        action=["move", "join"],
        resource=["activity:*"]
    )

    # Allow everyone to view the board
    policy.add_statement(
        roles=[spectator_role, player_role, admin_role],
        effect="allow",
        action=["view_board"],
        resource=["activity:*"]
    )

    # Explicitly deny spectators from making moves (this should override any allows)
    policy.add_statement(
        roles=[spectator_role],
        effect="deny",
        action=["move", "join"],
        resource=["activity:*"]
    )

    # Debug: Check what's in the policy
    print("=== Policy Debug Info ===")
    print(f"Roles: {list(policy.roles.keys())}")
    print(f"Identities: {list(policy.identities.keys())}")
    print(f"Identity roles: {dict(policy.identity_roles)}")
    print(f"Statements: {len(policy.policies)}")
    for i, stmt in enumerate(policy.policies):
        print(
            f"  Statement {i}: {stmt.effect} {stmt.action} on {stmt.resource} for roles {stmt.role_ids}")
    print()

    # Create a TicTacToe game
    game = TicTacToeGame("demo_game", "alice", "bob")
    game.set_policy(policy)

    print("=== Policy-Enforced TicTacToe Demo ===")
    print(f"Players: Alice vs Bob")
    print(f"Spectator: Charlie")
    print(f"Admin: Admin")
    print()

    # Test 1: Alice (player) makes a valid move
    print("Test 1: Alice (player) makes a move...")
    success, message = game.make_move("alice", 0, 0)
    print(f"Result: {success}, Message: {message}")
    print()

    # Test 2: Bob (player) makes a valid move
    print("Test 2: Bob (player) makes a move...")
    success, message = game.make_move("bob", 1, 1)
    print(f"Result: {success}, Message: {message}")
    print()

    # Test 3: Charlie (spectator) tries to make a move - should be denied
    print("Test 3: Charlie (spectator) tries to make a move...")
    success, message = game.make_move("charlie", 0, 1)
    print(f"Result: {success}, Message: {message}")
    print()

    # Test 4: Charlie (spectator) views the board - should be allowed
    print("Test 4: Charlie (spectator) views the board...")
    try:
        game.require_permission("charlie", "view_board")
        print("Result: True, Charlie can view the board")
    except PermissionError as e:
        print(f"Result: False, {e}")
    print()

    # Test 5: Admin makes a move (even though not in the game) - should be allowed by policy
    print("Test 5: Admin tries to make a move...")
    success, message = game.make_move("admin", 0, 2)
    print(f"Result: {success}, Message: {message}")
    print()

    # Test 6: Show all available permissions for different roles
    print("Available permissions for this activity:")
    permissions = game.get_all_permissions()
    for action, description in permissions.items():
        print(f"  {action}: {description}")
    print()

    # Test 7: Show policy evaluation for different scenarios
    print("Policy evaluation examples:")
    scenarios = [
        ("alice", "move"),
        ("bob", "move"),
        ("charlie", "move"),
        ("charlie", "view_board"),
        ("admin", "move"),
        ("admin", "admin"),
    ]

    for identity_id, action in scenarios:
        result = game.evaluate_policy(identity_id, action)
        print(f"  {identity_id} -> {action}: {result.passed} ({result.reason})")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(demo_policy_enforced_game())
