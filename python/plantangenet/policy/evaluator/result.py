# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

from pydantic import BaseModel
from typing import Optional, List
from ..statement import Statement
from ...topics.message import Message


class EvaluationResult(BaseModel):

    passed: bool
    reason: str
    statement: Optional[Statement] = None
    messages: List[Message] = []

    def __bool__(self):
        return self.passed
