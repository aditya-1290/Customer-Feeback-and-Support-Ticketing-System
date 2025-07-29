from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import List
import schemas, models
from database import get_db
from core.security import decode_access_token

router = APIRouter()

async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

@router.post("/create_ticket", response_model=schemas.TicketResponseOut)
def create_ticket(ticket: schemas.TicketCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_ticket = models.Ticket(
        user_id=current_user.id,
        subject=ticket.subject,
        description=ticket.description,
        priority=ticket.priority,
        status=models.TicketStatus.open
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.get("/get_tickets", response_model=List[schemas.TicketResponseOut])
def get_tickets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == models.UserRole.support_agent:
        tickets = db.query(models.Ticket).all()
    else:
        tickets = db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).all()
    return tickets

@router.post("/add_ticket_response/{ticket_id}/responses", response_model=schemas.TicketResponseResponse)
def add_ticket_response(ticket_id: int, response: schemas.TicketResponseCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    # Authorization check: only ticket owner or support agent can add response
    if current_user.role != models.UserRole.support_agent and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add response to this ticket")
    new_response = models.TicketResponse(
        ticket_id=ticket_id,
        responder_id=current_user.id,
        message=response.message
    )
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    return new_response

@router.patch("/update_ticket_status/{ticket_id}", response_model=schemas.TicketResponseOut)
def update_ticket_status(ticket_id: int, ticket_update: schemas.TicketUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    # Authorization check: only support agents can update ticket status
    if current_user.role != models.UserRole.support_agent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update ticket status")
    if ticket_update.status:
        ticket.status = ticket_update.status
    db.commit()
    db.refresh(ticket)
    return ticket
