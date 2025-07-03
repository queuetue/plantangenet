# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from plantangenet.policy.storage_mixin import PolicyStorageMixin


class Statement(PolicyStorageMixin, BaseModel):
    id: str = Field(..., description="Unique identifier for the statement.")
    role_names: List[str] = []
    effect: str = Field(..., description="allow or deny")
    action: List[str]
    resource: List[str]
    condition: Dict[str, Any] = Field(default_factory=dict)
    delivery: Optional[str] = None
    cost: Optional[int] = None
    capabilities: Optional[Dict[str, Any]] = None
