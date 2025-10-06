from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class VMStatus(Base):
    __tablename__ = "vm_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vm_id = Column(Integer, ForeignKey('vm_master.id'), nullable=False)
    status = Column(String(20), nullable=False)
    os = Column(String(50), nullable=True)
    cpu_utilization = Column(String(50), nullable=True)
    memory_utilization = Column(Float, nullable=True)
    disk_utilization = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Integer, default=1, nullable=True)

    vm_master = relationship("VMMaster", back_populates="vm_statuses")
