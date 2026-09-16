# app/models/user.py

from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class UserBase(BaseModel):
    username: str
    role: str  # "General", "Misiones", "Nuevo Sur", "San Agustín"
    name: str
    email: Optional[str] = None
    is_active: bool = True

class UserInDB(UserBase):
    password_hash: str

class UserResponse(UserBase):
    pass

class LoginRequest(BaseModel):
    username: str
    password: str
