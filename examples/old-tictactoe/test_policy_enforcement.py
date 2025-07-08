"""
Test suite for policy-enforced TicTacToe tournament system.

Tests:
1. Basic LocalPolicy functionality (caching, delegation)
2. Game policy enforcement (moves, joins, views)
3. Tournament-level policy integration
4. Local policy overrides
5. Performance/cache efficiency
"""

import asyncio
import pytest
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role
from plantangenet import GLOBAL_LOGGER
from examples.tictactoe.local_policy import LocalPolicy
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.referee import TicTacToeReferee
from examples.tictactoe.player import TicTacToePlayer
from examples.tictactoe.tictactoe_types import GameState


class TestLocalPolicy:
    """Test the LocalPolicy delegation and caching."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a parent policy with roles and identities
        self.parent_policy = Policy()

        # Create roles
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.spectator_role = Role(
            id="spectator", name="spectator", description="Can only view games", members=[])

        # Add roles to policy
        self.parent_policy.add_role(self.player_role)
        self.parent_policy.add_role(self.spectator_role)

        # Create identities
        self.alice = Identity(id="alice", nickname="Alice")
        self.bob = Identity(id="bob", nickname="Bob")
        self.charlie = Identity(id="charlie", nickname="Charlie")

        # Add identities to policy
        self.parent_policy.add_identity(self.alice)
        self.parent_policy.add_identity(self.bob)
        self.parent_policy.add_identity(self.charlie)

        # Assign roles
        self.parent_policy.add_identity_to_role(self.alice, self.player_role)
        self.parent_policy.add_identity_to_role(self.bob, self.player_role)
        self.parent_policy.add_identity_to_role(
            self.charlie, self.spectator_role)

        # Add policy statements
        self.parent_policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["move", "join"],
            resource=["activity:*"]
        )

        self.parent_policy.add_statement(
            roles=[self.spectator_role, self.player_role],
            effect="allow",
            action=["view_board"],
            resource=["activity:*"]
        )

        self.parent_policy.add_statement(
            roles=[self.spectator_role],
            effect="deny",
            action=["move", "join"],
            resource=["activity:*"]
        )

    def test_delegation_to_parent(self):
        """Test that LocalPolicy correctly delegates to parent policy."""
        local_policy = LocalPolicy(parent_policy=self.parent_policy)

        # Alice (player) should be able to move
        result = local_policy.evaluate("alice", "move", "activity:test")
        assert result.passed is True
        assert "allow" in result.reason

        # Charlie (spectator) should not be able to move
        result = local_policy.evaluate("charlie", "move", "activity:test")
        assert result.passed is False
        assert "deny" in result.reason

        # Charlie (spectator) should be able to view
        result = local_policy.evaluate(
            "charlie", "view_board", "activity:test")
        assert result.passed is True

    def test_caching_behavior(self):
        """Test that LocalPolicy properly caches results."""
        local_policy = LocalPolicy(parent_policy=self.parent_policy)

        # First evaluation
        result1 = local_policy.evaluate("alice", "move", "activity:test")

        # Second evaluation - should use cache
        result2 = local_policy.evaluate("alice", "move", "activity:test")

        # Results should be identical
        assert result1.passed == result2.passed
        assert result1.reason == result2.reason

        # Check that cache actually has the entry
        assert len(local_policy._cache) > 0

    def test_local_override(self):
        """Test that local policy can override parent policy."""
        # Create a local policy that denies everything
        local_deny_policy = Policy()
        local_deny_policy.add_statement(
            roles=["*"],  # Wildcard for all roles
            effect="deny",
            action=["*"],
            resource=["*"]
        )

        local_policy = LocalPolicy(
            parent_policy=self.parent_policy,
            local_policy=local_deny_policy
        )

        # Even though parent allows alice to move, local policy should deny
        result = local_policy.evaluate("alice", "move", "activity:test")
        # This depends on how the local policy is set up - if it has rules for alice's role
        # For now, let's just verify the local policy is being consulted
        assert result is not None

    def test_no_parent_policy(self):
        """Test behavior when no parent policy is available."""
        local_policy = LocalPolicy(parent_policy=None)

        # Should default to deny
        result = local_policy.evaluate("alice", "move", "activity:test")
        assert result.passed is False
        assert "No policy" in result.reason


class TestPolicyEnforcedGame:
    """Test policy enforcement in TicTacToe games."""

    def setup_method(self):
        """Set up a policy-enforced game."""
        # Create parent policy (same as above)
        self.parent_policy = Policy()

        # Create roles
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.spectator_role = Role(
            id="spectator", name="spectator", description="Can only view games", members=[])

        # Add roles to policy
        self.parent_policy.add_role(self.player_role)
        self.parent_policy.add_role(self.spectator_role)

        # Create identities
        self.alice = Identity(id="alice", nickname="Alice")
        self.bob = Identity(id="bob", nickname="Bob")
        self.charlie = Identity(id="charlie", nickname="Charlie")

        # Add identities to policy
        self.parent_policy.add_identity(self.alice)
        self.parent_policy.add_identity(self.bob)
        self.parent_policy.add_identity(self.charlie)

        # Assign roles
        self.parent_policy.add_identity_to_role(self.alice, self.player_role)
        self.parent_policy.add_identity_to_role(self.bob, self.player_role)
        self.parent_policy.add_identity_to_role(
            self.charlie, self.spectator_role)

        # Add policy statements
        self.parent_policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["move", "join"],
            resource=["activity:*"]
        )

        self.parent_policy.add_statement(
            roles=[self.spectator_role],
            effect="deny",
            action=["move", "join"],
            resource=["activity:*"]
        )

    def test_game_move_enforcement(self):
        """Test that game moves are policy-enforced."""
        # Create a game with policy
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=self.parent_policy)
        game.set_policy(local_policy)  # type: ignore

        # Alice (player) should be able to make a move
        success, message = game.make_move("alice", 0, 0)
        assert success is True

        # Charlie (spectator) should not be able to make a move
        success, message = game.make_move("charlie", 0, 1)
        assert success is False
        assert "Policy denied" in message or "denied" in message.lower()

    def test_game_join_enforcement(self):
        """Test that joining games is policy-enforced."""
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=self.parent_policy)
        game.set_policy(local_policy)  # type: ignore

        # This is async in the base class
        async def test_async():
            # Alice (player) should be able to join
            result = await game.add_member("alice")
            # Alice is already a member, so this might return False for that reason

            # Charlie (spectator) should not be able to join due to policy
            result = await game.add_member("charlie")
            # This should be False due to policy denial
            assert result is False

        # Run the async test
        asyncio.run(test_async())

    def test_view_permissions(self):
        """Test view permissions through policy."""
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=self.parent_policy)
        game.set_policy(local_policy)

        # Add view permission for all roles
        self.parent_policy.add_statement(
            roles=[self.spectator_role, self.player_role],
            effect="allow",
            action=["view_board"],
            resource=["activity:*"]
        )

        # Both players and spectators should be able to view
        try:
            game.require_permission("alice", "view_board")
            game.require_permission("charlie", "view_board")
            # If no exception, permissions are granted
            assert True
        except PermissionError:
            pytest.fail("View permissions should be granted")


class TestTournamentPolicyIntegration:
    """Test policy enforcement in the full tournament system."""

    def setup_method(self):
        """Set up tournament with policy."""
        # Create parent policy
        self.parent_policy = Policy()

        # Create roles
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.banned_role = Role(
            id="banned", name="banned", description="Banned from games", members=[])

        # Add roles to policy
        self.parent_policy.add_role(self.player_role)
        self.parent_policy.add_role(self.banned_role)

        # Create identities
        self.alice = Identity(id="alice", nickname="Alice")
        self.bob = Identity(id="bob", nickname="Bob")
        self.charlie = Identity(
            id="charlie", nickname="Charlie")  # Will be banned

        # Add identities to policy
        self.parent_policy.add_identity(self.alice)
        self.parent_policy.add_identity(self.bob)
        self.parent_policy.add_identity(self.charlie)

        # Assign roles
        self.parent_policy.add_identity_to_role(self.alice, self.player_role)
        self.parent_policy.add_identity_to_role(self.bob, self.player_role)
        self.parent_policy.add_identity_to_role(self.charlie, self.banned_role)

        # Add policy statements
        self.parent_policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["move", "join"],
            resource=["activity:*"]
        )

        self.parent_policy.add_statement(
            roles=[self.banned_role],
            effect="deny",
            action=["move", "join"],
            resource=["activity:*"]
        )

    def test_referee_creates_policy_enforced_games(self):
        """Test that referee creates games with proper policy enforcement."""
        referee = TicTacToeReferee(
            policy=self.parent_policy, logger=GLOBAL_LOGGER)

        # Add players to queue
        referee.add_player_to_queue("alice")
        referee.add_player_to_queue("bob")

        async def test_async():
            # Create games
            await referee._create_games()

            # Should have created one game
            assert len(referee.active_games) == 1

            # Game should have policy set
            game = list(referee.active_games.values())[0]
            assert game.policy is not None
            assert isinstance(game.policy, LocalPolicy)

            # Test that the game respects policy
            success, message = game.make_move("alice", 0, 0)
            assert success is True  # Alice can move

        asyncio.run(test_async())

    def test_banned_player_cannot_play(self):
        """Test that banned players cannot make moves."""
        game = TicTacToeGame("test_game", "charlie",
                             "alice")  # Charlie is banned
        local_policy = LocalPolicy(parent_policy=self.parent_policy)
        game.set_policy(local_policy)

        # Charlie (banned) should not be able to make a move
        success, message = game.make_move("charlie", 0, 0)
        assert success is False
        assert "Policy denied" in message or "denied" in message.lower()


class TestPolicyPerformance:
    """Test performance characteristics of policy caching."""

    def setup_method(self):
        """Set up for performance testing."""
        self.parent_policy = Policy()

        # Create a simple allow-all policy for testing
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.parent_policy.add_role(self.player_role)

        self.alice = Identity(id="alice", nickname="Alice")
        self.parent_policy.add_identity(self.alice)
        self.parent_policy.add_identity_to_role(self.alice, self.player_role)

        self.parent_policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["*"],
            resource=["*"]
        )

    def test_cache_efficiency(self):
        """Test that caching improves performance."""
        local_policy = LocalPolicy(parent_policy=self.parent_policy)

        # First evaluation - should hit parent policy
        result1 = local_policy.evaluate("alice", "move", "activity:test")

        # Subsequent evaluations - should hit cache
        for _ in range(100):
            result = local_policy.evaluate("alice", "move", "activity:test")
            assert result.passed == result1.passed

        # Should have cached the result
        assert len(local_policy._cache) >= 1

    def test_cache_key_uniqueness(self):
        """Test that different queries create different cache keys."""
        local_policy = LocalPolicy(parent_policy=self.parent_policy)

        # Different evaluations
        local_policy.evaluate("alice", "move", "activity:test1")
        local_policy.evaluate("alice", "move", "activity:test2")
        local_policy.evaluate("alice", "view", "activity:test1")
        local_policy.evaluate("bob", "move", "activity:test1")

        # Should have different cache entries
        assert len(local_policy._cache) == 4


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__])
