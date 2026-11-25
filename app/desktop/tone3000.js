/* TONE3000 for the desktop editor: signing in, letting the person choose a tone on TONE3000's own pages, and fetching the one model
 * they asked for. Nothing here runs until they press Browse TONE3000. No Electron in this file: what fetches, keeps and tells the
 * time is handed in, so that node can test it against a simulated service.
 *
 * As TONE3000's API asks (tone3000.com/api, terms of 17 November 2026): the publishable key only, PKCE, one model when it is asked
 * for, nothing mirrored or kept as a catalogue, and the creator, the licence and the address go with the tone. */
"use strict";
const crypto = require("node:crypto");

const SERVICE = "https://www.tone3000.com";
/* Where the sign-in page sends the window at the end. A local address needs no registration with TONE3000; nothing listens there:
 * the program reads the address before the window goes to it. */
const REDIRECT = "http://localhost:3001/callback";
/* The key that may be in a program. The other one, t3k_cs_, is a password of the person's account and is refused. */
const isPublishable = key => typeof key === "string" && /^t3k_pub_[A-Za-z0-9_-]{6,200}$/.test(key);
const KINDS = { capture: { format: "nam", architecture: "2" }, ir: { format: "ir" } };
const LIMIT = { capture: 8 * 1024 * 1024, ir: 24 * 1024 * 1024, picture: 3 * 1024 * 1024, json: 4 * 1024 * 1024 };
const EARLY = 60 * 1000;

class ToneError extends Error { constructor(code, message) { super(message); this.code = code; } }
const fail = (code, message) => { throw new ToneError(code, message); };
const url64 = raw => raw.toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const text = (v, most) => String(v === null || v === undefined ? "" : v).replace(/[\u0000-\u001f\u007f]/g, " ").trim().slice(0, most);
const whole = v => (Number.isSafeInteger(Number(v)) && Number(v) > 0 ? Number(v) : null);

/* A new request: its secrets stay here, the service gets their hash and the state. */
function newRequest(kind, random = crypto.randomBytes) {
  if (!Object.hasOwn(KINDS, kind)) fail("kind", "unknown kind");
  const verifier = url64(random(48)), state = url64(random(24));
  return { kind, verifier, state, challenge: url64(crypto.createHash("sha256").update(verifier).digest()) };
}

function authorizeUrl(service, clientId, request, hint) {
  const q = new URLSearchParams({ client_id: clientId, redirect_uri: REDIRECT, response_type: "code", code_challenge: request.challenge,
    code_challenge_method: "S256", state: request.state, prompt: "select_tone", menubar: "true", format: KINDS[request.kind].format });
  if (KINDS[request.kind].architecture) q.set("architecture", KINDS[request.kind].architecture);
  if (hint) q.set("login_hint", hint);
  return `${service}/api/v1/oauth/authorize?${q}`;
}

/* The address the service sends the window to at the end; it is read, never opened. null when it is another one. */
function readCallback(address, request) {
  let url;
  try { url = new URL(address); } catch (e) { return null; }
  if (url.origin + url.pathname.replace(/\/$/, "") !== REDIRECT || url.username || url.password) return null;
  const q = url.searchParams, got = Buffer.from(q.get("state") || ""), want = Buffer.from(request.state);
  const ours = got.length === want.length && crypto.timingSafeEqual(got, want);
  if (q.get("canceled") === "true" && (!q.get("state") || ours)) return { canceled: true, code: ours ? q.get("code") || null : null };
  if (!ours) return { error: "state" };
  if (q.get("error")) return { error: text(q.get("error"), 60) };
  const toneId = whole(q.get("tone_id"));
  if (!q.get("code") || !toneId) return { error: "incomplete" };
  return { code: q.get("code"), toneId };
}

/* What the page is told of a tone and of its models; the licence and the creator go with it. */
function toneOf(raw, service) {
  if (!raw || typeof raw !== "object" || !whole(raw.id)) fail("answer", "TONE3000 answered with something else.");
  const user = raw.user && typeof raw.user === "object" ? raw.user : {};
  const picture = (Array.isArray(raw.images) ? raw.images : []).find(u => typeof u === "string" && /^https:\/\//.test(u)) || null;
  return { id: whole(raw.id), title: text(raw.title, 120) || "Untitled", creator: text(user.username || user.display_name, 80) || "unknown", gear: text(raw.gear, 40), format: text(raw.format, 20),
    license: text(raw.license, 40), description: text(raw.description, 600), makes: (Array.isArray(raw.makes) ? raw.makes : []).map(m => text(m && m.name !== undefined ? m.name : m, 60)).filter(Boolean).slice(0, 6),
    picture, address: typeof raw.url === "string" && raw.url.startsWith("https://www.tone3000.com/") ? raw.url.slice(0, 300) : `${SERVICE}/tones/${whole(raw.id)}` };
}
function modelsOf(raw, kind) {
  const list = raw && Array.isArray(raw.data) ? raw.data : Array.isArray(raw) ? raw : fail("answer", "TONE3000 answered with something else.");
  return list.filter(m => m && whole(m.id) && typeof m.model_url === "string").filter(m => kind === "ir" ? m.architecture_version === null || m.architecture_version === undefined || String(m.architecture_version) === ""
    : String(m.architecture_version) === "2").map(m => ({ id: whole(m.id), name: text(m.name, 120) || "Model " + whole(m.id), size: text(m.size, 20), url: m.model_url }));
}
/* The token goes to TONE3000 only. */
function ownAddress(address, service) {
  let url;
  try { url = new URL(address); } catch (e) { return false; }
  const own = new URL(service);
  if (url.username || url.password) return false;
  return url.origin === own.origin || url.protocol === "https:" && own.protocol === "https:" && /(^|\.)tone3000\.com$/.test(url.hostname) && !url.port;
}
/* A file name the editor takes, and the kind of file it says it is. */
function fileOf(kind, name, raw) {
  const base = text(name, 120).normalize("NFC").replace(/\.(nam|wav|json)$/i, "").replace(/[\\/:*?"<>|]+/g, " ").replace(/\s+/g, " ").trim().slice(0, 60) || "TONE3000";
  if (kind === "ir") {
    if (raw.length < 44 || raw.toString("latin1", 0, 4) !== "RIFF" || raw.toString("latin1", 8, 12) !== "WAVE") fail("file", "This impulse response is not a .wav file.");
    return { name: base + ".wav", type: "audio/wav" };
  }
  let model;
  try { model = JSON.parse(raw.toString("utf8")); } catch (e) { fail("file", "This capture is not a .nam file."); }
  if (!model || typeof model !== "object" || !model.architecture) fail("file", "This capture is not a .nam file.");
  return { name: base + ".nam", type: "application/json" };
}

/* client: { clientId, service?, fetch, store: {load, save, clear}, now? }. One sign-in and one refresh at a time. */
function connect({ clientId, service = SERVICE, fetch, store, now = Date.now }) {
  if (!isPublishable(clientId)) fail("key", "This program has no publishable TONE3000 key.");
  const models = new Map(), pictures = new Map();
  let refreshing = null;
  const signedIn = () => { const t = store.load(); return !!(t && t.refresh); };

  async function read(response, most, what) {
    const declared = Number(response.headers.get("content-length") || 0);
    if (declared > most) fail("size", "This file is too large.");
    const raw = Buffer.from(await response.arrayBuffer());
    if (raw.length > most) fail("size", "This file is too large.");
    return raw;
  }
  async function answer(response) {
    const raw = await read(response, LIMIT.json);
    try { return JSON.parse(raw.toString("utf8")); } catch (e) { return fail("answer", "TONE3000 answered with something else."); }
  }
  async function once(address, options) {
    try { return await fetch(address, { ...options, redirect: "manual" }); } catch (e) { return fail("network", "TONE3000 could not be reached. Check the Internet connection."); }
  }
  /* Redirects are followed here, so that the token never goes to another place with them. */
  async function send(address, options = {}) {
    let headers = { ...options.headers };
    for (let hop = 0; hop < 5; hop++) {
      const response = await once(address, { ...options, headers });
      if (![301, 302, 303, 307, 308].includes(response.status)) return response;
      let next;
      try { next = new URL(response.headers.get("location") || "", address); } catch (e) { break; }
      if (options.method && options.method !== "GET" || next.username || next.password || next.protocol !== "https:" && next.origin !== new URL(service).origin) break;
      if (!ownAddress(next.href, service)) { headers = { ...headers }; delete headers.authorization; }
      address = next.href;
    }
    return fail("service", "TONE3000 has a problem. Try again later.");
  }
  async function token(fields) {
    const response = await send(`${service}/api/v1/oauth/token`, { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ ...fields, client_id: clientId }).toString() });
    if (response.status === 400 || response.status === 401) { if (fields.grant_type === "refresh_token") store.clear(); fail("signin", "Please sign in to TONE3000 again."); }
    if (response.status === 429) fail("limit", "TONE3000 is busy. Wait a minute and try again.");
    if (!response.ok) fail("service", "TONE3000 did not accept the sign-in.");
    const got = await answer(response);
    if (typeof got.access_token !== "string" || !got.access_token || String(got.token_type || "bearer").toLowerCase() !== "bearer") fail("answer", "TONE3000 answered with something else.");
    const kept = store.load() || {};
    const seconds = Number(got.expires_in);
    store.save({ access: got.access_token, refresh: typeof got.refresh_token === "string" && got.refresh_token ? got.refresh_token : kept.refresh || null,
      until: now() + (Number.isFinite(seconds) && seconds > 0 ? seconds : 300) * 1000 });
  }
  const exchange = (code, request) => token({ grant_type: "authorization_code", code, code_verifier: request.verifier, redirect_uri: REDIRECT });
  async function access(anew) {
    const t = store.load();
    if (!t) fail("signin", "Please sign in to TONE3000.");
    if (!anew && t.access && now() < t.until - EARLY) return t.access;
    if (!t.refresh) { store.clear(); fail("signin", "Please sign in to TONE3000 again."); }
    refreshing = refreshing || token({ grant_type: "refresh_token", refresh_token: t.refresh }).finally(() => { refreshing = null; });
    await refreshing;
    return store.load().access;
  }
  async function get(address, options = {}) {
    if (!ownAddress(address, service)) fail("address", "This file is kept outside TONE3000.");
    let response;
    for (let again = 0; again < 2; again++) {
      response = await send(address, { ...options, headers: { ...options.headers, authorization: "Bearer " + await access(again === 1) } });
      if (response.status !== 401) break;
    }
    if (response.status === 401) { store.clear(); fail("signin", "Please sign in to TONE3000 again."); }
    if (response.status === 403 || response.status === 404) fail("gone", "This tone is private or no longer on TONE3000.");
    if (response.status === 429) fail("limit", "TONE3000 is busy. Wait a minute and try again.");
    if (!response.ok) fail("service", "TONE3000 has a problem. Try again later.");
    return response;
  }
  const api = async path => answer(await get(`${service}/api/v1${path}`));

  /* The tone the person chose, and the models of it the pedal can use. */
  async function chosen(kind, toneId) {
    const tone = toneOf(await api(`/tones/${toneId}${kind === "capture" ? "?architecture=2" : ""}`), service);
    const list = modelsOf(await api(`/models?tone_id=${toneId}&page=1&page_size=100${kind === "capture" ? "&architecture=2" : ""}`), kind);
    if (!list.length) fail("none", kind === "ir" ? "This tone has no impulse response." : "This tone has no capture the pedal can play (NAM A2).");
    models.clear();
    for (const m of list) models.set(m.id, { ...m, kind, tone });
    pictures.clear();
    if (tone.picture) pictures.set(tone.id, tone.picture);
    return { tone: { ...tone, picture: !!tone.picture }, models: list.map(({ id, name, size }) => ({ id, name, size })) };
  }
  /* The file of one model of the tone just chosen. */
  async function model(id) {
    const m = models.get(whole(id));
    if (!m) fail("gone", "Choose the tone again.");
    const raw = await read(await get(m.url), LIMIT[m.kind]);
    return { raw, ...fileOf(m.kind, models.size > 1 ? `${m.tone.title} ${m.name}` : m.tone.title, raw) };
  }
  /* The tone's picture, without the token: it is kept elsewhere. */
  async function picture(id) {
    const address = pictures.get(whole(id));
    if (!address) fail("gone", "no picture");
    const response = await send(address, {});
    const type = String(response.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
    if (!response.ok || !["image/png", "image/jpeg", "image/webp", "image/gif", "image/avif"].includes(type)) fail("file", "no picture");
    return { raw: await read(response, LIMIT.picture), type };
  }
  return { signedIn, exchange, chosen, model, picture, signOut() { store.clear(); models.clear(); pictures.clear(); },
    authorizeUrl: (request, hint) => authorizeUrl(service, clientId, request, hint), service };
}

module.exports = { SERVICE, REDIRECT, KINDS, ToneError, isPublishable, newRequest, authorizeUrl, readCallback, toneOf, modelsOf, ownAddress, fileOf, connect };
