# app/schemas/token.py
from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    type: str
    name: Optional[str] = None
    scopes: List[str] = []
