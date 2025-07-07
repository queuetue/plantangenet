# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from pydantic import BaseModel
from typing import List


class Role(BaseModel):
    id: str
    name: str
    description: str
    members: List[str]
