# API segura de biblioteca

API REST modular con FastAPI, SQLAlchemy 2, MySQL, Alembic, contraseñas Argon2 y JWT.

## Requisitos

- Python 3.12 o superior
- Docker y Docker Compose

## Instalación local (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Edite `.env`: defina las credenciales de MySQL (`MYSQL_USER`, `MYSQL_PASSWORD` y
`MYSQL_ROOT_PASSWORD`), actualice `DATABASE_URL` con esas credenciales y genere
`SECRET_KEY` sin guardarla en el repositorio:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Inicie MySQL y aplique las migraciones:

```powershell
docker compose up -d db
alembic upgrade head
```

La aplicación nunca crea tablas al arrancar. Para iniciar la API:

```powershell
fastapi dev app/main.py
```

La documentación está en `/docs` (solo fuera de producción), la comprobación de
salud en `/api/v1/health` y todas las rutas de negocio tienen el prefijo `/api/v1`.

## Administrador inicial

Después de aplicar las migraciones, cree el primer administrador de forma
interactiva. El script solicita la contraseña con `getpass`; no la imprime ni la
guarda en el código:

```powershell
python -m app.scripts.crear_admin
```

El endpoint público de registro solo puede crear usuarios con rol `socio`.
Administradores pueden crear bibliotecarios y otros administradores desde
`POST /api/v1/usuarios`.

## Migraciones

Las migraciones versionadas están en `alembic/versions`. Cada cambio de esquema
debe tener su migración, revisarse antes de aplicarse y contar con un `downgrade`.

```powershell
alembic history
alembic current
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
alembic downgrade -1
alembic downgrade base
```

Las migraciones incluidas crean el esquema inicial, añaden el estado de
pago de multas, usuarios, refresh tokens y auditoría de los préstamos. En un
entorno de desarrollo nuevo, ejecute `alembic upgrade head` antes de iniciar la API.

## Cloudinary y detalle de libros

Las portadas se guardan en Cloudinary (carpeta `biblioteca/portadas`) y en MySQL
solo se guardan la URL (`imagen_url`) y el `public_id` (`imagen_public_id`).

1. En `.env` defina `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` y
   `CLOUDINARY_API_SECRET` (Cloudinary → Settings → API Keys).
2. Aplique la migración nueva: `alembic upgrade head` (agrega `sinopsis`,
   `editorial`, `num_paginas`, `idioma` e `imagen_public_id`).

Endpoints (admin/bibliotecario; envían `multipart/form-data`):

| Método | Ruta | Qué hace |
| --- | --- | --- |
| POST | `/api/v1/libros` | Crea libro con detalle y portada opcional (`imagen`) |
| PATCH | `/api/v1/libros/{id}` | Edita detalle y/o reemplaza la portada |
| PUT | `/api/v1/libros/{id}/portada` | Sube o reemplaza solo la portada |
| DELETE | `/api/v1/libros/{id}/portada` | Quita la portada (y la borra de Cloudinary) |
| DELETE | `/api/v1/libros/{id}` | Elimina el libro (solo admin) y su portada |

La portada admite JPG, PNG o WEBP de hasta 5 MB. Los GET son públicos y
devuelven `imagen_url`, `sinopsis`, `editorial`, `num_paginas` e `idioma`.

### Probar con la página de demostración

```powershell
fastapi dev app/main.py                 # terminal 1 (puerto 8000)
cd ../frontend; python -m http.server 5173   # terminal 2
```

Abra http://localhost:5173 (ese puerto ya está en `CORS_ORIGINS`).

### Desde un frontend (React, etc.)

```js
const fd = new FormData();
fd.append("titulo", "Cien años de soledad");
fd.append("isbn", "9780307474728");
fd.append("anio_publicacion", 1967);
fd.append("ejemplares", 3);
fd.append("autor_id", 1);
fd.append("categoria_ids", "1,2");
fd.append("sinopsis", "...");
fd.append("imagen", archivo);            // <input type="file">
await fetch(`${API}/libros`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd });
// No fije Content-Type: el navegador agrega el boundary.
```

## Pruebas

```powershell
pytest --cov=app --cov-report=term-missing
```

Las pruebas usan `TEST_DATABASE_URL`; el valor de ejemplo apunta a SQLite y no
usa la base MySQL de desarrollo.

## Roles y permisos

| Rol | Permisos |
|---|---|
| Anónimo | Registro, login, salud y consulta del catálogo |
| Socio | Perfil, préstamos y multas propios; catálogo |
| Bibliotecario | Catálogo, socios, préstamos, devoluciones, multas y reportes |
| Admin | Permisos del bibliotecario, borrados y gestión de usuarios/roles |

Un socio nunca puede consultar préstamos de otro socio. Los refresh tokens se
almacenan por identificador, rotan al renovarse y se revocan al cerrar sesión,
cambiar contraseña, cambiar rol o desactivar una cuenta.

## Conceptos de seguridad

- **Autenticación y autorización:** la autenticación confirma quién inició
  sesión. La autorización decide qué acciones permite su rol o propiedad. Un
  `401` significa que falta una credencial válida; un `403`, que el usuario
  autenticado no tiene permiso.
- **Hash de contraseñas:** Argon2 es deliberadamente costoso para dificultar
  ataques de diccionario. Incluye una sal aleatoria en el hash almacenado.
  MD5, SHA-1 y SHA-256 son demasiado rápidos para proteger contraseñas.
- **JWT:** contiene encabezado, claims y firma, codificados en Base64URL. Está
  firmado, no cifrado: no se deben incluir secretos en sus claims. `exp` limita
  su vigencia.
- **Access y refresh tokens:** el access token dura minutos para reducir el
  impacto de una filtración. El refresh token dura más tiempo, se almacena por
  `jti` y se rota en cada renovación; reutilizar uno revocado invalida las
  sesiones de refresh del usuario.
- **OAuth2 Password Flow de FastAPI:** `OAuth2PasswordRequestForm` recibe
  usuario/correo y contraseña como formulario; `OAuth2PasswordBearer` extrae
  el token Bearer y publica el flujo de autorización en OpenAPI.
- **Alembic:** `upgrade` aplica cambios y `downgrade` los revierte. La
  autogeneración compara metadatos y esquema, pero no deduce cambios de datos ni
  siempre reconoce renombres o reglas de negocio; cada revisión requiere
  inspección manual.
- **Rate limiting:** restringir intentos por IP dificulta ataques automatizados
  de fuerza bruta contra login y registro.
- **CORS:** es una política del navegador para solicitudes desde otros orígenes.
  La API permite los orígenes configurados en `CORS_ORIGINS`; producción no
  admite el comodín `*`.

## Endpoints principales

| Ruta | Anónimo | Socio | Bibliotecario | Admin |
|---|---:|---:|---:|---:|
| `POST /api/v1/auth/registro`, `/login`, `/refresh` | Sí | Sí | Sí | Sí |
| `GET /api/v1/health`, catálogo `GET /libros`, `/autores`, `/categorias` | Sí | Sí | Sí | Sí |
| `POST` / `PATCH` catálogo | No | No | Sí | Sí |
| `DELETE` catálogo | No | No | No | Sí |
| `/api/v1/auth/me`, `/logout`, `/me/password` | No | Sí | Sí | Sí |
| `/api/v1/socios/me*` | No | Propio | No | No |
| `GET` / `POST /api/v1/socios`, `GET` / `PATCH /socios/{id}` | No | No | Sí | Sí |
| `DELETE /api/v1/socios/{id}` | No | No | No | Sí |
| `GET /api/v1/prestamos*` | No | Propio | Sí | Sí |
| Crear/devolver/pagar préstamos | No | No | Sí | Sí |
| `GET /api/v1/reportes/*` | No | No | Sí | Sí |
| `/api/v1/usuarios*` | No | No | No | Sí |

Las respuestas de colecciones incluyen `items`, `total`, `skip` y `limit`.
Los errores 401 envían `WWW-Authenticate: Bearer`. El middleware agrega
`X-Request-ID` y registra método, ruta, código HTTP y duración sin guardar
contraseñas ni tokens.

## Entrega

Antes de publicar, completar los nombres de los integrantes y el nombre del
aprendiz en el repositorio. Los commits por fase y por migración se realizan en
el repositorio Git de entrega del equipo.

**Integrantes:** completar con nombres y apellidos del equipo.
