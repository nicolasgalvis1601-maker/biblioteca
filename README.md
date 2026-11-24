# Biblioteca

Sistema de biblioteca con API (FastAPI + MySQL + Cloudinary) y una página web.

```
Biblioteca/
├── backend/                API
│   ├── app/
│   │   ├── core/           configuración, base de datos, seguridad, Cloudinary
│   │   ├── models/         tablas (SQLAlchemy)
│   │   ├── schemas/        validación de datos (Pydantic)
│   │   ├── controllers/    lógica de negocio
│   │   ├── routes/         endpoints (/api/v1/...)
│   │   └── scripts/        crear_admin.py
│   ├── alembic/            migraciones de la base de datos
│   ├── tests/              pruebas automáticas
│   ├── .env.example        plantilla de configuración (copiar a .env)
│   └── Dockerfile
├── frontend/               página web (HTML, CSS y JavaScript, sin instalar nada)
│   ├── index.html
│   ├── css/styles.css
│   └── js/                 config, api, auth, catalog, detail, admin, main
├── docs/MER.txt            modelo entidad-relación
└── docker-compose.yml      MySQL + API con Docker (opcional)
```

## Puesta en marcha (Windows, PowerShell)

### 1. Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env        # solo la primera vez; luego edita .env con tus datos
alembic upgrade head               # crea las tablas en MySQL
python -m app.scripts.crear_admin  # crea el primer administrador
fastapi dev app/main.py            # API en http://localhost:8000/docs
```
En `.env` define `DATABASE_URL`, `SECRET_KEY` (mínimo 32 caracteres) y las tres variables `CLOUDINARY_*`.

### 2. Frontend (otra terminal)
```powershell
cd frontend
python -m http.server 5173         # abre http://localhost:5173
```
Usa `localhost` (no `127.0.0.1` si no lo agregaste a `CORS_ORIGINS`). La dirección de la API está en `frontend/js/config.js`.

## Autenticación
| Rol | Puede |
| --- | --- |
| Visitante | Ver el catálogo y el detalle de los libros |
| Socio | Lo anterior, con cuenta propia (se crea desde la página con «Crear cuenta») |
| Bibliotecario | Agregar y editar libros, portadas, autores y categorías |
| Administrador | Todo lo anterior, eliminar libros y gestionar usuarios |

- El token de acceso dura 15 minutos. La página lo renueva sola con el refresh token (7 días) y cierra la sesión si ya no es válido.
- Al cerrar sesión se revoca el refresh token en el servidor.
- Inicio de sesión limitado a 10 intentos por minuto y registro a 5, y las cuentas se bloquean tras intentos fallidos.
- Las claves van solo en `backend/.env`, que está en `.gitignore`. Nunca lo subas ni lo compartas.

## Despliegue
Pasos completos en la guía de despliegue que te di en el chat. Resumen:
1. Sube el proyecto a GitHub (el `.env` NO se sube).
2. Crea una base MySQL en la nube y copia su cadena de conexión a `DATABASE_URL`.
3. API: servicio web con Docker, carpeta `backend`, con las variables del `.env`, `ENVIRONMENT=prod` y `CORS_ORIGINS` con la dirección de la página.
4. Página: sitio estático con carpeta `frontend`. Pon la dirección de la API en `frontend/js/config.js`.
5. Crea el primer administrador una sola vez desde tu PC, apuntando `DATABASE_URL` a la base en la nube.

## Pruebas
```powershell
cd backend
python -m pytest -q
```

## Docker (opcional)
```powershell
docker compose --env-file backend/.env up --build
```
Más detalles del backend en `backend/README.md`.
