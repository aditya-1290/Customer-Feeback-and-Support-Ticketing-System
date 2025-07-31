from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    customer = "customer"
    support_agent = "support_agent"

class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Ticket schemas
class TicketBase(BaseModel):
    subject: str
    description: str
    priority: Optional[str] = None

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None

class TicketResponseBase(BaseModel):
    message: str

class TicketResponseCreate(TicketResponseBase):
    pass

class TicketResponseResponse(TicketResponseBase):
    id: int
    responder_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class TicketResponseOut(TicketBase):
    id: int
    user_id: int
    status: TicketStatus
    created_at: datetime
    responses: List[TicketResponseResponse] = []

    class Config:
        from_attributes = True
