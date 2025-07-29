from fastapi import APIRouter, Request, Form, Depends, status, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import models
from core import security
import logging
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("uvicorn.access")

@router.post("/login")
async def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    """Enhanced login endpoint with proper user data return"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.password_hash):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid email or password"}
        )
    
    if user.role.value != role:
        return JSONResponse(
            status_code=400,
            content={"error": f"User is not a {role}"}
        )
    
    access_token = security.create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "name": user.name,
            "id": str(user.id)
        }
    )
    
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "id": user.id
            }
        }
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response

@router.get("/dashboard")
async def get_dashboard(request: Request, db: Session = Depends(get_db)):
    """Router that redirects to appropriate dashboard"""
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    
    try:
        # Remove "Bearer " prefix if present
        token = token.replace("Bearer ", "").strip()
        payload = security.decode_access_token(token)
        
        if not payload:
            raise ValueError("Invalid token")
        
        user_role = payload.get("role")
        if user_role == "customer":
            return RedirectResponse(url="/customer_dashboard")
        elif user_role == "support_agent":
            return RedirectResponse(url="/support_agent_dashboard")
        else:
            raise ValueError("Unknown role")
            
    except Exception as e:
        logger.error(f"Dashboard redirect error: {str(e)}")
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response

@router.get("/support_agent_dashboard", response_class=HTMLResponse)
async def support_agent_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Complete support agent dashboard endpoint"""
    try:
        # Get and validate token
        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse(url="/login")
        
        token = token.replace("Bearer ", "").strip()
        payload = security.decode_access_token(token)
        
        if not payload:
            raise ValueError("Invalid token")
        
        # Verify user exists
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        
        if not user:
            raise ValueError("User not found")
        
        if user.role.value != "support_agent":
            raise ValueError("Unauthorized access")
        
        # Get tickets and prepare context
        tickets = db.query(models.Ticket).order_by(models.Ticket.created_at.desc()).all()
        
        context = {
            "request": request,
            "user": {
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "id": user.id
            },
            "tickets": tickets
        }
        
        response = templates.TemplateResponse(
            "support_agent_dashboard.html",
            context
        )
        
        # Prevent caching
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
        
    except Exception as e:
        logger.error(f"Support dashboard error: {str(e)}")
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response

@router.get("/customer_dashboard", response_class=HTMLResponse)
async def customer_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Complete customer dashboard endpoint"""
    try:
        # Get and validate token
        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse(url="/login")
        
        token = token.replace("Bearer ", "").strip()
        payload = security.decode_access_token(token)
        
        if not payload:
            raise ValueError("Invalid token")
        
        # Verify user exists
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        
        if not user:
            raise ValueError("User not found")
        
        if user.role.value != "customer":
            raise ValueError("Unauthorized access")
        
        # Get user's tickets
        tickets = (
            db.query(models.Ticket)
            .filter(models.Ticket.user_id == user.id)
            .order_by(models.Ticket.created_at.desc())
            .all()
        )
        
        context = {
            "request": request,
            "user": {
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "id": user.id
            },
            "tickets": tickets
        }
        
        response = templates.TemplateResponse(
            "customer_dashboard.html",
            context
        )
        
        # Prevent caching
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
        
    except Exception as e:
        logger.error(f"Customer dashboard error: {str(e)}")
        response = RedirectResponse(url="/login")
        response.delete_cookie("access_token")
        return response
    
@router.get("/debug_token")
async def debug_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return {"error": "No token found"}
    
    token = token.replace("Bearer ", "").strip()
    payload = security.decode_access_token(token)
    
    return {
        "raw_token": token,
        "decoded_payload": payload
    }
    
# @router.post("/login")
# async def post_login(
#     request: Request,
#     email: str = Form(...),
#     password: str = Form(...),
#     role: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     user = db.query(models.User).filter(models.User.email == email).first()
#     if not user or not security.verify_password(password, user.password_hash):
#         return JSONResponse(
#             status_code=400,
#             content={"error": "Invalid email or password"}
#         )
    
#     if user.role.value != role:
#         return JSONResponse(
#             status_code=400,
#             content={"error": f"User is not a {role}"}
#         )
    
#     # Create token with extended expiration
#     token_data = {
#         "sub": user.email,
#         "role": user.role.value,
#         "name": user.name,
#         "id": str(user.id)
#     }
    
#     access_token = security.create_access_token(data=token_data)
    
#     response = JSONResponse(
#         content={
#             "access_token": access_token,
#             "token_type": "bearer",
#             "user": {
#                 "name": user.name,
#                 "email": user.email,
#                 "role": user.role.value,
#                 "id": user.id
#             }
#         }
#     )
    
#     # Set secure cookie with longer lifespan
#     response.set_cookie(
#         key="access_token",
#         value=f"Bearer {access_token}",
#         httponly=True,
#         secure=False,  # Set to True in production with HTTPS
#         samesite="lax",
#         max_age=60 * 60 * 24,  # 24 hours
#         path="/"  # Make cookie available across all paths
#     )
    
#     return response

# @router.get("/dashboard")
# async def get_dashboard(request: Request, db: Session = Depends(get_db)):
#     """Enhanced dashboard router with better error handling"""
#     # Get token from cookies
#     token = request.cookies.get("access_token")
#     if not token:
#         print("No token found - redirecting to login")
#         return RedirectResponse(url="/login")

#     try:
#         # Clean token
#         clean_token = token.replace("Bearer ", "").strip()
        
#         # Decode token
#         payload = security.decode_access_token(clean_token)
#         if not payload:
#             print("Invalid token payload")
#             raise ValueError("Invalid token payload")
        
#         # Verify required fields
#         if not all(key in payload for key in ["sub", "role"]):
#             print("Missing required token fields")
#             raise ValueError("Missing required token fields")
        
#         # Get user role
#         user_role = payload.get("role")
#         print(f"User role from token: {user_role}")  # Debugging
        
#         # Check if role is enum and get value if needed
#         if hasattr(user_role, 'value'):
#             user_role = user_role.value
        
#         # Redirect based on role
#         if user_role == "customer":
#             print("Redirecting to customer dashboard")
#             return RedirectResponse(url="/customer_dashboard")
#         elif user_role == "support_agent":
#             print("Redirecting to support agent dashboard")
#             return RedirectResponse(url="/support_agent_dashboard")
#         else:
#             print(f"Unknown role: {user_role}")
#             raise ValueError(f"Unknown role: {user_role}")
            
#     except Exception as e:
#         print(f"Dashboard redirect error: {str(e)}")
#         # Clear invalid token and redirect to login
#         response = RedirectResponse(url="/login")
#         response.delete_cookie("access_token")
#         return response
    
# logger = logging.getLogger("uvicorn.access")

# @router.get("/customer_dashboard", response_class=HTMLResponse)
# async def customer_dashboard(request: Request, db: Session = Depends(get_db)):
#     try:
#         token = request.cookies.get("access_token")
#         if not token:
#             return RedirectResponse(url="/login")
        
#         clean_token = token.replace("Bearer ", "").strip()
#         payload = security.decode_access_token(clean_token)
        
#         if not payload:
#             raise ValueError("Invalid token")
        
#         # Get user with relaxed role check
#         user_email = payload.get("sub")
#         user = db.query(models.User).filter(models.User.email == user_email).first()
#         if not user:
#             raise ValueError("User not found")
        
#         # Get tickets
#         tickets = db.query(models.Ticket).filter(models.Ticket.user_id == user.id).all()
        
#         response = templates.TemplateResponse(
#             "customer_dashboard.html",
#             {
#                 "request": request,
#                 "user": {
#                     "name": user.name,
#                     "email": user.email,
#                     "role": user.role.value,
#                     "id": user.id
#                 },
#                 "tickets": tickets
#             }
#         )
        
#         # Refresh cookie on successful access
#         response.set_cookie(
#             key="access_token",
#             value=f"Bearer {clean_token}",
#             httponly=True,
#             max_age=60 * 60 * 24,
#             path="/"
#         )
        
#         return response
        
#     except Exception as e:
#         logging.error(f"Customer dashboard error: {str(e)}")
#         response = RedirectResponse(url="/login")
#         response.delete_cookie("access_token")
#         return response


@router.get("/inspect_token")
async def inspect_token(request: Request):
    """Endpoint to inspect the current token"""
    token = request.cookies.get("access_token")
    if not token:
        return {"status": "no token found"}
    
    try:
        clean_token = token.replace("Bearer ", "").strip()
        payload = security.decode_access_token(clean_token)
        
        return {
            "raw_token": token,
            "clean_token": clean_token,
            "decoded_payload": payload,
            "payload_type": {k: type(v) for k, v in payload.items()} if payload else None
        }
    except Exception as e:
        return {"error": str(e)}
    
    
    
from uuid import uuid4

@router.post("/login")
async def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.password_hash):
        return JSONResponse(status_code=400, content={"error": "Invalid credentials"})

    if user.role.value != role:
        return JSONResponse(status_code=403, content={"error": "Role mismatch"})

    # Generate unique session ID
    session_id = str(uuid4())
    
    # Create session-specific token
    token = security.create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "name": user.name,
            "id": str(user.id),
            "session_id": session_id
        }
    )

    response = JSONResponse(content={
        "access_token": token,
        "token_type": "bearer",
        "session_id": session_id
    })

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # True in production
        max_age=86400,  # 24 hours
        path="/"
    )

    # Set token cookie
    response.set_cookie(
        key=f"token_{session_id}",
        value=token,
        httponly=True,
        secure=False,
        max_age=86400,
        path="/"
    )

    return response

@router.get("/dashboard")
async def get_dashboard(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/login")

    token = request.cookies.get(f"token_{session_id}")
    if not token:
        return RedirectResponse(url="/login")

    try:
        payload = security.decode_access_token(token)
        if not payload or payload.get("session_id") != session_id:
            raise ValueError("Invalid session")

        # Redirect based on role
        role = payload.get("role")
        if role == "customer":
            return RedirectResponse(url="/customer_dashboard")
        elif role == "support_agent":
            return RedirectResponse(url="/support_agent_dashboard")
        else:
            raise ValueError("Unknown role")
            
    except Exception as e:
        response = RedirectResponse(url="/login")
        response.delete_cookie("session_id")
        response.delete_cookie(f"token_{session_id}")
        return response

@router.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    response = RedirectResponse(url="/login")
    
    if session_id:
        response.delete_cookie(f"token_{session_id}")
    
    response.delete_cookie("session_id")
    return response


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = request.cookies.get(f"token_{session_id}")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid session")

    payload = security.decode_access_token(token)
    if not payload or payload.get("session_id") != session_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.get("/customer_dashboard", response_class=HTMLResponse)
async def customer_dashboard(
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "customer":
        raise HTTPException(status_code=403, detail="Forbidden")

    tickets = db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).all()
    
    return templates.TemplateResponse(
        "customer_dashboard.html",
        {
            "request": request,
            "user": {
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role.value,
                "id": current_user.id
            },
            "tickets": tickets
        }
    )