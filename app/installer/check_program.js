/* node --experimental-websocket app/installer/check_program.js PROGRAM ENGINE LOADER OUTPUT   (tools/check_desktop_installer.py)
 *
 * The built desktop program, outside the screens, with a profile of its own and --no-pedal, so that no real port is ever given to
 * it; its installer's page gets the MIDI and serial ports of a simulated pedal instead. No device is opened. */
"use strict";
const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const W = require("./wire.js"), F = require("./flash.js"), V = require("./views.js");
const { Engine, SimulatedPedal } = require("./simulated_pedal.js");

const [PROGRAM, ENGINE, LOADER, OUTPUT] = process.argv.slice(2);
const INSTALL = "hyperrig://installer/index.html";
const sleep = ms => new Promise(done => setTimeout(done, ms));
const sha = b => crypto.createHash("sha256").update(b).digest("hex");

/* Put in the page before its own scripts: ports that are the simulated pedal's, and that behave as Chromium's. */
const PORTS = fs.readFileSync(path.join(__dirname, "fake_ports.js"), "utf8");
const FAKE = `${PORTS};(() => {
  const inputs = new Map(), outputs = new Map(), waiting = new Map();
  let next = 1, present = false;
  const port = (id, name, type) => HrFakePorts.fakePort({ id, name, type, send: bytes => simOut(JSON.stringify({ id, bytes: Array.from(bytes) })) });
  const access = { inputs, outputs, sysexEnabled: true, onstatechange: null };
  Object.defineProperty(navigator, "requestMIDIAccess", { value: async () => access });
  const ask = line => new Promise(done => { const n = next++; waiting.set(n, done); simOut(JSON.stringify({ serial: n, line })); });
  /* the pedal misses the first command after the port is opened, as it does now and then */
  const serialPort = HrFakePorts.fakeSerialPort({ answer: ask, lose: 1 });
  Object.defineProperty(navigator, "serial", { value: { getPorts: async () => present ? [serialPort] : [], addEventListener() {} } });
  window.__sim = {
    ports(list) {
      for (const map of [inputs, outputs]) for (const [k, p] of map) if (!list.some(x => x.id === p.id.slice(2))) { p.state = "disconnected"; map.delete(k); if (p.onstatechange) p.onstatechange({ port: p }); }
      for (const x of list) { if (!inputs.has("i-" + x.id)) inputs.set("i-" + x.id, port("i-" + x.id, x.name, "input")); if (!outputs.has("o-" + x.id)) outputs.set("o-" + x.id, port("o-" + x.id, x.name, "output")); }
    },
    serial(on) { present = on; },
    deliver(id, bytes) { const p = inputs.get("i-" + id); if (p) p.deliver(bytes); },
    answer(n, text) { const f = waiting.get(n); waiting.delete(n); if (f) f(text); },
  };
  window.HYPERRIG_TIMES = { look: 60, settle: 60 };
})();`;

class Page {
  constructor(address) {
    this.id = 0;
    this.waiting = new Map();
    this.onevent = () => {};
    this.socket = new WebSocket(address);
    this.open = new Promise((done, fail) => { this.socket.onopen = done; this.socket.onerror = fail; });
    this.socket.onmessage = e => {
      const m = JSON.parse(e.data);
      if (m.id) { const w = this.waiting.get(m.id); this.waiting.delete(m.id); if (m.error) w.fail(new Error(m.error.message)); else w.done(m.result); } else this.onevent(m);
    };
  }
  call(method, params = {}) { const id = ++this.id; return new Promise((done, fail) => { this.waiting.set(id, { done, fail }); this.socket.send(JSON.stringify({ id, method, params })); }); }
  async evaluate(expression) {
    const r = await this.call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true, allowUnsafeEvalBlockedByCSP: false });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400));
    return r.result.value;
  }
}
/* The program with its window. */
class Run {
  static async start(program, profile, { pedal = null, size = [1280, 860] } = {}) {
    const run = new Run();
    fs.mkdirSync(profile, { recursive: true });
    const endpoint = path.join(profile, "DevToolsActivePort");
    fs.rmSync(endpoint, { force: true });
    run.process = spawn(program, ["--no-pedal", "--off-screen", "--install", `--profile=${profile}`, "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0"], { stdio: "ignore" });
    let code = null;
    run.process.on("exit", c => { code = c; });
    for (let i = 0; i < 400 && !(fs.existsSync(endpoint) && fs.readFileSync(endpoint, "utf8").trim()); i++) { if (code !== null) return { ended: code }; await sleep(100); }
    const port = fs.readFileSync(endpoint, "utf8").split(/\r?\n/)[0];
    let target = null;
    for (let i = 0; i < 200 && !target; i++) { try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p => p.type === "page" && p.url.startsWith("hyperrig:")); } catch (e) { /* not yet */ } if (!target) { if (code !== null) return { ended: code }; await sleep(100); } }
    assert.ok(target && target.url === INSTALL, `the program does not open the installer: ${target && target.url}`);
    run.page = new Page(target.webSocketDebuggerUrl);
    await run.page.open;
    for (const d of ["Page", "Runtime"]) await run.page.call(d + ".enable");
    await run.page.call("Emulation.setDeviceMetricsOverride", { width: size[0], height: size[1], deviceScaleFactor: 1, mobile: false });
    run.errors = [];
    run.page.onevent = m => {
      if (m.method === "Runtime.exceptionThrown") run.errors.push(m.params.exceptionDetails.text + " " + ((m.params.exceptionDetails.exception || {}).description || ""));
      if (m.method === "Runtime.bindingCalled" && m.params.name === "simOut") run.heard(JSON.parse(m.params.payload));
    };
    run.pedal = pedal;
    run.links = new Map();
    run.queue = Promise.resolve();
    return run;
  }
  async simulate() {
    await this.page.call("Runtime.addBinding", { name: "simOut" });
    await this.page.call("Page.addScriptToEvaluateOnNewDocument", { source: FAKE });
    await this.page.call("Page.navigate", { url: INSTALL });
    await this.until("document.readyState === 'complete' && !!window.__sim", "the page");
    this.following = setInterval(() => this.follow(), 40);
    await this.follow(true);
  }
  async follow(force) {
    const now = JSON.stringify(this.pedal.ports()) + (this.pedal.mode === "hyperrig" && this.pedal.plugged);
    if (now === this.known && !force) return;
    this.known = now;
    for (const [id, link] of this.links) if (!this.pedal.ports().some(p => p.id === id)) { link.closed = true; this.links.delete(id); }
    await this.page.evaluate(`__sim.ports(${JSON.stringify(this.pedal.ports())}); __sim.serial(${this.pedal.mode === "hyperrig" && this.pedal.plugged})`).catch(() => {});
  }
  heard(m) {
    if (m.serial) { this.pedal.console().ask(m.line).then(text => this.page.evaluate(`__sim.answer(${m.serial}, ${JSON.stringify(text)})`)).catch(() => {}); return; }
    this.queue = this.queue.then(async () => {
      const id = m.id.slice(2);
      let link = this.links.get(id);
      if (!link || link.closed) {
        try { link = await this.pedal.open(id); } catch (e) { return; }
        this.links.set(id, link);
        link.onmessage = bytes => { this.page.evaluate(`__sim.deliver(${JSON.stringify(id)}, ${JSON.stringify(Array.from(bytes))})`).catch(() => {}); };
      }
      try { link.send(Uint8Array.from(m.bytes)); } catch (e) { /* the cable is out */ }
    });
  }
  async until(expression, what, seconds = 30) {
    const limit = Date.now() + seconds * 1000;
    for (;;) {
      if (await this.page.evaluate(expression).catch(() => false)) return;
      if (Date.now() > limit) throw new Error(`${what}: ${JSON.stringify(await this.state())}`);
      await sleep(60);
    }
  }
  state() { return this.page.evaluate(`({ screen: document.body.dataset.screen, title: document.getElementById("title").textContent, text: document.getElementById("text").textContent, pedal: document.getElementById("pedalFw").textContent,
    safe: document.getElementById("safe").textContent, actions: [...document.querySelectorAll("#actions button")].map(b => b.dataset.act), log: document.getElementById("log").textContent.split("\\n").slice(-6) })`); }
  async title(text, seconds) { await this.until(`document.getElementById("title").textContent === ${JSON.stringify(text)}`, text, seconds); }
  async press(act) { await this.until(`!!document.querySelector('#actions button[data-act="${act}"]')`, act); await this.page.evaluate(`document.querySelector('#actions button[data-act="${act}"]').click()`); }
  async answer(yes = true) { await this.until("document.getElementById('ask').open", "the question"); await this.page.evaluate(`document.getElementById("${yes ? "askYes" : "askNo"}").click()`); }
  async picture(name) {
    await sleep(350);
    const r = await this.page.call("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path.join(OUTPUT, name + ".png"), Buffer.from(r.data, "base64"));
  }
  /* No text that does not fit, no page wider than its window. */
  async layout(what) {
    const bad = await this.page.evaluate(`(() => { const out = []; if (document.documentElement.scrollWidth > innerWidth + 1) out.push("wider than the window");
      for (const e of document.querySelectorAll("h2, .text, .actions button, .safe, .keep, .steps li, header *")) { const r = e.getBoundingClientRect(); if (r.width && (r.right > innerWidth + 1 || r.bottom > innerHeight + 1 || r.left < -1 || r.top < -1)) out.push((e.id || e.className || e.tagName) + " " + Math.round(r.bottom) + "/" + innerHeight); }
      const t = document.querySelector(".talk").getBoundingClientRect(), s = document.querySelector(".stage").getBoundingClientRect(); if (s.bottom > t.top + 1) out.push("the two parts overlap"); return out; })()`);
    assert.deepEqual(bad, [], what);
  }
  async close() {
    clearInterval(this.following);
    try { await Promise.race([this.page.call("Browser.close"), sleep(3000)]); } catch (e) { /* gone */ }
    for (let i = 0; i < 100 && this.process.exitCode === null; i++) await sleep(100);
    if (this.process.exitCode === null) this.process.kill();
    await sleep(300);
  }
}

const LOCKS = `(async () => {
  const out = {}, no = async (name, f) => { try { const v = await f(); out[name] = "done " + String(v).slice(0, 40); } catch (e) { out[name] = "refused"; } };
  out.node = [typeof require, typeof process, typeof module].join();
  out.secure = isSecureContext; out.origin = origin;
  await no("https", () => fetch("https://github.com/"));
  await no("the editor's files", () => fetch("hyperrig://editor/tank-mini.html"));
  await no("eval", () => (0, eval)("1"));
  await no("inline script", () => new Promise((ok, bad) => { const s = document.createElement("script"); s.textContent = "window.__x = 1"; document.head.append(s); setTimeout(() => window.__x ? ok() : bad(), 60); }));
  await no("midi", () => navigator.requestMIDIAccess({ sysex: true }));
  await no("camera", () => navigator.mediaDevices.getUserMedia({ video: true }));
  await no("clipboard", () => navigator.clipboard.readText());
  await no("hid", () => navigator.hid.requestDevice({ filters: [] }));
  out.ports = (await navigator.serial.getPorts()).length;
  out.window = window.open("https://example.com/") === null;
  out.outside = [];
  for (const p of ["main.js", "..%2fmanifest.json", "store/load?unit=..&name=x", "store/backups?unit=../..", "store/load?unit=0123456789abcdef&name=..%2f..%2fnote.json", "store/nothing", "simulated_pedal.js", "test_installer.js"]) { try { out.outside.push((await fetch(p)).status); } catch (e) { out.outside.push(0); } }
  const post = async (p, body) => { try { return (await fetch(p, { method: "POST", body })).status; } catch (e) { return 0; } };
  out.wrong = [await post("store/save?unit=0123456789abcdef&kind=stock&about={}", "short"), await post("store/save?unit=x&kind=stock&about={}", new Uint8Array(0x100000)), await post("store/keep?unit=0123456789abcdef", "{}"), await post("store/load?unit=0123456789abcdef", "")];
  return out;
})()`;

/* ---- a pedal with a firmware in the form of the stock one, made of noise ---- */
const random = (seed, n) => { const out = new Uint8Array(n); for (let i = 0, at = 0; at < n; i++, at += 32) out.set(crypto.createHash("sha256").update(`${seed} ${i}`).digest().subarray(0, Math.min(32, n - at)), at); return out; };
function stockFlash(unit) {
  const vm = 0x95000, length = vm - 0x4000, plain = new Uint8Array(length).fill(0xff), body = random("stock", length - 0xc00);
  body.set(W.ascii("TANK MINI_011\0"), 0x1000);
  plain.set(body, 0x120);
  const config = random("cfg", 0x17f), at = 0x120 + body.length, end = at + config.length;
  plain.set(config, at);
  const record = (i, name, crc, offset, size, flags, reserved, index) => {
    const r = new Uint8Array(32);
    W.put(r, 2, crc, 2); W.put(r, 4, offset, 4); W.put(r, 8, size, 4); r[12] = flags; r[13] = reserved; W.put(r, 14, index, 2);
    r.set(W.ascii(name), 16);
    W.put(r, 0, W.crc16(r.subarray(2)), 2);
    plain.set(r, 32 * i);
  };
  record(1, "app.bin", W.crc16(body), 0x120, body.length, 0x82, 0xff, 0);
  record(2, "cfg_tool.bin", W.crc16(config), at, config.length, 0x82, 0xff, 0);
  record(3, "VM", 0xffff, vm, 0xbe000 - vm, 0x12, 0x81, 0);
  record(4, "PRCT", 0xffff, 0, vm, 0x92, 0x82, 0);
  record(5, "BTIF", 0xffff, 0xbe000, 0x1000, 0x92, 0x81, 0);
  record(6, "USR", 0xffff, 0xbf000, 0x40000, 0x92, 0x81, 1);
  record(0, "app_area_head", W.crc16(plain.subarray(32, end)), 0x2000120, end, 0x83, 0xff, 0);
  const flash = new Uint8Array(F.CAPACITY).fill(0xff);
  flash.set(random("boot", 0x4000));
  flash.set(W.sfc(plain, F.KEY), 0x4000);
  for (const [name, a, n] of [["radio", 0xbe000, 0x1000], ["amps", 0xbf000, 0x30000], ["key", 0xff000, 0x1000]]) flash.set(random(name + unit, n), a);
  return flash;
}

(async () => {
  fs.mkdirSync(OUTPUT, { recursive: true });
  const program = path.join(PROGRAM, "HyperRig", "HyperRig.exe"), inside = path.join(PROGRAM, "HyperRig", "resources", "app", "installer", "firmware");
  const about = JSON.parse(fs.readFileSync(path.join(inside, "firmware.json"), "utf8")), image = new Uint8Array(fs.readFileSync(path.join(inside, "image.bin")));
  const report = { kind: "desktop-installer-check", hardware_test: false, firmware: about.version + " " + about.build, loader: about.loader, steps: {} }, steps = report.steps;
  const engine = new Engine(ENGINE), hrid = `HRID 1 ${about.version} ${about.build} banks=3`;
  const profile = n => path.join(OUTPUT, "profile-" + n);
  const expected = (before, after) => {
    assert.ok(W.same(after.subarray(F.APP, F.APP_END), F.areaFor(image, before.subarray(F.APP))), "HyperRig's area with this pedal's partitions");
    assert.ok(W.same(after.subarray(0, 0x4000), before.subarray(0, 0x4000)) && W.same(after.subarray(0x82000, 0x95000), before.subarray(0x82000, 0x95000)) && W.same(after.subarray(0xbe000), before.subarray(0xbe000)));
    assert.deepEqual([F.describe(after).kind, F.describe(after).whole], ["hyperrig", true]);
  };
  try {
    /* the locks, without a pedal */
    let run = await Run.start(program, profile(0));
    await run.title(V.TROUBLE.busy[0]);                              // MIDI is refused with --no-pedal
    const locks = await run.page.evaluate(LOCKS);
    assert.deepEqual([locks.node, locks.secure, locks.origin], ["undefined,undefined,undefined", true, "hyperrig://installer"]);
    for (const k of ["https", "the editor's files", "eval", "inline script", "midi", "camera", "clipboard", "hid"]) assert.equal(locks[k], "refused", k);
    assert.deepEqual([locks.ports, locks.window], [0, true]);
    assert.ok(locks.outside.every(s => s >= 400 || s === 0), JSON.stringify(locks.outside));
    assert.ok(locks.wrong.every(s => s >= 400 || s === 0), JSON.stringify(locks.wrong));
    assert.ok(!fs.existsSync(path.join(profile(0), "pedals", "0123456789abcdef", "note.json")));
    steps.locks = locks;
    await run.close();

    /* from the original 011, with the cable pulled once, and back */
    const before = stockFlash(1), pedal = await new SimulatedPedal(engine, before, { hrid, restart: 600 }).start();
    pedal.plugged = false;
    run = await Run.start(program, profile(1), { pedal });
    await run.simulate();
    await run.title(V.search().title);
    await run.picture("1-search");
    await run.layout("search");
    pedal.plug();
    await run.title("Ready for HyperRig");
    await run.picture("2-ready");
    await run.layout("ready");
    /* only a copy, which changes nothing */
    await run.press("save");
    await run.title("Your pedal is saved", 60);
    await run.layout("saved");
    const untouched = await pedal.flash();
    assert.ok(W.same(untouched.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(untouched.subarray(0xbe000), before.subarray(0xbe000)) && pedal.mode === "stock");
    await run.press("home");
    await run.title("Ready for HyperRig");
    await run.press("install");
    await sleep(300);
    await run.picture("3-question");
    await run.answer(false);
    assert.equal((await run.state()).title, "Ready for HyperRig");
    await run.press("install");
    const start = Date.now();
    await run.answer();
    await run.until("document.body.dataset.screen === 'work'", "the work");
    await run.until("parseInt(document.getElementById('meterFill').style.width) >= 20", "a fifth", 60);
    await run.picture("4-work");
    await run.layout("work");
    await run.title("HyperRig is on your pedal", 120);
    steps["seconds from 011 to HyperRig, simulated"] = Math.round((Date.now() - start) / 100) / 10;
    await run.picture("5-done");
    await run.layout("done");
    expected(before, await pedal.flash());
    const units = fs.readdirSync(path.join(profile(1), "pedals")), folder = path.join(profile(1), "pedals", units[0]);
    assert.equal(units.length, 1);
    const copies = fs.readdirSync(folder).filter(n => n.endsWith(".bin"));
    assert.equal(copies.length, 1);
    const copy = new Uint8Array(fs.readFileSync(path.join(folder, copies[0])));
    /* the copy is the whole pedal, with the loader that its own firmware had stored */
    assert.ok(W.same(copy.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(copy.subarray(0xbe000), before.subarray(0xbe000)) && F.bootDecision(F.withoutApplication(copy)).outcome === "loader");
    assert.equal(JSON.parse(fs.readFileSync(path.join(folder, "note.json"), "utf8")).state, "written");
    steps.copy = copies[0];
    await run.press("home");
    await run.until("!!document.querySelector('#actions button[data-act=restore]')", "restoring is offered");
    assert.deepEqual((await run.state()).actions, ["editor", "restore"]);
    await run.press("restore");
    await run.answer();
    await run.title("The original is back", 120);
    const back = await pedal.flash();
    assert.ok(W.same(back.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(back.subarray(0xbe000), before.subarray(0xbe000)));
    steps.restore = "the original firmware and its user area, byte for byte";

    /* the cable is pulled while it writes */
    await run.press("home");
    await run.title("Ready for HyperRig");
    await run.press("install");
    await run.answer();
    /* the meter still shows the end of the job before until this one begins */
    await run.until("document.body.dataset.screen === 'work' && parseInt(document.getElementById('meterFill').style.width) < 60", "the job has begun", 60);
    await run.until("parseInt(document.getElementById('meterFill').style.width) >= 60", "more than half", 120);
    pedal.pull();
    await run.title(V.TROUBLE.unplugged[0], 60);
    await run.picture("6-trouble");
    await run.layout("trouble");
    assert.match((await run.state()).safe, /waits in update mode/);
    pedal.plug();
    await run.title("Let's finish the job");
    await run.picture("7-resume");
    await run.layout("resume");
    /* the program is closed and opened again, and the power went in between */
    await run.close();
    assert.deepEqual(run.errors, []);
    await pedal.powerCycle();
    assert.equal(pedal.mode, "loader");
    run = await Run.start(program, profile(1), { pedal });
    await run.simulate();
    await run.title("Let's finish the job");
    await run.press("continue");
    await run.title("HyperRig is on your pedal", 120);
    expected(before, await pedal.flash());
    steps.interrupted = "the cable pulled, the program closed, the power gone; finished after that";
    /* a small window and a large one */
    for (const [w, h] of [[420, 700], [900, 620], [1920, 1080]]) {
      await run.page.call("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
      await sleep(250);
      if (w > 640) await run.layout(`${w} by ${h}`);
      await run.picture(`8-${w}`);
    }
    await run.press("editor");
    await run.until("location.href.startsWith('hyperrig://editor/')", "the editor");
    await run.until("!!document.getElementById('hrFirmware') && !!document.querySelector('#miniPortStatus .hrinst')", "the ways back to the installer");
    /* the way in the settings; the bar has no button for it */
    await run.until("!!document.getElementById('hrFirmware') && !document.getElementById('hrFwBtn')", "the Firmware part of the settings");
    await run.page.evaluate("document.querySelector('#hrFirmware button').click()");
    await run.until(`location.href === ${JSON.stringify(INSTALL)}`, "the installer again");
    steps.editor = "to the editor and back";
    assert.deepEqual(run.errors, []);
    await run.close();

    /* a changed file stops the program before any window */
    const damaged = path.join(OUTPUT, "damaged");
    fs.cpSync(path.join(PROGRAM, "HyperRig"), damaged, { recursive: true });
    const file = path.join(damaged, "resources", "app", "installer", "firmware", "image.bin"), raw = fs.readFileSync(file);
    raw[12345] ^= 1;
    fs.writeFileSync(file, raw);
    const ended = await Run.start(path.join(damaged, "HyperRig.exe"), profile(2));
    assert.equal(ended.ended, 3, "a damaged firmware was not refused");
    fs.rmSync(damaged, { recursive: true, force: true });
    steps.damaged = "refused at the start";
    report.held = true;
  } finally { engine.close(); }
  fs.writeFileSync(path.join(OUTPUT, "report.json"), JSON.stringify(report, null, 1) + "\n");
  console.log(JSON.stringify(report, null, 1));
  process.exit(0);
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
