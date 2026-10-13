import asyncio
from datetime import datetime
from fastapi import HTTPException
from app.database import db_manager
from app.repository import repo
from app.websocket_manager import ws_manager

class VehicleService:

    @staticmethod
    def ejecutar_movimiento_individual(id_vehiculo: int, id_comando: int, origen: str):
        # 1. Validar vehículo activo
        vehiculo = repo.sp_obtener_vehiculo(id_vehiculo)
        if not vehiculo or not vehiculo.get('activo'):
            raise HTTPException(status_code=404, detail="Vehículo no encontrado o inactivo")

        # 2. Validar comando activo perteneciente al vehículo
        comandos = repo.sp_obtener_comandos_vehiculo(id_vehiculo)
        comando_obj = next((c for c in comandos if c['id_comando'] == id_comando and c['activo']), None)
        if not comando_obj:
            raise HTTPException(status_code=400, detail="El comando no existe o no pertenece a este vehículo")

        nombre_comando = comando_obj['comando']

        # 3. Transacción Atómica: SP sp_actualizar_estado + SP sp_registrar_historial
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            repo.sp_actualizar_estado_tx(cursor, id_vehiculo, nombre_comando)
            repo.sp_registrar_historial_tx(cursor, id_vehiculo, id_comando, origen)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error en BD RDS: {str(e)}")
        finally:
            cursor.close()
            conn.close()

        # 4. Notificar evento por WebSocket
        event = {
            "evento": "MOVIMIENTO_INDIVIDUAL",
            "id_vehiculo": id_vehiculo,
            "comando": nombre_comando,
            "origen": origen,
            "timestamp": datetime.utcnow().isoformat()
        }
        asyncio.create_task(ws_manager.broadcast(id_vehiculo, event))

        return {"status": "ok", "mensaje": "Movimiento individual ejecutado e historizado"}

    @staticmethod
    async def ejecutar_demo_async(id_vehiculo: int, id_demo: int):
        if ws_manager.is_demo_running(id_vehiculo):
            raise HTTPException(status_code=409, detail="Ya hay una DEMO en ejecución para este vehículo")

        movimientos = repo.sp_obtener_movimientos_demo(id_demo)
        if not movimientos:
            raise HTTPException(status_code=404, detail="La DEMO no contiene movimientos")

        ws_manager.set_demo_running(id_vehiculo, True)

        try:
            await ws_manager.broadcast(id_vehiculo, {
                "evento": "DEMO_INICIO",
                "id_vehiculo": id_vehiculo,
                "id_demo": id_demo,
                "total_movimientos": len(movimientos)
            })

            for mov in movimientos:
                if not ws_manager.is_demo_running(id_vehiculo):
                    await ws_manager.broadcast(id_vehiculo, {"evento": "DEMO_CANCELADA", "id_vehiculo": id_vehiculo})
                    break

                nombre_cmd = mov.get('comando', f"CMD_{mov.get('id_comando')}")

                # Emitir movimiento por WS
                await ws_manager.broadcast(id_vehiculo, {
                    "evento": "DEMO_MOVIMIENTO",
                    "orden": mov["orden"],
                    "comando": nombre_cmd,
                    "duracion_ms": mov["duracion_ms"],
                    "pausa_ms": mov["pausa_ms"]
                })

                # SP sp_actualizar_estado (SIN sp_registrar_historial)
                repo.sp_actualizar_estado(id_vehiculo, nombre_cmd)

                # Temporización no bloqueante
                tiempo_sec = (mov["duracion_ms"] + mov["pausa_ms"]) / 1000.0
                await asyncio.sleep(tiempo_sec)

            await ws_manager.broadcast(id_vehiculo, {"evento": "DEMO_FIN", "id_vehiculo": id_vehiculo})

        finally:
            ws_manager.set_demo_running(id_vehiculo, False)