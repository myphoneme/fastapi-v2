# app/routers/monitor.py
import asyncio
import platform
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal  # If you only have get_db, replace SessionLocal usage accordingly
from app.core.auth import get_current_user
from app.crud.vm_master import get_all_master_vms
from app.crud.vm_status import create_vm_status 

# Optional deps for metrics (comment out if you only want pings now)
import paramiko           # pip install paramiko
import json
from concurrent.futures import ThreadPoolExecutor

try:
    import winrm  # pip install pywinrm
except Exception:
    winrm = None

router = APIRouter(
    prefix="/monitor",
    tags=["VM Monitoring"],
    dependencies=[Depends(get_current_user)]
)

# =========================
# CONFIG
# =========================
PING_INTERVAL_SEC = 1                 # live dashboard refresh frequency
PING_CONCURRENCY = 150                # high concurrency safe for ping
PING_TIMEOUT_MS = 800                 # per-host ping timeout

METRIC_INTERVAL_CRON_MINUTE = 0       # run on the hour (minute=0)
METRIC_CONCURRENCY = 16               # smaller, SSH/WinRM are expensive
METRIC_TIMEOUT_S = 8                  # per-host metric timeout
VM_LIST_REFRESH_SEC = 60              # refresh vm list for ping loop
# =========================

# Runtime state
_live_cache: Dict[str, Dict[str, Any]] = {}   # ip -> {vm_ip, vm_name, reachable, checked_at}
_cache_lock = asyncio.Lock()
_ping_task: Optional[asyncio.Task] = None
_metric_task: Optional[asyncio.Task] = None
_vm_snapshot: List[Any] = []                  # cached list of VM rows for ping loop
_vm_snapshot_ts: float = 0.0

# Thread pool for blocking SSH/WinRM
_executor = ThreadPoolExecutor(max_workers=METRIC_CONCURRENCY)

# -------------------------
# Helpers: Ping
# -------------------------
def _build_ping_cmd(ip: str) -> List[str]:
    if platform.system().lower().startswith("win"):
        return ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), ip]  # Windows timeout ms
    else:
        secs = max(1, (PING_TIMEOUT_MS + 999)//1000)
        return ["ping", "-c", "1", "-W", str(secs), ip]             # Linux/mac timeout sec

async def _ping(ip: str) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            *_build_ping_cmd(ip),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        rc = await proc.wait()
        return rc == 0
    except Exception:
        return False

# -------------------------
# Helpers: Metrics
# -------------------------
def _ssh_run(ip: str, username: str, password: str, cmd: str, timeout: int = METRIC_TIMEOUT_S) -> str:
    """
    Blocking SSH run using paramiko. Called inside a thread pool.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # internal network; adjust for security
    try:
        client.connect(ip, username=username, password=password, timeout=timeout, banner_timeout=timeout, auth_timeout=timeout)
        _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        if err and not out:
            raise RuntimeError(err.strip())
        return out
    finally:
        client.close()

def _winrm_run(ip: str, username: str, password: str, ps: str, timeout: int = METRIC_TIMEOUT_S) -> str:
    """
    Blocking WinRM run (HTTP 5985). Prefer HTTPS:5986 in production.
    """
    if winrm is None:
        raise RuntimeError("pywinrm not installed")
    s = winrm.Session(f'http://{ip}:5985/wsman', auth=(username, password))
    r = s.run_ps(ps)
    if r.status_code != 0:
        raise RuntimeError((r.std_err or b"").decode(errors="ignore"))
    return (r.std_out or b"").decode(errors="ignore")

async def _collect_metrics(vm) -> Dict[str, Any]:
    """
    Try Linux (SSH). If that fails, try Windows (WinRM).
    Returns a dict matching your VMStatus fields (except created_at).
    """
    ip = vm.ip
    user = vm.username
    pwd = vm.password

    # ---- Linux attempt (fast, simple parsing)
    try:
        loop = asyncio.get_running_loop()
        # OS
        os_out = await loop.run_in_executor(_executor, _ssh_run, ip, user, pwd,
            r"""(grep -m1 '^PRETTY_NAME=' /etc/os-release | cut -d= -f2 | tr -d '"') || uname -sr""")
        # CPU (% busy)
        cpu_out = await loop.run_in_executor(_executor, _ssh_run, ip, user, pwd,
            r"""mpstat 1 1 | awk '/Average/ && $3 ~ /all/ {printf("%.1f",$NF?100-$NF:0)}' || top -bn1 | awk '/Cpu/ {printf("%.1f",100-$8)}'""")
        # RAM (% used)
        ram_out = await loop.run_in_executor(_executor, _ssh_run, ip, user, pwd,
            r"""free -m | awk '/Mem:/ {printf("%.1f", ($3/$2)*100)}'""")
        # DISK (mount:used%)
        disk_out = await loop.run_in_executor(_executor, _ssh_run, ip, user, pwd,
            r"""df -P -x tmpfs -x devtmpfs | awk 'NR>1{print $6":"$5}'""")

        disk_map = {}
        for line in disk_out.splitlines():
            if ":" in line:
                mnt, used = line.strip().split(":", 1)
                disk_map[mnt] = used
        return {
            "status": "UP",
            "os": os_out.strip()[:50] or None,
            "cpu_utilization": (cpu_out.strip() or "0").split()[0],  # keep as string per your schema
            "memory_utilization": float((ram_out.strip() or "0").split()[0]),
            "disk_utilization": ";".join(f"{k} {v}" for k, v in disk_map.items())[:200],
        }
    except Exception as linux_err:
        pass

    # ---- Windows attempt
    try:
        if winrm is None:
            raise RuntimeError("pywinrm not installed")
        loop = asyncio.get_running_loop()
        os_ps = r"(Get-CimInstance Win32_OperatingSystem).Caption"
        cpu_ps = r"(Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue"
        ram_ps = r"(Get-Counter '\Memory\% Committed Bytes In Use').CounterSamples.CookedValue"
        disk_ps = r"Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select DeviceID,Size,FreeSpace | ConvertTo-Json"

        os_out  = await loop.run_in_executor(_executor, _winrm_run, ip, user, pwd, os_ps)
        cpu_out = await loop.run_in_executor(_executor, _winrm_run, ip, user, pwd, cpu_ps)
        ram_out = await loop.run_in_executor(_executor, _winrm_run, ip, user, pwd, ram_ps)
        disk_js = await loop.run_in_executor(_executor, _winrm_run, ip, user, pwd, disk_ps)

        try:
            disks = json.loads(disk_js)
            if isinstance(disks, dict):
                disks = [disks]
        except Exception:
            disks = []

        disk_items = []
        for d in disks:
            size = float(d.get("Size") or 0) or 0.0
            free = float(d.get("FreeSpace") or 0) or 0.0
            used_pct = 0.0 if size == 0 else (1.0 - (free/size)) * 100.0
            disk_items.append(f"{d.get('DeviceID','?')}: {used_pct:.0f}%")
        return {
            "status": "UP",
            "os": (os_out.strip() or "")[:50] or None,
            "cpu_utilization": f"{float(cpu_out.strip() or 0):.1f}",
            "memory_utilization": float(ram_out.strip() or 0.0),
            "disk_utilization": ";".join(disk_items)[:200],
        }
    except Exception as win_err:
        # Reached here → reachable+creds but failed to get metrics
        return {
            "status": "UP",
            "os": None,
            "cpu_utilization": None,
            "memory_utilization": None,
            "disk_utilization": None,
        }

# -------------------------
# VM list cache (reduces DB load)
# -------------------------
def _load_vms_now() -> List[Any]:
    db: Session = SessionLocal()
    try:
        return get_all_master_vms(db)
    finally:
        db.close()

async def _ensure_vm_snapshot() -> List[Any]:
    global _vm_snapshot, _vm_snapshot_ts
    now = asyncio.get_running_loop().time()
    if now - _vm_snapshot_ts > VM_LIST_REFRESH_SEC or not _vm_snapshot:
        loop = asyncio.get_running_loop()
        _vm_snapshot = await loop.run_in_executor(None, _load_vms_now)
        _vm_snapshot_ts = now
    return _vm_snapshot

# -------------------------
# Live ping loop (every second)
# -------------------------
async def _ping_cycle() -> None:
    vms = await _ensure_vm_snapshot()
    sem = asyncio.Semaphore(PING_CONCURRENCY)

    async def check(vm):
        async with sem:
            up = await _ping(vm.ip)
        return vm, up

    results = await asyncio.gather(*(check(vm) for vm in vms))
    now_iso = datetime.now(timezone.utc).isoformat()

    new_cache = {}
    for vm, up in results:
        new_cache[vm.ip] = {
            "vm_ip": vm.ip,
            "vm_name": getattr(vm, "vm_name", None),
            "reachable": up,
            "checked_at": now_iso
        }

    async with _cache_lock:
        _live_cache.clear()
        _live_cache.update(new_cache)

async def _ping_loop():
    # small initial wait to let app settle
    await asyncio.sleep(0.2)
    while True:
        start = asyncio.get_running_loop().time()
        try:
            await _ping_cycle()
        except Exception:
            # TODO: add logging
            pass
        elapsed = asyncio.get_running_loop().time() - start
        sleep_for = max(0.0, PING_INTERVAL_SEC - elapsed)
        await asyncio.sleep(sleep_for)

# -------------------------
# Hourly metric loop (store via CRUD)
# -------------------------
async def _collect_metrics_once():
    """
    For each VM:
      - If unreachable or creds missing -> store DOWN (or UP w/o metrics)
      - If reachable & creds -> gather metrics and store
    Writes one row per VM using create_vm_status(...)
    """
    # Load VMs fresh at collection time
    vms = await _ensure_vm_snapshot()

    # First, reuse live cache reachability if it's fresh; otherwise ping quickly
    async with _cache_lock:
        cache_copy = dict(_live_cache)

    # Build tasks
    metric_sem = asyncio.Semaphore(METRIC_CONCURRENCY)

    async def handle_vm(vm):
        ip = vm.ip
        reachable = cache_copy.get(ip, {}).get("reachable")
        if reachable is None:
            reachable = await _ping(ip)

        data = {
            "vm_id": vm.id,
            "status": "UP" if reachable else "DOWN",
            "os": None,
            "cpu_utilization": None,
            "memory_utilization": None,
            "disk_utilization": None,
            "is_active": 1,
        }

        if reachable and vm.username and vm.password:
            async with metric_sem:
                try:
                    metrics = await asyncio.wait_for(_collect_metrics(vm), timeout=METRIC_TIMEOUT_S + 2)
                    data.update(metrics)
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass

        # DB write (blocking) in default threadpool to avoid blocking loop
        def _db_write(d):
            db: Session = SessionLocal()
            try:
                create_vm_status(db, d)   # time-series insert
                db.commit()
            finally:
                db.close()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _db_write, data)

    await asyncio.gather(*(handle_vm(vm) for vm in vms))

def _seconds_until_next_hour(now: datetime) -> float:
    nxt = (now.replace(minute=METRIC_INTERVAL_CRON_MINUTE, second=0, microsecond=0)
           + timedelta(hours=1 if now.minute >= METRIC_INTERVAL_CRON_MINUTE else 0))
    return (nxt - now).total_seconds()

async def _metric_loop():
    # align to the hour (minute=0 by default)
    await asyncio.sleep(0.5)
    while True:
        now = datetime.now(timezone.utc)
        await asyncio.sleep(_seconds_until_next_hour(now))
        try:
            await _collect_metrics_once()
        except Exception:
            # TODO: add logging
            pass

# -------------------------
# FastAPI lifecycle & endpoints
# -------------------------
@router.on_event("startup")
async def _start_background():
    global _ping_task, _metric_task
    if _ping_task is None or _ping_task.done():
        _ping_task = asyncio.create_task(_ping_loop())
    if _metric_task is None or _metric_task.done():
        _metric_task = asyncio.create_task(_metric_loop())

@router.on_event("shutdown")
async def _stop_background():
    global _ping_task, _metric_task
    for t in (_ping_task, _metric_task):
        if t and not t.done():
            t.cancel()
            try:
                await t
            except Exception:
                pass

@router.get("/live", summary="Live reachability (1s cadence, not stored)")
async def live_status():
    async with _cache_lock:
        data = list(_live_cache.values())
    return {"count": len(data), "interval_sec": PING_INTERVAL_SEC, "data": data}

@router.post("/collect-now", summary="Collect metrics immediately and store one row per VM")
async def collect_now():
    await _collect_metrics_once()
    return {"status": "ok", "message": "Metrics collected and stored."}
