"""Marketplace listings: persistent submissions, FNS-aware verification and quarantine uploads."""
from __future__ import annotations

import hashlib
import mimetypes
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.core.database import get_db
from app.core.file_security import safe_filename, private_storage_path, ensure_within_private_storage, read_limited, validate_upload
from app.core.config import settings
from app.models import User

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

ALLOWED = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
MAX_FILE_BYTES = min(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024, 10 * 1024 * 1024)


def _valid_inn(inn: str) -> bool:
    inn = (inn or "").strip()
    if len(inn) == 10 and inn.isdigit():
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return sum(int(inn[i]) * weights[i] for i in range(9)) % 11 % 10 == int(inn[9])
    if len(inn) == 12 and inn.isdigit():
        w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        c1 = sum(int(inn[i]) * w1[i] for i in range(10)) % 11 % 10
        c2 = sum(int(inn[i]) * w2[i] for i in range(11)) % 11 % 10
        return c1 == int(inn[10]) and c2 == int(inn[11])
    return False


def _verification_status(account_type: str, inn: Optional[str]) -> str:
    if account_type == "self_employed":
        if not inn or len(inn) != 12 or not _valid_inn(inn):
            return "rejected_invalid_inn"
        return "pending_fns"
    if account_type in {"individual_entrepreneur", "company", "employer", "education_center"}:
        if not inn or len(inn) != 10 or not _valid_inn(inn):
            return "rejected_invalid_inn"
        return "pending_fns"
    return "pending"


def _scan_file(path: str) -> str:
    """Fail closed for publication: use local ClamAV when available, otherwise quarantine."""
    clamscan = shutil.which("clamscan")
    if not clamscan:
        return "quarantine"
    try:
        result = subprocess.run([clamscan, "--no-summary", path], capture_output=True, text=True, timeout=45)
        return "clean" if result.returncode == 0 else "infected"
    except Exception:
        return "quarantine"


@router.get("/listings")
async def list_listings(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("""
        SELECT id, account_type, kind, title, description, direction, contact_email,
               verification_status, moderation_status, created_at
        FROM marketplace_listings
        WHERE moderation_status = 'published' AND verification_status IN ('verified','pending_fns')
        ORDER BY created_at DESC LIMIT 100
    """))).mappings().all()
    return [dict(row) for row in rows]


@router.post("/listings", status_code=201)
async def create_listing(
    request: Request,
    account_type: str = Form(...),
    kind: str = Form(..., max_length=80),
    title: str = Form(..., max_length=255),
    description: str = Form(..., max_length=10000),
    direction: Optional[str] = Form(None, max_length=120),
    contact_email: Optional[str] = Form(None, max_length=255),
    inn: Optional[str] = Form(None, max_length=20),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    allowed_types = {"self_employed", "individual_entrepreneur", "company", "employer", "education_center"}
    if account_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Неверный тип участника")
    verification = _verification_status(account_type, inn)
    if verification == "rejected_invalid_inn":
        raise HTTPException(status_code=422, detail="Укажите корректный ИНН: для самозанятого/физлица — 12 цифр, для ИП/организации — 10 цифр")

    result = await db.execute(text("""
        INSERT INTO marketplace_listings
          (user_id, account_type, kind, title, description, direction, contact_email, inn, verification_status, moderation_status)
        VALUES (:user_id, :account_type, :kind, :title, :description, :direction, :contact_email, :inn, :verification_status, 'pending')
        RETURNING id, created_at
    """), {
        "user_id": current_user.id if current_user else None,
        "account_type": account_type,
        "kind": kind.strip(),
        "title": title.strip(),
        "description": description.strip(),
        "direction": (direction or "").strip() or None,
        "contact_email": (contact_email or (current_user.email if current_user else "")).strip() or None,
        "inn": (inn or "").strip() or None,
        "verification_status": verification,
    })
    row = result.mappings().one()
    await db.commit()
    return {"id": row["id"], "verification_status": verification, "moderation_status": "pending", "message": "Объявление сохранено и отправлено на проверку."}


@router.post("/listings/{listing_id}/files", status_code=201)
async def upload_listing_file(
    listing_id: int,
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text("SELECT id, user_id FROM marketplace_listings WHERE id=:id"), {"id": listing_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if row["user_id"] is not None and (not current_user or row["user_id"] != current_user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к файлу объявления")

    ext = validate_upload(file.filename, file.content_type, ALLOWED)
    data = await read_limited(file, MAX_FILE_BYTES)
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")
    # Basic signature checks prevent renamed executables from entering the document pipeline.
    signatures = {
        ".pdf": data.startswith(b"%PDF-"),
        ".png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": data.startswith(b"\xff\xd8\xff"),
        ".jpeg": data.startswith(b"\xff\xd8\xff"),
        ".docx": data.startswith(b"PK\x03\x04"),
        ".doc": data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
    }
    if not signatures.get(ext, False):
        raise HTTPException(status_code=400, detail="Содержимое файла не соответствует расширению")

    filename = safe_filename(file.filename)
    stored = private_storage_path("marketplace", filename, current_user.id if current_user else 0)
    path = ensure_within_private_storage(stored)
    path.write_bytes(data)
    scan_status = _scan_file(str(path))
    if scan_status == "infected":
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Файл отклонён антивирусной проверкой")

    sha256 = hashlib.sha256(data).hexdigest()
    await db.execute(text("""
        INSERT INTO marketplace_files (listing_id, original_name, stored_path, content_type, size_bytes, sha256, scan_status)
        VALUES (:listing_id, :original_name, :stored_path, :content_type, :size_bytes, :sha256, :scan_status)
    """), {
        "listing_id": listing_id,
        "original_name": filename,
        "stored_path": str(path),
        "content_type": file.content_type or mimetypes.guess_type(filename)[0],
        "size_bytes": len(data),
        "sha256": sha256,
        "scan_status": scan_status,
    })
    await db.commit()
    return {"message": "Файл принят в защищённое хранилище", "scan_status": scan_status, "sha256": sha256}
