from datetime import datetime, timedelta
from jose import JWTError, jwt
import time
import os
from uuid import uuid4
import logging
from typing import Optional

SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secure-key-123456")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24 hours

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Add session-specific claims
    to_encode.update({
        "exp": int(time.mktime(expire.timetuple())),
        "jti": str(uuid4()),  # Unique token identifier
        "iat": int(time.time())  # Issued at timestamp
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_exp": True,
                "verify_exp": True,
                "require_iat": True
            }
        )
        return payload
    except JWTError as e:
        logging.error(f"Token validation failed: {str(e)}")
        return None
    

# def decode_access_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
#         # Convert string role back to enum if needed
#         if 'role' in payload:
#             from models import UserRole
#             try:
#                 payload['role'] = UserRole(payload['role'])
#             except ValueError:
#                 pass
                
#         return payload
#     except JWTError as e:
#         print(f"Token decode error: {str(e)}")
#         return None
       
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now() + expires_delta
#     else:
#         expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
    
#     # Ensure all values are serializable
#     for key, value in to_encode.items():
#         if hasattr(value, 'value'):  # Handle enum values
#             to_encode[key] = value.value
#         elif not isinstance(value, (str, int, float, bool, list, dict)):
#             to_encode[key] = str(value)
    
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# async def get_current_user(request: Request, db: Session = Depends(get_db)):
#     session_id = request.cookies.get("session_id")
#     if not session_id:
#         raise HTTPException(status_code=401, detail="Not authenticated")

#     token = request.cookies.get(f"token_{session_id}")
#     if not token:
#         raise HTTPException(status_code=401, detail="Invalid session")

#     payload = decode_access_token(token)
#     if not payload or payload.get("session_id") != session_id:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     user_email = payload.get("sub")
#     user = db.query(models.User).filter(models.User.email == user_email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return user