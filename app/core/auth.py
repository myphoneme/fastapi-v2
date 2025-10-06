from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from app.core import decode_token
from typing import Dict
from sqlalchemy.orm import Session
from app.database import get_db
# from app.database.db import get_db
from app.helper import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_token_payload(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token=token)
        return payload
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    


def get_current_user(payload:Dict = Depends(get_token_payload), db:Session = Depends(get_db)):
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Use an access token !!")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Subject not found !!")
    user = get_user_by_id(db, int(sub))
    if hasattr(user,"is_active") and not user.is_active:
        raise HTTPException(status_code=403, detail="User was deleted !!")
    return user


