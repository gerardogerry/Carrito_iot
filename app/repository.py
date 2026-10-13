from app.database import db_manager

class IoTRepository:
    """Capa de persistencia que ejecuta los 21 Stored Procedures en MySQL / Amazon RDS."""

    # Helper interno para ejecutar SPs de lectura (SELECT)
    def _execute_read_sp(self, sp_name: str, args: list = None):
        conn = db_manager.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.callproc(sp_name, args or [])
            results = []
            for r in cursor.stored_results():
                results.extend(r.fetchall())
            return results
        finally:
            cursor.close()
            conn.close()

    # Helper interno para ejecutar SPs de escritura (INSERT, UPDATE, DELETE)
    def _execute_write_sp(self, sp_name: str, args: list):
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.callproc(sp_name, args)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    # ==================== 1. VEHÍCULOS (5 SP) ====================
    def sp_crear_vehiculo(self, nombre: str, descripcion: str, activo: bool):
        self._execute_write_sp('sp_crear_vehiculo', [nombre, descripcion, activo])

    def sp_obtener_vehiculos(self):
        return self._execute_read_sp('sp_obtener_vehiculos')

    def sp_obtener_vehiculo(self, id_vehiculo: int):
        res = self._execute_read_sp('sp_obtener_vehiculo', [id_vehiculo])
        return res[0] if res else None

    def sp_actualizar_vehiculo(self, id_vehiculo: int, nombre: str, descripcion: str, activo: bool):
        self._execute_write_sp('sp_actualizar_vehiculo', [id_vehiculo, nombre, descripcion, activo])

    def sp_eliminar_vehiculo(self, id_vehiculo: int):
        self._execute_write_sp('sp_eliminar_vehiculo', [id_vehiculo])

    # ==================== 2. COMANDOS (4 SP) ====================
    def sp_crear_comando(self, id_vehiculo: int, comando: str, descripcion: str, activo: bool):
        self._execute_write_sp('sp_crear_comando', [id_vehiculo, comando, descripcion, activo])

    def sp_obtener_comandos_vehiculo(self, id_vehiculo: int):
        return self._execute_read_sp('sp_obtener_comandos_vehiculo', [id_vehiculo])

    def sp_actualizar_comando(self, id_comando: int, comando: str, descripcion: str, activo: bool):
        self._execute_write_sp('sp_actualizar_comando', [id_comando, comando, descripcion, activo])

    def sp_eliminar_comando(self, id_comando: int):
        self._execute_write_sp('sp_eliminar_comando', [id_comando])

    # ==================== 3. ESTADO (2 SP) ====================
    def sp_obtener_estado(self, id_vehiculo: int):
        res = self._execute_read_sp('sp_obtener_estado', [id_vehiculo])
        return res[0] if res else None

    def sp_actualizar_estado(self, id_vehiculo: int, ultimo_comando: str):
        self._execute_write_sp('sp_actualizar_estado', [id_vehiculo, ultimo_comando])

    def sp_actualizar_estado_tx(self, cursor, id_vehiculo: int, ultimo_comando: str):
        """Versión para ejecutar dentro de una transacción activa."""
        cursor.callproc('sp_actualizar_estado', [id_vehiculo, ultimo_comando])

    # ==================== 4. HISTORIAL (2 SP) ====================
    def sp_registrar_historial(self, id_vehiculo: int, id_comando: int, origen: str):
        self._execute_write_sp('sp_registrar_historial', [id_vehiculo, id_comando, origen])

    def sp_registrar_historial_tx(self, cursor, id_vehiculo: int, id_comando: int, origen: str):
        """Versión para ejecutar dentro de una transacción activa."""
        cursor.callproc('sp_registrar_historial', [id_vehiculo, id_comando, origen])

    def sp_obtener_historial(self, id_vehiculo: int, limite: int = 10):
        res = self._execute_read_sp('sp_obtener_historial', [id_vehiculo])
        return res[:limite]

    # ==================== 5. DEMO (4 SP) ====================
    def sp_crear_demo(self, id_vehiculo: int, nombre: str, descripcion: str):
        self._execute_write_sp('sp_crear_demo', [id_vehiculo, nombre, descripcion])

    def sp_obtener_demos(self, id_vehiculo: int):
        return self._execute_read_sp('sp_obtener_demos', [id_vehiculo])

    def sp_actualizar_demo(self, id_demo: int, nombre: str, descripcion: str):
        self._execute_write_sp('sp_actualizar_demo', [id_demo, nombre, descripcion])

    def sp_eliminar_demo(self, id_demo: int):
        self._execute_write_sp('sp_eliminar_demo', [id_demo])

    # ==================== 6. MOVIMIENTOS DEMO (4 SP) ====================
    def sp_agregar_movimiento_demo(self, id_demo: int, id_comando: int, orden: int, duracion_ms: int, pausa_ms: int):
        self._execute_write_sp('sp_agregar_movimiento_demo', [id_demo, id_comando, orden, duracion_ms, pausa_ms])

    def sp_obtener_movimientos_demo(self, id_demo: int):
        return self._execute_read_sp('sp_obtener_movimientos_demo', [id_demo])

    def sp_actualizar_movimiento_demo(self, id_movimiento: int, orden: int, duracion_ms: int, pausa_ms: int):
        self._execute_write_sp('sp_actualizar_movimiento_demo', [id_movimiento, orden, duracion_ms, pausa_ms])

    def sp_eliminar_movimiento_demo(self, id_movimiento: int):
        self._execute_write_sp('sp_eliminar_movimiento_demo', [id_movimiento])

repo = IoTRepository()