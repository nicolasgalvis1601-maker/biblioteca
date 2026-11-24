"""Detalle del libro y public_id de la portada en Cloudinary.

Revision ID: 0007_detalle_libros
Revises: 6339f7f0d6fc
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_detalle_libros"
down_revision = "6339f7f0d6fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("libros", sa.Column("sinopsis", sa.Text(), nullable=True))
    op.add_column(
        "libros", sa.Column("editorial", sa.String(length=100), nullable=True)
    )
    op.add_column("libros", sa.Column("num_paginas", sa.Integer(), nullable=True))
    op.add_column(
        "libros", sa.Column("idioma", sa.String(length=30), nullable=True)
    )
    op.add_column(
        "libros",
        sa.Column("imagen_public_id", sa.String(length=255), nullable=True),
    )
    # La URL de Cloudinary puede superar 255 caracteres con transformaciones.
    with op.batch_alter_table("libros") as batch_op:
        batch_op.alter_column(
            "imagen_url",
            existing_type=sa.String(length=255),
            type_=sa.String(length=500),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("libros") as batch_op:
        batch_op.alter_column(
            "imagen_url",
            existing_type=sa.String(length=500),
            type_=sa.String(length=255),
            existing_nullable=True,
        )
        batch_op.drop_column("imagen_public_id")
        batch_op.drop_column("idioma")
        batch_op.drop_column("num_paginas")
        batch_op.drop_column("editorial")
        batch_op.drop_column("sinopsis")
