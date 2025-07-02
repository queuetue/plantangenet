# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from plantangenet.mixins.base import OceanMixinBase


class PolicyMixin(OceanMixinBase):
    """
    A mixin for policy management within a Gyre.
    This mixin provides methods to apply and enforce policies across Shards.
    """

    def apply_policy(self, policy):
        # Logic to apply a policy
        pass

    @property
    def message_types(self):
        """Return the peer's message types."""
        result = super().message_types
        result.update([
            "policy.apply",
        ])
        return result
