"""
Widget and rendering mixins for Plantangenet agents and activities.
"""
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from plantangenet.core import RegistrableComponent


class WidgetProviderMixin(RegistrableComponent, ABC):
    """Mixin to provide widget rendering capabilities for agents and activities."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """
        Get a text-based widget representation.

        Args:
            asset: The type of widget/asset to render (e.g., "default", "compact", "detailed")
            **kwargs: Additional rendering parameters

        Returns:
            str: Text representation of the widget
        """
        pass

    def __render__(self, width=300, height=80, asset="default", style="default", font=None, color=None, text_color=None, **kwargs):
        """
        Unified render method for dashboard/compositor use.
        Returns a PIL Image (or array) for asset requests, and text/JSON for others.
        Subclasses should override for custom rendering.
        """
        # By default, subclasses should implement get_default_asset for image assets
        if asset in ("default", "widget"):
            # This will raise if not implemented in subclass
            return getattr(self, 'get_default_asset', lambda **kw: (_ for _ in ()).throw(NotImplementedError(f"get_default_asset not implemented for {self.__class__.__name__}")))(width=width, height=height)
        # Fallback to text widget or JSON
        if asset == "text":
            return self.get_widget(asset=asset, **kwargs)
        if asset == "json":
            return self._render_json(**kwargs)
        raise NotImplementedError(
            f"__render__ not implemented for asset '{asset}' in {self.__class__.__name__}")

    def _render_json(self, **kwargs) -> str:
        """Default JSON rendering implementation."""
        data = self.get_render_data()
        return json.dumps(data, indent=kwargs.get('indent', 2))

    @abstractmethod
    def get_render_data(self) -> Dict[str, Any]:
        """
        Get the data to be rendered.

        Returns:
            Dict[str, Any]: Data to be serialized for rendering
        """
        pass


class StatsAgentMixin(WidgetProviderMixin):
    """Mixin for agents that track game statistics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_games = 0
        self.stats_data = {}

    def record_game_result(self, *args, **kwargs):
        """Record the result of a completed game. Override in subclasses."""
        self.total_games += 1

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get a summary of statistics."""
        return {
            "total_games": self.total_games,
            **self.stats_data
        }

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Default widget implementation for stats."""
        if self.total_games == 0:
            return f"{self.__class__.__name__}: No games played yet"

        summary = self.get_stats_summary()
        return f"{self.__class__.__name__}: {summary.get('total_games', 0)} games"

    def get_render_data(self) -> Dict[str, Any]:
        """Get stats data for rendering."""
        return self.get_stats_summary()


class GamePlayerMixin(WidgetProviderMixin):
    """Mixin for game player agents."""

    def __init__(self, player_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_id = player_id
        self.games_played = 0
        self.wins = 0
        self.performance_data = {}

    def record_game_result(self, won: bool, **kwargs):
        """Record the result of a completed game."""
        self.games_played += 1
        if won:
            self.wins += 1

    def get_win_rate(self) -> float:
        """Get the win rate."""
        return self.wins / max(1, self.games_played)

    def get_player_stats(self) -> Dict[str, Any]:
        """Get player statistics."""
        return {
            "player_id": self.player_id,
            "games_played": self.games_played,
            "wins": self.wins,
            "win_rate": self.get_win_rate(),
            **self.performance_data
        }

    def get_widget(self, asset: str = "default", **kwargs) -> str:
        """Default widget implementation for players."""
        win_rate = self.get_win_rate() * 100
        return f"Player {self.player_id}: {self.games_played} games, {self.wins} wins ({win_rate:.1f}%)"

    def get_render_data(self) -> Dict[str, Any]:
        """Get player data for rendering."""
        return self.get_player_stats()
