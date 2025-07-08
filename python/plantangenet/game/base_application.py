"""
Base application framework for Plantangenet games.
"""
import argparse
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from plantangenet.session.session import Session
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.policy.role import Role
from plantangenet.game.session_dashboard import SessionDashboardServer


class GameApplication(ABC):
    """Base class for game tournament applications."""

    def __init__(self, game_name: str):
        self.game_name = game_name
        self.session: Optional[Session] = None
        self.session_dashboard: Optional[SessionDashboardServer] = None
        self.players: Dict[str, Any] = {}
        self.stats_agent: Optional[Any] = None
        self.dashboard_compositor: Optional[Any] = None

    @abstractmethod
    def create_game_factory(self, config: Dict[str, Any]) -> Callable:
        """Create a factory function for creating game instances."""
        pass

    @abstractmethod
    def create_player_agent(self, player_config: Dict[str, Any]) -> Any:
        """Create a player agent from configuration."""
        pass

    @abstractmethod
    def create_stats_agent(self, config: Dict[str, Any]) -> Any:
        """Create a statistics tracking agent."""
        pass

    def create_policy(self, config: Dict[str, Any]) -> Policy:
        """Create game policy with player permissions."""
        policy = Policy()

        # Create player role
        player_role = Role(
            id="player",
            name="player",
            description=f"Can play {self.game_name}",
            members=[]
        )
        policy.add_role(player_role)

        # Add player identities
        for player_config in config.get("players", []):
            player_id = player_config["id"]
            identity = Identity(id=player_id, nickname=player_id.title())
            policy.add_identity(identity)
            policy.add_identity_to_role(identity, player_role)

        # Add permissions
        actions = config.get("player_actions", ["move", "join", "play"])
        policy.add_statement(
            roles=[player_role],
            effect="allow",
            action=actions,
            resource=["activity:*"]
        )

        return policy

    def create_session(self, config: Dict[str, Any], policy: Policy) -> Session:
        """Create game session."""
        admin_identity = Identity(id="admin", nickname="Admin")
        policy.add_identity(admin_identity)

        session_id = config.get("session_id", f"{self.game_name}_session")
        return Session(id=session_id, policy=policy, identity=admin_identity)

    async def setup_dashboard_compositor(self, config: Dict[str, Any]):
        """Setup visual dashboard compositor if requested."""
        if not config.get("dashboard", False):
            return

        try:
            from plantangenet.comdec import MJPEGComdec
            # Import dashboard from game-specific module
            dashboard_class = self.get_dashboard_class()
            if not dashboard_class:
                return

            self.dashboard_compositor = dashboard_class(
                width=config.get("dashboard_width", 1200),
                height=config.get("dashboard_height", 800),
                dpi=96
            )
            self.dashboard_compositor.layout_direction = "vertical"
            self.dashboard_compositor.widget_size = config.get(
                "widget_size", (120, 80))
            self.dashboard_compositor.padding = 20

            mjpeg_comdec = MJPEGComdec(port=config.get("dashboard_port", 8080))
            self.dashboard_compositor.add_comdec(mjpeg_comdec)
            if self.session:
                self.session.add_compositor(
                    "dashboard", self.dashboard_compositor)
            await self.dashboard_compositor.initialize_comdecs()
            self.dashboard_compositor.start_streaming()

            dashboard_port = config.get("dashboard_port", 8080)
            print(
                f"{self.game_name} dashboard enabled at http://localhost:{dashboard_port}/")
        except ImportError:
            print("Dashboard dependencies not available, skipping visual dashboard")

    def get_dashboard_class(self):
        """Override in subclasses to provide dashboard class."""
        return None

    async def setup_session_dashboard(self, config: Dict[str, Any]):
        """Setup session status dashboard."""
        port = config.get("session_dashboard_port", 8081)
        self.session_dashboard = SessionDashboardServer(port=port)
        self.session_dashboard.set_session(self.session)
        print(
            f"Session dashboard available at http://localhost:{port}/session")
        print(f"Session API available at http://localhost:{port}/api/session")

    async def initialize(self, config: Dict[str, Any]):
        """Initialize the game application."""
        # Create policy and session
        policy = self.create_policy(config)
        self.session = self.create_session(config, policy)

        # Create stats agent
        self.stats_agent = self.create_stats_agent(config)
        if self.stats_agent:
            self.session.add_agent(self.stats_agent)

        # Create player agents
        for player_config in config.get("players", []):
            player = self.create_player_agent(player_config)
            self.players[player_config["id"]] = player
            self.session.add_agent(player)

        # Setup dashboards
        await self.setup_dashboard_compositor(config)
        await self.setup_session_dashboard(config)

    @abstractmethod
    async def run_tournament(self, config: Dict[str, Any]):
        """Run the game tournament."""
        pass

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "num_rounds": 0,  # 0 = endless
            "games_per_round": 2,
            "dashboard": False,
            "dashboard_width": 1200,
            "dashboard_height": 800,
            "dashboard_port": 8080,
            "session_dashboard_port": 8081,
            "widget_size": (120, 80),
            "players": []
        }

    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description=f"{self.game_name} Tournament")
        parser.add_argument("--rounds", type=int, default=0,
                            help="Number of tournament rounds (0 = endless)")
        parser.add_argument("--games-per-round", type=int, default=2,
                            help="Games per round")
        parser.add_argument("--dashboard", action="store_true",
                            help="Enable browser-based visual dashboard")
        parser.add_argument("--dashboard-port", type=int, default=8080,
                            help="Port for visual dashboard")
        parser.add_argument("--session-port", type=int, default=8081,
                            help="Port for session dashboard")
        return parser.parse_args()

    async def start_dashboard_servers(self, config: Dict[str, Any]) -> List:
        """Start dashboard servers and return tasks."""
        tasks = []

        if self.dashboard_compositor:
            async def stream_dashboard():
                while True:
                    if self.dashboard_compositor:
                        frame = self.dashboard_compositor.compose()
                        await self.dashboard_compositor.comdec_manager.broadcast_frame(frame)
                    await asyncio.sleep(1/15)  # ~15 FPS
            tasks.append(asyncio.create_task(stream_dashboard()))

        if self.session_dashboard:
            tasks.append(asyncio.create_task(
                self.session_dashboard.start_server()))

        return tasks

    async def run(self):
        """Main entry point to run the application."""
        args = self.parse_args()
        config = self.get_default_config()

        # Update config with command line args
        config.update({
            "num_rounds": args.rounds,
            "games_per_round": args.games_per_round,
            "dashboard": args.dashboard,
            "dashboard_port": args.dashboard_port,
            "session_dashboard_port": args.session_port,
        })

        # Initialize application
        await self.initialize(config)

        # Start servers
        server_tasks = await self.start_dashboard_servers(config)

        # Run tournament
        tournament_task = asyncio.create_task(self.run_tournament(config))

        try:
            await tournament_task
        finally:
            # Cancel server tasks
            for task in server_tasks:
                task.cancel()

        print(f"\n{self.game_name} tournament completed!")
