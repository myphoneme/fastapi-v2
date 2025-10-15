from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.vm_master import VMMasterCreate, VMMasterUpdate, VMMasterResponse
from app.crud.vm_master import (
    get_all_master_vms,
    add_vm,
    update_master_vm,
    delete_master_vm,
    get_master_vm_by_id,
)

from app.core.auth import get_current_user

router = APIRouter(
    prefix="/vm",
    tags=["VM Master"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=list[VMMasterResponse])
def read_vms(db: Session = Depends(get_db)):
    return get_all_master_vms(db)

@router.get("/{vm_id}", response_model=VMMasterResponse)
def read_vm(vm_id: int, db: Session = Depends(get_db)):
    vm = get_master_vm_by_id(db, vm_id)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    return vm

@router.post("/", response_model=VMMasterResponse, status_code=status.HTTP_201_CREATED)
def create_vm(vm_data: VMMasterCreate, db: Session = Depends(get_db)):
    return add_vm(db, vm_data)

@router.put("/{vm_id}", response_model=VMMasterResponse)
def update_vm(vm_id: int, vm_update: VMMasterUpdate, db: Session = Depends(get_db)):
    vm = update_master_vm(db, vm_id, vm_update)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found or already deleted")
    return vm

@router.delete("/{vm_id}", response_model=VMMasterResponse)
def delete_vm(vm_id: int, db: Session = Depends(get_db)):
    return delete_master_vm(db, vm_id)

