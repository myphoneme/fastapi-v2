from sqlalchemy.orm import Session
from app.schemas.vm_master import VMMasterUpdate, VMMasterCreate
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.vm_master import VMMaster


def get_all_master_vms(db: Session):
    vms = db.query(VMMaster).filter(VMMaster.is_active == 1).all()
    return vms

def add_vm(db: Session, vm_data: VMMasterCreate):
    new_vm = VMMaster(**vm_data.model_dump())
    db.add(new_vm)
    db.commit()
    db.refresh(new_vm)
    return new_vm

def update_master_vm(
    db: Session,
    vm_id: int,
    vm_update: VMMasterUpdate
):
    existing_vm = db.query(VMMaster).filter(VMMaster.id == vm_id, VMMaster.is_active == 1).first()
    if not existing_vm:
        return None
    update_data = vm_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_vm, field, value)
    db.commit()
    db.refresh(existing_vm)
    return existing_vm

def delete_master_vm(db: Session, vm_id: int):
    existing_vm = db.query(VMMaster).filter(VMMaster.id == vm_id, VMMaster.is_active == 1).first()
    if not existing_vm:
        raise HTTPException(status_code=404, detail="VM not found or already deleted.")
    try:
        existing_vm.is_active = 0
        db.commit()
        db.refresh(existing_vm)
        return existing_vm
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Cannot delete VM because it is referenced in other tables (e.g., vm_status). Please remove dependencies first."
        )

def get_master_vm_by_id(db: Session, vm_id: int):
    existing_vm = db.query(VMMaster).filter(VMMaster.id == vm_id, VMMaster.is_active == 1).first()
    if not existing_vm:
        return None
    return existing_vm


