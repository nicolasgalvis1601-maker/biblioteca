/* ---------- Detalle ---------- */
function openDetail(id){
  const l = S.books.get(+id); if(!l) return;
  const rows = [["ISBN",l.isbn],["Año",l.anio_publicacion],["Editorial",l.editorial],["Páginas",l.num_paginas],["Idioma",l.idioma],
    ["Categorías",(l.categorias||[]).map(c=>c.nombre).join(", ")],["Ejemplares",`${l.disponibles} de ${l.ejemplares} disponibles`]]
    .filter(r=>r[1]).map(r=>`<dt>${r[0]}</dt><dd>${esc(r[1])}</dd>`).join("");
  $("detailBody").innerHTML = `
    <button class="btn line x" data-close aria-label="Cerrar detalle">Cerrar</button>
    <div class="d-cover"><div class="cv">${cover(l)}</div></div>
    <h2 class="d-title">${esc(l.titulo)}</h2>
    <div class="d-au">${esc(l.autor?.nombre)}${l.autor?.nacionalidad?`, ${esc(l.autor.nacionalidad)}`:""}</div>
    ${l.sinopsis?`<p class="syn">${esc(l.sinopsis)}</p>`:`<p class="syn" style="color:var(--mut)">Este libro todavía no tiene sinopsis.</p>`}
    <dl>${rows}</dl>
    ${isStaff()?`<div class="acts"><button class="btn" data-edit="${l.id}">Editar libro</button>
      ${S.user.rol==="admin"?`<button class="btn danger" data-del="${l.id}">Eliminar</button>`:""}</div>`:""}`;
  $("detail").showModal();
}
