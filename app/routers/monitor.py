import threading
import time
import subprocess
from fastapi import APIRouter #, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.vm_master import get_all_master_vms
# from app.core.auth import get_current_user  
from app.schemas.monitor import VMRequest
from app.utils.ssh_client import check_vm

router = APIRouter(prefix="/monitor", tags=["VM Monitoring"]) #, dependencies=[Depends(get_current_user)]

# Global dictionary to store VM reachability status
vm_status_cache = {}

def ping_ip(ip: str) -> bool:
    """Ping an IP address and return True if reachable, False otherwise."""
    try:
        # Windows: use '-n 1', Linux/Mac: use '-c 1'
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False

def monitor_vms(db_session_factory):
    while True:
        db: Session = next(db_session_factory())
        vms = get_all_master_vms(db)
        for vm in vms:
            ip = vm.ip
            status = ping_ip(ip)
            vm_status_cache[ip] = {"vm_ip":ip,"vm_name": vm.vm_name, "reachable": status}
        db.close()
        time.sleep(1)

def start_monitoring_thread(db_session_factory):
    thread = threading.Thread(target=monitor_vms, args=(db_session_factory,), daemon=True)
    thread.start()

# Start the monitoring thread when the module is imported
start_monitoring_thread(get_db)

@router.get("/ping")
def get_vm_status():
    """API endpoint to get the latest reachability status of all VMs."""
    return list(vm_status_cache.values())

@router.post("/utilization")
def vm_status(request: VMRequest):
    return check_vm(request.ip, request.username, request.password)
