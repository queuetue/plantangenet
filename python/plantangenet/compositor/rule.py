# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Dict, Any, Protocol
from plantangenet.collector.multi_axis_frame import MultiAxisFrame


class CompositionRule(Protocol):
    def __call__(self, data: Dict[str, Any],
                 frame: 'MultiAxisFrame') -> Dict[str, Any]: ...
