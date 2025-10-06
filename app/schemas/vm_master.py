from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VMMasterBase(BaseModel):
    vm_name: str = Field(..., max_length=500)
    ip: str = Field(..., max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=100)
    project_name: str = Field(..., max_length=100)
    cluster: Optional[str] = Field(None, max_length=200)
    node: Optional[str] = Field(None, max_length=100)
    remarks: Optional[str] = Field(None, max_length=500)
    is_active: Optional[int] = 1  # Or use bool if you prefer

class VMMasterCreate(VMMasterBase):
    pass

class VMMasterUpdate(BaseModel):
    vm_name: Optional[str] = Field(None, max_length=500)
    ip: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=100)
    project_name: Optional[str] = Field(None, max_length=100)
    cluster: Optional[str] = Field(None, max_length=200)
    node: Optional[str] = Field(None, max_length=100)
    remarks: Optional[str] = Field(None, max_length=500)
    # is_active: Optional[int] = None  # Or bool

class VMMasterResponse(VMMasterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True