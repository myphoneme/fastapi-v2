from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.vm_status import VMStatus
# from app.models.vm_master import VMMaster
from app.schemas.vm_status import VMStatusCreate, VMStatusUpdate

def get_all_vm_statuses(db: Session):
    return db.query(VMStatus).filter(VMStatus.is_active == 1).all()

def get_vm_status_by_id(db: Session, status_id: int):
    vm_status = db.query(VMStatus).filter(VMStatus.id == status_id, VMStatus.is_active == 1).first()
    if not vm_status:
        return None
    return vm_status

def create_vm_status(db: Session, vm_status_data: VMStatusCreate):
    new_status = VMStatus(**vm_status_data.model_dump())
    db.add(new_status)
    try:
        db.commit()
        db.refresh(new_status)
        return new_status
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity error while creating VM status.")

def update_vm_status(db: Session, status_id: int, vm_status_update: VMStatusUpdate):
    vm_status = db.query(VMStatus).filter(VMStatus.id == status_id, VMStatus.is_active == 1).first()
    if not vm_status:
        return None
    update_data = vm_status_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vm_status, field, value)
    db.commit()
    db.refresh(vm_status)
    return vm_status

def delete_vm_status(db: Session, status_id: int):
    vm_status = db.query(VMStatus).filter(VMStatus.id == status_id, VMStatus.is_active == 1).first()
    if not vm_status:
        raise HTTPException(status_code=404, detail="VM status not found or already deleted.")
    try:
        vm_status.is_active = 0
        db.commit()
        db.refresh(vm_status)
        return vm_status
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete VM status due to related dependencies.")