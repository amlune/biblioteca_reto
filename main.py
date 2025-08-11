from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import Base, engine, get_db
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema Biblioteca", description="Prueba técnica de Sistema de Biblioteca")

limite_prestamos = {
    "estudiante": 3,
    "profesor": 5,
    "visitante": 1
}

dias_prestamos = {
    "estudiante": 14,
    "profesor": 30,
    "visitante": 7
}

@app.get("/")
def root():
    return {"mensaje": "Funcionando."}

# Endpoints Usuarios
@app.post("/crear_usuario", response_model=schemas.Usuario)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    new_user = models.Usuario(**usuario.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/usuarios", response_model=List[schemas.Usuario])
def obtener_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).all()
    return usuarios


# Endpoints Libros
@app.post("/crear_libro", response_model=schemas.Libro)
def crear_libro(libro: schemas.LibroCreate, db: Session = Depends(get_db)):
    new_book = models.Libro(**libro.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@app.get("/libros", response_model=List[schemas.Libro])
def obtener_libros(db: Session = Depends(get_db)):
    libros = db.query(models.Libro).all()
    return libros

# Endpoints Prestamo
@app.post("/crear_prestamo", response_model=schemas.Prestamo)
def crear_prestamo(prestamo: schemas.PrestamoCreate, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == prestamo.usuario_id).first()
    libro = db.query(models.Libro).filter(models.Libro.id == prestamo.libro_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    if libro.disponible == 0:
        raise HTTPException(status_code=400, detail="Libro no disponible")
    libro.disponible -= 1

    # Multas
    if(usuario.multas or 0) > 10000:
        raise HTTPException(status_code=400, detail="Usuario con multas pendientes")

    # Reservas
    reserva = db.query(models.Reserva).filter(
        models.Reserva.libro_id == libro.id,
        models.Reserva.estado == "activo"
    ).order_by(models.Reserva.fecha_creacion.asc()).first() if hasattr(models, 'Reserva') else None
    
    if reserva and reserva.usuario_id != usuario.id:
        raise HTTPException(status_code=400, detail="Libro reservado por otro usuario")

    # Stock Físico
    if libro.tipo.lower() == "fisico" and libro.stock <= 0:
        raise HTTPException(status_code=400, detail="Stock no disponible")  
    
    # Limite de préstamos por tipo
    prestamos_activos = db.query(models.Prestamo).filter(
        models.Prestamo.usuario_id == usuario.id,
        models.Prestamo.estado == "activo"
    ).count()
    
    limite = limite_prestamos.get(usuario.tipo.lower(), 0)
    if prestamos_activos >= limite:
        raise HTTPException(status_code=400, detail="Límite de préstamos alcanzado")
    
    # No prestar el mismo libro dos veces al mismo usuario
    ultimo_prestamo = db.query(models.Prestamo).filter(
        models.Prestamo.usuario_id == usuario.id,
        models.Prestamo.libro_id == libro.id,
    ).order_by(models.Prestamo.fecha_inicio.desc()).first()
    
    if ultimo_prestamo and ultimo_prestamo.estado == "devuelto":
        raise HTTPException(status_code=400, detail="El libro ya ha sido prestado a este usuario")
    
    # Calcular fecha fin segun tipo
    dias = dias_prestamos.get(usuario.tipo.lower(), 0)
    fecha_fin = datetime.astimezone() + timedelta(days=dias)
    
    nuevo_prestamo = models.Prestamo(
        usuario_id = usuario.id,
        libro_id = libro.id,
        fecha_fin = fecha_fin
    )
    
    db.add(nuevo_prestamo)
    
    if libro.tipo.lower() == "fisico":
        libro.stock -= 1
        db.add(libro)
    
    db.commit()
    db.refresh(nuevo_prestamo)
    return nuevo_prestamo