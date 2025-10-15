from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.vm_status import VMStatusCreate, VMStatusUpdate, VMStatusResponse
from app.crud.vm_status import (
    get_all_vm_statuses,
    get_vm_status_by_id,
    create_vm_status,
    update_vm_status,
    delete_vm_status,
)
from app.core.auth import get_current_user

router = APIRouter(
    prefix="/status",
    tags=["VM Status"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=list[VMStatusResponse])
def read_vm_statuses(db: Session = Depends(get_db)):
    return get_all_vm_statuses(db)

@router.get("/{status_id}", response_model=VMStatusResponse)
def read_vm_status(status_id: int, db: Session = Depends(get_db)):
    vm_status = get_vm_status_by_id(db, status_id)
    if not vm_status:
        raise HTTPException(status_code=404, detail="VM status not found")
    return vm_status

@router.post("/", response_model=VMStatusResponse, status_code=status.HTTP_201_CREATED)
def create_status(vm_status_data: VMStatusCreate, db: Session = Depends(get_db)):
    return create_vm_status(db, vm_status_data)

@router.put("/{status_id}", response_model=VMStatusResponse)
def update_status(status_id: int, vm_status_update: VMStatusUpdate, db: Session = Depends(get_db)):
    vm_status = update_vm_status(db, status_id, vm_status_update)
    if not vm_status:
        raise HTTPException(status_code=404, detail="VM status not found or already deleted")
    return vm_status

@router.delete("/{status_id}", response_model=VMStatusResponse)
def delete_status(status_id: int, db: Session = Depends(get_db)):
    return delete_vm_status(db, status_id)
