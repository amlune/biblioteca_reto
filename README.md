# 📚 Sistema de Biblioteca

API REST en **FastAPI** para gestionar usuarios, libros, préstamos, reservas y compras, con validaciones y reglas de negocio.

---

## 🚀 Instalación
```bash
git clone https://github.com/amlune/biblioteca_reto.git
cd biblioteca_reto
python -m venv venv
source .\venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn main:app --reload
```

[Swagger Docs](http://127.0.0.1:8000/docs)

## EndPoints

- Usuarios → POST /crear_usuario · GET /usuarios
- Libros → POST /crear_libro · GET /libros
- Préstamos → POST /crear_prestamo · PUT /prestamos/{id}/extender · PUT /prestamos/{id}/devolver
- Reservas → POST /crear_reservas · GET /reservas
- Compras → POST /crear_compra · GET /compras

## Ejemplos para Swagger

- Crear Usuario
```
{
  "nombre": "Juan Pérez",
  "tipo": "estudiante",
  "multas": 0
}
```

- Crear Libro
```
{
  "titulo": "Introducción a Python",
  "categoria": "academico",
  "tipo": "fisico",
  "stock": 5,
  "stock_minimo": 2
}
```

- Crear Préstamo
```
{
  "usuario_id": 1,
  "libro_id": 1
}
```

- Crear Compra
```
{
  "usuario_id": 1,
  "libro_id": 1,
  "cantidad": 4,
  "precio_final": 30000
}
```
