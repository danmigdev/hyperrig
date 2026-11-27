/* The desktop editor of HyperRig for the TANK-MINI: a window with the editor's page, which is in this folder and was checked
 * by its builder. The page runs in a sandbox, without Node and without the network; it reaches the pedal through the serial
 * interface it uses in a browser, and the pedal's port is the only one it is given; over Bluetooth, which the page also uses as
 * in a browser, the only device it is given is one that says the pedal's name. Nothing is sent anywhere, unless the person
 * presses Browse TONE3000: then this process, not the page, talks to TONE3000 (tone3000.js), and TONE3000's own page opens in a
 * window of its own; or Browse Patchstorage: then this process asks Patchstorage (patchstorage.js), and only reads.
 *
 * The installer is a page of its own (app/installer), with the pedal's MIDI port; it has the firmware and the loader with it and
 * keeps its copies of the pedal in this computer's profile (store.js). --install starts with it.
 *
 * Switches, for checks: --no-pedal gives the page no port and no Bluetooth device, --off-screen opens the window outside the screens, --profile=FOLDER
 * keeps the settings and the log there, and with --off-screen --tone3000=ADDRESS is a simulated TONE3000 and --patchstorage=ADDRESS
 * a simulated Patchstorage. */
"use strict";
const { app, BrowserWindow, Menu, dialog, protocol, safeStorage, screen, session, shell } = require("electron");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const rules = require("./rules.js");
const { store: storeIn, SIZE: FLASH_SIZE } = require("./store.js");
const t3k = require("./tone3000.js");
const share = require("./patchstorage.js");

const EDITOR = path.join(__dirname, "editor");
const NO_PEDAL = app.commandLine.hasSwitch("no-pedal");
const OFF_SCREEN = app.commandLine.hasSwitch("off-screen");
let manifest = null, win = null, log = null, zoom = { auto: true }, copies = null;

app.setName("HyperRig");
if (app.commandLine.getSwitchValue("profile")) app.setPath("userData", path.resolve(app.commandLine.getSwitchValue("profile")));
for (const name of ["disable-background-networking", "disable-component-update", "disable-domain-reliability", "disable-sync", "no-pings"])
  app.commandLine.appendSwitch(name);
if (OFF_SCREEN) {
  app.commandLine.appendSwitch("disable-backgrounding-occluded-windows");
  app.commandLine.appendSwitch("disable-features", "CalculateNativeWinOcclusion");
}
protocol.registerSchemesAsPrivileged([{ scheme: rules.SCHEME, privileges: { standard: true, secure: true, supportFetchAPI: true } }]);

/* The editor's files, each as its builder left it. */
const files = new Map();
function load() {
  manifest = JSON.parse(fs.readFileSync(path.join(__dirname, "manifest.json"), "utf8"));
  for (const [name, hash] of Object.entries(manifest.files)) {
    const raw = fs.readFileSync(path.join(EDITOR, ...name.split("/")));
    if (crypto.createHash("sha256").update(raw).digest("hex") !== hash) throw new Error(name);
    files.set(name, raw);
  }
  if (!files.has("web/tank-mini.html")) throw new Error("web/tank-mini.html");
  for (const [name, hash] of Object.entries(manifest.installer || {})) {
    const raw = fs.readFileSync(path.join(__dirname, "installer", ...name.split("/")));
    if (crypto.createHash("sha256").update(raw).digest("hex") !== hash) throw new Error("installer/" + name);
    files.set("installer/" + name, raw);
  }
  if (manifest.installer) copies = storeIn(path.join(app.getPath("userData"), "pedals"));
}
const hasInstaller = () => files.has("installer/index.html");

/* The page's diagnostic lines stay on this computer: one file per start, the last twenty. */
const LOG_LIMIT = 20 * 1024 * 1024;
function openLog() {
  const folder = path.join(app.getPath("userData"), "logs");
  fs.mkdirSync(folder, { recursive: true });
  const old = fs.readdirSync(folder).filter(n => /^editor-.*\.jsonl$/.test(n)).sort();
  for (const name of old.slice(0, Math.max(0, old.length - 19))) fs.rmSync(path.join(folder, name), { force: true });
  log = { folder, file: path.join(folder, `editor-${new Date().toISOString().replace(/[:.]/g, "-")}.jsonl`), size: 0 };
}
function writeLog(rows) {
  if (!log || !rows.length || log.size > LOG_LIMIT) return;
  const text = rows.join("\n") + "\n";
  log.size += text.length;
  try { fs.appendFileSync(log.file, text); } catch (e) { log = { ...log, size: Infinity }; }
}
const note = (kind, more) => writeLog([JSON.stringify({ t: new Date().toISOString(), kind: "app_" + kind, ...more })]);

/* Each port the system lists, once, in the log: its form, so that a pedal that is not found can be explained. */
const described = new Set();
function describe(device, pedal) {
  const text = JSON.stringify(device);
  if (described.has(text) || described.size > 50) return;
  described.add(text);
  const instance = String((device && (device.deviceInstanceId || device.device_instance_id)) || "");
  note("port", { pedal, keys: Object.keys(device || {}), instance: instance.split("\\").slice(0, 2).join("\\"), vendor: device && (device.vendorId ?? device.vendor_id) });
}

/* TONE3000. The sign-in is kept with the system's own protection, and only for this user of this computer. */
const TONE_PLACE = "persist:tone3000";
const toneService = OFF_SCREEN ? app.commandLine.getSwitchValue("tone3000") : "";
let tones = null, toneWindow = null;
function toneKeeper() {
  const file = path.join(app.getPath("userData"), "tone3000.bin");
  let kept = null, read = false;
  return {
    load() {
      if (!read) { read = true; try { kept = JSON.parse(safeStorage.decryptString(fs.readFileSync(file))); } catch (e) { kept = null; } }
      return kept && { ...kept };
    },
    save(value) { kept = { ...value }; read = true; try { if (safeStorage.isEncryptionAvailable()) fs.writeFileSync(file, safeStorage.encryptString(JSON.stringify(value))); } catch (e) { /* until the program ends */ } },
    clear() { kept = null; read = true; try { fs.rmSync(file, { force: true }); } catch (e) { /* nothing there */ } },
  };
}
function setUpTones() {
  const clientId = toneService ? "t3k_pub_check0000" : (manifest.tone3000 || {}).client_id;
  if (!t3k.isPublishable(clientId)) return;
  tones = t3k.connect({ clientId, service: toneService || undefined, fetch: (address, options) => fetch(address, { ...options, cache: "no-store", signal: AbortSignal.timeout(60000) }), store: toneKeeper() });
  const place = session.fromPartition(TONE_PLACE);
  place.webRequest.onBeforeRequest((details, done) => done({ cancel: !rules.mayVisit(details.url, toneService) }));
  place.setPermissionCheckHandler(() => false);
  place.setPermissionRequestHandler((contents, permission, done) => done(false));
  place.setDevicePermissionHandler(() => false);
  place.on("will-download", event => event.preventDefault());
}
/* TONE3000's page in a window of its own, until it sends the window back with the tone that was chosen. */
function chooseTone(kind) {
  const request = t3k.newRequest(kind);
  return new Promise(resolve => {
    let over = false;
    const finish = value => {
      if (over) return;
      over = true;
      const w = toneWindow;
      toneWindow = null;
      if (w && !w.isDestroyed()) w.destroy();
      if (win && !OFF_SCREEN) win.focus();
      resolve(value);
    };
    const at = win.getBounds();
    toneWindow = new BrowserWindow({ parent: win, width: 1060, height: 820, minWidth: 420, minHeight: 520, show: !OFF_SCREEN, backgroundColor: "#111111", title: "TONE3000", autoHideMenuBar: true,
      ...(OFF_SCREEN ? { x: -4000, y: 0 } : { x: Math.round(at.x + (at.width - 1060) / 2), y: Math.round(at.y + (at.height - 820) / 2) }), icon: path.join(__dirname, "icon.png"),
      webPreferences: { partition: TONE_PLACE, sandbox: true, contextIsolation: true, nodeIntegration: false, spellcheck: false, webviewTag: false, navigateOnDragDrop: false, devTools: false,
        backgroundThrottling: !OFF_SCREEN } });
    if (OFF_SCREEN) toneWindow.showInactive();
    toneWindow.setMenu(null);
    const contents = toneWindow.webContents;
    const look = (event, address) => {
      const url = event.url || address, back = t3k.readCallback(url, request);
      if (!back && rules.mayVisit(url, toneService)) return;
      event.preventDefault();
      if (back) finish(back);
    };
    contents.on("will-navigate", look);
    contents.on("will-redirect", look);
    contents.setWindowOpenHandler(({ url }) => { if (rules.mayOpen(url)) shell.openExternal(url); return { action: "deny" }; });
    contents.on("will-attach-webview", event => event.preventDefault());
    contents.on("did-fail-load", (event, code, text, url, main) => { if (main && code !== -3) finish({ error: "network" }); });
    toneWindow.on("page-title-updated", event => event.preventDefault());
    toneWindow.on("closed", () => finish({ canceled: true }));
    toneWindow.loadURL(tones.authorizeUrl(request)).catch(() => {});
  }).then(async back => {
    if (back.error === "network") throw new t3k.ToneError("network", "TONE3000 could not be reached. Check the Internet connection.");
    if (back.error) throw new t3k.ToneError("signin", back.error === "access_denied" ? "TONE3000 was not allowed to continue." : "TONE3000 came back with something else. Try again.");
    if (back.code) await tones.exchange(back.code, request);
    return back.canceled ? { canceled: true } : tones.chosen(kind, back.toneId);
  });
}
const json = (value, status = 200) => new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
async function toneAnswer(what, request) {
  const q = new URL(request.url).searchParams;
  if (what === "status") return json({ available: !!tones, signedIn: !!tones && tones.signedIn() });
  if (!tones || request.method !== (what === "picture" ? "GET" : "POST")) return new Response("", { status: 404 });
  try {
    if (what === "select") {
      if (toneWindow) { toneWindow.focus(); return json({ error: { code: "busy", message: "TONE3000 is already open." } }); }
      const kind = q.get("kind");
      if (!Object.hasOwn(t3k.KINDS, kind)) return new Response("", { status: 404 });
      return json(await chooseTone(kind));
    }
    if (what === "model") {
      const file = await tones.model(q.get("id"));
      return new Response(file.raw, { headers: { "content-type": "application/octet-stream", "x-file-name": encodeURIComponent(file.name), "cache-control": "no-store" } });
    }
    if (what === "picture") {
      const picture = await tones.picture(q.get("id"));
      return new Response(picture.raw, { headers: { "content-type": picture.type, "cache-control": "no-store", "x-content-type-options": "nosniff" } });
    }
    if (what === "signout") {
      tones.signOut();
      await session.fromPartition(TONE_PLACE).clearStorageData();
      return json({ signedIn: false });
    }
  } catch (e) {
    note("tone3000", { what, code: e.code || e.name });
    return json({ error: { code: e.code || "other", message: e instanceof t3k.ToneError ? e.message : "Something went wrong with TONE3000. Try again." } }, what === "select" ? 200 : 502);
  }
  return new Response("", { status: 404 });
}

/* Patchstorage: looking and fetching, only with a place there, which the builder gives. */
const shareService = OFF_SCREEN ? app.commandLine.getSwitchValue("patchstorage") : "";
let shares = null;
function setUpShares() {
  const platform = shareService ? 9001 : (manifest.patchstorage || {}).platform;
  if (!share.isPlatform(platform)) return;
  shares = share.connect({ platform, service: shareService || undefined, agent: "HyperRig/" + manifest.version, fetch: (address, options) => fetch(address, { ...options, cache: "no-store", signal: AbortSignal.timeout(60000) }) });
}
async function shareAnswer(what, request) {
  const q = new URL(request.url).searchParams;
  if (what === "status") return json({ available: !!shares, upload: share.UPLOAD });
  if (!shares || request.method !== "POST") return new Response("", { status: 404 });
  try {
    if (what === "search") return json(await shares.search(q.get("q"), q.get("page")));
    if (what === "patch") return json(await shares.patch(q.get("id")));
    if (what === "file") return new Response(await shares.file(q.get("id"), q.get("file")), { headers: { "content-type": "application/octet-stream", "cache-control": "no-store", "x-content-type-options": "nosniff" } });
  } catch (e) {
    note("patchstorage", { what, code: e.code || e.name });
    return json({ error: { code: e.code || "other", message: e instanceof share.ShareError ? e.message : "Something went wrong with Patchstorage. Try again." } }, 502);
  }
  return new Response("", { status: 404 });
}

/* The installer's copies and notes. */
async function storeAnswer(what, request) {
  const q = new URL(request.url).searchParams, unit = q.get("unit");
  if (!copies || !hasInstaller()) return new Response("", { status: 404 });
  try {
    if (request.method === "GET" && what === "backups") return json(copies.backups(unit));
    if (request.method === "GET" && what === "note") return json(copies.note(unit));
    if (request.method === "GET" && what === "load") return new Response(copies.load(unit, q.get("name")), { headers: { "content-type": "application/octet-stream", "cache-control": "no-store" } });
    if (request.method === "POST" && what === "save") {
      const raw = Buffer.from(await request.arrayBuffer());
      if (raw.length !== FLASH_SIZE) return new Response("", { status: 400 });
      const name = copies.save(unit, q.get("kind"), raw, JSON.parse(q.get("about") || "{}"));
      note("backup", { name });
      return json({ name });
    }
    if (request.method === "POST" && what === "keep") { copies.keep(unit, await request.text()); return new Response(null, { status: 204 }); }
    if (request.method === "POST" && what === "open") {
      fs.mkdirSync(copies.folder, { recursive: true });
      if (!OFF_SCREEN) shell.openPath(copies.folder);
      return new Response(null, { status: 204 });
    }
  } catch (e) {
    note("store", { what, error: e.code || e.name, text: String(e.message).slice(0, 80) });
    return new Response("", { status: e.code === "ENOENT" ? 404 : 500 });
  }
  return new Response("", { status: 404 });
}

async function answer(request) {
  const name = rules.fileOf(request.url);
  if (name && name.startsWith("installer/store/")) return storeAnswer(name.slice("installer/store/".length), request);
  if (request.method === "POST" && name === "installer/log") {
    writeLog(rules.logRows(await request.text()));
    return new Response(null, { status: 204 });
  }
  if (name && name.startsWith("web/tone3000/")) return toneAnswer(name.slice("web/tone3000/".length), request);
  if (name && name.startsWith("web/patchstorage/")) return shareAnswer(name.slice("web/patchstorage/".length), request);
  if (request.method === "POST" && name === "web/log") {
    writeLog(rules.logRows(await request.text()));
    return new Response(null, { status: 204 });
  }
  if (name === "web/zoom" && win) {
    const by = new URL(request.url).searchParams.get("by");
    if (request.method === "POST") zoomTo(by);
    return new Response(JSON.stringify({ ...rules.zoomShown(zoom, ...win.getContentSize()), installer: hasInstaller() }), { headers: { "content-type": "application/json", "cache-control": "no-store" } });
  }
  const raw = request.method === "GET" && name ? files.get(name) : null;
  if (!raw) return new Response("", { status: 404 });
  return new Response(raw, { headers: { "content-type": rules.typeOf(name), "content-security-policy": rules.isInstaller(request.url) ? rules.INSTALLER_POLICY : rules.POLICY,
    "cache-control": "no-store", "x-content-type-options": "nosniff" } });
}

function guard(ses) {
  ses.protocol.handle(rules.SCHEME, answer);
  ses.on("will-download", (event, item) => {
    if (!rules.maySave(item.getURL())) { event.preventDefault(); note("save_refused", {}); return; }
    const name = rules.saveName(item.getFilename());
    if (OFF_SCREEN) {                        // a check: no question is asked, and the file stays with the check's profile
      const folder = path.join(app.getPath("userData"), "saved");
      fs.mkdirSync(folder, { recursive: true });
      item.setSavePath(path.join(folder, name));
    } else item.setSaveDialogOptions({ title: "Save", defaultPath: path.join(app.getPath("documents"), name), filters: [{ name: "HyperRig", extensions: ["json"] }, { name: "All files", extensions: ["*"] }] });
    item.once("done", (e, state) => note("save", { state }));
  });
  ses.webRequest.onBeforeRequest((details, done) => done({ cancel: !rules.mayLoad(details.url) }));
  const allowed = (permission, origin, details) => !(NO_PEDAL && /^midi/.test(permission)) && rules.mayUse(permission, origin, details);
  ses.setPermissionCheckHandler((contents, permission, origin, details) => allowed(permission, origin, details));
  ses.setPermissionRequestHandler((contents, permission, done, details) => done(allowed(permission, rules.originOf(details.requestingUrl), details) && rules.ownPage(details.requestingUrl)));
  ses.setDevicePermissionHandler(details => {
    if (details.deviceType !== "serial") return false;
    const pedal = rules.isPedal(details.device);
    describe(details.device, pedal);
    return !NO_PEDAL && pedal && rules.mayUse("serial", details.origin);
  });
  ses.on("select-serial-port", (event, list, contents, done) => {
    event.preventDefault();
    const found = NO_PEDAL ? [] : rules.pedals(list);
    note("ports", { seen: list.length, pedals: found.length });
    if (found.length === 1) { done(found[0].portId); return; }
    if (!found.length) {
      done("");
      dialog.showMessageBox(win, { type: "info", title: "HyperRig", message: "No TANK-MINI with HyperRig was found.",
        detail: "Connect the pedal to this computer by USB, wait a few seconds and try again. A pedal that runs M-VAVE's firmware does not appear here"
          + (hasInstaller() ? ": put HyperRig on it first." : "."),
        buttons: hasInstaller() ? ["OK", "Install HyperRig..."] : ["OK"], cancelId: 0, defaultId: 0 }).then(r => { if (r.response === 1) goTo(rules.INSTALL); });
      return;
    }
    const buttons = [...found.map(rules.portLabel), "Cancel"];
    const chosen = dialog.showMessageBoxSync(win, { type: "question", title: "HyperRig", message: "More than one pedal is connected.", buttons,
      cancelId: buttons.length - 1 });
    done(chosen < found.length ? found[chosen].portId : "");
  });
}

/* The page asked for a Bluetooth device ("Connect via Bluetooth"). Chromium scans and says what it has found so far, again and
 * again, until it is answered. The answer is the pedal with HyperRig, a moment after the first one shows so that a second one
 * can; the person chooses among several. None within the time ends the request, with a word about what to do. Only the editor's
 * page is answered, and nothing with --no-pedal. Of other devices only their number is noted. */
const AIR = { wait: 15000, settle: 800 };
let air = null;
/* A start goes the way the editor was connected last (hrBootAir in product-ui.js). A page may look for a Bluetooth device only when
 * the person clicked, so once the editor's page is loaded the program says it for the page, as a click; the page connects over
 * Bluetooth when that was the way last time, and otherwise does nothing. Not finding the pedal then is no news: the page goes on
 * over the cable, and no dialog says so. */
let airBootUntil = 0;
function airBoot(contents) {
  if (NO_PEDAL || !rules.isEditor(contents.getURL())) return;
  airBootUntil = Date.now() + 5000;
  contents.executeJavaScript('void (typeof hrBootAir === "function" && hrBootAir())', true).catch(() => {});
}
function airEnd(id) {
  if (!air) return;
  const { done, timer, settle } = air;
  air = null;
  clearTimeout(timer);
  clearTimeout(settle);
  done(id);
}
function airChoose() {
  if (!air) return;
  const found = air.found;
  air.settle = null;
  if (!found.length) return;                                // it went away again: keep waiting
  note("air", { seen: air.seen, pedals: found.length });
  if (found.length === 1) { airEnd(found[0].deviceId); return; }
  const buttons = [...found.map(d => d.deviceName), "Cancel"];
  const chosen = dialog.showMessageBoxSync(win, { type: "question", title: "HyperRig", message: "More than one pedal is near.", buttons, cancelId: buttons.length - 1 });
  airEnd(chosen < found.length ? found[chosen].deviceId : "");
}
function airAsked(event, list, done, contents) {
  event.preventDefault();
  if (NO_PEDAL || !rules.isEditor(contents.getURL())) { done(""); return; }
  if (!air) {
    const quiet = Date.now() < airBootUntil;
    air = { done, found: [], seen: 0, settle: null, timer: setTimeout(() => {
      note("air", { seen: air ? air.seen : 0, pedals: 0 });
      airEnd("");
      if (!quiet && win && !win.isDestroyed()) dialog.showMessageBox(win, { type: "info", title: "HyperRig", message: "No pedal with HyperRig was found over Bluetooth.",
        detail: "Switch Bluetooth on at the pedal: hold A and B for 3 seconds. Keep the pedal near this computer, whose Bluetooth has to be on, and try again." });
    }, AIR.wait) };
  }
  air.done = done;
  air.seen = Array.isArray(list) ? list.length : 0;
  air.found = rules.airPedals(list);
  if (air.found.length && !air.settle) air.settle = setTimeout(airChoose, AIR.settle);
}

/* The size of everything: it fits the window until the person chooses one. */
function applyZoom() {
  if (!win || win.isDestroyed()) return;
  const { factor } = rules.zoomOf(zoom, ...win.getContentSize());
  if (Math.abs(win.webContents.getZoomFactor() - factor) > 0.001) win.webContents.setZoomFactor(factor);
}
function zoomTo(by) {
  if (!win) return;
  zoom = rules.zoomBy(zoom, by, ...win.getContentSize());
  applyZoom();
  keepState();
}
function keepState() {
  if (!win || win.isDestroyed()) return;
  try { fs.writeFileSync(stateFile(), JSON.stringify(OFF_SCREEN ? { zoom } : { ...win.getNormalBounds(), maximized: win.isMaximized(), zoom })); } catch (e) { /* the next start is at the usual place */ }
}

const stateFile = () => path.join(app.getPath("userData"), "window.json");
function savedState() { try { return JSON.parse(fs.readFileSync(stateFile(), "utf8")); } catch (e) { return null; } }

function open() {
  const saved = savedState();
  zoom = saved && saved.zoom && typeof saved.zoom === "object" ? saved.zoom : { auto: true };
  const place = OFF_SCREEN ? { x: -4000, y: 0, width: 1440, height: 1000 } : rules.placeOf(saved, screen.getAllDisplays().map(d => d.workArea));
  win = new BrowserWindow({ ...place, minWidth: 380, minHeight: 520, show: false, backgroundColor: "#071819", title: "HyperRig", autoHideMenuBar: true,
    icon: path.join(__dirname, "icon.png"),
    webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false, spellcheck: false, webviewTag: false, navigateOnDragDrop: false,
      devTools: false, backgroundThrottling: !OFF_SCREEN } });
  if (saved && saved.maximized && !OFF_SCREEN) win.maximize();
  win.once("ready-to-show", () => { if (OFF_SCREEN) win.showInactive(); else win.show(); });
  win.on("close", keepState);
  win.on("resize", applyZoom);
  win.on("closed", () => { win = null; });
  const contents = win.webContents;
  contents.on("did-finish-load", () => { applyZoom(); airBoot(contents); });
  contents.on("select-bluetooth-device", (event, list, done) => airAsked(event, list, done, contents));
  contents.setWindowOpenHandler(({ url }) => { if (rules.mayOpen(url)) shell.openExternal(url); return { action: "deny" }; });
  contents.on("will-navigate", (event, url) => {
    if (rules.ownPage(url)) return;
    event.preventDefault();
    if (rules.mayOpen(url)) shell.openExternal(url);
  });
  contents.on("will-attach-webview", event => event.preventDefault());
  contents.on("will-prevent-unload", event => {       // the page has changes that are not saved on the pedal, or is writing to it
    const installing = rules.isInstaller(contents.getURL());
    const answer = dialog.showMessageBoxSync(win, installing ? { type: "warning", title: "HyperRig", message: "Your pedal is being written.",
      detail: "If you stop now, it waits in update mode and you can finish any time.", buttons: ["Keep going", "Stop"], defaultId: 0, cancelId: 0 }
      : { type: "question", title: "HyperRig", message: "There are changes you have not saved on the pedal.",
        buttons: ["Keep editing", "Close without saving"], defaultId: 0, cancelId: 0 });
    if (answer === 1) event.preventDefault();
  });
  contents.on("render-process-gone", (event, details) => {
    note("page_gone", { reason: details.reason });
    if (!win || details.reason === "clean-exit") return;
    const installing = rules.isInstaller(contents.getURL());
    dialog.showMessageBoxSync(win, { type: "error", title: "HyperRig", message: "The window stopped. It will start again.",
      detail: installing ? "A pedal that was being written waits, and you can finish." : "The pedal is not affected." });
    win.loadURL(installing ? rules.INSTALL : rules.START);
  });
  win.on("page-title-updated", event => event.preventDefault());
  win.setTitle(`HyperRig ${manifest.version}`);
  win.loadURL(app.commandLine.hasSwitch("install") && hasInstaller() ? rules.INSTALL : rules.START);
}
const goTo = address => { if (win && !win.isDestroyed()) win.loadURL(address).catch(() => {}); };

function menu() {
  const item = (label, accelerator, click) => ({ label, accelerator, click });
  const shown = (label, accelerator, by) => ({ label, accelerator, registerAccelerator: false, click: () => zoomTo(by) });
  const template = [
    ...(process.platform === "darwin" ? [{ role: "appMenu" }, { role: "editMenu" }] : []),
    ...(hasInstaller() ? [{ label: "Pedal", submenu: [item("Editor", undefined, () => goTo(rules.START)), item("Install, update or restore...", undefined, () => goTo(rules.INSTALL))] }] : []),
    { label: "View", submenu: [item("Reload", "CmdOrCtrl+R", () => win && win.webContents.reload()), { type: "separator" },
      shown("Larger", "CmdOrCtrl+Plus", "in"), shown("Smaller", "CmdOrCtrl+-", "out"), shown("Fit to the window", "CmdOrCtrl+0", "auto"),
      { type: "separator" }, { role: "togglefullscreen" }] },
    { label: "Help", submenu: [item("HyperRig on GitHub", undefined, () => shell.openExternal("https://github.com/danmigdev/hyperrig")),
      item("Open the folder with the logs", undefined, () => log && shell.openPath(log.folder)), { type: "separator" },
      item("About HyperRig", undefined, () => dialog.showMessageBox(win, { type: "info", title: "HyperRig", message: `HyperRig ${manifest.version}`,
        detail: `Editor ${manifest.revision}, for the firmware build ${manifest.firmware}.\n\nNot affiliated with M-VAVE. The licences are in the folder "licenses" beside the program.` }))] },
    ...(process.platform === "darwin" ? [] : [{ label: "Quit", submenu: [{ role: "quit" }] }]),
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => { if (win) { if (win.isMinimized()) win.restore(); win.focus(); } });
  app.on("window-all-closed", () => app.quit());
  app.whenReady().then(() => {
    try { load(); } catch (e) {
      const text = `This copy of HyperRig is damaged (${e.message}). Please download it again.`;
      if (OFF_SCREEN) console.error(text); else dialog.showErrorBox("HyperRig", text);
      app.exit(3);
      return;
    }
    try { openLog(); } catch (e) { log = null; }
    note("start", { version: manifest.version, revision: manifest.revision, electron: process.versions.electron, system: process.platform + " " + process.getSystemVersion() });
    guard(session.defaultSession);
    setUpTones();
    setUpShares();
    if (hasInstaller()) note("installer", { firmware: (manifest.firmware_carried || {}).version || null });
    menu();
    open();
  });
}
