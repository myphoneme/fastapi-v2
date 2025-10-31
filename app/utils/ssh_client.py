import paramiko
import socket
import subprocess
from pysnmp.hlapi import *
# from pysnmp.hlapi import getCmd
# import re
# import logging

def get_os_type(ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command("uname")
    output = stdout.read().decode().lower()
    if "linux" in output:
        return "linux"
    stdin, stdout, stderr = ssh_client.exec_command("systeminfo")
    output = stdout.read().decode().lower()
    if "windows" in output:
        return "windows"
    return "unknown"

def get_metrics_linux(ssh_client):
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'"
    mem_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}'"
    disk_cmd = "df -h --output=source,pcent | grep '^/dev/'"

    #why we are using these commands too like this? istead of top, free, df -h?
    r""" top shows a live dashboard with CPU, memory, etc.

    -b = batch mode (non-interactive)

    -n1 = only 1 snapshot (not continuous)

    grep 'Cpu(s)' = pick the line with CPU info

    awk '{print $2 + $4}' = adds user + system CPU usage, ignoring idle and other overhead. """

    stdin, stdout, stderr = ssh_client.exec_command(cpu_cmd)
    cpu_util = stdout.read().decode().strip() + '%'

    stdin, stdout, stderr = ssh_client.exec_command(mem_cmd)
    mem_util = stdout.read().decode().strip() + '%'

    stdin, stdout, stderr = ssh_client.exec_command(disk_cmd)
    disks_raw = stdout.read().decode().strip().split('\n')
    disks = {}
    for line in disks_raw:
        parts = line.split()
        if len(parts) == 2:
            disks[parts[0].split('/')[-1]] = parts[1]

    return cpu_util, mem_util, disks

def get_metrics_windows(ssh_client):
    cpu_cmd = "wmic cpu get loadpercentage"
    mem_cmd = 'wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value'
    disk_cmd = 'wmic logicaldisk get name,freespace,size'

    # CPU
    stdin, stdout, stderr = ssh_client.exec_command(cpu_cmd)
    cpu_lines = [line.strip() for line in stdout.read().decode().splitlines() if line.strip()]
    if len(cpu_lines) < 2 or not cpu_lines[1].isdigit():
        cpu_util = "N/A"
    else:
        cpu_util = cpu_lines[1] + '%'

    # Memory
    stdin, stdout, stderr = ssh_client.exec_command(mem_cmd)
    mem_data = [line for line in stdout.read().decode().splitlines() if '=' in line]
    try:
        free = int([x for x in mem_data if x.startswith('FreePhysicalMemory=')][0].split('=')[1])
        total = int([x for x in mem_data if x.startswith('TotalVisibleMemorySize=')][0].split('=')[1])
        mem_util = str(round((1 - free / total) * 100, 2)) + '%'
    except (IndexError, ValueError, ZeroDivisionError):
        mem_util = "N/A"

    # Disk
    stdin, stdout, stderr = ssh_client.exec_command(disk_cmd)
    disks = {}
    lines = [line.strip() for line in stdout.read().decode().splitlines() if line.strip()]
    for line in lines[1:]:  # Skip the header
        parts = line.split()
        if len(parts) == 3:
            free, name, size = parts
            try:
                percent = str(round((1 - int(free)/int(size)) * 100, 2)) + '%'
            except ZeroDivisionError:
                percent = "N/A"
            disks[name] = percent
    return cpu_util, mem_util, disks


# def snmp_reachable(ip: str, community: str = "public", port: int = 161, timeout: int = 2) -> bool:
#     """
#     Check if a device is reachable via SNMP (v2c).
#     Returns True if reachable, False otherwise.
#     """
#     iterator = getCmd(
#         SnmpEngine(),
#         CommunityData(community, mpModel=1),  # SNMPv2c
#         UdpTransportTarget((ip, port), timeout=timeout, retries=0),
#         ContextData(),
#         ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0"))  # sysUpTime.0
#     )

#     errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

#     if errorIndication:
#         return False  # No response or timeout
#     if errorStatus:
#         return True   # Responded with error = reachable
#     return True        # Responded successfully

def check_vm(ip, username, password):
    if not username or not password:
        is_reachable = ping_ip(ip)
        # if not is_reachable:
        #     is_reachable = snmp_reachable(ip)
        return {
            "ip": ip,
            "status": "reachable" if is_reachable else "not reachable",
            "os": None,
            "cpu_utilization": None,
            "memory_utilization": None,
            "disk_utilization": None
        }

    else:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=ip, username=username, password=password, timeout=5)

            os_type = get_os_type(client)

            if os_type == "linux":
                cpu, mem, disk = get_metrics_linux(client)
            elif os_type == "windows":
                cpu, mem, disk = get_metrics_windows(client)
            else:
                return {
                    "ip": ip,
                    "status": "not reachable",
                    "os": os_type,
                    "cpu_utilization": None,
                    "memory_utilization": None,
                    "disk_utilization": None,
                }

            return {
                "ip": ip,
                "status": "reachable",
                "os": os_type,
                "cpu_utilization": cpu,
                "memory_utilization": mem,
                "disk_utilization": disk,
            }
        except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout, paramiko.AuthenticationException):
            return {
                "ip": ip,
                "status": "not reachable",
                "os": None,
                "cpu_utilization": None,
                "memory_utilization": None,
                "disk_utilization": None,
            }
        finally:
            client.close()



 

def run_command_on_vm(ip, username, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip, username=username, password=password, timeout=5)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        return {
            "ip": ip,
            "status": "success",
            "stdout": output,
            "stderr": error or None
        }
    except (paramiko.ssh_exception.NoValidConnectionsError, socket.timeout, paramiko.AuthenticationException) as e:
        return {
            "ip": ip,
            "status": "failed",
            "error": str(e)
        }
    finally:
        client.close()


import sys

def ping_ip(ip: str) -> bool:
    try:
        if sys.platform.startswith("win"):
            # Windows ping: -n count, -w timeout (ms)
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "1000", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Linux/Mac ping: -c count, -W timeout (s)
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return result.returncode == 0
    except Exception:
        return False
