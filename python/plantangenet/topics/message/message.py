from typing import Optional
from pydantic import BaseModel


class Message(BaseModel):
    subject: str
    sender: Optional[str] = None
    target: Optional[str] = None
    payload: bytes = b""
    priority: int = 0
    time: float = 0.0
