from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable = False)
    password = Column(String(250), nullable=False)
    role     = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    is_active = Column(Integer, default=1, nullable=True)






    
    