import asyncio


class GameAppContext:
    """
    Async context manager for managing the lifecycle of game app background services (e.g., dashboard server).
    Usage:
        async with GameAppContext(app):
            await app.run_tournament()
    """

    def __init__(self, app):
        self.app = app
        self._dashboard = getattr(app, 'dashboard_server', None)

    async def __aenter__(self):
        # Start dashboard/server if present
        if self._dashboard and hasattr(self._dashboard, 'start'):
            await self._dashboard.start()
        return self.app

    async def __aexit__(self, exc_type, exc, tb):
        # Stop dashboard/server if present
        if self._dashboard and hasattr(self._dashboard, 'stop'):
            try:
                await self._dashboard.stop()
            except asyncio.CancelledError:
                pass  # Suppress shutdown noise
        # Optionally handle other cleanup here
        return False  # Propagate exceptions if any
