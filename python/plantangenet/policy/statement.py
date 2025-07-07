# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT
from abc import abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Statement(BaseModel):
    id: str
    role_ids: List[str]
    effect: str
    action: List[str]
    resource: List[str]
    condition: Dict[str, Any]
    delivery: Optional[str]
    cost: Optional[int]
    capabilities: Optional[Dict[str, Any]]
