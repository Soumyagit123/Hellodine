"""WebSocket connection manager for realtime kitchen updates."""
from fastapi import WebSocket
from typing import Dict
import json
import uuid


class KitchenConnectionManager:
    def __init__(self):
        # branch_id -> list of WebSocket connections
        self.active: Dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, branch_id: str):
        await websocket.accept()
        if branch_id not in self.active:
            self.active[branch_id] = []
        self.active[branch_id].append(websocket)

    def disconnect(self, websocket: WebSocket, branch_id: str):
        if branch_id in self.active:
            self.active[branch_id].remove(websocket)

    async def broadcast_to_branch(self, branch_id: str, message: dict):
        if branch_id in self.active:
            dead = []
            for ws in self.active[branch_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active[branch_id].remove(ws)


manager = KitchenConnectionManager()
