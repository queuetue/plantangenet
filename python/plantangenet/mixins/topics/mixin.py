import inspect
from .helpers import on_topic
from plantangenet.mixins.base import OceanMixinBase


class TopicsMixin(OceanMixinBase):
    """Mixin for managing topic subscriptions and handlers."""

    def __init__(self, keep=False):
        self._topic_subscriptions = []
        self.register_topic_handlers(keep=keep)

    async def setup(self, *args, **kwargs) -> None:
        self.register_topic_handlers()
        await self.apply_topic_subscriptions()

    def register_topic_handlers(self, keep=False):
        if not keep:
            self._topic_subscriptions = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            topic = getattr(attr, "__topic__", None)
            if topic is None:
                continue
            if not callable(attr):
                self.logger.warning(
                    f"{attr_name} for topic {topic} is not callable, skipping.")
                continue
            if not inspect.iscoroutinefunction(attr):
                self.logger.warning(
                    f"{attr_name} for topic {topic} is not a coroutine function, skipping.")
                continue
            self._topic_subscriptions.append((topic, attr))

    async def apply_topic_subscriptions(self):
        for topic, handler in self._topic_subscriptions:
            await self.subscribe(topic, handler)

    @on_topic("omni.reset")
    async def omni__reset(self, message: dict):
        """Reset the Omni state."""
        self.logger.info("Resetting Omni state.")
        self._ocean__frames = 0
        self._ocean__frame_delta = 0

    @property
    def status(self) -> dict:
        """Return the status of the mixin."""
        status = super().status
        status["topic_subscriptions"] = self._topic_subscriptions
        return status
