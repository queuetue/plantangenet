# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from .topics.mixin import TopicsMixin
from .status.mixin import StatusMixin
from .status.watch import watch


class TurnMixin(TopicsMixin, StatusMixin):
    turn: int = watch(default=1, include_in_dict=True)
    pass


__all__ = [
    "TurnMixin",
    "TopicsMixin",
    "StatusMixin",
    "watch",
]
