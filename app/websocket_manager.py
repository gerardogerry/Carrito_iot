from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    """Gestiona conexiones en tiempo real por cada vehículo."""
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.running_demos: Dict[int, bool] = {}

    async def connect(self, websocket: WebSocket, id_vehiculo: int):
        await websocket.accept()
        if id_vehiculo not in self.active_connections:
            self.active_connections[id_vehiculo] = []
        self.active_connections[id_vehiculo].append(websocket)

    def disconnect(self, websocket: WebSocket, id_vehiculo: int):
        if id_vehiculo in self.active_connections:
            if websocket in self.active_connections[id_vehiculo]:
                self.active_connections[id_vehiculo].remove(websocket)
            if not self.active_connections[id_vehiculo]:
                del self.active_connections[id_vehiculo]

    async def broadcast(self, id_vehiculo: int, message: dict):
        if id_vehiculo in self.active_connections:
            for connection in self.active_connections[id_vehiculo]:
                await connection.send_json(message)

    def is_demo_running(self, id_vehiculo: int) -> bool:
        return self.running_demos.get(id_vehiculo, False)

    def set_demo_running(self, id_vehiculo: int, running: bool):
        self.running_demos[id_vehiculo] = running

ws_manager = ConnectionManager()