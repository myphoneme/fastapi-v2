from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.vm_master import VMMasterResponse

class VMStatusBase(BaseModel):
    vm_id: int
    ip : str = Field(..., max_length=50)
    status: str = Field(..., max_length=20)
    os: Optional[str] = Field(None, max_length=50)
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    disk_utilization: Optional[str] = None

class VMStatusCreate(VMStatusBase):
    pass

class VMStatusUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20)
    os: Optional[str] = Field(None, max_length=50)
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    disk_utilization: Optional[str] = None

class VMStatusResponse(VMStatusBase):
    id: int
    created_at: datetime
    vm_master: Optional[VMMasterResponse]
    class Config:
        orm_mode = True