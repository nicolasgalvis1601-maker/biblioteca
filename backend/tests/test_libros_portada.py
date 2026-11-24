import json

import pytest

from app.core.cloudinary import ImagenSubida
from app.routes import libros as libros_route
from tests.test_security_api import admin_login, create_librarian

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


@pytest.fixture
def cloud(monkeypatch):
    """Cloudinary simulado: registra subidas y borrados."""
    estado = {"subidas": [], "borradas": []}

    def subir(file):
        from app.core.cloudinary import TIPOS_PERMITIDOS
        from fastapi import HTTPException

        if file.content_type not in TIPOS_PERMITIDOS:
            raise HTTPException(422, "La portada debe ser una imagen JPG, PNG o WEBP")
        n = len(estado["subidas"]) + 1
        estado["subidas"].append(n)
        return ImagenSubida(
            url=f"https://res.cloudinary.com/demo/portada{n}.png",
            public_id=f"biblioteca/portadas/portada{n}",
        )

    monkeypatch.setattr(libros_route, "subir_imagen_cloudinary", subir)
    monkeypatch.setattr(
        libros_route, "eliminar_imagen_cloudinary", estado["borradas"].append
    )
    return estado


@pytest.fixture
def staff(client, db):
    admin_token = admin_login(client, db)
    headers = {"Authorization": f"Bearer {admin_token}"}
    autor = client.post("/api/v1/autores", headers=headers, json={"nombre": "Gabo"}).json()
    cat = client.post("/api/v1/categorias", headers=headers, json={"nombre": "Novela"}).json()
    return headers, autor["id"], cat["id"]


def datos(autor_id, cat_id, isbn="9781234567890"):
    return {
        "titulo": "cien años de soledad",
        "isbn": isbn,
        "anio_publicacion": 1967,
        "ejemplares": 2,
        "autor_id": autor_id,
        "categoria_ids": json.dumps([cat_id]),
        "sinopsis": "La historia de los Buendía en Macondo.",
        "editorial": "Sudamericana",
        "num_paginas": 471,
        "idioma": "Español",
    }


def test_crear_libro_guarda_detalle_y_portada_en_bd(client, staff, cloud):
    headers, autor_id, cat_id = staff
    r = client.post(
        "/api/v1/libros",
        headers=headers,
        data=datos(autor_id, cat_id),
        files={"imagen": ("portada.png", PNG, "image/png")},
    )
    assert r.status_code == 201, r.text
    libro = r.json()
    assert libro["imagen_url"] == "https://res.cloudinary.com/demo/portada1.png"
    assert libro["editorial"] == "Sudamericana"
    assert libro["num_paginas"] == 471
    assert libro["sinopsis"].startswith("La historia")
    assert "imagen_public_id" not in libro

    # Persistió en la base de datos (lo ve cualquiera, sin token)
    otra = client.get(f"/api/v1/libros/{libro['id']}").json()
    assert otra["imagen_url"] == libro["imagen_url"]
    assert otra["idioma"] == "Español"


def test_crear_libro_sin_portada_es_valido(client, staff, cloud):
    headers, autor_id, cat_id = staff
    r = client.post("/api/v1/libros", headers=headers, data=datos(autor_id, cat_id))
    assert r.status_code == 201
    assert r.json()["imagen_url"] is None
    assert cloud["subidas"] == []


def test_datos_invalidos_devuelven_422_y_no_suben_imagen(client, staff, cloud):
    headers, autor_id, cat_id = staff
    malo = datos(autor_id, cat_id, isbn="123")
    r = client.post(
        "/api/v1/libros", headers=headers, data=malo,
        files={"imagen": ("p.png", PNG, "image/png")},
    )
    assert r.status_code == 422
    assert cloud["subidas"] == []


def test_categoria_ids_basura_devuelve_422(client, staff, cloud):
    headers, autor_id, cat_id = staff
    malo = datos(autor_id, cat_id) | {"categoria_ids": "abc"}
    assert client.post("/api/v1/libros", headers=headers, data=malo).status_code == 422


def test_archivo_que_no_es_imagen_se_rechaza(client, staff, cloud):
    headers, autor_id, cat_id = staff
    r = client.post(
        "/api/v1/libros", headers=headers, data=datos(autor_id, cat_id),
        files={"imagen": ("x.txt", b"hola", "text/plain")},
    )
    assert r.status_code == 422


def test_isbn_duplicado_borra_la_imagen_huerfana(client, staff, cloud):
    headers, autor_id, cat_id = staff
    files = lambda: {"imagen": ("p.png", PNG, "image/png")}
    assert client.post("/api/v1/libros", headers=headers, data=datos(autor_id, cat_id), files=files()).status_code == 201
    r = client.post("/api/v1/libros", headers=headers, data=datos(autor_id, cat_id), files=files())
    assert r.status_code == 409
    assert cloud["borradas"] == ["biblioteca/portadas/portada2"]


def test_reemplazar_portada_borra_la_anterior(client, staff, cloud):
    headers, autor_id, cat_id = staff
    libro = client.post(
        "/api/v1/libros", headers=headers, data=datos(autor_id, cat_id),
        files={"imagen": ("p.png", PNG, "image/png")},
    ).json()
    r = client.put(
        f"/api/v1/libros/{libro['id']}/portada", headers=headers,
        files={"imagen": ("nueva.png", PNG, "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["imagen_url"].endswith("portada2.png")
    assert cloud["borradas"] == ["biblioteca/portadas/portada1"]


def test_patch_actualiza_detalle_sin_tocar_portada(client, staff, cloud):
    headers, autor_id, cat_id = staff
    libro = client.post(
        "/api/v1/libros", headers=headers, data=datos(autor_id, cat_id),
        files={"imagen": ("p.png", PNG, "image/png")},
    ).json()
    r = client.patch(
        f"/api/v1/libros/{libro['id']}", headers=headers,
        data={"editorial": "Alfaguara", "num_paginas": 500},
    )
    assert r.status_code == 200
    assert r.json()["editorial"] == "Alfaguara"
    assert r.json()["imagen_url"] == libro["imagen_url"]
    assert cloud["borradas"] == []


def test_quitar_portada_y_eliminar_libro_limpian_cloudinary(client, staff, cloud):
    headers, autor_id, cat_id = staff
    libro = client.post(
        "/api/v1/libros", headers=headers, data=datos(autor_id, cat_id),
        files={"imagen": ("p.png", PNG, "image/png")},
    ).json()
    r = client.delete(f"/api/v1/libros/{libro['id']}/portada", headers=headers)
    assert r.status_code == 200 and r.json()["imagen_url"] is None
    assert cloud["borradas"] == ["biblioteca/portadas/portada1"]

    client.put(
        f"/api/v1/libros/{libro['id']}/portada", headers=headers,
        files={"imagen": ("p.png", PNG, "image/png")},
    )
    assert client.delete(f"/api/v1/libros/{libro['id']}", headers=headers).status_code == 204
    assert cloud["borradas"][-1] == "biblioteca/portadas/portada2"


def test_sin_token_no_puede_subir_portadas(client, staff, cloud):
    _, autor_id, cat_id = staff
    r = client.post("/api/v1/libros", data=datos(autor_id, cat_id))
    assert r.status_code == 401
