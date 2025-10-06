from app.models import User
from sqlalchemy.orm import Session


def insert_user(db:Session,data:dict):
    user = User(**data)
    db.add(user)
    return user 

def get_user_by_email(db:Session, email:str):
    user = db.query(User).filter(User.email == email).first()
    return user
