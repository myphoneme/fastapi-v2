# app/helper/files.py
from __future__ import annotations

import os
import re
import secrets
from pathlib import Path
from typing import Iterable, Optional, Tuple
from fastapi import UploadFile, HTTPException, status

# Set a base directory where all uploads live (e.g., app/static/uploads)
# You can switch this to read from settings if you prefer
UPLOAD_BASE = Path(__file__).resolve().parents[1] / "static" / "uploads"
UPLOAD_BASE.mkdir(parents=True, exist_ok=True)

# allow simple folder names only (letters, numbers, dashes, underscores, slashes subfolders optional)
FOLDER_RE = re.compile(r"^[A-Za-z0-9_\-/]+$")

def _safe_folder(folder: str) -> Path:
    """
    Ensures 'folder' is a simple relative path and resolves inside UPLOAD_BASE.
    Prevents '../' tricks.
    """
    if not folder:
        folder = "misc"
    if not FOLDER_RE.fullmatch(folder):
        raise HTTPException(status_code=400, detail="Invalid folder name.")

    dest = (UPLOAD_BASE / folder).resolve()
    if UPLOAD_BASE not in dest.parents and dest != UPLOAD_BASE:
        raise HTTPException(status_code=400, detail="Invalid folder path.")
    dest.mkdir(parents=True, exist_ok=True)
    return dest

def _ext_from_filename(name: str) -> str:
    # returns like ".png" or ""
    base = os.path.basename(name)
    _, dot, ext = base.rpartition(".")
    return f".{ext.lower()}" if dot else ""

def _gen_filename(ext: str) -> str:
    # random, collision-resistant name
    return f"{secrets.token_hex(16)}{ext}"

async def save_upload_file(
    file: UploadFile,
    folder: str,
    *,
    allowed_extensions: Optional[Iterable[str]] = None,   # e.g. {".png",".jpg",".pdf"}
    max_bytes: Optional[int] = 10 * 1024 * 1024,          # 10 MB default
    return_url_prefix: str = "/static/uploads"            # mount in main.py
) -> dict:
    """
    Saves a single UploadFile to disk under UPLOAD_BASE/<folder>/randomname.ext
    Returns a dict with useful info: path, url, size, original_name, content_type
    """
    # 1) basic validation
    ext = _ext_from_filename(file.filename or "")
    if allowed_extensions is not None and ext not in set(e.lower() for e in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed: {ext or 'no extension'}",
        )

    dest_dir = _safe_folder(folder)
    safe_name = _gen_filename(ext)
    dest_path = dest_dir / safe_name

    # 2) write in chunks
    size = 0
    chunk_size = 1024 * 1024  # 1 MB
    try:
        with dest_path.open("wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                out.write(chunk)
                size += len(chunk)
                if max_bytes is not None and size > max_bytes:
                    out.close()
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (>{max_bytes} bytes)",
                    )
    finally:
        await file.close()

    # 3) build relative URL (so nginx/uvicorn StaticFiles can serve it)
    # UPLOAD_BASE/... -> /static/uploads/...
    rel_path = dest_path.relative_to(UPLOAD_BASE)
    url = f"{return_url_prefix}/{rel_path.as_posix()}"

    return {
        "path": str(dest_path),              # absolute path on disk
        "relative_path": str(rel_path),      # relative to UPLOAD_BASE
        "url": url,                           # public URL (once mounted)
        "size": size,
        "original_name": file.filename,
        "content_type": file.content_type,
        "stored_name": safe_name,
        "folder": folder,
        "extension": ext,
    }

async def save_multiple(
    files: Iterable[UploadFile],
    folder: str,
    **kwargs
) -> Tuple[dict, ...]:
    """
    Save multiple files and return a tuple of results in the same order.
    """
    results = []
    for f in files:
        results.append(await save_upload_file(f, folder, **kwargs))
    return tuple(results)
