#!/usr/bin/env python3
"""
Demo of TicTacToe Game with Policy-Based Referee Integration
Shows how to integrate the policy-based referee with the game system.
"""

import asyncio
from typing import Dict, List, Optional
from plantangenet.session.referees.tictactoe import TicTacToeReferee
from plantangenet.session.referee import Judgement


class PolicyBasedTicTacToeGame:
    """
    TicTacToe game that uses a policy-based referee for all state changes.
    Players propose moves, and the referee adjudicates them.
    """

    def __init__(self, game_id: str, player_x: str, player_o: str):
        self.game_id = game_id
        self.player_x = player_x
        self.player_o = player_o
        self.referee = TicTacToeReferee()
        self.game_over = False
        self.winner = None

    def propose_move(self, player_id: str, row: int, col: int) -> tuple[bool, str, dict]:
        """
        Player proposes a move. Returns (success, message, game_state).
        """
        if self.game_over:
            return False, "Game is already over", self.get_game_state()

        if player_id not in [self.player_x, self.player_o]:
            return False, f"Player {player_id} is not in this game", self.get_game_state()

        # Determine player symbol
        player_symbol = "X" if player_id == self.player_x else "O"

        # Create proposed board state
        new_board = [row[:]
                     for row in self.referee.get_current_board()]  # Deep copy
        new_board[row][col] = player_symbol

        # Create proposal
        proposed_state = {
            "board": new_board,
            "player": player_symbol,
            "move": {"row": row, "col": col},
            "game_id": self.game_id,
            "proposer": player_id
        }

        # Adjudicate with referee
        result = self.referee.adjudicate([proposed_state])

        if result.judgement == Judgement.WIN:
            # Move accepted
            self._check_game_end()
            return True, f"Move accepted: {result.info.get('reason', '')}", self.get_game_state()
        elif result.judgement == Judgement.CHEAT:
            return False, f"Move rejected - cheating detected: {result.info.get('reason', '')}", self.get_game_state()
        elif result.judgement == Judgement.ERROR:
            return False, f"Move rejected - error: {result.info.get('reason', '')}", self.get_game_state()
        else:
            return False, f"Move rejected: {result.info.get('reason', '')}", self.get_game_state()

    def propose_moves_from_multiple_players(self, moves: List[tuple]) -> tuple[bool, str, dict]:
        """
        Multiple players propose moves simultaneously. 
        moves is a list of (player_id, row, col) tuples.
        """
        if self.game_over:
            return False, "Game is already over", self.get_game_state()

        proposals = []
        for player_id, row, col in moves:
            if player_id not in [self.player_x, self.player_o]:
                continue

            player_symbol = "X" if player_id == self.player_x else "O"
            new_board = [row[:] for row in self.referee.get_current_board()]
            new_board[row][col] = player_symbol

            proposals.append({
                "board": new_board,
                "player": player_symbol,
                "move": {"row": row, "col": col},
                "game_id": self.game_id,
                "proposer": player_id
            })

        if not proposals:
            return False, "No valid proposals", self.get_game_state()

        # Adjudicate all proposals
        result = self.referee.adjudicate(proposals)

        if result.judgement == Judgement.WIN:
            self._check_game_end()
            reason = result.info.get('reason', '')
            if result.info.get('consensus'):
                return True, f"Consensus move accepted: {reason}", self.get_game_state()
            else:
                return True, f"Valid move selected: {reason}", self.get_game_state()
        elif result.judgement == Judgement.CONTEST:
            return False, f"Multiple valid moves proposed - no consensus: {result.info.get('reason', '')}", self.get_game_state()
        else:
            return False, f"All moves rejected: {result.info.get('reason', '')}", self.get_game_state()

    def _check_game_end(self):
        """Check if the game has ended."""
        winner = self.referee.check_winner()
        if winner:
            self.game_over = True
            self.winner = self.player_x if winner == "X" else self.player_o
        elif self.referee.is_board_full():
            self.game_over = True
            self.winner = "DRAW"

    def get_game_state(self) -> dict:
        """Get the current game state."""
        return {
            "game_id": self.game_id,
            "board": self.referee.get_current_board(),
            "current_player": self.referee.get_current_player(),
            "player_x": self.player_x,
            "player_o": self.player_o,
            "game_over": self.game_over,
            "winner": self.winner
        }

    def print_board(self):
        """Print the current board state."""
        board = self.referee.get_current_board()
        print("  0 1 2")
        for i, row in enumerate(board):
            print(f"{i} {' '.join(row)}")
        print()


async def demo_single_player_moves():
    """Demo: Players take turns making individual moves."""
    print("=== Demo: Single Player Moves ===")
    game = PolicyBasedTicTacToeGame("game1", "Alice", "Bob")

    moves = [
        ("Alice", 1, 1),  # X to center
        ("Bob", 0, 0),    # O to corner
        ("Alice", 2, 2),  # X to opposite corner
        ("Bob", 0, 2),    # O blocks
        ("Alice", 2, 0),  # X wins
    ]

    for player, row, col in moves:
        print(f"{player} proposes move to ({row}, {col})")
        success, message, state = game.propose_move(player, row, col)

        print(f"  Result: {message}")
        game.print_board()

        if state["game_over"]:
            if state["winner"] == "DRAW":
                print("🤝 Game ended in a draw!")
            else:
                print(f"🎉 Game over! Winner: {state['winner']}")
            break
    print()


async def demo_consensus_moves():
    """Demo: Both players agree on the same move."""
    print("=== Demo: Consensus Moves ===")
    game = PolicyBasedTicTacToeGame("game2", "Alice", "Bob")

    print("Both Alice and Bob propose X to (1,1)")
    success, message, state = game.propose_moves_from_multiple_players([
        ("Alice", 1, 1),
        ("Alice", 1, 1)  # Same move proposed twice (consensus)
    ])

    print(f"Result: {message}")
    game.print_board()
    print()


async def demo_conflicting_moves():
    """Demo: Players propose different moves."""
    print("=== Demo: Conflicting Moves ===")
    game = PolicyBasedTicTacToeGame("game3", "Alice", "Bob")

    print("Alice proposes X to (0,0), Bob proposes X to (1,1)")
    success, message, state = game.propose_moves_from_multiple_players([
        ("Alice", 0, 0),
        ("Bob", 1, 1)  # Different move - should cause contest
    ])

    print(f"Result: {message}")
    game.print_board()
    print()


async def demo_cheating_attempt():
    """Demo: Player tries to cheat."""
    print("=== Demo: Cheating Attempt ===")
    game = PolicyBasedTicTacToeGame("game4", "Alice", "Bob")

    # Alice makes a valid move first
    game.propose_move("Alice", 1, 1)
    print("Alice moves X to (1,1)")
    game.print_board()

    # Now it's Bob's turn, but Alice tries to move again
    print("Alice tries to move again (out of turn)")
    success, message, state = game.propose_move("Alice", 0, 0)

    print(f"Result: {message}")
    game.print_board()
    print()


async def main():
    """Run all demos."""
    print("🎮 Policy-Based TicTacToe Game Demo")
    print("=" * 50)
    print()

    await demo_single_player_moves()
    await demo_consensus_moves()
    await demo_conflicting_moves()
    await demo_cheating_attempt()

    print("✅ All demos completed!")

if __name__ == "__main__":
    asyncio.run(main())
