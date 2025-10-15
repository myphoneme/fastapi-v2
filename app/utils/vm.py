import mysql.connector
import requests
import json
import datetime
from app.helper.common import decrypt_password
from pytz import timezone
import datetime

ist = timezone('Asia/Kolkata')
now_ist = datetime.datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

# mypass = "xyz123"
# incpass = encrypt_password(mypass)
# print(f"Encrypted: {incpass}")
# decPass = decrypt_password(incpass)
# print(f"Decrypted: {decPass}")
# exit()
# Connect to the database where both tables exist: vm_database
db = mysql.connector.connect(
    host="127.0.0.1",
    user="remotedbuser",
    password="remotedbuser",
    database="fastapi_db"
)
cursor = db.cursor()

api_url = "http://127.0.0.1:8000/monitor/utilization"
headers = {"internal-token": "WQ2mT2Aq-4lXThGpW_4J4K1uJX7n5P4tGwcj5V7vYGE"}

# Fetch VM credentials from vm_details
cursor.execute("SELECT id, ip, username, password FROM vm_master where is_active=1")
vms = cursor.fetchall()
print(vms)
# print(f"Found {len(vms)} VMs in the database.")
# exit()

success = []
failed = []
for vm_id, ip, username, password in vms:
    print(f"\nFetching status for VM {ip}...")
 

    try:
        if not username  or not password  :
            # print('password or username not found') 
             
            payload = {
                "ip": ip
            }

            response = requests.post(api_url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            status = data.get("status", "unknown")
            os_type = "unknown"
            cpu_usage = 0
            memory_usage = 0
            disk_usage = "{}"
            #  print("Payload without credentials:", payload)
            #  exit()
        else:
            print('password and username found',decrypt_password(password))
            payload = {
                "username": username,
                "password": decrypt_password(password),
                "ip": ip
            }
            response = requests.post(api_url, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 'not reachable':
                payload = {
                    "ip": ip
                }
                response = requests.post(api_url, json=payload, timeout=20)
                response.raise_for_status()
                data = response.json()
                status = data.get("status", "unknown")
                print(f" Status of {ip} is {status}")
                os_type = "unknown"
                cpu_usage = 0
                memory_usage = 0
                disk_usage = "{}"
                # print(data.get("status"))
                # exit('exit with if')
            else: 
                # print("Reachable")
                # exit('Exited')
                status = data.get("status", "unknown")
                os_type = data.get("os", "unknown").lower() if data.get("os", "unknown") is not None else "unknown"
                cpu_raw = data.get("cpu_utilization", "0%")
                memory_raw = data.get("memory_utilization", "0%")

                try:
                    cpu_usage = float(cpu_raw.rstrip('%')) if cpu_raw is not None else 0
                except Exception:
                    cpu_usage = 0

                try:
                    memory_usage = float(memory_raw.rstrip('%')) if memory_raw is not None else 0
                except Exception:
                    memory_usage = 0

            # Get disk utilization and filter if OS is Linux
                disk_util = data.get("disk_utilization", {})
                if "linux" in os_type:
                    filtered_disk_util = {k: v for k, v in disk_util.items() if k.startswith("sd")}
                else:
                    filtered_disk_util = disk_util

                disk_usage = json.dumps(filtered_disk_util)
                # print("Payload with credentials:", payload)
                # exit()
       

        # print(f"VM {ip} - Status: {status}, OS: {os_type}, CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}")
        # exit()

        # Insert into vm_status table
        cursor.execute("""
            INSERT INTO vm_status (vm_id, ip, status, os, cpu_utilization, memory_utilization, disk_utilization, created_at, is_active)
            VALUES (%s,%s, %s, %s, %s, %s, %s,%s,%s)
        """, (vm_id, ip, status, os_type, cpu_usage, memory_usage, disk_usage, now_ist, 1))
        db.commit()

        print(f"Status data saved for VM {ip}")
        success.append(ip)

    except Exception as e:
        print(f"Failed for VM {ip}: {e}")
        failed.append(ip)

# Close connection
cursor.close()
db.close()

# Print summary
print(f"Successfully fetched status for VMs: {success}")
print(f"Failed to fetch status for VMs: {failed}")
