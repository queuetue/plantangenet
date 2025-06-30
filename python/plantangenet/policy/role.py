# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from typing import List
from pydantic import BaseModel, Field


class Role(BaseModel):
    id: str = Field(..., description="Unique identifier for the role.")
    name: str = Field(..., description="Name of the role.")
    description: str = Field(..., description="Description of the role.")
    members: List[str] = Field(
        default_factory=list, description="List of members associated with this role.")
