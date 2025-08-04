from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    peer_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
