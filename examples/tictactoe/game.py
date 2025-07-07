from examples.tictactoe.tictactoe_types import GameBoard, GameState, PlayerSymbol
from typing import Tuple, Dict, Optional
from plantangenet.activities.multi_member_turn_based import MultiMemberTurnbasedActivity
from plantangenet.activities.policy_mixin import TurnBasedPolicyMixin


class TicTacToeGame(TurnBasedPolicyMixin, MultiMemberTurnbasedActivity):
    def __init__(self, game_id: str, player_x: str, player_o: str):
        super().__init__()
        self.id = game_id
        self.player_x = player_x
        self.player_o = player_o
        self.members = [player_x, player_o]
        self.current_turn_index = 0
        self.turn_count = 0
        self.board = GameBoard(game_id, player_x, player_o)
        self.board.state = GameState.IN_PROGRESS

    def make_move(self, member_id: str, row: int, col: int) -> Tuple[bool, str]:
        # Policy enforcement - check if the member can make a move
        try:
            self.require_turn_permission(member_id, "move", {
                "row": row,
                "col": col,
                # Copy for context
                "board_state": [row[:] for row in self.board.board]
            })
        except PermissionError as e:
            return False, str(e)

        # Validate move
        if self.board.state != GameState.IN_PROGRESS:
            return False, "Game not in progress"

        if row < 0 or row > 2 or col < 0 or col > 2:
            return False, "Invalid position"

        if self.board.board[row][col] != " ":
            return False, "Position already occupied"

        # Check if it's the player's turn using base class turn logic
        if not self.is_member_turn(member_id):
            return False, "Not your turn"

        # Determine symbol
        expected_symbol = PlayerSymbol.X.value if self.current_turn_index == 0 else PlayerSymbol.O.value
        self.board.board[row][col] = expected_symbol

        # Check for win
        winner = self._check_winner()
        if winner:
            self.board.winner = winner
            self.board.state = GameState.FINISHED
        elif self._is_activity_full():
            self.board.state = GameState.FINISHED
            self.board.winner = "DRAW"
        else:
            self.next_turn()
            self.board.current_player = PlayerSymbol.O.value if expected_symbol == PlayerSymbol.X.value else PlayerSymbol.X.value

        return True, "Move successful"

    def _check_winner(self) -> Optional[str]:
        board = self.board.board

        # Check rows
        for row in board:
            if row[0] == row[1] == row[2] != " ":
                # Find which player has this symbol
                symbol = row[0]
                return self.player_x if symbol == PlayerSymbol.X.value else self.player_o

        # Check columns
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != " ":
                symbol = board[0][col]
                return self.player_x if symbol == PlayerSymbol.X.value else self.player_o

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] != " ":
            symbol = board[0][0]
            return self.player_x if symbol == PlayerSymbol.X.value else self.player_o
        if board[0][2] == board[1][1] == board[2][0] != " ":
            symbol = board[0][2]
            return self.player_x if symbol == PlayerSymbol.X.value else self.player_o

        return None

    def _is_activity_full(self) -> bool:
        for row in self.board.board:
            for cell in row:
                if cell == " ":
                    return False
        return True

    def _check_completion(self) -> bool:
        return self.board.state == GameState.FINISHED

    def _available(self) -> bool:
        return self.board.state == GameState.IN_PROGRESS and len(self.members) == 2

    def is_member_turn(self, member_id: str) -> bool:
        """Check if it's the given member's turn."""
        if len(self.members) == 0:
            return False
        current_player = self.members[self.current_turn_index % len(
            self.members)]
        return current_player == member_id

    def next_turn(self) -> None:
        """Advance to the next turn."""
        self.current_turn_index = (
            self.current_turn_index + 1) % len(self.members)
        self.turn_count += 1

    def _is_active_player(self, identity) -> bool:
        """Override from TurnBasedPolicyMixin to check if identity can act on current turn."""
        identity_str = str(identity) if not isinstance(
            identity, str) else identity
        return self.is_member_turn(identity_str)

    async def add_member(self, member_id: str) -> bool:
        """Add a member to the game."""
        # Policy enforcement
        try:
            self.require_permission(member_id, "join")
        except PermissionError:
            return False

        if len(self.members) >= 2:
            return False  # Game is full
        if member_id in self.members:
            return False  # Already a member

        self.members.append(member_id)
        if len(self.members) == 1:
            self.player_x = member_id
        elif len(self.members) == 2:
            self.player_o = member_id

        return True

    async def remove_member(self, member_id: str) -> bool:
        """Remove a member from the game."""
        # Policy enforcement
        try:
            self.require_permission(member_id, "leave")
        except PermissionError:
            return False

        if member_id not in self.members:
            return False

        self.members.remove(member_id)
        # If a player leaves, the game is over
        self.board.state = GameState.FINISHED
        other_player = [m for m in [
            self.player_x, self.player_o] if m != member_id]
        if other_player:
            self.board.winner = other_player[0]

        return True

    @property
    def turn_order(self):
        # Return the order of player IDs
        return [self.player_x, self.player_o]

    @property
    def current_turn(self):
        # Return the player whose turn it is
        return self.members[self.current_turn_index]

    @property
    def game_state(self):
        """Expose the current game state for test compatibility."""
        return self.board.state

    def get_activity_specific_permissions(self) -> Dict[str, str]:
        """Get TicTacToe-specific permissions."""
        return {
            'move': 'Make a move on the board',
            'pass_turn': 'Pass the current turn (not applicable to TicTacToe)',
            'forfeit': 'Forfeit the game',
            'view_board': 'View the current board state',
        }
