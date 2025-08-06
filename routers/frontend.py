from fastapi import APIRouter, Request, Form, Depends, status, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from database import get_db
import models
from core import security
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})

@router.post("/register")
def post_register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(request, "register.html", {"request": request, "error": "Email already registered"})
    hashed_password = security.get_password_hash(password)
    new_user = models.User(name=name, email=email, password_hash=hashed_password, role=role)
    print(new_user)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@router.post("/login")
def post_login(request: Request, email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    print(type(user))
    if not user or not security.verify_password(password, user.password_hash) or user.role.value != role:
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": "Invalid credentials or role"})
    # Redirect to dashboard with user_email as query parameter
    response = RedirectResponse(url=f"/dashboard?user_email={user.email}", status_code=status.HTTP_302_FOUND)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db), user_email: str = None):
    if not user_email:
        return RedirectResponse(url="/login")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    user_role = user.role.value
    if user_role == "customer":
        return RedirectResponse(url=f"/customer_dashboard?user_email={user_email}")
    elif user_role == "support_agent":
        return RedirectResponse(url=f"/support_agent_dashboard?user_email={user_email}")
    else:
        return RedirectResponse(url="/login")

@router.get("/customer_dashboard", response_class=HTMLResponse)
def customer_dashboard(request: Request, db: Session = Depends(get_db), user_email: str = None):
    if not user_email:
        return RedirectResponse(url="/login")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    logger.info("Customer Dashboard accessed by user: %s with role: %s", user.email, user.role.value)
    tickets = db.query(models.Ticket).options(joinedload(models.Ticket.responses).joinedload(models.TicketResponse.responder)).filter(models.Ticket.user_id == user.id).order_by(models.Ticket.created_at.desc()).limit(3).all()
    response = templates.TemplateResponse("customer_dashboard.html", {"request": request, "user": user, "tickets": tickets})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/support_agent_dashboard", response_class=HTMLResponse)
def support_agent_dashboard(request: Request, db: Session = Depends(get_db), user_email: str = None):
    if not user_email:
        return RedirectResponse(url="/login")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    logger.info("Support Agent Dashboard accessed by user: %s with role: %s", user.email, user.role.value)
    tickets = db.query(models.Ticket).options(joinedload(models.Ticket.responses).joinedload(models.TicketResponse.responder)).order_by(models.Ticket.created_at.desc()).limit(3).all()
    response = templates.TemplateResponse("support_agent_dashboard.html", {"request": request, "user": user, "tickets": tickets})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/customer_tickets", response_class=HTMLResponse)
def customer_tickets(request: Request, db: Session = Depends(get_db), user_email: str = None):
    if not user_email:
        return RedirectResponse(url="/login")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    tickets = db.query(models.Ticket).filter(models.Ticket.user_id == user.id).order_by(models.Ticket.created_at.desc()).all()
    response = templates.TemplateResponse("customer_tickets.html", {"request": request, "user": user, "tickets": tickets})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/support_agent_tickets", response_class=HTMLResponse)
def support_agent_tickets(
    request: Request,
    db: Session = Depends(get_db),
    user_email: str = None,
    status: str = None,
    priority: str = None,
    customer_name: str = None
):
    if not user_email:
        return RedirectResponse(url="/login")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    query = db.query(models.Ticket).join(models.User, models.Ticket.user_id == models.User.id)
    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    if customer_name:
        query = query.filter(models.User.name.ilike(f"%{customer_name}%"))
    tickets = query.order_by(models.Ticket.created_at.desc()).all()
    response = templates.TemplateResponse("support_agent_tickets.html", {"request": request, "user": user, "tickets": tickets})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/logout")
def logout():
    # No cookie to delete, just redirect to login
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response

@router.get("/user_info")
def user_info(db: Session = Depends(get_db), user_email: str = None):
    if not user_email:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return {"email": user.email, "name": user.name, "role": user.role.value}
