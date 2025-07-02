from plantangenet import Buoy
from plantangenet.omni import watch
from typing import Any, Callable, Coroutine, Optional, Union


class FakeBuoy(Buoy):

    health: int = watch(default=100)  # type: ignore

    async def update_transport(self):
        pass

    async def setup_transport(self, urls: list[str]) -> None:
        pass

    async def publish(self, topic: str, data: Union[str, bytes, dict]) -> None:
        pass

    async def subscribe(self, topic: str, callback: Callable[..., Coroutine[Any, Any, Any]]) -> Any:
        return True

    async def update_storage(self):
        pass

    async def setup_storage(self, urls: list[str]) -> None:
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

    @property
    def connected(self) -> bool:
        return True
