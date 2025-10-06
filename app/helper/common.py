import logging
from pprint import pformat
from typing import Any
from pydantic import BaseModel
from app.models import User
from sqlalchemy.orm import Session
from app.schemas import UserInDB


 

logger = logging.getLogger("uvicorn.error")

def show(msg: str, value: Any) -> None:
    """
    Debug helper: pretty-print a value with a message.
    """
    if isinstance(value, BaseModel):
        value = value.model_dump()
    logger.debug("%s:\n%s", msg, pformat(value))


 
def get_user_by_id(db:Session,id:int):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        return None
    else:
        return UserInDB.model_validate(user).model_dump()

