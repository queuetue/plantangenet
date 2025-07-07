from typing import List
from pydantic import BaseModel, Field


class Identity(BaseModel):
    id: str
    nickname: str = "identity"
    metadata: dict = {}
    roles: List[str] = Field(default_factory=list)
