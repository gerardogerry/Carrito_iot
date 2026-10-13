from pydantic import BaseModel
from typing import Optional

# --- Vehículos ---
class VehiculoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

class VehiculoUpdate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

# --- Comandos ---
class ComandoCreate(BaseModel):
    comando: str
    descripcion: Optional[str] = None
    activo: bool = True

class ComandoUpdate(BaseModel):
    comando: str
    descripcion: Optional[str] = None
    activo: bool = True

# --- Movimiento Individual ---
class MovimientoRequest(BaseModel):
    id_comando: int
    origen: Optional[str] = "API_POST"

# --- DEMO ---
class DemoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class MovimientoDemoCreate(BaseModel):
    id_comando: int
    orden: int
    duracion_ms: int
    pausa_ms: int