"""
Integration tests for state management and coordination in TicTacToe.
"""
from plantangenet import GLOBAL_LOGGER
from examples.tictactoe.referee import TicTacToeReferee
from examples.tictactoe.stats import TicTacToeStats
from examples.tictactoe.game import TicTacToeGame
from examples.tictactoe.tictactoe_types import GameState, PlayerSymbol


class TestStateManagement:
    def test_shared_state_coordination(self, policy_with_players, session_with_policy):
        policy, _, _, _ = policy_with_players
        session = session_with_policy
        referee = TicTacToeReferee(policy=policy, logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)
        session.add_agent(referee)
        session.add_agent(stats)
        assert referee in session.agents
        assert stats in session.agents

    def test_game_state_management(self, policy_with_players):
        game = TicTacToeGame("test_game", "alice", "bob")
        assert game.game_state.value == GameState.IN_PROGRESS.value
        flat_board = [cell for row in game.board.board for cell in row]
        assert len(flat_board) == 9
        assert all(cell == " " for cell in flat_board)
        success, _ = game.make_move("alice", 0, 0)
        assert success
        assert game.board.board[0][0] == PlayerSymbol.X.value
        success, _ = game.make_move("bob", 1, 1)
        assert success
        assert game.board.board[1][1] == PlayerSymbol.O.value

    def test_tournament_state_aggregation(self, policy_with_players):
        stats = TicTacToeStats()
        stats.record_game_result("alice", "bob", "alice")
        stats.record_game_result("bob", "alice", "bob")
        stats.record_game_result("alice", "bob", "tie")
        assert stats.total_games == 3
        assert stats.player_wins["alice"] == 1
        assert stats.player_wins["bob"] == 1
        assert stats.ties == 1

    def test_coordinated_cleanup(self, policy_with_players, session_with_policy):
        policy, _, _, _ = policy_with_players
        session = session_with_policy
        referee = TicTacToeReferee(policy=policy, logger=GLOBAL_LOGGER)
        stats = TicTacToeStats(logger=GLOBAL_LOGGER)
        session.add_agent(referee)
        session.add_agent(stats)
        referee.add_player_to_queue("alice")
        stats.record_game_result("alice", "bob", "alice")
        assert referee in session.agents
        assert stats in session.agents
