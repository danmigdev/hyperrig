/* What the desktop editor permits: which port, which address, which permission. No I/O, so that node can test it. */
"use strict";

const SCHEME = "hyperrig";
const ORIGIN = SCHEME + "://editor";
const START = ORIGIN + "/tank-mini.html";
const INSTALLER = SCHEME + "://installer";   // the installer's page: its own place, with MIDI and without the editor's data
const INSTALL = INSTALLER + "/index.html";
// The pedal while HyperRig runs on it: the vendor of the chip with HyperRig's product; before the released 0.2.0, 3654 with any. The vendor of the chip by itself is
// many other devices', the original firmware and the chip's own loader among them.
const PEDAL = { vendor: 0x4c4a, product: 0x5155 }, BEFORE = 0x3654;
const SITE = /^https:\/\/(?:github\.com\/danmigdev\/hyperrig|www\.tone3000\.com|patchstorage\.com)(?:[/?#]|$)/;
const PERMISSIONS = new Set(["serial", "clipboard-sanitized-write", "screen-wake-lock", "fullscreen"]);
const INSTALLER_PERMISSIONS = new Set(["serial", "midi", "midiSysex", "clipboard-sanitized-write", "screen-wake-lock"]);
const TYPES = { html: "text/html; charset=utf-8", js: "text/javascript; charset=utf-8", json: "application/json", css: "text/css; charset=utf-8",
  svg: "image/svg+xml", png: "image/png", woff2: "font/woff2", txt: "text/plain; charset=utf-8", md: "text/plain; charset=utf-8", bin: "application/octet-stream" };
const POLICY = ["default-src 'none'", "script-src 'self' 'unsafe-inline' 'unsafe-eval'", "worker-src 'self' blob:", "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:", "font-src 'self' data:", "connect-src 'self'", "base-uri 'none'", "form-action 'none'", "frame-src 'none'",
  "object-src 'none'"].join("; ");

const INSTALLER_POLICY = ["default-src 'none'", "script-src 'self'", "style-src 'self' 'unsafe-inline'", "img-src 'self'", "font-src 'self'", "connect-src 'self'", "base-uri 'none'",
  "form-action 'none'", "frame-src 'none'", "object-src 'none'"].join("; ");

/* A serial port as Chromium describes it: with a vendor on some systems, with a Windows instance id on others. */
function isPedal(port) {
  if (!port || typeof port !== "object") return false;
  const first = keys => { for (const key of keys) { const v = port[key]; if (v !== undefined && v !== null && v !== "") return v; } return undefined; };
  const vendor = first(["vendorId", "vendor_id", "usbVendorId"]), product = first(["productId", "product_id", "usbProductId"]), id = first(["deviceInstanceId", "device_instance_id"]);
  if (vendor !== undefined) {
    if (Number(vendor) === BEFORE) return true;
    if (Number(vendor) !== PEDAL.vendor) return false;
    if (product !== undefined) return Number(product) === PEDAL.product;
    return typeof id === "string" && /[\\#]VID_4C4A&PID_5155(?:&|\\|#|$)/i.test(id);
  }
  return typeof id === "string" && /[\\#]VID_(?:4C4A&PID_5155|3654)(?:&|\\|#|$)/i.test(id);
}
const pedals = list => (Array.isArray(list) ? list.filter(isPedal) : []);
const portLabel = port => String((port && (port.displayName || port.portName)) || "TANK-MINI");

/* The path of a file inside the bundle, or null: only the editor's own address and the installer's, no way out of their folders. */
const PLACES = { editor: ["web/", "tank-mini.html"], installer: ["installer/", "index.html"] };
function fileOf(address) {
  let url;
  try { url = new URL(address); } catch (e) { return null; }
  if (url.protocol !== SCHEME + ":" || !Object.hasOwn(PLACES, url.host)) return null;
  const [folder, first] = PLACES[url.host];
  let name;
  try { name = decodeURIComponent(url.pathname).replace(/^\/+/, "") || first; } catch (e) { return null; }
  return /^[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)*$/.test(name) && !name.split("/").some(part => /^\.+$/.test(part)) ? folder + name : null;
}
/* Whose page an address is; a custom scheme has no origin of its own. */
function originOf(address) {
  let url;
  try { url = new URL(address); } catch (e) { return ""; }
  return url.protocol === SCHEME + ":" ? SCHEME + "://" + url.host : url.origin;
}
const isInstaller = address => originOf(address) === INSTALLER;
/* What TONE3000's own window may load: the web, over https, in a place of its own. */
/* A file to save: one the editor's page made itself (a preset, a report), nothing from anywhere else. */
const maySave = address => /^blob:hyperrig:\/\/editor\/[0-9a-f-]+$/i.test(String(address));
/* Its name, without any path and without what Windows does not take; never empty. */
const saveName = name => String(name || "").replace(/^.*[\\/]/, "").replace(/[<>:"|?*\u0000-\u001f\u007f]/g, "").replace(/^[ .]+|[ .]+$/g, "").slice(0, 120) || "HyperRig.json";
const mayVisit = (address, service) => /^(?:https|wss|blob|data):/.test(String(address)) || !!service && (String(address) + "/").startsWith(service + "/");
const ownPage = address => fileOf(address) !== null;
/* What a page may load: itself, and what it makes. */
const mayLoad = address => ownPage(address) || /^(?:blob|data):/.test(String(address)) && !/^blob:(?!hyperrig:)/.test(String(address)) || String(address).startsWith("devtools:");
/* What may open in the person's browser: the project's own pages, and those of the tones and presets they load. */
const mayOpen = address => SITE.test(String(address));
function mayUse(permission, origin, details) {
  const who = String(origin || "").replace(/\/$/, "");
  if (who === INSTALLER) return INSTALLER_PERMISSIONS.has(permission);
  return who === ORIGIN && (PERMISSIONS.has(permission) || permission === "fileSystem" && !!details && details.fileAccessType === "readable" && details.isDirectory !== true);
}
const typeOf = name => TYPES[String(name).split(".").pop().toLowerCase()] || "application/octet-stream";

/* A window's place, kept only when it can be seen on a screen of today. */
function placeOf(saved, screens) {
  const base = { width: 1280, height: 860 };
  if (!saved || ![saved.x, saved.y, saved.width, saved.height].every(Number.isInteger) || saved.width < 360 || saved.height < 400) return base;
  const seen = screens.some(s => saved.x < s.x + s.width - 80 && saved.x + saved.width > s.x + 80 && saved.y >= s.y - 8 && saved.y < s.y + s.height - 60);
  return seen ? { x: saved.x, y: saved.y, width: saved.width, height: saved.height } : base;
}

/* The size of everything. By itself it fits the window: the editor is drawn for 1360 by 900. */
const STEPS = [0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.25, 1.4, 1.6, 1.8, 2, 2.25, 2.5, 3];
const fits = (width, height) => Math.round(Math.max(0.8, Math.min(2.5, width / 1360, height / 900)) * 20) / 20;
/* No larger than leaves the page 820 by 480: beyond that it becomes the phone's page. */
const largest = (width, height) => Math.max(0.8, Math.min(3, width / 820, height / 480));
function zoomOf(state, width, height) {
  const auto = !(state && Number.isFinite(state.factor) && state.factor >= 0.5 && state.factor <= 3);
  return { auto, factor: auto ? fits(width, height) : Math.min(state.factor, Math.max(1, largest(width, height))) };
}
function zoomBy(state, by, width, height) {
  if (by === "auto") return { auto: true };
  const now = zoomOf(state, width, height).factor, limit = Math.max(1, largest(width, height));
  const next = by === "in" ? STEPS.find(s => s > now + 0.01 && s <= limit + 0.001) : by === "out" ? [...STEPS].reverse().find(s => s < now - 0.01) : undefined;
  return next === undefined ? state : { auto: false, factor: next };
}
function zoomShown(state, width, height) {
  const now = zoomOf(state, width, height), limit = Math.max(1, largest(width, height));
  return { percent: Math.round(now.factor * 100), auto: now.auto, in: STEPS.some(s => s > now.factor + 0.01 && s <= limit + 0.001), out: STEPS.some(s => s < now.factor - 0.01) };
}
/* The page's own diagnostic lines, as it posts them; anything else is dropped. */
function logRows(text) {
  if (typeof text !== "string" || text.length > 1024 * 1024) return [];
  let rows;
  try { rows = JSON.parse(text); } catch (e) { return []; }
  return Array.isArray(rows) ? rows.filter(r => r && typeof r === "object").map(r => JSON.stringify(r)) : [];
}

module.exports = { SCHEME, ORIGIN, START, INSTALLER, INSTALL, PEDAL, POLICY, INSTALLER_POLICY, STEPS, originOf, isInstaller, fits, zoomOf, zoomBy, zoomShown, isPedal, pedals, portLabel, fileOf, ownPage, mayLoad, mayOpen, mayVisit, maySave, saveName, mayUse, typeOf, placeOf, logRows };
