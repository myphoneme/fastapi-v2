from fastapi import UploadFile,Request
import uuid
from pathlib import Path
import shutil


UPLOAD_DIR = Path("uploads/logs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)




async def upload_file(request: Request, file: UploadFile ):
    uid = uuid.uuid4().hex
    file_path = UPLOAD_DIR / f"{uid}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Use request.base_url to generate full URL dynamically
    file_url = str(request.base_url) + f"files/{uid}_{file.filename}"

    return {
        "file_name": file.filename,
        "file_path": file_path.as_posix(),
        "file_url": file_url
    }
    