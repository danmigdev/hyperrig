/* Presets of others on Patchstorage, for the desktop editor: looking, and fetching the one file that is asked for. Read only: no account, no password, no token,
 * no cookie, nothing is sent but the question; publishing is on Patchstorage's own page, in the person's browser. Nothing here runs until they press Browse
 * Patchstorage. No Electron in this file: what fetches is handed in, so that node can test it against a simulated service.
 *
 * The public API of Patchstorage (patchstorage.com/docs/api/beta): the patches of one platform, HyperRig's, a page at a time, nothing mirrored; the creator, the
 * licence and the address go with the file. A file must be a HyperRig preset; the editor reads it strictly (app/mini/product-presetfile.js). */
"use strict";

const SERVICE = "https://patchstorage.com";
const UPLOAD = SERVICE + "/upload-a-patch/";
const LIMIT = { json: 2 * 1024 * 1024, file: 4 * 1024 * 1024 };
const PAGE = 20, TEXT = 60;
/* The orders of the list: the newest, the most downloaded, the most liked (Patchstorage has likes, no marks), each from the top. */
const ORDERS = { new: "date", downloads: "download_count", likes: "like_count" };

class ShareError extends Error { constructor(code, message) { super(message); this.code = code; } }
const fail = (code, message) => { throw new ShareError(code, message); };
const isPlatform = v => Number.isSafeInteger(v) && v > 0;
const whole = v => (typeof v !== "boolean" && v !== null && v !== "" && Number.isSafeInteger(Number(v)) && Number(v) > 0 ? Number(v) : null);
const count = v => (Number.isSafeInteger(v) && v >= 0 ? v : 0);
// Control characters, and those that hide or turn around what is written.
const hides = c => c < 32 && c !== 10 || c >= 127 && c <= 159 || c === 0xad || c >= 0x200b && c <= 0x200f || c >= 0x2028 && c <= 0x202e || c >= 0x2060 && c <= 0x2069 || c === 0xfeff;
const NAMED = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " };
/* Words of the service as plain text: its marks are taken out, and its entities are read once. */
function text(v, most, lines) {
  let s = String(v === null || v === undefined ? "" : typeof v === "string" || typeof v === "number" ? v : "").slice(0, 20000);
  s = s.replace(/<(script|style)\b[^]*?<\/\1\s*>/gi, " ").replace(/<(?:br|\/p|\/li|\/h\d)\b[^>]*>/gi, lines ? "\n" : " ").replace(/<[^>]*>/g, " ");
  s = s.replace(/&(?:#(\d{1,7})|#x([0-9a-f]{1,6})|([a-z]{2,8}));/gi, (all, d, x, n) => {
    if (n) return NAMED[n.toLowerCase()] ?? all;
    const c = d ? Number(d) : parseInt(x, 16);
    return c > 0 && c <= 0x10ffff && !(c >= 0xd800 && c <= 0xdfff) ? String.fromCodePoint(c) : " ";
  });
  s = Array.from(s, ch => (hides(ch.codePointAt(0)) || ch === "\n" && !lines ? " " : ch)).join("");
  return s.replace(/[ \t]+/g, " ").replace(/ ?\n[ \n]*/g, "\n").trim().slice(0, most).trim();
}
const day = v => (typeof v === "string" && /^\d{4}-\d\d-\d\d/.test(v) ? v.slice(0, 10) : "");
const pageOf = v => (typeof v === "string" && /^https:\/\/patchstorage\.com\/[A-Za-z0-9_.~%-]{1,200}\/?$/.test(v) ? v : SERVICE + "/");
const creatorOf = raw => text(raw && typeof raw.author === "object" && raw.author ? raw.author.name || raw.author.slug : "", 80) || "unknown";

/* What the page is told of a patch. null when it is none, or of another platform. */
function shortOf(raw, platform) {
  if (!raw || typeof raw !== "object" || !whole(raw.id) || !raw.platform || whole(raw.platform.id) !== platform) return null;
  return { id: whole(raw.id), title: text(raw.title, 120) || "Untitled", creator: creatorOf(raw), about: text(raw.excerpt, 240), day: day(raw.updated_at || raw.created_at), downloads: count(raw.download_count), likes: count(raw.like_count), address: pageOf(raw.url) };
}
function licenceOf(raw) {
  const l = raw && typeof raw.license === "object" && raw.license ? raw.license : {};
  return [text(l.name, 80), text(l.custom_license_text, 100)].filter(Boolean).join(": ") || "not given: ask its creator";
}
function filesOf(raw) {
  return (Array.isArray(raw.files) ? raw.files : []).slice(0, 20).map(f => ({ id: whole(f && f.id), name: text(f && f.filename, 120), size: count(f && f.filesize) }))
    .filter(f => f.id && /\.json$/i.test(f.name) && f.size <= LIMIT.file);
}

/* { platform, service?, fetch, agent? }: the numbers of HyperRig's platform and, for checks, a service of this computer. */
function connect({ platform, service = SERVICE, fetch, agent = "HyperRig" }) {
  if (!isPlatform(platform)) fail("platform", "This program has no place on Patchstorage.");
  const own = new URL(service);
  let known = null, working = false;

  async function once(address) {
    try { return await fetch(address, { method: "GET", redirect: "manual", credentials: "omit", referrerPolicy: "no-referrer", headers: { "user-agent": agent, accept: "application/json" } }); }
    catch (e) { return fail("network", "Patchstorage could not be reached. Check the Internet connection."); }
  }
  /* Redirects stay on Patchstorage. */
  async function get(address) {
    for (let hop = 0; hop < 4; hop++) {
      const response = await once(address);
      if (![301, 302, 303, 307, 308].includes(response.status)) {
        if (response.status === 404 || response.status === 403 || response.status === 400) fail("gone", "This preset is no longer on Patchstorage.");
        if (response.status === 429) fail("limit", "Patchstorage is busy. Wait a minute and try again.");
        if (!response.ok) fail("service", "Patchstorage has a problem. Try again later.");
        return response;
      }
      let next;
      try { next = new URL(response.headers.get("location") || "", address); } catch (e) { break; }
      if (next.origin !== own.origin || next.username || next.password) break;
      address = next.href;
    }
    return fail("service", "Patchstorage has a problem. Try again later.");
  }
  async function read(response, most) {
    if (Number(response.headers.get("content-length") || 0) > most) fail("size", "This file is too large for a preset.");
    if (!response.body || !response.body.getReader) {
      const raw = Buffer.from(await response.arrayBuffer());
      return raw.length > most ? fail("size", "This file is too large for a preset.") : raw;
    }
    const parts = [], reader = response.body.getReader();
    let size = 0;
    for (;;) {
      let part;
      try { part = await reader.read(); } catch (e) { fail("network", "Patchstorage could not be reached. Check the Internet connection."); }
      if (part.done) return Buffer.concat(parts);
      size += part.value.length;
      if (size > most) { reader.cancel().catch(() => {}); fail("size", "This file is too large for a preset."); }
      parts.push(Buffer.from(part.value));
    }
  }
  async function answer(response) {
    const raw = await read(response, LIMIT.json);
    try { return JSON.parse(raw.toString("utf8")); } catch (e) { return fail("answer", "Patchstorage answered with something else."); }
  }
  /* One question at a time. */
  async function alone(f) {
    if (working) fail("busy", "Wait for Patchstorage to answer.");
    working = true;
    try { return await f(); } finally { working = false; }
  }

  const search = (words, page, order) => alone(async () => {
    const at = Math.min(500, whole(page) || 1), by = Object.hasOwn(ORDERS, order) ? ORDERS[order] : ORDERS.new, w = text(words, TEXT);
    const q = new URLSearchParams({ "platforms[]": String(platform), per_page: String(PAGE), page: String(at), orderby: by, order: "desc" });
    if (w) q.set("search", w);
    const response = await get(`${service}/api/beta/patches?${q}`), list = await answer(response);
    if (!Array.isArray(list)) fail("answer", "Patchstorage answered with something else.");
    const pages = whole(response.headers.get("x-wp-totalpages")) || (list.length ? at : 0), total = Number(response.headers.get("x-wp-total"));
    return { page: at, pages, total: Number.isSafeInteger(total) && total >= 0 ? total : null, list: list.slice(0, PAGE).map(x => shortOf(x, platform)).filter(Boolean) };
  });
  const patch = id => alone(async () => {
    const n = whole(id);
    if (!n) fail("gone", "This preset is no longer on Patchstorage.");
    known = null;
    const raw = await answer(await get(`${service}/api/beta/patches/${n}`)), short = shortOf(raw, platform);
    if (!short || short.id !== n) fail("answer", "Patchstorage answered with something else.");
    const out = { ...short, about: text(raw.content, 3000, true) || short.about, license: licenceOf(raw), files: filesOf(raw) };
    known = { id: n, files: new Set(out.files.map(f => f.id)) };
    return out;
  });
  /* A file of the patch that was just looked at; its address is made here and not taken from the answer. */
  const file = (id, fid) => alone(async () => {
    const n = whole(id), f = whole(fid);
    if (!known || known.id !== n || !known.files.has(f)) fail("gone", "Choose the preset again.");
    const raw = await read(await get(`${service}/api/beta/patches/${n}/files/${f}/download/`), LIMIT.file);
    let d;
    try { d = JSON.parse(raw.toString("utf8")); } catch (e) { fail("file", "This file is not a HyperRig preset."); }
    if (!d || typeof d !== "object" || d.format !== "hyperrig-preset") fail("file", "This file is not a HyperRig preset.");
    return raw;
  });
  return { search, patch, file };
}

module.exports = { SERVICE, UPLOAD, LIMIT, PAGE, ShareError, isPlatform, text, shortOf, licenceOf, filesOf, connect };
