from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class VMStatus(Base):
    __tablename__ = "vm_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vm_id = Column(Integer, ForeignKey('vm_master.id'), nullable=False)
    ip = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    os = Column(String(50), nullable=True)
    cpu_utilization = Column(String(50), nullable=True)
    memory_utilization = Column(Float, nullable=True)
    disk_utilization = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    is_active = Column(Boolean, server_default="1", nullable=False)

    vm_master = relationship("VMMaster", back_populates="vm_statuses")

