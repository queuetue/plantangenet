# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
BaseCompositor: Abstract base for all compositors (frame, graph, ML, etc).
Defines the minimal interface for a compositor.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, List


class BaseCompositor(ABC):
    """
    Abstract base class for all compositors.
    Provides a minimal, generic API for adding rules and composing outputs.
    """

    def __init__(self):
        self.composition_rules: List[Callable] = []

    def add_composition_rule(self, rule: Callable):
        self.composition_rules.append(rule)

    @abstractmethod
    def compose(self, *args, **kwargs) -> Any:
        """Produce a composed output (frame, graph, etc)."""
        pass

    @abstractmethod
    def transform(self, data: Any, **kwargs) -> Any:
        """Apply transformation to input data (unified interface for ML/Graph/etc)."""
        pass
