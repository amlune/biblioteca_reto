from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Usuario
class UsuarioBase(BaseModel):
    nombre: str
    tipo: str
    multas: Optional[float] = 0

class UsuarioCreate(UsuarioBase):
    pass

class Usuario(UsuarioBase):
    id: int
    class Config:
        orm_mode = True


# Libro
class LibroBase(BaseModel):
    titulo: str
    categoria: Optional[str] = None
    estado: str
    tipo: str
    stock: int

class LibroCreate(LibroBase):
    pass

class Libro(LibroBase):
    id: int
    class Config:
        orm_mode = True

# Prestamo
class PrestamoBase(BaseModel):
    usuario_id: int
    libro_id: int

class PrestamoCreate(PrestamoBase):
    pass

class Prestamo(PrestamoBase):
    id: int
    fecha_inicio: datetime
    fecha_fin: datetime | None
    estado: str
    class Config:
        orm_mode = True
        
# Compra
class CompraBase(BaseModel):
    usuario_id: int
    libro_id: int
    precio_final: float

class CompraCreate(CompraBase):
    pass

class Compra(CompraBase):
    id: int
    fecha: datetime
    class Config:
        orm_mode = True
        
# Reserva
class ReservaBase(BaseModel):
    usuario_id: int
    libro_id: int

class ReservaCreate(ReservaBase):
    pass

class Reserva(ReservaBase):
    id: int
    fecha_creacion: datetime
    estado: str
    class Config:
        orm_mode = True