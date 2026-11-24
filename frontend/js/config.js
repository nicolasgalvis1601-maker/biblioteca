/* Dirección de la API. Cámbiala al desplegar. */
const API = ["localhost", "127.0.0.1"].includes(location.hostname)
  ? "http://localhost:8000/api/v1"
  : "https://TU-API.onrender.com/api/v1";   // <- pon aquí la dirección de tu API desplegada
const PAGE = 12;
const $ = (id) => document.getElementById(id);
const S = { q:"", cat:"", skip:0, total:0, token:null, user:null, cats:[], autores:[], editing:null, books:new Map() };
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const isStaff = () => S.user && ["admin","bibliotecario"].includes(S.user.rol);

function toast(t){ const el=$("toast"); el.textContent=t; el.classList.add("on"); clearTimeout(toast.t); toast.t=setTimeout(()=>el.classList.remove("on"),3200); }
function errText(d){ if(Array.isArray(d)) return d.map(e=>`${(e.loc||[]).slice(-1)}: ${e.msg}`).join(". "); return typeof d==="string"?d:"Ocurrió un error inesperado"; }
