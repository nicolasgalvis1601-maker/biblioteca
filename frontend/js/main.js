/* ---------- Eventos ---------- */
$("grid").onclick=(e)=>{ const b=e.target.closest(".book"); if(b) openDetail(b.dataset.id); };
$("chips").onclick=(e)=>{ const c=e.target.closest(".chip"); if(!c) return; S.cat=c.dataset.c; document.querySelectorAll(".chip").forEach(x=>x.setAttribute("aria-pressed",x===c)); load(true); };
$("more").onclick=()=>load(false);
$("sf").onsubmit=(e)=>{ e.preventDefault(); S.q=$("q").value.trim(); load(true); };
let t; $("q").oninput=()=>{ clearTimeout(t); t=setTimeout(()=>{ S.q=$("q").value.trim(); load(true); },350); };
document.addEventListener("click",async(e)=>{
  if(e.target.closest("[data-close]")) e.target.closest("dialog").close();
  const ed=e.target.closest("[data-edit]"); if(ed) openForm(S.books.get(+ed.dataset.edit));
  const del=e.target.closest("[data-del]");
  if(del){ const l=S.books.get(+del.dataset.del);
    if(!confirm(`¿Eliminar «${l.titulo}»? También se borrará su portada. Esta acción no se puede deshacer.`)) return;
    try{ await api(`/libros/${l.id}`,{method:"DELETE"}); $("detail").close(); toast("Libro eliminado"); load(true); }catch(err){ toast(err.message); } }
  if(e.target.tagName==="DIALOG") e.target.close();   // clic en el fondo
});

(async()=>{ await restore(); await loadCats(); load(true); })();
