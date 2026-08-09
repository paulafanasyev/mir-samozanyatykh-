"""
WebRTC API v7.0
Видеозвонки между пользователями и клиентами
"""

import json
import uuid
from typing import Dict, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Call

router = APIRouter(prefix="/api/webrtc", tags=["webrtc"])

# Хранилище активных комнат: room_id -> {user_id: websocket}
rooms: Dict[str, Dict[int, WebSocket]] = {}


class WebRTCSignaling:
    """Signaling сервер для WebRTC"""

    async def join_room(self, room_id: str, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in rooms:
            rooms[room_id] = {}
        rooms[room_id][user_id] = websocket

        # Уведомить других участников
        for uid, ws in rooms[room_id].items():
            if uid != user_id:
                await ws.send_json({
                    "type": "user-joined",
                    "user_id": user_id,
                    "room_id": room_id,
                })

    def leave_room(self, room_id: str, user_id: int):
        if room_id in rooms and user_id in rooms[room_id]:
            del rooms[room_id][user_id]
            if not rooms[room_id]:
                del rooms[room_id]
            else:
                # Уведомить остальных
                import asyncio
                for uid, ws in rooms.get(room_id, {}).items():
                    asyncio.create_task(ws.send_json({
                        "type": "user-left",
                        "user_id": user_id,
                    }))

    async def broadcast(self, room_id: str, message: dict, exclude_user: int = None):
        if room_id in rooms:
            for uid, ws in rooms[room_id].items():
                if uid != exclude_user:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        pass


signaling = WebRTCSignaling()


@router.websocket("/call/{room_id}")
async def webrtc_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = "",
):
    """WebRTC signaling endpoint для видеозвонков"""
    user_id = 0
    if token:
        from app.core.security import decode_token
        try:
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await signaling.join_room(room_id, user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Ретрансляция signaling сообщений
            message["from_user_id"] = user_id
            await signaling.broadcast(room_id, message, exclude_user=user_id)

    except WebSocketDisconnect:
        signaling.leave_room(room_id, user_id)
    except Exception:
        signaling.leave_room(room_id, user_id)


@router.post("/room/create")
async def create_room(
    client_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """Создание комнаты для видеозвонка"""
    room_id = str(uuid.uuid4())[:8]
    return {
        "room_id": room_id,
        "url": f"/api/webrtc/call/{room_id}",
        "client_id": client_id,
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/room/{room_id}/status")
async def room_status(room_id: str):
    """Статус комнаты"""
    participants = list(rooms.get(room_id, {}).keys())
    return {
        "room_id": room_id,
        "participants_count": len(participants),
        "participants": participants,
        "is_active": len(participants) > 0,
    }
