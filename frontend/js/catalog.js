/* ---------- Catálogo ---------- */
function cover(l){
  if (l.imagen_url) return `<img src="${esc(l.imagen_url)}" alt="Portada de ${esc(l.titulo)}" loading="lazy">`;
  let h=0; for (const c of l.titulo) h=(h*31+c.charCodeAt(0))%360;
  return `<div class="ph" style="--h:${h}">${esc(l.titulo)}</div>`;
}
function card(l){
  S.books.set(l.id,l);
  const ok = l.disponibles>0;
  return `<button class="book" data-id="${l.id}">
    <div class="cv">${cover(l)}</div>
    <h3>${esc(l.titulo)}</h3>
    <div class="au">${esc(l.autor?.nombre)}</div>
    <span class="tag ${ok?"":"no"}">${ok?`${l.disponibles} disponible${l.disponibles>1?"s":""}`:"Sin ejemplares ahora"}</span>
  </button>`;
}
async function load(reset){
  if (reset){ S.skip=0; S.books.clear(); $("grid").innerHTML=""; }
  const p = new URLSearchParams({ skip:S.skip, limit:PAGE });
  if (S.q) p.set("buscar",S.q);
  if (S.cat) p.set("categoria_id",S.cat);
  try{
    const j = await api("/libros?"+p);
    S.total = j.total; S.skip += j.items.length;
    $("grid").insertAdjacentHTML("beforeend", j.items.map(card).join(""));
    if (!S.total) $("grid").innerHTML = `<div class="empty">${S.q||S.cat?"No hay libros con esa búsqueda. Prueba con otro título o quita el filtro.":"Aún no hay libros en el catálogo."+(isStaff()?" Usa «Agregar libro» para publicar el primero.":"")}</div>`;
    $("count").textContent = S.total ? `${S.total} libro${S.total>1?"s":""}` : "";
    $("more").hidden = S.skip >= S.total;
  }catch(e){ $("grid").innerHTML = `<div class="empty">${esc(e.message)}</div>`; $("more").hidden=true; }
}
async function loadCats(){
  try{
    const [c,a] = await Promise.all([api("/categorias?limit=100"), api("/autores?limit=100")]);
    S.cats=c.items; S.autores=a.items;
    $("chips").innerHTML = `<button class="chip" aria-pressed="${!S.cat}" data-c="">Todos</button>` +
      S.cats.map(c=>`<button class="chip" aria-pressed="${S.cat==c.id}" data-c="${c.id}">${esc(c.nombre)}</button>`).join("");
  }catch{}
}
