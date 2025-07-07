from abc import ABC, abstractmethod
from typing import Optional, Tuple


class TurnbasedActivity(ABC):
    """
    Abstract base class for a turn-based activity.
    This class provides the basic structure for a turn-based activity, including methods for making moves,
    checking for a win, and managing activity state.
    """
    _activity__max_members: int = 1
    _activity__turn: int = 0

    @abstractmethod
    def make_move(self, member_id: str, row: int, col: int) -> Tuple[bool, str]:
        """
        Make a move in the activity.

        Args:
            member_id (str): The ID of the member making the move.
            row (int): The row index for the move.
            col (int): The column index for the move.

        Returns:
            Tuple[bool, str]: A tuple indicating success and a message.
        """

    @abstractmethod
    def _check_completion(self) -> bool:
        """
        Check if the activity is complete (e.g., a member has won or the board is full).

        Returns:
            bool: True if the activity is complete, False otherwise.
        """

    @abstractmethod
    def _available(self) -> bool:
        """
        Check if the activity is available for play.

        Returns:
            bool: True if the activity is available, False otherwise.
        """

    @property
    def advertisement(self) -> Optional[dict]:
        """
        Get the advertisement for the activity.

        Returns:
            Optional[dict]: A dictionary containing activity details, or None if not available.
        """
        return {
            "description": "A multimember turn-based activity."
        }
