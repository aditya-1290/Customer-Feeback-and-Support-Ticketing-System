from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class UserRole(enum.Enum):
    customer = "customer"
    support_agent = "support_agent"

class TicketStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    tickets = relationship("Ticket", back_populates="user")
    responses = relationship("TicketResponse", back_populates="responder")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.open, nullable=False)
    created_at = Column(DateTime, default=datetime.now())

    user = relationship("User", back_populates="tickets")
    responses = relationship("TicketResponse", back_populates="ticket")

class TicketResponse(Base):
    __tablename__ = "ticket_responses"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now())

    ticket = relationship("Ticket", back_populates="responses")
    responder = relationship("User", back_populates="responses")
