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
    if libro.stock == 0:
        raise HTTPException(status_code=400, detail="Libro no disponible")
    libro.stock -= 1

    # Multas
    if(usuario.multas or 0) > 10000:
        raise HTTPException(status_code=400, detail="Usuario con multas pendientes")

    # Reservas
    reserva_prioritaria = db.query(models.Reserva).filter(
        models.Reserva.libro_id == libro.id,
        models.Reserva.estado == "activa"
    ).order_by(models.Reserva.fecha_creacion.asc()).first()

    if reserva_prioritaria:
        if reserva_prioritaria.usuario_id != usuario.id:
            raise HTTPException(status_code=400, detail="El libro está reservado por otro usuario")
        else:
            reserva_prioritaria.estado = "completada"
            db.add(reserva_prioritaria)

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
    fecha_fin = datetime.now() + timedelta(days=dias)
    
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

@app.put("/prestamos/{prestamo_id}/extender", response_model=schemas.Prestamo)
def extender_prestamo(prestamo_id: int, db: Session = Depends(get_db)):
    prestamo = db.query(models.Prestamo).filter(models.Prestamo.id == prestamo_id).first()
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == prestamo.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Solo profesores
    if usuario.tipo.lower() != "profesor":
        raise HTTPException(status_code=403, detail="Acceso denegado, sólo profesores pueden extender préstamos")
    
    if getattr(prestamo, "extension_usada", False):
        raise HTTPException(status_code=400, detail="Este préstamo ya fue extendido una vez")
    
    prestamo.fecha_fin = prestamo.fecha_fin + timedelta(days=15)
    prestamo.extension_usada = True
    db.commit()
    db.refresh(prestamo)
    return prestamo

@app.put("/prestamos/{prestamo_id}/devolver")
def devolver_prestamo(prestamo_id: int, perdido: bool = False, db: Session = Depends(get_db)):
    prestamo = db.query(models.Prestamo).filter(models.Prestamo.id == prestamo_id).first()
    
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if prestamo.estado != "activo":
        raise HTTPException(status_code=400, detail="El préstamo ya fue cerrado")

    usuario = db.query(models.Usuario).filter(models.Usuario.id == prestamo.usuario_id).first()
    libro = db.query(models.Libro).filter(models.Libro.id == prestamo.libro_id).first()
    multa = 0
    hoy = datetime.now()
    if perdido:
        multa += 5000  
    elif hoy > prestamo.fecha_fin:
        dias_retraso = (hoy - prestamo.fecha_fin).days
        multa += dias_retraso * 2000

    if hoy > prestamo.fecha_fin + timedelta(days=30):
        multa *= 2

    usuario.multas = (usuario.multas or 0) + multa

    prestamo.estado = "devuelto"
    prestamo.fecha_fin = hoy

    if libro.tipo.lower() == "fisico" and not perdido:
        libro.stock += 1

    db.add_all([usuario, prestamo, libro])
    db.commit()
    return {"mensaje": "Préstamo devuelto", "multa_generada": multa}

# Endpoint Reserva

@app.post("/crear_reservas", response_model=schemas.Reserva)
def crear_reserva(reserva: schemas.ReservaCreate, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == reserva.usuario_id).first()
    libro = db.query(models.Libro).filter(models.Libro.id == reserva.libro_id).first()
    
    if not usuario: 
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not libro: 
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    reserva_existente = db.query(models.Reserva).filter(
        models.Reserva.usuario_id == usuario.id,
        models.Reserva.libro_id == libro.id,
        models.Reserva.estado == "activa"    
    ).first()
    if reserva_existente:
        raise HTTPException(status_code=400, detail="Reserva ya existe para este libro y usuario")
    
    nueva_reserva = models.Reserva(usuario_id=usuario.id, libro_id=libro.id)
    db.add(nueva_reserva)
    db.commit()
    db.refresh(nueva_reserva)
    
    return nueva_reserva

@app.get("/reservas", response_model=List[schemas.Reserva])
def obtener_reservas(db: Session = Depends(get_db)):
    reservas = db.query(models.Reserva).all()
    return reservas

# Compras
@app.post("/crear_compra", response_model=schemas.Compra)
def crear_compra(compra: schemas.CompraCreate, db: Session = Depends(get_db)):
    usuario =  db.query(models.Usuario).filter(models.Usuario.id == compra.usuario_id).first()
    libro = db.query(models.Libro).filter(models.Libro.id == compra.libro_id).first()
    
    if not usuario: 
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not libro: 
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    # Validación de multas
    if (usuario.multas or 0) > 20000:
        raise HTTPException(status_code=400, detail="El usuario tiene multas pendientes")
    
    # Validar si el usuario ya tiene el libro prestado y activo
    prestamo_activo = db.query(models.Prestamo).filter(
        models.Prestamo.usuario_id == usuario.id,
        models.Prestamo.libro_id == libro.id,
        models.Prestamo.estado == "activo"    
    ).first()
    
    if prestamo_activo:
        raise HTTPException(status_code=400, detail="El usuario tiene prestamos pendientes")
    
    # Calcular precio final con descuentos
    precio_final = compra.precio_final
    
    if usuario.tipo.lower() == "profesor" and libro.categoria and libro.categoria.lower() == "academico":
        precio_final = precio_final * 0.8  # Aplicar descuento del 20%
    elif usuario.tipo.lower() == "estudiante" and libro.tipo and libro.tipo.lower() == "digital":
        precio_final = precio_final * 0.85
        
    # Validar volumen
    if compra.cantidad > 5:
        precio_final *= 0.85
    elif compra.cantidad > 3:
        precio_final *= 0.90
        
    # Validar y decrementar el stock físico
    if libro.tipo.lower() == "fisico":
        if libro.stock <= compra.cantidad:
            raise HTTPException(status_code=400, detail="Stock no disponible")
        libro.stock -= compra.cantidad
        db.add(libro)

        stock_minimo = getattr(libro, "stock_minimo", 1)
        if libro.stock < stock_minimo:
            libro.stock += 5 
            print(f"Stock de '{libro.titulo}' repuesto automáticamente.")
        
    nueva_compra = models.Compra(
        usuario_id = usuario.id,
        libro_id = libro.id,
        precio_final = precio_final,
        fecha = datetime.now()
    )
    db.add(nueva_compra)
    db.commit()
    db.refresh(nueva_compra)
    return nueva_compra

@app.get("/compras", response_model=List[schemas.Compra])
def obtener_comprar(db: Session = Depends(get_db)): 
    return db.query(models.Compra).all()