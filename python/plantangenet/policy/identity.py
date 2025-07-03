# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from plantangenet.policy.storage_mixin import PolicyStorageMixin


class Identity(PolicyStorageMixin, BaseModel):
    id: str = Field(..., description="Unique identifier for the identity.")
    nickname: str = Field(..., description="Nickname for the identity.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the identity.")
    roles: List[str] = Field(
        default_factory=list, description="List of roles assigned to this identity.")
