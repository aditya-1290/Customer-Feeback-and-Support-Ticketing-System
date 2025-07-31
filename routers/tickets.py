from fastapi import APIRouter, Depends, HTTPException, Request, Header, Form, Query
from fastapi import status
from sqlalchemy.orm import Session
from typing import List
import schemas, models
from database import get_db
from core.security import verify_password
from fastapi.responses import RedirectResponse
from fastapi import Request, Form, Query


router = APIRouter()

async def get_current_user(email: str = Form(None), email_query: str = Query(None), db: Session = Depends(get_db)):
    # Accept email from form data or query parameter
    actual_email = email or email_query
    if not actual_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(models.User).filter(models.User.email == actual_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

@router.post("/create_ticket")
def create_ticket(
    subject: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    email: str = Form(None)
):
    # Only allow customers to create tickets
    if current_user.role != models.UserRole.customer:
        redirect_url = f"/{current_user.role.value}_dashboard?user_email={current_user.email}"
        return RedirectResponse(url=redirect_url, status_code=303)
    new_ticket = models.Ticket(
        user_id=current_user.id,
        subject=subject,
        description=description,
        priority=priority,
        status=models.TicketStatus.open
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    # Redirect back to customer dashboard after ticket creation
    redirect_url = f"/customer_dashboard?user_email={current_user.email}"
    return RedirectResponse(url=redirect_url, status_code=303)

@router.get("/get_tickets", response_model=List[schemas.TicketResponseOut])
def get_tickets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == models.UserRole.support_agent:
        tickets = db.query(models.Ticket).all()
    else:
        tickets = db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).all()
    return tickets

@router.post("/add_ticket_response/{ticket_id}/responses")
def add_ticket_response(
    request: Request,
    ticket_id: int,
    message: str = Form(...),
    email: str = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    # Authorization check: only ticket owner or support agent can add response
    if current_user.role != models.UserRole.support_agent and ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add response to this ticket")
    new_response = models.TicketResponse(
        ticket_id=ticket_id,
        responder_id=current_user.id,
        message=message
    )
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=303)
    else:
        if current_user.role == models.UserRole.customer:
            redirect_url = f"/customer_dashboard?user_email={email}"
        else:
            redirect_url = f"/support_agent_dashboard?user_email={email}"
        return RedirectResponse(url=redirect_url, status_code=303)

from fastapi import Form

from fastapi.responses import RedirectResponse
from fastapi import Form, Request

@router.post("/update_ticket_status/{ticket_id}")
def update_ticket_status(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    email: str = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    # Authorization check: only support agents can update ticket status
    if current_user.role != models.UserRole.support_agent:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update ticket status")
    if status:
        ticket.status = status
    db.commit()
    db.refresh(ticket)
    # Redirect back to support agent dashboard or tickets page
    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=303)
    else:
        redirect_url = f"/support_agent_dashboard?user_email={email}"
        return RedirectResponse(url=redirect_url, status_code=303)

@router.post("/test_create_ticket")
def test_create_ticket(email: str = Form(...), password: str = Form(...), subject: str = Form(...), description: str = Form(...), priority: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    # Create ticket for authenticated user
    new_ticket = models.Ticket(
        user_id=user.id,
        subject=subject,
        description=description,
        priority=priority,
        status=models.TicketStatus.open
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket
