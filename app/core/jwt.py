from app.core import settings
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, ExpiredSignatureError, JWTError 


def _encode(payload: Dict , expiry_time_delta : Optional[timedelta] = None):
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    if expiry_time_delta is None:
       expiry =  now + timedelta(minutes=settings.access_token_expire_minutes)
    else:
       expiry = now + expiry_time_delta
    
    to_encode['exp'] = expiry
    

    return jwt.encode(to_encode,settings.secret_key,algorithm=settings.algorithm)

def create_token(subject:str, name : str , scopes : list  = [])->str:
   payload = {"sub" : subject, "name" : name, "type":"access", "scopes": scopes}
   return _encode(payload)

def refresh_token(subject:str):
   payload = {"sub" : subject, "type" : "refresh"}
   return _encode(payload)

def decode_token(token:str):
   try:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
   except ExpiredSignatureError as e:
      raise ValueError("Token expired") from e
   except JWTError as e:
      raise ValueError(f"Invalid token {token} ") from e
      

