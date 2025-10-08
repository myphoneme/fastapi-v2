from pydantic import BaseModel
from typing import Optional


class VMRequest(BaseModel):
    ip: str
    username: Optional[str] = None
    password: Optional[str] = None