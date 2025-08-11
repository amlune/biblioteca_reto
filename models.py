from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # estudiante, profesor, visitante
    multas = Column(Float, default=0.0)

class Libro(Base):
    __tablename__ = "libros"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    categoria = Column(String, nullable=True)
    estado = Column(String, default="disponible")  # disponible, prestado, reservado y mantenimiento
    tipo = Column(String, nullable=False)  # fisico, digital
    stock = Column(Integer, default=0)
    precio_fisico = Column(Float, nullable=True)
    precio_digital = Column(Float, nullable=True)
    stock_minimo = Column(Integer, default=1)


class Prestamo(Base):
    __tablename__ = "prestamos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.now)
    fecha_fin = Column(DateTime, nullable=True)
    estado = Column(String, default="activo")
    extension_usada = Column(Integer, default=0)  # 0 = no usada, 1 = usada
    
class Compra(Base):
    __tablename__ = "compras"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    fecha = Column(DateTime, default=datetime.now)
    precio_final = Column(Float, nullable=False)

class Reserva(Base):
    __tablename__ = "reservas"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now
                            )
    estado = Column(String, default="activo")