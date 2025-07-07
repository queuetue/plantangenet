# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from .topic import TopicsMixin
from .omni import OmniMixin
from ..helpers import watch


class TurnMixin(TopicsMixin, OmniMixin):
    turn: int = watch(default=1)
    pass


__all__ = [
    "TurnMixin",
    "TopicsMixin",
    "watch",
]
