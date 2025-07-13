#!/usr/bin/env python3
"""
Demo of TicTacToe Policy-Based Referee
Shows how the new referee adjudicates proposed board states.
"""

from plantangenet.session.referees.tictactoe import TicTacToeReferee
from plantangenet.session.referee import Judgement


def print_board(board):
    """Print a TicTacToe board in a nice format."""
    print("  0 1 2")
    for i, row in enumerate(board):
        print(f"{i} {' '.join(row)}")
    print()


def demo_consensus_move():
    """Demo: Both players agree on a valid move."""
    print("=== Demo: Consensus on Valid Move ===")
    referee = TicTacToeReferee()

    print("Initial board:")
    print_board(referee.get_current_board())
    print(f"Current player: {referee.get_current_player()}")

    # Both players propose X moves to (0,0)
    states = [
        {
            "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 0}
        },
        {
            "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 0}
        }
    ]

    print("Both players propose: X to (0,0)")
    result = referee.adjudicate(states)

    print(f"Judgement: {result.judgement}")
    print(f"Reason: {result.info.get('reason')}")
    print(f"Consensus: {result.info.get('consensus')}")

    print("\nBoard after adjudication:")
    print_board(referee.get_current_board())
    print(f"Current player: {referee.get_current_player()}")
    print()


def demo_conflicting_moves():
    """Demo: Players propose different moves."""
    print("=== Demo: Conflicting Moves ===")
    referee = TicTacToeReferee()

    print("Initial board:")
    print_board(referee.get_current_board())

    # Players propose different moves
    states = [
        {
            "board": [["X", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 0}
        },
        {
            "board": [[" ", "X", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 0, "col": 1}
        }
    ]

    print("Player 1 proposes: X to (0,0)")
    print("Player 2 proposes: X to (0,1)")

    result = referee.adjudicate(states)

    print(f"Judgement: {result.judgement}")
    print(f"Reason: {result.info.get('reason')}")
    print(f"Valid states: {result.info.get('valid_states')}")
    print(f"Invalid states: {result.info.get('invalid_states')}")

    print("\nBoard after adjudication:")
    print_board(referee.get_current_board())
    print(f"Current player: {referee.get_current_player()}")
    print()


def demo_cheating_attempt():
    """Demo: Player tries to cheat."""
    print("=== Demo: Cheating Attempt ===")
    referee = TicTacToeReferee()

    print("Initial board:")
    print_board(referee.get_current_board())
    print(f"Current player: {referee.get_current_player()}")

    # Player tries to play out of turn
    states = [
        {
            "board": [["O", " ", " "], [" ", " ", " "], [" ", " ", " "]],
            "player": "O",  # Wrong! Should be X's turn
            "move": {"row": 0, "col": 0}
        }
    ]

    print("Player proposes: O to (0,0) - but it's X's turn!")

    result = referee.adjudicate(states)

    print(f"Judgement: {result.judgement}")
    print(f"Reason: {result.info.get('reason')}")

    print("\nBoard after adjudication (should be unchanged):")
    print_board(referee.get_current_board())
    print(f"Current player: {referee.get_current_player()}")
    print()


def demo_full_game():
    """Demo: Play a full game using the referee."""
    print("=== Demo: Full Game ===")
    referee = TicTacToeReferee()

    moves = [
        # X to center
        {
            "board": [[" ", " ", " "], [" ", "X", " "], [" ", " ", " "]],
            "player": "X",
            "move": {"row": 1, "col": 1}
        },
        # O to corner
        {
            "board": [["O", " ", " "], [" ", "X", " "], [" ", " ", " "]],
            "player": "O",
            "move": {"row": 0, "col": 0}
        },
        # X to opposite corner
        {
            "board": [["O", " ", " "], [" ", "X", " "], [" ", " ", "X"]],
            "player": "X",
            "move": {"row": 2, "col": 2}
        },
        # O blocks
        {
            "board": [["O", " ", "O"], [" ", "X", " "], [" ", " ", "X"]],
            "player": "O",
            "move": {"row": 0, "col": 2}
        },
        # X wins
        {
            "board": [["O", " ", "O"], [" ", "X", " "], ["X", " ", "X"]],
            "player": "X",
            "move": {"row": 2, "col": 0}
        }
    ]

    for i, move in enumerate(moves):
        print(
            f"Turn {i+1}: {move['player']} to ({move['move']['row']}, {move['move']['col']})")

        result = referee.adjudicate([move])
        print(f"  Judgement: {result.judgement}")

        if result.judgement == Judgement.WIN:
            print_board(referee.get_current_board())

            winner = referee.check_winner()
            if winner:
                print(f"🎉 Game Over! Winner: {winner}")
                break
            elif referee.is_board_full():
                print("🤝 Game Over! It's a draw!")
                break
            else:
                print(f"  Next player: {referee.get_current_player()}")
        else:
            print(f"  Move rejected: {result.info.get('reason')}")
            break
        print()


def main():
    """Run all demos."""
    print("🎮 TicTacToe Policy-Based Referee Demo")
    print("=" * 50)
    print()

    demo_consensus_move()
    demo_conflicting_moves()
    demo_cheating_attempt()
    demo_full_game()

    print("✅ All demos completed!")


if __name__ == "__main__":
    main()
