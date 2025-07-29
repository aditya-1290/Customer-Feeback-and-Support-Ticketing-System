from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
import logging
import time
import os
from uuid import uuid4

# Generate a proper secret key or use environment variable
SECRET_KEY = os.getenv("SECRET_KEY", "fdfsdlfhsjkdfhsdjfweirrwoowoidhfjclsdfhkjsdhfkjsdhf1234567890")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Convert expiration to UNIX timestamp (integer)
    to_encode.update({
        "exp": int(time.mktime(expire.timetuple())),
        "jti": str(uuid4()),  # Unique token identifier
        "iat": int(time.time())  # Issued at timestamp
    })
    
    # Ensure all values are serializable
    for key, value in to_encode.items():
        if hasattr(value, 'value'):  # Handle enum values
            to_encode[key] = value.value
        elif not isinstance(value, (str, int, float, bool, list, dict)):
            to_encode[key] = str(value)
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
            }  # Ensure exp claim exists
        )
        
        # Convert expiration to datetime for easier handling
        if 'exp' in payload:
            # Defensive check: convert exp to int if it's a string
            try:
                exp_int = int(payload['exp'])
            except (ValueError, TypeError):
                exp_int = int(float(payload['exp']))
            payload['exp_datetime'] = datetime.fromtimestamp(exp_int)
        
        return payload
    except JWTError as e:
        logging.error(f"Token decode error: {str(e)}")
        return None
