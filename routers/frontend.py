from fastapi import APIRouter, Request, Form, Depends, status, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from core import security
from fastapi.responses import JSONResponse
# from starlette.middleware.sessions import SessionMiddleware
# from fastapi import FastAPI

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Add session middleware to app (this requires app instance, so will be added in main.py)
# For now, we will handle sessions via cookies manually or use JWT tokens in headers for API calls.

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
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

from fastapi.responses import JSONResponse

@router.post("/login")
def post_login(request: Request, email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.password_hash) or user.role.value != role:
        return JSONResponse(status_code=400, content={"error": "Invalid credentials or role"})
    access_token = security.create_access_token(data={"sub": user.email, "role": user.role.value})
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    # Redirect to dashboard page routes
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    token = token.removeprefix("Bearer ").strip()
    payload = security.decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")
    user_role = payload.get("role")
    if user_role == "customer":
        return RedirectResponse(url="/customer_dashboard")
    elif user_role == "support_agent":
        return RedirectResponse(url="/support_agent_dashboard")
    else:
        return RedirectResponse(url="/login")

@router.get("/customer_dashboard", response_class=HTMLResponse)
def customer_dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    token = token.removeprefix("Bearer ").strip()
    payload = security.decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")
    user_email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    tickets = db.query(models.Ticket).filter(models.Ticket.user_id == user.id).order_by(models.Ticket.created_at.desc()).all()
    return templates.TemplateResponse("customer_dashboard.html", {"request": request, "user": user, "tickets": tickets})

@router.get("/support_agent_dashboard", response_class=HTMLResponse)
def support_agent_dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    token = token.removeprefix("Bearer ").strip()
    payload = security.decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")
    user_email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    # For support agent, show all tickets (or you can filter assigned tickets if applicable)
    tickets = db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).all()
    return templates.TemplateResponse("support_agent_dashboard.html", {"request": request, "user": user, "tickets": tickets})

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
