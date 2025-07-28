from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from core import security
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI

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

from core import security

@router.post("/login")
def post_login(request: Request, email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.password_hash) or user.role.value != role:
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": "Invalid credentials or role"})
    access_token = security.create_access_token(data={"sub": user.email, "role": user.role.value})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    token = token.removeprefix("Bearer ").strip()
    payload = security.decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")
    user_email = payload.get("sub")
    user_role = payload.get("role")
    if user_role == "customer":
        user = None
        if user_email:
            user = db.query(models.User).filter(models.User.email == user_email).first()
        return templates.TemplateResponse(request, "customer_dashboard.html", {"request": request, "user": user})
    elif user_role == "support_agent":
        return templates.TemplateResponse(request, "support_agent_dashboard.html", {"request": request})
    else:
        return RedirectResponse(url="/login")

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
