from typing import Annotated


class TickMixin:
    """
    Stateless tick timer object. Does not manage its own scheduling.
    Should be ticked by a manager or app/session.
    """

    def __init__(self, repeating: bool = True, running: bool = True):
        self.repeating = repeating
        self.running = running
        self.cycles = 0

    def tick(self, **kwargs):
        if self.running:
            self.cycles += 1
            if not self.repeating:
                self.running = False
