"""Secure file handling helpers."""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(filename: str | None, default: str = "file") -> str:
    name = Path(filename or default).name
    name = SAFE_NAME_RE.sub("_", name).strip("._")
    return name[:120] or default


def private_storage_path(kind: str, filename: str, owner_id: int) -> str:
    root = Path("data") / "private" / kind
    root.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix.lower()
    return str(root / f"{owner_id}_{uuid.uuid4().hex}{ext}")


def ensure_within_private_storage(path: str) -> Path:
    root = Path("data/private").resolve()
    candidate = Path(path).resolve()
    if root != candidate and root not in candidate.parents:
        raise HTTPException(status_code=400, detail="Недопустимый путь к файлу")
    return candidate

async def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Файл превышает допустимый размер")
    return data


def validate_upload(filename: str | None, content_type: str | None, allowed_extensions: set[str]) -> str:
    name = safe_filename(filename)
    ext = Path(name).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Недопустимый тип файла")
    return ext
