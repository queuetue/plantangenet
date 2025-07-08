"""
Base classes for turn-based game activities.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

from plantangenet.activities.multi_member_turn_based import MultiMemberTurnbasedActivity
from plantangenet.activities.policy_mixin import PolicyEnforcedActivity
from plantangenet.game.widget_mixins import WidgetProviderMixin


class GameState(Enum):
    """Common game states for turn-based games."""
    WAITING_FOR_PLAYERS = "waiting_for_players"
    IN_PROGRESS = "in_progress"
    GAME_OVER = "game_over"
    PAUSED = "paused"


class TurnBasedGameActivity(MultiMemberTurnbasedActivity, PolicyEnforcedActivity, WidgetProviderMixin):
    """
    Base class for turn-based game activities with policy enforcement and widget support.

    This class provides common functionality for turn-based games like:
    - Turn management
    - Player management
    - Game state tracking
    - Policy enforcement
    - Widget rendering
    """

    def __init__(self, game_id: str, *player_ids: str, max_players: int = 4):
        self.game_id = game_id
        self.game_state = GameState.WAITING_FOR_PLAYERS
        self.frames_elapsed = 0
        self.members = set(player_ids)
        self.turn_order = list(player_ids) if player_ids else []
        self.current_turn_index = 0
        self.max_players = max_players

        # Initialize base classes
        MultiMemberTurnbasedActivity.__init__(self)
        PolicyEnforcedActivity.__init__(self)

        # Start game if we have players
        if player_ids:
            self.game_state = GameState.IN_PROGRESS

    @property
    def current_turn(self) -> Optional[str]:
        """Get the current player's turn."""
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn_index]

    def advance_turn(self):
        """Advance to the next player's turn."""
        if self.turn_order:
            self.current_turn_index = (
                self.current_turn_index + 1) % len(self.turn_order)

    # Abstract methods that subclasses must implement
    @abstractmethod
    def make_game_move(self, player_id: str, *args, **kwargs) -> Tuple[bool, str]:
        """
        Make a game-specific move.

        Args:
            player_id: The player making the move
            *args, **kwargs: Game-specific move parameters

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def get_game_state(self) -> Dict[str, Any]:
        """
        Get the current game state as a dictionary.

        Returns:
            Dict containing the current game state
        """
        pass

    # Implementations of MultiMemberTurnbasedActivity abstract methods
    def make_move(self, member_id: str, row: int, col: int) -> Tuple[bool, str]:
        """
        Standard move interface - delegates to game-specific implementation.

        Args:
            member_id: The player making the move
            row: Move parameter (game-specific meaning)
            col: Move parameter (game-specific meaning)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        return self.make_game_move(member_id, row, col)

    def _check_completion(self) -> bool:
        """Check if the game is complete."""
        return self.game_state == GameState.GAME_OVER

    def _available(self) -> bool:
        """Check if the game is available for play."""
        return self.game_state == GameState.IN_PROGRESS

    def _is_activity_full(self) -> bool:
        """Check if the game is full."""
        return len(self.members) >= self.max_players

    async def add_member(self, member_id: str) -> bool:
        """Add a member to the game."""
        if len(self.members) >= self.max_players:
            return False

        self.members.add(member_id)
        self.turn_order.append(member_id)

        if self.game_state == GameState.WAITING_FOR_PLAYERS and len(self.members) > 0:
            self.game_state = GameState.IN_PROGRESS

        return True

    async def remove_member(self, member_id: str) -> bool:
        """Remove a member from the game."""
        if member_id not in self.members:
            return False

        self.members.remove(member_id)
        if member_id in self.turn_order:
            self.turn_order.remove(member_id)

        if len(self.members) == 0:
            self.game_state = GameState.GAME_OVER

        return True

    def get_activity_specific_permissions(self) -> Dict[str, str]:
        """Return game-specific action permissions."""
        return {
            "move": "Make a move in the game",
            "join": "Join the game",
            "view_board": "View the current game state",
            "play": "Participate in the game"
        }

    # Widget/rendering support
    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Get a text-based widget representation of the game."""
        state = self.get_game_state()
        return f"Game {self.game_id}: {state.get('state', 'unknown')} - Turn: {state.get('current_turn', 'none')}"

    def get_render_data(self) -> Dict[str, Any]:
        """Get game data for rendering."""
        return self.get_game_state()

    def __render__(self, format: str = "json", **kwargs) -> str:
        """Render the game state as JSON."""
        import json
        return json.dumps(self.get_game_state(), indent=kwargs.get('indent', 2))
