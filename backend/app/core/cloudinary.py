import logging
from dataclasses import dataclass

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile

from app.core.config import get_settings

logger = logging.getLogger("biblioteca.cloudinary")

settings = get_settings()

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

CARPETA_PORTADAS = "biblioteca/portadas"
TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB


@dataclass(frozen=True)
class ImagenSubida:
    url: str
    public_id: str


def subir_imagen_cloudinary(file: UploadFile) -> ImagenSubida:
    """Valida y sube una portada a Cloudinary.

    Devuelve la URL segura y el public_id (necesario para borrarla después).
    """
    if file.content_type not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail="La portada debe ser una imagen JPG, PNG o WEBP",
        )

    contenido = file.file.read(TAMANO_MAXIMO_BYTES + 1)
    if not contenido:
        raise HTTPException(status_code=422, detail="El archivo está vacío")
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=413, detail="La portada no puede pesar más de 5 MB"
        )

    try:
        resultado = cloudinary.uploader.upload(
            contenido,
            folder=CARPETA_PORTADAS,
            resource_type="image",
        )
    except Exception as exc:  # error de red, credenciales, imagen corrupta...
        logger.exception("Fallo al subir la portada a Cloudinary")
        raise HTTPException(
            status_code=502,
            detail="No se pudo subir la portada a Cloudinary",
        ) from exc

    return ImagenSubida(
        url=resultado["secure_url"], public_id=resultado["public_id"]
    )


def eliminar_imagen_cloudinary(public_id: str | None) -> None:
    """Borra una portada de Cloudinary. Nunca lanza: solo registra el error."""
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id, resource_type="image")
    except Exception:
        logger.exception("No se pudo borrar %s de Cloudinary", public_id)
