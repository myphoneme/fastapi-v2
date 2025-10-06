from pydantic import BaseModel , EmailStr,ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    name:  str
    email: EmailStr
    role : int

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id:int
    created_at : datetime
    

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[int] = None
   
class UserInDB(UserResponse):
    password :str
    is_active : bool 
    model_config = ConfigDict(from_attributes=True)
