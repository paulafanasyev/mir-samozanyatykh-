"""
WebSocket API v6.7 — real-time уведомления
"""

import json
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api/ws", tags=["websocket"])


class ConnectionManager:
    """Менеджер WebSocket соединений"""

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, channel: str = "general"):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int, channel: str = "general"):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if channel in self.channels:
            self.channels[channel].discard(websocket)
            if not self.channels[channel]:
                del self.channels[channel]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            dead = set()
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.active_connections[user_id].discard(ws)

    async def broadcast(self, message: dict, channel: str = "general"):
        if channel in self.channels:
            dead = set()
            for ws in self.channels[channel]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self.channels[channel].discard(ws)


manager = ConnectionManager()


@router.websocket("/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str = "general", token: str = ""):
    """WebSocket endpoint для real-time уведомлений"""
    user_id = 0
    if token:
        from app.core.security import decode_token
        try:
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await manager.connect(websocket, user_id, channel)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("broadcast"):
                await manager.broadcast({
                    "type": "message", "channel": channel,
                    "user_id": user_id, "data": message,
                }, channel)
            else:
                await manager.send_personal_message({
                    "type": "message", "channel": channel,
                    "user_id": user_id, "data": message,
                }, user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, channel)
    except Exception:
        manager.disconnect(websocket, user_id, channel)


# ============ NOTIFICATION HELPERS ============

async def notify_user(user_id: int, title: str, body: str, data: dict = None):
    await manager.send_personal_message({
        "type": "notification", "title": title,
        "body": body, "data": data or {},
    }, user_id)


async def notify_deal_update(user_id: int, deal_id: int, status: str):
    await notify_user(
        user_id=user_id, title="Сделка обновлена",
        body=f"Статус сделки #{deal_id} изменён на {status}",
        data={"deal_id": deal_id, "status": status},
    )
