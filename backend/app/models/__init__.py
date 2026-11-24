"""Importa todos los modelos para que SQLAlchemy resuelva las relaciones."""
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.libro import Libro
from app.models.prestamo import Prestamo
from app.models.refresh_token import RefreshToken
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario

__all__ = ["Autor", "Categoria", "Libro", "Prestamo", "RefreshToken", "Socio", "RolUsuario", "Usuario"]
