from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from app.models import (
    VehiculoCreate, VehiculoUpdate, ComandoCreate, ComandoUpdate,
    MovimientoRequest, DemoCreate, MovimientoDemoCreate
)
from app.repository import repo
from app.websocket_manager import ws_manager
from app.service import VehicleService

# Inicialización Estándar de FastAPI (Swagger UI nativo en /docs)
app = FastAPI(
    title="API Vehículo IoT - Práctica 2.5",
    description="API RESTful y WebSocket integrada con los 21 Stored Procedures del esquema vehiculo_iot en Amazon RDS.",
    version="1.0.0"
)

# ==================== WEBSOCKET ====================
@app.websocket("/ws/vehiculo/{id_vehiculo}")
async def websocket_endpoint(websocket: WebSocket, id_vehiculo: int):
    await ws_manager.connect(websocket, id_vehiculo)
    estado = repo.sp_obtener_estado(id_vehiculo)
    await websocket.send_json({"evento": "ESTADO_INICIAL", "datos": estado})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, id_vehiculo)

# ==================== 1. VEHÍCULOS (5 SP) ====================
@app.post("/api/vehiculos", tags=["Vehículos"], status_code=201)
def sp_crear_vehiculo(datos: VehiculoCreate):
    """SP 1: sp_crear_vehiculo"""
    repo.sp_crear_vehiculo(datos.nombre, datos.descripcion, datos.activo)
    return {"status": "ok", "mensaje": "Vehículo creado"}

@app.get("/api/vehiculos", tags=["Vehículos"])
def sp_obtener_vehiculos():
    """SP 2: sp_obtener_vehiculos"""
    return repo.sp_obtener_vehiculos()

@app.get("/api/vehiculos/{id_vehiculo}", tags=["Vehículos"])
def sp_obtener_vehiculo(id_vehiculo: int):
    """SP 3: sp_obtener_vehiculo"""
    res = repo.sp_obtener_vehiculo(id_vehiculo)
    if not res:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return res

@app.post("/api/vehiculos/{id_vehiculo}/actualizar", tags=["Vehículos"])
def sp_actualizar_vehiculo(id_vehiculo: int, datos: VehiculoUpdate):
    """SP 4: sp_actualizar_vehiculo"""
    repo.sp_actualizar_vehiculo(id_vehiculo, datos.nombre, datos.descripcion, datos.activo)
    return {"status": "ok", "mensaje": "Vehículo actualizado"}

@app.post("/api/vehiculos/{id_vehiculo}/eliminar", tags=["Vehículos"])
def sp_eliminar_vehiculo(id_vehiculo: int):
    """SP 5: sp_eliminar_vehiculo"""
    repo.sp_eliminar_vehiculo(id_vehiculo)
    return {"status": "ok", "mensaje": "Vehículo eliminado"}

# ==================== 2. COMANDOS (4 SP) ====================
@app.post("/api/vehiculos/{id_vehiculo}/comandos", tags=["Comandos"], status_code=201)
def sp_crear_comando(id_vehiculo: int, datos: ComandoCreate):
    """SP 6: sp_crear_comando"""
    repo.sp_crear_comando(id_vehiculo, datos.comando, datos.descripcion, datos.activo)
    return {"status": "ok", "mensaje": "Comando creado"}

@app.get("/api/vehiculos/{id_vehiculo}/comandos", tags=["Comandos"])
def sp_obtener_comandos_vehiculo(id_vehiculo: int):
    """SP 7: sp_obtener_comandos_vehiculo"""
    return repo.sp_obtener_comandos_vehiculo(id_vehiculo)

@app.post("/api/comandos/{id_comando}/actualizar", tags=["Comandos"])
def sp_actualizar_comando(id_comando: int, datos: ComandoUpdate):
    """SP 8: sp_actualizar_comando"""
    repo.sp_actualizar_comando(id_comando, datos.comando, datos.descripcion, datos.activo)
    return {"status": "ok", "mensaje": "Comando actualizado"}

@app.post("/api/comandos/{id_comando}/eliminar", tags=["Comandos"])
def sp_eliminar_comando(id_comando: int):
    """SP 9: sp_eliminar_comando"""
    repo.sp_eliminar_comando(id_comando)
    return {"status": "ok", "mensaje": "Comando eliminado"}

# ==================== 3. ESTADO (2 SP) ====================
@app.post("/api/vehiculos/{id_vehiculo}/estado/actualizar", tags=["Estado"])
def sp_actualizar_estado(id_vehiculo: int, ultimo_comando: str):
    """SP 10: sp_actualizar_estado"""
    repo.sp_actualizar_estado(id_vehiculo, ultimo_comando)
    return {"status": "ok", "mensaje": "Estado actualizado"}

@app.get("/api/vehiculos/{id_vehiculo}/estado", tags=["Estado"])
def sp_obtener_estado(id_vehiculo: int):
    """SP 11: sp_obtener_estado"""
    return repo.sp_obtener_estado(id_vehiculo)

# ==================== 4. HISTORIAL (2 SP) ====================
@app.post("/api/vehiculos/{id_vehiculo}/historial/registrar", tags=["Historial"])
def sp_registrar_historial(id_vehiculo: int, id_comando: int, origen: str = "API_POST"):
    """SP 12: sp_registrar_historial"""
    repo.sp_registrar_historial(id_vehiculo, id_comando, origen)
    return {"status": "ok", "mensaje": "Historial registrado"}

@app.get("/api/vehiculos/{id_vehiculo}/historial", tags=["Historial"])
def sp_obtener_historial(id_vehiculo: int):
    """SP 13: sp_obtener_historial (Máximo 10 registros)"""
    return repo.sp_obtener_historial(id_vehiculo, limite=10)

# Coordinación de Movimiento Individual (SP 10 + SP 12 en Transacción)
@app.post("/api/vehiculos/{id_vehiculo}/movimiento", tags=["Movimiento Individual"])
def ejecutar_movimiento(id_vehiculo: int, datos: MovimientoRequest):
    """Transacción atómica: sp_actualizar_estado + sp_registrar_historial + Notificación WS"""
    return VehicleService.ejecutar_movimiento_individual(id_vehiculo, datos.id_comando, datos.origen)

# ==================== 5. DEMO (4 SP) ====================
@app.post("/api/vehiculos/{id_vehiculo}/demos", tags=["DEMO"], status_code=201)
def sp_crear_demo(id_vehiculo: int, datos: DemoCreate):
    """SP 14: sp_crear_demo"""
    repo.sp_crear_demo(id_vehiculo, datos.nombre, datos.descripcion)
    return {"status": "ok", "mensaje": "DEMO creada"}

@app.get("/api/vehiculos/{id_vehiculo}/demos", tags=["DEMO"])
def sp_obtener_demos(id_vehiculo: int):
    """SP 15: sp_obtener_demos"""
    return repo.sp_obtener_demos(id_vehiculo)

@app.post("/api/demos/{id_demo}/actualizar", tags=["DEMO"])
def sp_actualizar_demo(id_demo: int, datos: DemoCreate):
    """SP 16: sp_actualizar_demo"""
    repo.sp_actualizar_demo(id_demo, datos.nombre, datos.descripcion)
    return {"status": "ok", "mensaje": "DEMO actualizada"}

@app.post("/api/demos/{id_demo}/eliminar", tags=["DEMO"])
def sp_eliminar_demo(id_demo: int):
    """SP 17: sp_eliminar_demo"""
    repo.sp_eliminar_demo(id_demo)
    return {"status": "ok", "mensaje": "DEMO eliminada"}

# ==================== 6. MOVIMIENTOS DEMO (4 SP) ====================
@app.post("/api/demos/{id_demo}/movimientos", tags=["DEMO Movimientos"], status_code=201)
def sp_agregar_movimiento_demo(id_demo: int, datos: MovimientoDemoCreate):
    """SP 18: sp_agregar_movimiento_demo"""
    repo.sp_agregar_movimiento_demo(id_demo, datos.id_comando, datos.orden, datos.duracion_ms, datos.pausa_ms)
    return {"status": "ok", "mensaje": "Movimiento agregado a DEMO"}

@app.get("/api/demos/{id_demo}/movimientos", tags=["DEMO Movimientos"])
def sp_obtener_movimientos_demo(id_demo: int):
    """SP 19: sp_obtener_movimientos_demo"""
    return repo.sp_obtener_movimientos_demo(id_demo)

@app.post("/api/movimientos-demo/{id_movimiento}/actualizar", tags=["DEMO Movimientos"])
def sp_actualizar_movimiento_demo(id_movimiento: int, datos: MovimientoDemoCreate):
    """SP 20: sp_actualizar_movimiento_demo"""
    repo.sp_actualizar_movimiento_demo(id_movimiento, datos.orden, datos.duracion_ms, datos.pausa_ms)
    return {"status": "ok", "mensaje": "Movimiento de DEMO actualizado"}

@app.post("/api/movimientos-demo/{id_movimiento}/eliminar", tags=["DEMO Movimientos"])
def sp_eliminar_movimiento_demo(id_movimiento: int):
    """SP 21: sp_eliminar_movimiento_demo"""
    repo.sp_eliminar_movimiento_demo(id_movimiento)
    return {"status": "ok", "mensaje": "Movimiento de DEMO eliminado"}

# Ejecución de DEMO vía WebSocket (NO guarda en historial)
@app.post("/api/vehiculos/{id_vehiculo}/demo/{id_demo}/ejecutar", tags=["DEMO Ejecución"])
async def ejecutar_demo(id_vehiculo: int, id_demo: int, bg_tasks: BackgroundTasks):
    bg_tasks.add_task(VehicleService.ejecutar_demo_async, id_vehiculo, id_demo)
    return {"status": "ok", "mensaje": "DEMO iniciada en segundo plano"}

@app.post("/api/vehiculos/{id_vehiculo}/demo/cancelar", tags=["DEMO Ejecución"])
def cancelar_demo(id_vehiculo: int):
    ws_manager.set_demo_running(id_vehiculo, False)
    return {"status": "ok", "mensaje": "Cancelación solicitada"}