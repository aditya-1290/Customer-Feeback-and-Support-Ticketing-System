from fastapi import Request, Response
from datetime import datetime, timedelta
from jose import jwt
from core import security
import time

async def refresh_token_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Only process successful responses
    if response.status_code >= 400:
        return response
    
    # Check if this is a dashboard route
    path = request.url.path
    if not any(path.startswith(p) for p in ["/customer_dashboard", "/support_agent_dashboard"]):
        return response
    
    # Get existing token
    token = request.cookies.get("access_token")
    if not token:
        return response
    
    try:
        clean_token = token.replace("Bearer ", "").strip()
        payload = security.decode_access_token(clean_token)
        
        # Refresh token if it will expire soon (within 30 minutes)
        exp_time = datetime.fromtimestamp(payload.get("exp"))
        if (exp_time - datetime.now()) < timedelta(minutes=30):
            new_token = security.create_access_token({
                "sub": payload.get("sub"),
                "role": payload.get("role"),
                "name": payload.get("name"),
                "id": payload.get("id")
            })
            
            response.set_cookie(
                key="access_token",
                value=f"Bearer {new_token}",
                httponly=True,
                max_age=60 * 60 * 24,
                path="/"
            )
            
    except Exception as e:
        pass
    
    return response