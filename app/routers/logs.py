from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from app.core.auth import get_current_user
from app.helper.path import LOGS_DIR
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File, Request
from app.helper import upload_file
import os
from fastapi.responses import JSONResponse
from datetime import datetime
from app.helper.path import LOGS_URL


router = APIRouter(prefix="/logs", tags=["Logs"], dependencies=[Depends(get_current_user)])


@router.post("/upload", dependencies = [Depends(get_current_user)])
async def uploadFile(request:Request,file: UploadFile = File(...)):
    return await upload_file(request,file)

@router.get("/path")
def get_logs_path():
    return {"logs_path": LOGS_DIR}

@router.get("/list")
def list_log_files(request: Request):
    if not os.path.exists(LOGS_DIR):
        return JSONResponse(status_code=404, content={"error": "Logs directory not found."})

    items = []
    for fname in os.listdir(LOGS_DIR):
        fpath = os.path.join(LOGS_DIR, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            items.append({
                "name": fname,
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                # build URL from the mounted app's NAME
                "url": str(request.url_for("log_files", path=fname)),
            })

    # sort by actual mtime (not the formatted string)
    items.sort(key=lambda x: os.path.getmtime(os.path.join(LOGS_DIR, x["name"])), reverse=True)

    return {"count": len(items), "files": items}

@router.get("/download/{filename}")
def download_log_file(filename: str):
    file_path = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Log file not found.")
    return JSONResponse(content={"file_url": f"{LOGS_URL}/{filename}"})

@router.delete("/delete/{filename}")
def delete_log_file(filename: str):
    file_path = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Log file not found.")
    os.remove(file_path)
    return {"detail": f"Log file '{filename}' deleted successfully."}