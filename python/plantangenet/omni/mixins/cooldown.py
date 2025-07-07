from .tick import TickMixin


class CooldownMixin(TickMixin):
    """
    Stateless cooldown timer object. Does not manage its own scheduling.
    Should be ticked by a manager or app/session.
    """

    def __init__(self, cooldown: float, repeating: bool = True, running: bool = True):
        super().__init__(repeating=repeating, running=running)
        self.cooldown = cooldown
        self._stamp = 0.0

    def tick(self, interval: float = 0.25, **kwargs):
        self._stamp += interval
        if self.ready_to_fire:
            super().tick(**kwargs)
            if not self.repeating:
                self.running = False

    @property
    def ready_to_fire(self) -> bool:
        return self.running and self._stamp >= self.cooldown

    @property
    def time_till_next_trigger(self) -> float:
        if self.running:
            return max(0.0, self.cooldown - self._stamp)
        return float('inf')
