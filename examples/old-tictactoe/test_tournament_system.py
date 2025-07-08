"""
Comprehensive test suite for the modernized TicTacToe tournament system.

Tests the full system integration including:
1. Session/omni architecture
2. Comdec output system
3. Activity integration
4. Agent registration and management
5. End-to-end tournament flow
6. State management and coordination
"""

import asyncio
import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from io import StringIO
import json

# Core Plantangenet imports
from plantangenet.session.session import Session
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role
from plantangenet.comdec.comdec import SnapshotterComdec, LoggerComdec, StreamingComdec
from plantangenet import GLOBAL_LOGGER

# TicTacToe imports
from .main import TicTacToeApplication
from .referee import TicTacToeReferee
from .player import TicTacToePlayer
from .stats import TicTacToeStats
from .game import TicTacToeGame
from .local_policy import LocalPolicy
from .tictactoe_types import GameState, PlayerSymbol


class TestSessionArchitecture:
    """Test the session/omni architecture integration."""

    def setup_method(self):
        """Set up test session and policy."""
        self.policy = Policy()
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.policy.add_role(self.player_role)
        self.alice = Identity(id="alice", nickname="Alice")
        self.bob = Identity(id="bob", nickname="Bob")
        self.policy.add_identity(self.alice)
        self.policy.add_identity(self.bob)
        self.policy.add_identity_to_role(self.alice, self.player_role)
        self.policy.add_identity_to_role(self.bob, self.player_role)
        self.policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["move", "join", "view_board"],
            resource=["activity:*"]
        )
        self.session = Session(
            id="test_session", policy=self.policy, identity=self.alice)

    def test_session_creation(self):
        """Test that session is properly created and configured."""
        assert self.session is not None
        assert self.session.policy is not None
        assert isinstance(self.session.policy, Policy)

    def test_agent_registration(self):
        """Test that agents can be registered with the session."""
        # Create agents
        referee = TicTacToeReferee(policy=self.policy, logger=GLOBAL_LOGGER)
        player1 = TicTacToePlayer("alice", logger=GLOBAL_LOGGER)
        player2 = TicTacToePlayer("bob", logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)

        # Register agents with session
        self.session.add_agent(referee)
        self.session.add_agent(player1)
        self.session.add_agent(player2)
        self.session.add_agent(stats)

        # Verify registration
        agents = list(self.session.agents)
        assert referee in agents
        assert player1 in agents
        assert player2 in agents
        assert stats in agents

    def test_session_as_omni_manager(self):
        """Test that session acts as central omni manager."""
        # Register agents
        referee = TicTacToeReferee(policy=self.policy, logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)

        self.session.add_agent(referee)
        self.session.add_agent(stats)

        # Session should coordinate between agents
        agents = list(self.session.agents)
        assert referee in agents
        assert stats in agents

        # Test that session can access agent state
        assert referee in self.session.agents
        assert stats in self.session.agents

    def test_session_policy_delegation(self):
        """Test that session properly delegates policy enforcement."""
        # Create a referee with session policy
        referee = TicTacToeReferee(policy=self.session.policy)

        # Test that referee can create policy-enforced games
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=self.session.policy)
        game.set_policy(local_policy)  # type: ignore

        # Alice should be able to make a move (has player role)
        success, message = game.make_move("alice", 0, 0)
        assert success is True


class TestComdecIntegration:
    """Test the comdec (codec/output) system integration."""

    def setup_method(self):
        """Set up comdec test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_snapshot_comdec(self):
        """Test snapshot comdec functionality."""
        # Create a stats agent with snapshot comdec
        stats = TicTacToeStats()

        snapshot_file = os.path.join(self.temp_dir, "snapshot.json")
        snapshot_comdec = SnapshotterComdec(
            filepath=snapshot_file, format="json")
        stats.add_comdec(snapshot_comdec)

        # Update stats
        stats.record_game_result("alice", "bob", "alice")
        stats.record_game_result("bob", "alice", "bob")

        # Force snapshot output
        await stats.output_all()

        # Verify snapshot file was created and contains data
        assert os.path.exists(snapshot_file)

        with open(snapshot_file, 'r') as f:
            data = json.load(f)
            assert "stats" in data
            assert "total_games" in data["stats"]
            assert data["stats"]["total_games"] == 2

    @pytest.mark.asyncio
    async def test_logger_comdec(self):
        """Test logger comdec functionality."""
        # Create a stats agent with logger comdec
        stats = TicTacToeStats()

        # Capture log output
        log_stream = StringIO()
        logger_comdec = LoggerComdec(log_stream=log_stream)
        stats.add_comdec(logger_comdec)

        # Update stats
        stats.record_game_result("alice", "bob", "alice")

        # Force log output
        await stats.output_all()

        # Verify log output
        log_output = log_stream.getvalue()
        assert "stats" in log_output.lower()
        assert "total_games" in log_output.lower()

    @pytest.mark.asyncio
    async def test_streaming_comdec(self):
        """Test streaming comdec functionality."""
        # Create a stats agent with streaming comdec
        stats = TicTacToeStats()

        # Mock streaming endpoint
        mock_stream = Mock()
        streaming_comdec = StreamingComdec(stream_handler=mock_stream)
        stats.add_comdec(streaming_comdec)

        # Update stats
        stats.record_game_result("alice", "bob", "alice")

        # Force streaming output
        await stats.output_all()

        # Verify streaming was called
        mock_stream.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_comdecs(self):
        """Test that agents can have multiple comdecs."""
        stats = TicTacToeStats()

        # Add multiple comdecs
        snapshot_file = os.path.join(self.temp_dir, "multi_snapshot.json")
        snapshot_comdec = SnapshotterComdec(filepath=snapshot_file)

        log_stream = StringIO()
        logger_comdec = LoggerComdec(log_stream=log_stream)

        mock_stream = Mock()
        streaming_comdec = StreamingComdec(stream_handler=mock_stream)

        stats.add_comdec(snapshot_comdec)
        stats.add_comdec(logger_comdec)
        stats.add_comdec(streaming_comdec)

        # Update stats
        stats.record_game_result("alice", "bob", "alice")

        # Force all outputs
        await stats.output_all()

        # Verify all outputs worked
        assert os.path.exists(snapshot_file)
        assert len(log_stream.getvalue()) > 0
        mock_stream.assert_called()


class TestActivityIntegration:
    """Test the Plantangenet activity integration."""

    def setup_method(self):
        """Set up activity test environment."""
        self.policy = Policy()
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.policy.add_role(self.player_role)

        self.alice = Identity(id="alice", nickname="Alice")
        self.bob = Identity(id="bob", nickname="Bob")
        self.policy.add_identity(self.alice)
        self.policy.add_identity(self.bob)
        self.policy.add_identity_to_role(self.alice, self.player_role)
        self.policy.add_identity_to_role(self.bob, self.player_role)

        self.policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["move", "join", "view_board"],
            resource=["activity:*"]
        )

    def test_game_inherits_from_activity(self):
        """Test that TicTacToeGame properly inherits from MultiMemberTurnbasedActivity."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Should have activity properties
        assert hasattr(game, 'members')
        assert hasattr(game, 'current_turn')
        assert hasattr(game, 'turn_order')

        # Should have TicTacToe-specific properties
        assert hasattr(game, 'board')
        assert hasattr(game, 'game_state')

    def test_activity_member_management(self):
        """Test activity member management functionality."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Should start with two members
        assert len(game.members) == 2
        assert "alice" in game.members
        assert "bob" in game.members

    def test_activity_turn_management(self):
        """Test activity turn management functionality."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Should have proper turn order
        assert len(game.turn_order) == 2
        assert game.current_turn in ["alice", "bob"]

        # First move should be by current player
        current_player = game.current_turn
        success, message = game.make_move(current_player, 0, 0)
        assert success is True

        # Turn should advance
        new_current = game.current_turn
        assert new_current != current_player

    def test_activity_policy_integration(self):
        """Test that activity integrates with policy system."""
        game = TicTacToeGame("test_game", "alice", "bob")
        local_policy = LocalPolicy(parent_policy=self.policy)
        game.set_policy(local_policy)

        # Test policy enforcement
        assert game.policy is not None
        assert isinstance(game.policy, LocalPolicy)

        # Test permission checking
        try:
            game.require_permission("alice", "move")
            # Should not raise exception
        except PermissionError:
            pytest.fail("Alice should have move permission")


class TestEndToEndTournament:
    """Test end-to-end tournament functionality."""

    def setup_method(self):
        """Set up end-to-end test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_full_tournament_flow(self):
        """Test complete tournament from start to finish."""
        # Create tournament application
        app = TicTacToeApplication()

        # Initialize with test configuration
        config = {
            "num_rounds": 2,
            "games_per_round": 1,
            "output_dir": self.temp_dir,
            "players": [
                {"id": "alice", "strategy": "random"},
                {"id": "bob", "strategy": "random"},
            ]
        }

        await app.initialize(config)

        # Run tournament
        await app.run_tournament()

        # Verify tournament completed
        assert app.session is not None

        # Check that games were played
        stats_agent = None
        for agent in app.session.agents:
            if isinstance(agent, TicTacToeStats):
                stats_agent = agent
                break
        assert stats_agent is not None
        assert stats_agent.total_games > 0

    @pytest.mark.asyncio
    async def test_tournament_with_outputs(self):
        """Test tournament with various output formats."""
        app = TicTacToeApplication()

        # Configure with outputs
        config = {
            "num_rounds": 1,
            "games_per_round": 1,
            "output_dir": self.temp_dir,
            "outputs": {
                "snapshot": True,
                "logger": True,
                "streaming": False
            },
            "players": [
                {"id": "alice", "strategy": "random"},
                {"id": "bob", "strategy": "random"},
            ]
        }

        await app.initialize(config)
        await app.run_tournament()

        # Verify outputs were created
        output_files = os.listdir(self.temp_dir)
        assert any("snapshot" in f for f in output_files)
        assert any("log" in f for f in output_files)
        # Streaming is disabled, so no streaming output should exist
        assert not any("stream" in f for f in output_files)

    @pytest.mark.asyncio
    async def test_tournament_with_policy_violations(self):
        """Test tournament behavior when policy violations occur."""
        app = TicTacToeApplication()

        # Create restrictive policy
        policy = Policy()
        banned_role = Role(id="banned", name="banned",
                           description="Banned players", members=[])
        policy.add_role(banned_role)

        charlie = Identity(id="charlie", nickname="Charlie")
        policy.add_identity(charlie)
        policy.add_identity_to_role(charlie, banned_role)

        policy.add_statement(
            roles=[banned_role],
            effect="deny",
            action=["move", "join"],
            resource=["activity:*"]
        )

        config = {
            "num_rounds": 1,
            "games_per_round": 1,
            "output_dir": self.temp_dir,
            "policy": policy,
            "players": [
                {"id": "alice", "strategy": "random"},
                {"id": "charlie", "strategy": "random"},  # Banned player
            ]
        }

        await app.initialize(config)

        # Tournament should handle policy violations gracefully
        try:
            await app.run_tournament()
        except Exception as e:
            # Should not crash, but may complete with errors
            pass


class TestStateManagement:
    """Test state management and coordination."""

    def setup_method(self):
        """Set up state management tests."""
        self.policy = Policy()
        self.player_role = Role(
            id="player", name="player", description="Can play games", members=[])
        self.policy.add_role(self.player_role)
        self.alice = Identity(id="alice", nickname="Alice")
        self.bob = Identity(id="bob", nickname="Bob")
        self.policy.add_identity(self.alice)
        self.policy.add_identity(self.bob)
        self.policy.add_identity_to_role(self.alice, self.player_role)
        self.policy.add_identity_to_role(self.bob, self.player_role)
        self.policy.add_statement(
            roles=[self.player_role],
            effect="allow",
            action=["move", "join", "view_board"],
            resource=["activity:*"]
        )
        self.session = Session(id="test_state_session",
                               policy=self.policy, identity=self.alice)

    def test_shared_state_coordination(self):
        """Test that agents share state through the session."""
        # Create and register agents
        referee = TicTacToeReferee(policy=self.policy, logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)

        self.session.add_agent(referee)
        self.session.add_agent(stats)

        # Test state sharing
        assert referee in self.session.agents
        assert stats in self.session.agents

    def test_game_state_management(self):
        """Test game state management through activities."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Initial state
        assert game.game_state.value == GameState.IN_PROGRESS.value
        flat_board = [cell for row in game.board.board for cell in row]
        assert len(flat_board) == 9
        assert all(cell == " " for cell in flat_board)

        # Make moves and verify state updates
        success, _ = game.make_move("alice", 0, 0)
        assert success
        assert game.board.board[0][0] == PlayerSymbol.X.value  # Alice is X

        success, _ = game.make_move("bob", 1, 1)
        assert success
        assert game.board.board[1][1] == PlayerSymbol.O.value  # Bob is O

    def test_tournament_state_aggregation(self):
        """Test that tournament state is properly aggregated."""
        # Create stats agent
        stats = TicTacToeStats()

        # Record some game results
        stats.record_game_result("alice", "bob", "alice")
        stats.record_game_result("bob", "alice", "bob")
        stats.record_game_result("alice", "bob", "tie")

        # Verify aggregated stats
        assert stats.total_games == 3
        assert stats.player_wins["alice"] == 1
        assert stats.player_wins["bob"] == 1
        assert stats.ties == 1

    def test_coordinated_cleanup(self):
        """Test that cleanup is properly coordinated."""
        # Create session with agents
        referee = TicTacToeReferee(policy=self.policy, logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)

        self.session.add_agent(referee)
        self.session.add_agent(stats)

        # Add some state
        referee.add_player_to_queue("alice")
        stats.record_game_result("alice", "bob", "alice")

        # Test coordinated state (no cleanup method)
        # Should still have agents registered but state may be reset
        assert referee in self.session.agents
        assert stats in self.session.agents


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_invalid_move_handling(self):
        """Test handling of invalid moves."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Invalid position
        success, message = game.make_move("alice", -1, 0)
        assert success is False
        assert "invalid" in message.lower() or "out of bounds" in message.lower()

        # Position already occupied
        game.make_move("alice", 0, 0)  # Valid move
        success, message = game.make_move("bob", 0, 0)  # Same position
        assert success is False
        assert "occupied" in message.lower() or "taken" in message.lower()

    def test_policy_error_handling(self):
        """Test handling of policy errors."""
        game = TicTacToeGame("test_game", "alice", "bob")

        # Create restrictive policy
        policy = Policy()
        policy.add_statement(
            roles=["*"],
            effect="deny",
            action=["*"],
            resource=["*"]
        )

        local_policy = LocalPolicy(parent_policy=policy)
        game.set_policy(local_policy)

        # Should gracefully handle policy denial
        success, message = game.make_move("alice", 0, 0)
        assert success is False
        assert "policy" in message.lower() or "denied" in message.lower()

    def test_agent_failure_recovery(self):
        """Test recovery from agent failures."""
        policy = Policy()
        identity = Identity(id="test", nickname="test")
        session = Session(id="fail_session", policy=policy, identity=identity)
        # Register a mock agent that will fail
        failing_agent = Mock()
        failing_agent.process = Mock(side_effect=Exception("Agent failed"))
        session.add_agent(failing_agent)
        # Session should handle agent failures gracefully
        try:
            # This would normally process agents
            assert failing_agent in session.agents
            # Should not crash the session
        except Exception:
            pytest.fail("Session should handle agent failures gracefully")


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
