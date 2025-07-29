from fastapi import APIRouter, Request, Form, Depends, status, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from core import security
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger("uvicorn.access")

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

@router.post("/login")
def post_login(request: Request, email: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.password_hash) or user.role.value != role:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials or role"})
    access_token = security.create_access_token(data={"sub": user.email, "role": user.role.value})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax")
    return response

@router.get("/logout")
def logout():
    # No cookie to delete, just redirect to login
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, db: Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return RedirectResponse(url="/login")
    token = authorization.removeprefix("Bearer ").strip()
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
    payload = security.decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")
    user_email = payload.get("sub")
    user_role = payload.get("role")
    logger.info(f"Customer Dashboard accessed by user: {user_email} with role: {user_role}")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    tickets = db.query(models.Ticket).filter(models.Ticket.user_id == user.id).order_by(models.Ticket.created_at.desc()).all()
    response = templates.TemplateResponse("customer_dashboard.html", {"request": request, "user": user, "tickets": tickets})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/support_agent_dashboard", response_class=HTMLResponse)
def support_agent_dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    payload = security.decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login")
    user_email = payload.get("sub")
    user_role = payload.get("role")
    logger.info(f"Support Agent Dashboard accessed by user: {user_email} with role: {user_role}")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login")
    # For support agent, show all tickets (or you can filter assigned tickets if applicable)
    tickets = db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).all()
    response = templates.TemplateResponse("support_agent_dashboard.html", {"request": request, "user": user, "tickets": tickets})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.get("/user_info")
def user_info(db: Session = Depends(get_db), authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    token = authorization.removeprefix("Bearer ").strip()
    payload = security.decode_access_token(token)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    user_email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return {"email": user.email, "name": user.name, "role": user.role.value}
