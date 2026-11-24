/* ---------- Formulario ---------- */
function fillSelects(sel=[]){
  $("autor").innerHTML = S.autores.length ? S.autores.map(a=>`<option value="${a.id}">${esc(a.nombre)}</option>`).join("") : `<option value="">Crea un autor primero</option>`;
  $("catBox").innerHTML = S.cats.length ? S.cats.map(c=>`<label><input type="checkbox" value="${c.id}" ${sel.includes(c.id)?"checked":""}>${esc(c.nombre)}</label>`).join("") : `<span style="color:var(--mut);font-size:14px">Crea una categoría primero</span>`;
}
function openForm(l){
  S.editing = l||null; $("formErr").textContent=""; $("bf").reset(); $("prev").style.display="none";
  $("ft").textContent = l ? "Editar libro" : "Nuevo libro";
  fillSelects(l ? (l.categorias||[]).map(c=>c.id) : []);
  if(l){ $("titulo").value=l.titulo; $("isbn").value=l.isbn; $("anio").value=l.anio_publicacion; $("ej").value=l.ejemplares;
    $("autor").value=l.autor?.id ?? l.autor_id; $("edi").value=l.editorial||""; $("pag").value=l.num_paginas||""; $("idi").value=l.idioma||""; $("sin").value=l.sinopsis||""; }
  $("detail").close(); $("formD").showModal(); $("titulo").focus();
}
$("btnNew").onclick=()=>openForm();
$("img").onchange=(e)=>{ const f=e.target.files[0]; $("prev").style.display=f?"block":"none"; if(f) $("prev").src=URL.createObjectURL(f); };
async function quickAdd(kind){
  const nombre = prompt(kind==="autor"?"Nombre del autor":"Nombre de la categoría (mínimo 3 letras)"); if(!nombre) return;
  try{ await api(kind==="autor"?"/autores":"/categorias",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nombre})});
    const keep=[...document.querySelectorAll("#catBox input:checked")].map(i=>+i.value); const au=$("autor").value;
    await loadCats(); fillSelects(keep); if(au) $("autor").value=au; toast(kind==="autor"?"Autor creado":"Categoría creada");
  }catch(e){ $("formErr").textContent=e.message; }
}
$("addAutor").onclick=()=>quickAdd("autor"); $("addCat").onclick=()=>quickAdd("cat");
$("bf").onsubmit=async(e)=>{
  e.preventDefault(); $("formErr").textContent="";
  const cats=[...document.querySelectorAll("#catBox input:checked")].map(i=>i.value);
  if(!cats.length) return $("formErr").textContent="Elige al menos una categoría.";
  const fd=new FormData(e.target); fd.set("categoria_ids",cats.join(","));
  for(const [k,v] of [...fd.entries()]) if(v===""|| (k==="imagen" && !v.name)) fd.delete(k);
  $("save").disabled=true;
  try{
    const ed=S.editing;
    await api(ed?`/libros/${ed.id}`:"/libros",{method:ed?"PATCH":"POST",body:fd});
    $("formD").close(); toast(ed?"Libro actualizado":"Libro guardado"); await load(true);
  }catch(err){ $("formErr").textContent=err.message; }
  $("save").disabled=false;
};
