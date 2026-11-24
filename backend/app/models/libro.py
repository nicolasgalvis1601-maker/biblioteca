from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.categoria import libro_categoria


class Libro(Base):
    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    anio_publicacion: Mapped[int] = mapped_column(Integer, nullable=False)
    ejemplares: Mapped[int | None] = mapped_column(
        Integer, default=1, nullable=True
    )

    # Detalle del libro
    sinopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    editorial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    num_paginas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    idioma: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Portada alojada en Cloudinary
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    imagen_public_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    autor_id: Mapped[int] = mapped_column(
        ForeignKey("autores.id"), nullable=False
    )

    autor: Mapped["Autor"] = relationship("Autor", back_populates="libros")
    categorias: Mapped[list["Categoria"]] = relationship(
        "Categoria",
        secondary=libro_categoria,
        back_populates="libros",
    )
    prestamos: Mapped[list["Prestamo"]] = relationship(
        "Prestamo", back_populates="libro"
    )
