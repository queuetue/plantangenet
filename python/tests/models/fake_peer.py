from plantangenet.gyre.peer import GyrePeer
from plantangenet import GLOBAL_LOGGER
from typing import Any, Callable, Coroutine, Optional, Union


class FakePeer(GyrePeer):
    async def update_transport(self):
        pass

    async def setup_transport(self, urls: list[str]) -> None:
        pass

    async def teardown_transport(self):
        pass

    async def publish(self, topic: str, data: Union[str, bytes, dict]) -> None:
        pass

    async def subscribe(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]) -> Any:
        return True

    async def update_storage(self):
        pass

    async def setup_storage(self, urls: list[str]) -> None:
        pass

    async def teardown_storage(self) -> None:
        pass

    async def get(self, key: str, actor=None) -> Optional[str]:
        return ""

    async def set(self, key: str, value: Any, nx: bool = False, ttl: Optional[int] = None, actor=None) -> list:
        return []

    async def delete(self, key: str, actor=None) -> list:
        return []

    async def keys(self, pattern: str = "*", actor=None) -> list[str]:
        return []

    async def exists(self, key: str, actor=None) -> bool:
        return True

    async def setup(self, *args, **kwargs) -> None:
        pass

    async def teardown(self) -> None:
        pass

    async def update(self) -> bool:
        return True

    @property
    def logger(self) -> Any:
        return GLOBAL_LOGGER

    @property
    def name(self) -> str:
        return "DummyPeer"

    @property
    def connected(self) -> bool:
        return True

    @property
    def disposition(self) -> str:
        return "active"

    @property
    def ttl(self) -> int:
        return 600

    def get_axis_data(self) -> dict[str, Any]:
        return {"position": 0.0, "impulse": {}, "metadata": {}}

    def get_axis_name(self) -> str:
        return "x"

    async def handle_heartbeat(self, message: dict) -> None:
        self.logger.info(f"Heartbeat received: {message}")

    async def on_pulse(self, data: dict) -> None:
        self.logger.info(f"Pulse received: {data}")
