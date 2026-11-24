/* Cliente de la API: agrega el token y renueva la sesión sola cuando vence.
   El backend rota los refresh tokens, así que solo se permite una renovación a la vez. */
let _refreshing = null;

function saveTokens(j) {
  S.token = j.access_token;
  sessionStorage.setItem("rt", j.refresh_token);
}

function renewSession() {
  const rt = sessionStorage.getItem("rt");
  if (!rt) return Promise.reject(new Error("sin sesión"));
  _refreshing ??= fetch(API + "/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: rt }),
  })
    .then(async (r) => { if (!r.ok) throw new Error("vencida"); saveTokens(await r.json()); })
    .finally(() => { _refreshing = null; });
  return _refreshing;
}

async function api(path, opt = {}, retry = true) {
  const h = { ...(opt.headers || {}) };
  if (S.token) h.Authorization = "Bearer " + S.token;
  let r;
  try { r = await fetch(API + path, { ...opt, headers: h }); }
  catch { throw new Error("No se pudo conectar con la API. Revisa que esté encendida en " + API); }

  const isAuthCall = path.startsWith("/auth/login") || path.startsWith("/auth/refresh");
  if (r.status === 401 && retry && !isAuthCall && sessionStorage.getItem("rt")) {
    try { await renewSession(); return api(path, opt, false); }
    catch { clearSession(); throw new Error("Tu sesión venció. Inicia sesión de nuevo."); }
  }
  if (r.status === 204) return null;
  const j = await r.json().catch(() => ({}));
  if (r.status === 429) throw new Error("Demasiados intentos. Espera un minuto e inténtalo de nuevo.");
  if (r.status === 423) throw new Error(errText(j.detail) || "Cuenta bloqueada temporalmente.");
  if (!r.ok) throw new Error(errText(j.detail));
  return j;
}
