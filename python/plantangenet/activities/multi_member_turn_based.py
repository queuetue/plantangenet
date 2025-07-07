from abc import abstractmethod
from typing import Optional
from .turn_based import TurnbasedActivity


class MultiMemberTurnbasedActivity(TurnbasedActivity):
    """
    Abstract base class for a multimember turn-based activity.
    """
    @abstractmethod
    def _check_winner(self) -> Optional[str]:
        """
        Check if there is a winner in the activity.
        Returns:
            Optional[str]: The ID of the winning member, or None if no winner.
        """

    @abstractmethod
    def _is_activity_full(self) -> bool:
        """
        Check if the activity board is full (no more moves possible).

        Returns:
            bool: True if the activity board is full, False otherwise.
        """

    @abstractmethod
    async def add_member(self, member_id: str) -> bool:
        """
        Add a member to the activity.

        Args:
            member_id (str): The ID of the member to add.

        Returns:
            bool: True if the member was added successfully, False otherwise.
        """

    @abstractmethod
    async def remove_member(self, member_id: str) -> bool:
        """
        Remove a member from the activity.

        Args:
            member_id (str): The ID of the member to remove.

        Returns:
            bool: True if the member was removed successfully, False otherwise.
        """
