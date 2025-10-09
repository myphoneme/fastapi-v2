from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship


class VMMaster(Base):
    __tablename__ = "vm_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vm_name = Column(String(500), nullable=False, unique=True)
    ip = Column(String(50), nullable=False)
    username = Column(String(50), nullable=True)
    password = Column(String(200), nullable=True)  
    project_name = Column(String(100), nullable=False)
    cluster = Column(String(200), nullable=True)
    node = Column(String(100), nullable=True)
    remarks = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    is_active = Column(Integer, default=1, nullable=True)
    vm_statuses = relationship("VMStatus", back_populates="vm_master")