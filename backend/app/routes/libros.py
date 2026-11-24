import json
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.controllers import libro as libro_controller
from app.controllers.libro import OrdenLibro
from app.core.cloudinary import eliminar_imagen_cloudinary, subir_imagen_cloudinary
from app.core.dependencies import get_db, paginacion, requiere_rol
from app.core.exceptions import ReglaNegocio
from app.models.usuario import RolUsuario
from app.routes.common import ERROR_RESPONSES
from app.schemas.libro import LibroCreate, LibroResponse, LibroUpdate
from app.schemas.pagina import Pagina

logger = logging.getLogger("biblioteca.api")

router = APIRouter(
    prefix="/libros",
    tags=["Libros"],
    responses=ERROR_RESPONSES,
)

STAFF = requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)


def _parsear_categorias(valor: Optional[str]) -> Optional[list[int]]:
    """Acepta '1', '1,2,3' o '[1,2,3]' (así llegan desde un formulario)."""
    if valor is None or not valor.strip():
        return None
    try:
        cargado = json.loads(valor)
        if isinstance(cargado, list):
            return [int(c) for c in cargado]
        return [int(cargado)]
    except (ValueError, TypeError):
        pass
    try:
        return [int(c) for c in valor.split(",") if c.strip()]
    except ValueError as exc:
        raise ReglaNegocio(
            "categoria_ids debe ser un número, una lista JSON o números separados por coma"
        ) from exc


def _validar(esquema, **datos):
    """Valida con Pydantic y devuelve 422 (no 500) si hay datos inválidos."""
    try:
        return esquema(**datos)
    except ValidationError as exc:
        raise RequestValidationError(
            exc.errors(include_url=False, include_context=False)
        ) from exc


def _hay_archivo(imagen: Optional[UploadFile]) -> bool:
    return bool(imagen and imagen.filename)


@router.get(
    "",
    response_model=Pagina[LibroResponse],
    summary="Buscar y listar libros",
)
def listar_libros(
    db: Annotated[Session, Depends(get_db)],
    pag: Annotated[dict, Depends(paginacion)],
    buscar: str | None = None,
    autor: str | None = None,
    categoria_id: int | None = None,
    desde: int | None = None,
    hasta: int | None = None,
    orden: OrdenLibro | None = None,
):
    return libro_controller.get_libros(
        db,
        pag["skip"],
        pag["limit"],
        buscar,
        autor,
        categoria_id,
        desde,
        hasta,
        orden,
    )


@router.get(
    "/autores/{autor_id}/libros",
    response_model=Pagina[LibroResponse],
    summary="Listar libros de un autor",
)
def listar_libros_por_autor(
    autor_id: int,
    db: Annotated[Session, Depends(get_db)],
    pag: Annotated[dict, Depends(paginacion)],
):
    return libro_controller.get_libros_by_autor(
        db, autor_id, pag["skip"], pag["limit"]
    )


@router.get(
    "/{libro_id}",
    response_model=LibroResponse,
    summary="Consultar un libro (detalle completo)",
)
def obtener_libro(
    libro_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    return libro_controller.get_libro_by_id(db, libro_id)


# Las rutas que reciben archivos son `def` (no `async def`): FastAPI las ejecuta
# en un hilo y la subida bloqueante a Cloudinary no frena el servidor.
@router.post(
    "",
    response_model=LibroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un libro con su detalle y portada (multipart/form-data)",
    dependencies=[STAFF],
)
def crear_libro(
    db: Annotated[Session, Depends(get_db)],
    titulo: str = Form(..., max_length=150),
    isbn: str = Form(...),
    anio_publicacion: int = Form(...),
    ejemplares: int = Form(...),
    autor_id: int = Form(...),
    categoria_ids: str = Form(..., description="Ej: 1  |  1,2  |  [1,2]"),
    sinopsis: Optional[str] = Form(None),
    editorial: Optional[str] = Form(None),
    num_paginas: Optional[int] = Form(None),
    idioma: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None, description="Portada JPG/PNG/WEBP, máx. 5 MB"),
):
    # 1) Validar datos antes de gastar una subida a Cloudinary
    libro_data = _validar(
        LibroCreate,
        titulo=titulo,
        isbn=isbn,
        anio_publicacion=anio_publicacion,
        ejemplares=ejemplares,
        autor_id=autor_id,
        categoria_ids=_parsear_categorias(categoria_ids) or [],
        sinopsis=sinopsis,
        editorial=editorial,
        num_paginas=num_paginas,
        idioma=idioma,
    )

    # 2) Subir la portada (si viene) y guardar URL + public_id en MySQL
    subida = subir_imagen_cloudinary(imagen) if _hay_archivo(imagen) else None
    try:
        return libro_controller.create_libro(
            db,
            libro_data,
            imagen_url=subida.url if subida else None,
            imagen_public_id=subida.public_id if subida else None,
        )
    except Exception:
        # Si MySQL rechaza el libro (ISBN repetido, autor inexistente...)
        # no dejamos una imagen huérfana en Cloudinary.
        if subida:
            eliminar_imagen_cloudinary(subida.public_id)
        raise


@router.patch(
    "/{libro_id}",
    response_model=LibroResponse,
    summary="Actualizar detalle y/o portada de un libro (multipart/form-data)",
    dependencies=[STAFF],
)
def actualizar_libro(
    libro_id: int,
    db: Annotated[Session, Depends(get_db)],
    titulo: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    anio_publicacion: Optional[int] = Form(None),
    ejemplares: Optional[int] = Form(None),
    autor_id: Optional[int] = Form(None),
    categoria_ids: Optional[str] = Form(None),
    sinopsis: Optional[str] = Form(None),
    editorial: Optional[str] = Form(None),
    num_paginas: Optional[int] = Form(None),
    idioma: Optional[str] = Form(None),
    imagen: Optional[UploadFile] = File(None),
):
    campos = {
        "titulo": titulo,
        "isbn": isbn,
        "anio_publicacion": anio_publicacion,
        "ejemplares": ejemplares,
        "autor_id": autor_id,
        "categoria_ids": _parsear_categorias(categoria_ids),
        "sinopsis": sinopsis,
        "editorial": editorial,
        "num_paginas": num_paginas,
        "idioma": idioma,
    }
    libro_update = _validar(
        LibroUpdate, **{k: v for k, v in campos.items() if v is not None}
    )

    anterior = libro_controller.get_imagen_public_id(db, libro_id)  # 404 si no existe
    subida = subir_imagen_cloudinary(imagen) if _hay_archivo(imagen) else None
    try:
        libro = libro_controller.update_libro(
            db,
            libro_id,
            libro_update,
            imagen_url=subida.url if subida else None,
            imagen_public_id=subida.public_id if subida else None,
        )
    except Exception:
        if subida:
            eliminar_imagen_cloudinary(subida.public_id)
        raise

    if subida:  # ya se guardó la nueva: se borra la portada anterior
        eliminar_imagen_cloudinary(anterior)
    return libro


@router.put(
    "/{libro_id}/portada",
    response_model=LibroResponse,
    summary="Subir o reemplazar solo la portada de un libro",
    dependencies=[STAFF],
)
def subir_portada(
    libro_id: int,
    imagen: UploadFile = File(..., description="Portada JPG/PNG/WEBP, máx. 5 MB"),
    db: Session = Depends(get_db),
):
    anterior = libro_controller.get_imagen_public_id(db, libro_id)
    subida = subir_imagen_cloudinary(imagen)
    try:
        libro = libro_controller.update_libro(
            db,
            libro_id,
            LibroUpdate(),
            imagen_url=subida.url,
            imagen_public_id=subida.public_id,
        )
    except Exception:
        eliminar_imagen_cloudinary(subida.public_id)
        raise
    eliminar_imagen_cloudinary(anterior)
    return libro


@router.delete(
    "/{libro_id}/portada",
    response_model=LibroResponse,
    summary="Quitar la portada de un libro",
    dependencies=[STAFF],
)
def quitar_portada(
    libro_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    anterior = libro_controller.get_imagen_public_id(db, libro_id)
    libro = libro_controller.quitar_portada(db, libro_id)
    eliminar_imagen_cloudinary(anterior)
    return libro


@router.delete(
    "/{libro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un libro (y su portada en Cloudinary)",
    dependencies=[requiere_rol(RolUsuario.admin)],
)
def eliminar_libro(
    libro_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    public_id = libro_controller.delete_libro(db, libro_id)
    eliminar_imagen_cloudinary(public_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
