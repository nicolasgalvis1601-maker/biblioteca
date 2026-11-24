/* Sesión: iniciar, crear cuenta, restaurar y cerrar. Define qué ve cada rol. */
const ROLES = { admin: "Administrador", bibliotecario: "Bibliotecario", socio: "Socio" };

function paintSession() {
  const on = !!S.user;
  $("btnLogin").hidden = on;
  $("btnLogout").hidden = !on;
  $("who").hidden = !on;
  $("btnNew").hidden = !isStaff();
  if (on) $("who").innerHTML = `${esc(S.user.nombre || S.user.email)}<span class="role">${ROLES[S.user.rol] || esc(S.user.rol)}</span>`;
}

function clearSession() {
  S.token = null; S.user = null;
  sessionStorage.removeItem("rt");
  paintSession();
}

async function restore() {
  if (!sessionStorage.getItem("rt")) return paintSession();
  try { await renewSession(); S.user = await api("/auth/me"); }
  catch { clearSession(); }
  paintSession();
}

async function logout() {
  const rt = sessionStorage.getItem("rt");
  try { if (rt) await api("/auth/logout", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) }); }
  catch {}                       // aunque falle, la sesión local se cierra igual
  clearSession(); toast("Sesión cerrada");
}

async function startSession(j) {
  saveTokens(j);
  S.user = await api("/auth/me");
  paintSession();
  $("authD").close();
  toast(`Hola, ${S.user.nombre}`);
}

function showTab(tab) {
  const login = tab === "login";
  $("loginF").hidden = !login; $("regF").hidden = login;
  $("tabLogin").setAttribute("aria-selected", login); $("tabReg").setAttribute("aria-selected", !login);
  $("loginErr").textContent = ""; $("regErr").textContent = "";
  $(login ? "em" : "rn").focus();
}
function openAuth(tab = "login") { $("authD").showModal(); showTab(tab); }

$("btnLogin").onclick = () => openAuth("login");
$("btnLogout").onclick = logout;
document.querySelectorAll("[data-tab]").forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));

$("loginF").onsubmit = async (e) => {
  e.preventDefault(); $("loginGo").disabled = true; $("loginErr").textContent = "";
  try {
    const j = await api("/auth/login", { method: "POST", body: new URLSearchParams({ username: $("em").value.trim(), password: $("pw").value }) });
    await startSession(j); $("pw").value = "";
  } catch (err) { $("loginErr").textContent = err.message; }
  $("loginGo").disabled = false;
};

$("regF").onsubmit = async (e) => {
  e.preventDefault(); $("regErr").textContent = "";
  if ($("rp").value !== $("rp2").value) return ($("regErr").textContent = "Las contraseñas no coinciden.");
  $("regGo").disabled = true;
  const body = { email: $("re").value.trim(), nombre: $("rn").value.trim(), password: $("rp").value, confirmar_password: $("rp2").value };
  if ($("rt").value.trim()) body.telefono = $("rt").value.trim();
  try {
    await api("/auth/registro", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await api("/auth/login", { method: "POST", body: new URLSearchParams({ username: body.email, password: body.password }) });
    await startSession(j); e.target.reset();
  } catch (err) { $("regErr").textContent = err.message; }
  $("regGo").disabled = false;
};
