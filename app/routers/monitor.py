import threading
import time
import subprocess
import platform
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
        system = platform.system()
        if system == "Windows":
            cmd = ["ping", "-n", "1", "-w", "1000", ip]
        else:  # Linux, Mac
            cmd = ["ping", "-c", "1", "-W", "1", ip]
        result = subprocess.run(
            cmd,
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


@router.post("/ping_status")
def ping_status(request: VMRequest):
    ip = request.ip
    status = ping_ip(ip)
    return {"ip": ip, "reachable": status}
# @app.post("/ping-status")
# def check_ping_status(request: PingRequest):
#     is_reachable = ping_ip(str(request.ip))
#     return {
#         "ip": request.ip,
#         "reachable": is_reachable
#     }