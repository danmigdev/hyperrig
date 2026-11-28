/* node app/installer/test_installer.js [ENGINE [LOADER]]
 *
 * The wire formats and the flash rules always; the whole course of installing, updating, restoring and being interrupted with
 * ENGINE, the loader's own engine compiled by tools/check_installer.py, and LOADER, an output directory of
 * tools/build_mini_stage.py. Everything is simulated: no device is opened, and no stock firmware is in here. */
"use strict";
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const W = require("./wire.js"), F = require("./flash.js"), P = require("./pedal.js"), V = require("./views.js"), { Installer, order } = require("./flow.js");
const { Engine, SimulatedPedal, stored } = require("./simulated_pedal.js");
const { noteOk } = require("../desktop/store.js");

const hex = text => Uint8Array.from(text.trim().split(/\s+/), v => parseInt(v, 16));
const sha = b => crypto.createHash("sha256").update(b).digest("hex");
const random = (seed, n) => { const out = new Uint8Array(n); for (let i = 0, at = 0; at < n; i++, at += 32) out.set(crypto.createHash("sha256").update(`${seed} ${i}`).digest().subarray(0, Math.min(32, n - at)), at); return out; };
const tests = [];
const test = (name, body) => tests.push([name, body]);

/* ---- the MIDI ports, with Chromium's rules: close() is carried out later, and a closed input drops what arrives ---- */
const { fakePort } = require("./fake_ports.js"), { midiOf } = require("./webmidi.js");
const nap = ms => new Promise(done => setTimeout(done, ms));
function fakeAccess(answer) {
  const inputs = new Map(), outputs = new Map(), input = fakePort({ id: "in", name: "USB-Midi", type: "input" });
  inputs.set("in", input);
  outputs.set("out", fakePort({ id: "out", name: "USB-Midi", type: "output", send: bytes => setTimeout(() => { for (const b of answer(bytes)) input.deliver(b); }, 0) }));
  return { inputs, outputs };
}
const ASK = Uint8Array.from([0xf0, 1, 0xf7]), REPLY = Uint8Array.from([0xf0, 2, 0xf7]);

/* ---- HyperRig's console: the first commands after the port is opened may be missed ---- */
const { fakeSerialPort } = require("./fake_ports.js"), { serialOf } = require("./serial.js");
function fakeConsole({ lose = 0, refuse = 0, silent = [] } = {}) {
  const asked = [], port = fakeSerialPort({ lose, refuse, answer: async line => {
    asked.push(line);
    if (silent.includes(line)) return null;
    return { HRID: "HRID 1 0.2.0-dev.2 8da4f256a64ab616 banks=3", STAGE: "STAGE 1 bcf00", "STAGE GO": "STAGE GO" }[line] || null;
  } });
  return { asked, serial: serialOf({ getPorts: async () => [port] }, { gap: 5 }) };
}

test("a pedal that misses the first commands after the port is opened is asked again", async () => {
  for (const lose of [0, 1, 3]) {
    const { asked, serial } = fakeConsole({ lose });
    const answers = await serial.talk(async ask => [await ask("HRID", "HRID", { ms: 40, tries: 5 }), await ask("STAGE", "STAGE", { ms: 40, tries: 5 })]);
    assert.deepEqual(answers, ["HRID 1 0.2.0-dev.2 8da4f256a64ab616 banks=3", "STAGE 1 bcf00"], `lose ${lose}`);
    assert.deepEqual(asked, ["HRID", "STAGE"], "the pedal heard each of them once");
  }
  const { serial } = fakeConsole({ lose: 5 });
  assert.equal(await serial.talk(ask => ask("HRID", "HRID", { ms: 20, tries: 5 })), null, "and not for ever");
});

test("the old way, for comparison: one question to each opening, asked once", async () => {
  const port = fakeSerialPort({ lose: 1, answer: async () => "HRID 1 x 0000000000000000 banks=3" });
  const oldAsk = async (line, start) => {
    await port.open({ baudRate: 115200 });
    const reader = port.readable.getReader(), writer = port.writable.getWriter();
    const timer = setTimeout(() => reader.cancel(), 30);
    try {
      await writer.write(new TextEncoder().encode(line + "\n"));
      const { value, done } = await reader.read();
      return done ? null : new TextDecoder().decode(value).split("\n").find(l => l.startsWith(start));
    } finally { clearTimeout(timer); await reader.cancel(); await port.close(); }
  };
  assert.equal(await oldAsk("HRID", "HRID"), null, "this is the fault that was found on the pedal");
});

test("what does something is asked once, and only after a question that was answered", async () => {
  const { asked, serial } = fakeConsole({ lose: 1, silent: ["STAGE GO"] });
  const answer = await serial.talk(async ask => await ask("HRID", "HRID", { ms: 40, tries: 5 }) ? ask("STAGE GO", "STAGE", { ms: 60 }) : "silent");
  assert.equal(answer, null);
  assert.deepEqual(asked, ["HRID", "STAGE GO"], "STAGE GO is not repeated");
  const deaf = fakeConsole({ lose: 5, silent: ["STAGE GO"] });
  assert.equal(await deaf.serial.talk(async ask => await ask("HRID", "HRID", { ms: 20, tries: 5 }) ? ask("STAGE GO", "STAGE", { ms: 20 }) : "silent"), "silent");
  assert.ok(!deaf.asked.includes("STAGE GO"));
});

test("a port that is busy is tried again, and one that stays busy is told", async () => {
  const { serial } = fakeConsole({ refuse: 3 });
  assert.equal(await serial.talk(ask => ask("HRID", "HRID", { ms: 40, tries: 3 })), "HRID 1 0.2.0-dev.2 8da4f256a64ab616 banks=3");
  const port = fakeSerialPort({ refuse: 1000, answer: async () => null }), lines = [];
  const stuck = serialOf({ getPorts: async () => [port] }, { gap: 1, opening: 4, log: x => lines.push(x) });
  assert.equal(await stuck.talk(ask => ask("HRID", "HRID")), null);
  assert.match(lines.join(), /in use/);
  assert.equal(await serialOf({ getPorts: async () => [] }).talk(async () => 1), null, "no pedal at all");
});

test("a pedal that goes away in the middle does not hold the program", async () => {
  const port = fakeSerialPort({ answer: async () => null });
  port.close = () => new Promise(() => {});          // never answered
  const start = Date.now();
  assert.equal(await serialOf({ getPorts: async () => [port] }, {}).talk(async ask => ask("HRID", "HRID", { ms: 50 })), null);
  assert.ok(Date.now() - start < 4000);
});

test("the ports of the tests follow Chromium: closed and opened again at once, a port is closed", async () => {
  const { inputs, outputs } = fakeAccess(() => []);
  for (const port of [inputs.get("in"), outputs.get("out")]) {
    await port.open();
    const closing = port.close(), opening = port.open();          // the old installer's order
    await Promise.all([closing, opening]);
    await nap(5);
    assert.equal(port.connection, "closed", "the closing comes after the opening, which did nothing");
    await port.open();
    assert.equal(port.connection, "open");
  }
});

test("a port that was closed and is opened again at once still hears the pedal", async () => {
  for (let turn = 0; turn < 5; turn++) {
    const midi = midiOf(fakeAccess(() => [REPLY]));
    let heard = 0;
    for (let i = 0; i < 4; i++) {
      const link = await midi.open("in|out");
      link.onmessage = () => { heard++; };
      link.send(ASK);
      await nap(5);
      link.close();          // not waited for, as the core does
    }
    assert.equal(heard, 4, "each answer came to the link that asked");
  }
});

test("the old way of closing and opening, for comparison, loses the answer", async () => {
  const access = fakeAccess(() => [REPLY]);
  let heard = 0;
  const oldOpen = async () => {
    const input = access.inputs.get("in"), output = access.outputs.get("out");
    await Promise.all([input.open(), output.open()]);
    input.onmidimessage = () => { heard++; };
    return { send: b => output.send(b), close: () => { input.onmidimessage = null; input.close(); output.close(); } };
  };
  const first = await oldOpen();
  first.send(ASK);
  await nap(5);
  assert.equal(heard, 1);
  first.close();
  const second = await oldOpen();
  second.send(ASK);
  await nap(5);
  assert.equal(heard, 1, "the second link hears nothing: this is the fault that was found on the pedal");
});

test("one link per port at a time; the next waits for the closing, and for a link that is never closed a limited time", async () => {
  const access = fakeAccess(() => []), midi = midiOf(access, { patience: 60 }), order = [];
  const first = await midi.open("in|out");
  const second = midi.open("in|out").then(link => { order.push("second open"); return link; });
  await nap(10);
  assert.deepEqual(order, [], "not while the first is there");
  order.push("first closed");
  first.close();
  const link = await second;
  assert.deepEqual(order, ["first closed", "second open"]);
  link.close();
  const stuck = await midi.open("in|out");
  await assert.rejects(midi.open("in|out"), e => e.code === "busy");
  stuck.close();
  (await midi.open("in|out")).close();
});

test("a port that went away is told, and the next can be opened", async () => {
  const access = fakeAccess(() => []), midi = midiOf(access);
  const link = await midi.open("in|out");
  let gone = 0;
  link.ongone = () => { gone++; };
  const input = access.inputs.get("in");
  input.state = "disconnected";
  input.onstatechange({ port: input });
  assert.equal(gone, 1);
  link.close();
  await assert.rejects(midi.open("in|out"), e => e.code === "gone");
  assert.deepEqual(await midi.list(), []);
});

/* ---- things to test with: an application area in the form of the pedal's, made of noise ---- */
function area({ vm = 0x82000, size = 0x77000, text, length = 0x7e000 }) {
  const plain = new Uint8Array(length).fill(0xff), body = random(text, size - 0x300);
  body.set(W.ascii(text + "\0"), 0x1000);
  plain.set(body, 0x120);
  const config = random("cfg", 0x17f), at = 0x120 + body.length;
  plain.set(config, at);
  const end = at + config.length;
  const record = (i, name, crc, offset, length, flags, reserved, index) => {
    const r = new Uint8Array(32);
    W.put(r, 2, crc, 2); W.put(r, 4, offset, 4); W.put(r, 8, length, 4);
    r[12] = flags; r[13] = reserved;
    W.put(r, 14, index, 2);
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
  return W.sfc(plain, F.KEY);
}
const HYPERRIG = area({ text: "HyperRig auth" });
const HRID = "HRID 1 0.2.0-test 0123456789abcdef banks=3";
function stockFlash(version = "011", unit = 1) {
  const vm = version === "011" ? 0x95000 : 0x82000, flash = new Uint8Array(F.CAPACITY).fill(0xff);
  flash.set(random("boot", 0x4000));
  flash.set(area({ vm, size: vm - 0x4000 - 0x900, text: "TANK MINI_" + version, length: vm - 0x4000 }), 0x4000);
  flash.set(random("vm" + unit, 0x700), vm + 0x2000);
  flash.set(random("radio" + unit, 0x1000), 0xbe000);
  flash.set(random("amps" + unit, 0x30000), 0xbf000);
  flash.set(random("key" + unit, 0x1000), 0xff000);
  return flash;
}

/* An image for the application partition of 011: what it uses reaches past APP_END. */
const WIDE = area({ text: "HyperRig auth", size: 0x8a000, length: 0x91000 });

/* ---- wire ---- */
test("frames of the stock firmware, as they were recorded", () => {
  assert.equal(W.stockFrame(W.IDENTITY).length, 10);
  const reply = hex("00 59 11 1b 00 00 54 41 4e 4b 20 4d 49 4e 49 5f 30 31 31 00 00 00 00 00 00 00 00 00 00 00 00 00 00 93");
  const sent = W.join([0xf0], W.pack7(reply, false), [0xf7]);
  assert.equal(W.identityOf(sent), "TANK MINI_011");
  assert.deepEqual(W.stockFrame(0x11, reply.subarray(6, 33)), sent);
  const request = W.packageRequest(W.join([0xf0], W.pack7(hex("00 59 30 08 00 00 00 00 44 00 00 00 02 00 b9"), true), [0xf7]));
  assert.deepEqual([request.address, request.length], [0x4400, 512]);
  assert.equal(W.packageAnswer(request, new Uint8Array(512)).length, 605);
  const last = W.packageRequest(W.join([0xf0], W.pack7(hex("00 59 30 08 00 00 00 00 00 00 e0 08 00 00 17"), true), [0xf7]));
  assert.deepEqual([last.address, last.length], [W.FINISHED, 8]);
  assert.equal(W.packageAnswer(last, W.SUCCESS).length, 29);
  for (let i = 0; i < sent.length; i++) { const bad = sent.slice(); bad[i] ^= 0x10; const name = W.identityOf(bad); assert.ok(name === null || name !== "TANK MINI_011" || i < 8 || i >= 34, `byte ${i}`); }
  for (const junk of [[], [0xf0], [0xf0, 0xf7], [0x90, 60, 100], [...sent.subarray(0, 20), 0xf7]]) { assert.equal(W.identityOf(Uint8Array.from(junk)), null); assert.equal(W.packageRequest(Uint8Array.from(junk)), null); assert.equal(W.loaderParse(Uint8Array.from(junk)), null); }
});
test("frames of the loader, and every damaged one", () => {
  const f = W.loaderFrame(W.OPS.READ, 0x1234, Uint8Array.of(1, 2, 3, 4, 0, 4)), r = W.loaderParse(f);
  assert.deepEqual([r.op, r.sequence, [...r.body]], [2, 0x1234, [1, 2, 3, 4, 0, 4]]);
  for (let i = 1; i < f.length - 1; i++) { const bad = f.slice(); bad[i] ^= 1; const p = W.loaderParse(bad); assert.ok(p === null || W.same(p.body, r.body) && p.op === r.op && p.sequence === r.sequence, `byte ${i}`); }
  for (let n = 0; n < 1030; n += 103) { const body = random("b" + n, n); assert.deepEqual(W.loaderParse(W.loaderFrame(0x11, 7, body)).body, body); }
  assert.equal(W.crc32(W.ascii("123456789")), 0xcbf43926);
  assert.equal(W.crc16(W.ascii("123456789")), 0x31c3);
  for (let n = 0; n < 40; n++) for (const flush of [true, false]) { const raw = random("p" + n, n), back = W.unpack7(W.pack7(raw, flush)); assert.deepEqual(back.subarray(0, n), raw); assert.ok(back.length - n <= 1); }
  assert.equal(W.unpack7(Uint8Array.of(1, 200)), null);
});

/* ---- flash ---- */
test("what is in a flash", () => {
  for (const v of ["009", "011"]) {
    const flash = stockFlash(v), is = F.describe(flash);
    assert.deepEqual([is.kind, is.version, is.whole, is.layout.vm], ["stock", v, true, v === "011" ? 0x95000 : 0x82000]);
    flash[0x4000 + 0x3456] ^= 1;
    assert.equal(F.describe(flash).whole, false);
    flash[0x4008] ^= 1;
    assert.deepEqual([F.describe(flash).kind, F.describe(flash).layout], ["none", null]);
  }
  const flash = stockFlash();
  flash.set(HYPERRIG, F.APP);
  assert.deepEqual([F.describe(flash).kind, F.describe(flash).whole, F.describe(flash).layout.vm], ["hyperrig", true, 0x82000]);
  flash.set(area({ text: "something else" }), F.APP);
  assert.equal(F.describe(flash).kind, "other");
  assert.throws(() => F.describe(flash.subarray(1)), { code: "size" });
});
test("partitions that are not a TANK-MINI's are not accepted", () => {
  for (const vm of [0x81000, 0x82001, 0xa1000]) {
    const flash = stockFlash();
    flash.set(area({ text: "TANK MINI_011", vm, size: 0x70000 }), F.APP);
    assert.equal(F.describe(flash).layout, null, vm.toString(16));
    assert.throws(() => F.areaFor(HYPERRIG, flash.subarray(F.APP, F.APP + 4096)), { code: "layout" });
  }
});
test("HyperRig's area keeps the pedal's partitions and is signed again", () => {
  const nine = stockFlash("009"), eleven = stockFlash("011");
  assert.ok(W.same(F.areaFor(HYPERRIG, nine.subarray(F.APP)), HYPERRIG), "on 009 the image comes out as it is");
  const made = F.areaFor(HYPERRIG, eleven.subarray(F.APP));
  let differ = 0;
  for (let i = 0; i < made.length; i++) if (made[i] !== HYPERRIG[i]) { differ++; assert.ok(i < 160, `byte ${i}`); }
  assert.ok(differ > 4);
  const flash = eleven.slice();
  flash.set(made, F.APP);
  const is = F.describe(flash);
  assert.deepEqual([is.kind, is.whole, is.layout.vm], ["hyperrig", true, 0x95000]);
  const bad = HYPERRIG.slice();
  bad[0x5000] ^= 1;
  assert.throws(() => F.areaFor(bad, nine.subarray(F.APP)), { code: "image" });
  assert.throws(() => F.areaFor(HYPERRIG.subarray(0, 4096), nine.subarray(F.APP)), { code: "image" });
});
test("what the loader cannot write is never planned", () => {
  const now = stockFlash(), target = F.installTarget(now, HYPERRIG, now.subarray(F.APP)), p = F.plan(now, target);
  assert.equal(p.order.at(-1), F.APP);
  assert.ok(p.order.every(a => a >= 0x4000 && a < 0x82000) && p.order.length <= 126 && p.windows === 1);
  for (const a of [0, 0x3fff, 0x82000, 0x95000, 0xbcf00, 0xbefff, 0xff000, 0xfffff]) { const t = target.slice(); t[a] ^= 1; assert.throws(() => F.plan(now, t), { code: "outside" }); }
  const t = now.slice();
  t[0xc0000] ^= 1;
  assert.deepEqual([F.plan(now, t).order, F.plan(now, t).windows], [[0xc0000, F.APP], 3]);
  assert.deepEqual([F.plan(now, now).order, F.plan(now, now).windows], [[], 0]);
  /* restoring: the application and the user area of the backup, and only if the rest of a larger stock is still there */
  const is = target.slice();
  is.fill(0x55, 0xc0000, 0xc8000);
  const back = F.restoreTarget(is, now);
  assert.ok(W.same(back, now));
  const broken = is.slice();
  broken[0x90000] ^= 1;
  assert.throws(() => F.restoreTarget(broken, now), { code: "outside" });
  const half = now.slice();
  half[0x7000] ^= 1;
  assert.throws(() => F.restoreTarget(is, half), { code: "backup" });
  assert.throws(() => F.restoreTarget(is, is), { code: "backup" });
});

/* ---- with the loader ---- */
const [ENGINE, LOADER, ONLY] = process.argv.slice(2);
const assets = LOADER ? (() => {
  const read = n => new Uint8Array(fs.readFileSync(path.join(LOADER, n)));
  const stream = read("stage-ota.bin");
  return { image: HYPERRIG, version: "0.2.0-test", build: "0123456789abcdef", pack: read("stage-package.bin"), stored: stream.length, code: read("stage-code.bin"), stream };
})() : null;
const TIMES = { look: 15, loader: 4000, back: 2500, settle: 8, pedal: { answer: 150, slow: 4000, first: 700, next: 500, end: 500, tries: 6 } };

if (assets) test("the bootloader's decision and the way back", () => {
  const flash = stockFlash(), bare = () => F.withoutApplication(flash);
  assert.equal(F.bootDecision(flash).outcome, "application");
  assert.equal(F.bootDecision(bare()).outcome, "reset");
  assert.deepEqual(F.wayBack(flash, assets.code), { ok: false, record: null, retire: null });
  stored(flash, assets.stream);
  assert.deepEqual([F.bootDecision(bare()).outcome, F.bootDecision(bare()).record, F.bootDecision(bare()).place], ["loader", 0xbcf00, 0xb7000]);
  assert.ok(W.same(F.bootDecision(bare()).code, assets.code));
  assert.deepEqual(F.wayBack(flash, assets.code), { ok: true, record: 0xbcf00, retire: null });
  assert.deepEqual(F.wayBack(flash, null), { ok: true, record: 0xbcf00, retire: null });
  for (const a of [0xb7004, 0xb7021, 0xb7030, 0xb7041, 0xb7400, 0xb9000, 0xbb000]) {
    const bad = flash.slice();
    bad[a] ^= 4;
    assert.equal(F.bootDecision(F.withoutApplication(bad)).outcome, "download mode", a.toString(16));
    assert.equal(F.wayBack(bad, assets.code).ok, false);
  }
  for (const a of [0xbcf00, 0xbcf06, 0xbcf09, 0xbcf48]) { const bad = flash.slice(); bad[a] ^= 4; assert.equal(F.bootDecision(F.withoutApplication(bad)).outcome, "reset"); }
  /* another loader's record above ours: it can be made void; one below does not matter */
  const above = flash.slice();
  const other = random("other loader", 1000);
  stored(above, other, { place: 0xb0000, record: 0xbdf00, name: "ota-TANK MINI_009" });
  assert.deepEqual(F.wayBack(above, assets.code), { ok: false, record: 0xbdf00, retire: 0xbdf00 });
  above.fill(0, 0xbdf06, 0xbdf08);
  assert.equal(F.wayBack(above, assets.code).ok, true);
  const below = flash.slice();
  stored(below, other, { place: 0xa0000, record: 0xb5f00 });
  assert.equal(F.wayBack(below, assets.code).ok, true);
  const alone = stockFlash();
  stored(alone, other, { place: 0xb0000, record: 0xbdf00 });
  assert.deepEqual(F.wayBack(alone, assets.code), { ok: false, record: 0xbdf00, retire: null });
});

/* A computer: its disk, and the screens that were shown. */
class Computer {
  constructor() { this.files = new Map(); this.notes = new Map(); this.full = false; this.bad = false; }
  store() {
    const list = unit => [...this.files.entries()].filter(([k]) => k.startsWith(unit + "/")).map(([, v]) => v.about);
    return { backups: async unit => list(unit), note: async unit => this.notes.get(unit) || null,
      save: async (unit, kind, bytes, about) => {
        if (this.full) throw new Error("no space");
        const name = `${this.files.size + 1}-${kind}.bin`;
        this.files.set(unit + "/" + name, { bytes: Uint8Array.from(bytes), about: { ...about, name, kind, time: about.time + this.files.size } });
        if (this.bad) this.files.get(unit + "/" + name).bytes[99] ^= 1;
        return name;
      },
      /* the notes the program's own store takes (app/desktop/store.js), and no other */
      load: async (unit, name) => this.files.get(unit + "/" + name).bytes.slice(), keep: async (unit, note) => {
        if (this.full) throw new Error("no space");
        if (!noteOk(JSON.parse(JSON.stringify(note)))) throw new Error("the store refuses this note: " + JSON.stringify(note));
        this.notes.set(unit, { ...note });
      } };
  }
  program(pedal, { own = assets, serial = true } = {}) {
    const views = [], lines = [];
    const env = { midi: { list: async () => pedal.ports(), open: id => pedal.open(id) }, serial: serial ? pedal.console() : null, store: this.store(), sha256: async b => sha(b), now: () => Date.now(), sleep: ms => new Promise(done => setTimeout(done, ms)) };
    const installer = new Installer(env, own, { show: v => views.push(v), log: l => lines.push(l), times: TIMES });
    return { installer, views, lines, last: () => views.at(-1), screens: () => views.map(v => v.screen).filter((s, i, all) => s !== all[i - 1]) };
  }
}
let engine = null;
async function pedalWith(flash, set = {}) { return new SimulatedPedal(engine, flash, { hrid: HRID, ...set }).start(); }
async function installed(computer, pedal, options) {
  const run = computer.program(pedal, options);
  await run.installer.home();
  await run.installer.act("install");
  return run;
}
const expected = (before, after) => {
  /* what the stock firmware stored, HyperRig with this pedal's partitions, everything else as it was */
  assert.ok(W.same(after.subarray(0, 0x4000), before.subarray(0, 0x4000)) && W.same(after.subarray(0x82000, 0x95000), before.subarray(0x82000, 0x95000)));
  assert.ok(W.same(after.subarray(0xbe000), before.subarray(0xbe000)), "the radio data, the user area and the last sector are as they were");
  assert.ok(W.same(after.subarray(F.APP, F.APP_END), F.areaFor(HYPERRIG, before.subarray(F.APP))));
  const is = F.describe(after);
  assert.deepEqual([is.kind, is.whole], ["hyperrig", true]);
};

test("an image for the application partition of 011: where it fits, how far the loader writes, and back", () => {
  const eleven = stockFlash("011"), nine = stockFlash("009");
  assert.ok(F.imageEnd(WIDE) > F.APP_END && F.imageEnd(WIDE) <= 0x95000 && F.imageEnd(HYPERRIG) <= F.APP_END);
  assert.equal(F.areaFor(WIDE, eleven.subarray(F.APP)).length, Math.ceil((F.imageEnd(WIDE) - F.APP) / 4096) * 4096, "only what it uses past APP_END");
  assert.throws(() => F.areaFor(WIDE, nine.subarray(F.APP)), { code: "size" }, "009's partition is smaller");
  const long = area({ text: "HyperRig auth", length: 0x91000 });
  assert.equal(F.areaFor(long, nine.subarray(F.APP)).length, 0x7e000, "a long image that uses less fits 009, cut");
  assert.equal(F.areaFor(long, eleven.subarray(F.APP)).length, 0x7e000, "and installs as before on 011");
  for (const length of [0x7d000, 0x9d000, 0x91800]) assert.throws(() => F.areaFor(area({ text: "HyperRig auth", length }), eleven.subarray(F.APP)), { code: "image" }, length.toString(16));
  const target = F.installTarget(eleven, WIDE, eleven.subarray(F.APP));
  assert.ok(F.reach(eleven, target) > F.APP_END && F.reach(eleven, target) <= 0x95000 && F.reach(eleven, eleven) === F.APP_END);
  assert.throws(() => F.plan(eleven, target), { code: "outside" }, "an older loader cannot write it");
  assert.throws(() => F.plan(eleven, target, F.reach(eleven, target) - 4096), { code: "outside" }, "a window that ends before what changes");
  assert.equal(F.plan(eleven, target, F.reach(eleven, target)).order.length, F.plan(eleven, target, 0x95000).order.length);
  const p = F.plan(eleven, target, 0x95000);
  assert.ok(p.end === 0x95000 && p.order.some(a => a >= F.APP_END && a < 0x95000) && p.order.at(-1) === F.APP && p.windows === 1);
  assert.deepEqual([F.describe(target).kind, F.describe(target).whole, F.describe(target).layout.vm], ["hyperrig", true, 0x95000]);
  assert.ok(W.same(F.restoreTarget(target, eleven, 0x95000), eleven), "the original comes back up to its VM");
  assert.throws(() => F.restoreTarget(target, eleven), { code: "outside" }, "not with a loader that cannot write past APP_END");
  const hello = new Uint8Array(51);
  hello.set(W.ascii("HRS1"));
  W.put(hello, 47, 0x95000, 4);
  assert.deepEqual([W.helloOf(hello).window, W.helloOf(hello.subarray(0, 47)).window], [0x95000, null]);
});

if (ENGINE && assets) {
  test("another original than 011 is not changed", async () => {
    for (const version of ["009", "010", "012"]) {
      const before = stockFlash(version === "009" ? "009" : "011"), pedal = await pedalWith(before), computer = new Computer();
      pedal.version = version;
      const run = computer.program(pedal);
      await run.installer.home();
      assert.deepEqual([run.last().title, run.last().actions], ["This version is not known yet", []], version);
      assert.match(run.last().text, new RegExp(`original firmware ${version}\\. HyperRig is installed from 011`));
      await run.installer.act("install");
      assert.notEqual(run.last().screen, "done");
      assert.ok(W.same(await pedal.flash(), before), "nothing was written");
      assert.equal(computer.files.size, 0);
    }
  });

  for (const version of ["011"]) test(`from the original ${version} to HyperRig, and back`, async () => {
    const before = stockFlash(version), pedal = await pedalWith(before), computer = new Computer();
    const run = await installed(computer, pedal);
    assert.deepEqual(run.screens(), ["ready", "work", "done"], run.lines.join("\n"));
    assert.equal(run.last().pedal, "HyperRig 0.2.0-test");
    assert.deepEqual(run.last().actions.map(a => a.id), ["editor-first", "home"], "after a first install the editor puts the presets to start with");
    assert.ok(!/switch it off/.test(run.last().text), "it came back by itself");
    const progress = run.views.filter(v => v.screen === "work").map(v => v.progress);
    assert.ok(progress.every((p, i) => !i || p >= progress[i - 1] - 1e-9) && progress.length > 60, "the progress only grows");
    const after = await pedal.flash();
    expected(before, after);
    assert.equal(pedal.mode, "hyperrig");
    const backups = [...computer.files.values()];
    assert.equal(backups.length, 1);
    assert.deepEqual([backups[0].about.kind, backups[0].about.version], ["stock", version]);
    const note = [...computer.notes.values()][0];
    assert.deepEqual([note.job, note.state], ["install", "written"]);
    /* the presets of HyperRig, then back to the original */
    const played = after.slice();
    played.fill(0x77, 0xc0000, 0xce000);
    played.fill(0x33, 0xfe000, 0xff000);
    await engine.talk("F", played);
    const again = computer.program(pedal);
    await again.installer.home();
    assert.deepEqual([again.last().title, again.last().actions.map(a => a.id)], ["HyperRig is on your pedal", ["editor", "restore"]]);
    await again.installer.act("restore");
    assert.equal(again.last().title, "The original is back", again.lines.join("\n"));
    const end = await pedal.flash();
    for (const [from, to] of [[0, 0x82000], [0x82000, version === "011" ? 0x95000 : 0x82000], [0xbe000, 0x100000]]) assert.ok(W.same(end.subarray(from, to), before.subarray(from, to)), `${from.toString(16)}`);
    assert.equal(pedal.mode, "stock");
    assert.deepEqual([...computer.files.values()].map(f => f.about.kind), ["stock", "hyperrig"]);
  });

  test("from the original to a HyperRig that uses more room, and back", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), own = { ...assets, image: WIDE };
    const run = await installed(computer, pedal, { own });
    assert.equal(run.last().screen, "done", run.lines.join("\n"));
    const after = await pedal.flash();
    assert.ok(onPedal(after, WIDE, before) && run.lines.some(l => /application up to 95000/.test(l)));
    assert.ok(W.same(after.subarray(0, F.APP), before.subarray(0, F.APP)) && W.same(after.subarray(0xbe000), before.subarray(0xbe000)));
    assert.deepEqual([F.describe(after).kind, F.describe(after).whole], ["hyperrig", true]);
    const again = computer.program(pedal, { own });
    await again.installer.home();
    await again.installer.act("restore");
    assert.equal(again.last().title, "The original is back", again.lines.join("\n"));
    const end = await pedal.flash();
    assert.ok(W.same(end.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(end.subarray(0xbe000), before.subarray(0xbe000)), "the original, up to its VM");
    assert.equal(pedal.mode, "stock");
  });

  /* HyperRig's area for this pedal at the head of its application, and the original's after it, up to its VM. */
  const onPedal = (after, image, before) => {
    const a = F.areaFor(image, before.subarray(F.APP));
    return W.same(after.subarray(F.APP, F.APP + a.length), a) && W.same(after.subarray(F.APP + a.length, 0x95000), before.subarray(F.APP + a.length, 0x95000));
  };
  /* A pedal that has HyperRig with a loader before 022, its presets on it; this program's HyperRig needs more room. */
  async function olderWithPresets(computer) {
    const before = stockFlash(), pedal = await pedalWith(before);
    await installed(computer, pedal);
    pedal.set.old = true;
    const played = await pedal.flash();
    played.fill(0x77, 0xc0000, 0xce000);
    played.fill(0x33, 0xfe000, 0xff000);
    await engine.talk("F", played);
    pedal.set.hrid = "HRID 1 0.5.0 0123456789abcdef banks=3";
    return { before, pedal, played };
  }
  const WIDE_ASSETS = { image: WIDE, version: "0.6.0", build: "ffff456789abcdef" };
  async function upgraded(pedal, before, played, computer, run) {
    assert.equal(run.last().screen, "done", run.lines.slice(-6).join("\n"));
    assert.equal(run.last().title, "HyperRig is on your pedal");
    const after = await pedal.flash();
    assert.ok(W.same(after.subarray(F.USER, F.USER_END), played.subarray(F.USER, F.USER_END)), "the presets, captures and IRs stay");
    assert.ok(onPedal(after, WIDE, before));
    assert.ok(W.same(after.subarray(0, F.APP), before.subarray(0, F.APP)) && W.same(after.subarray(0xbe000, F.USER), before.subarray(0xbe000, F.USER)) && W.same(after.subarray(F.USER_END), before.subarray(F.USER_END)));
    assert.equal(pedal.set.old, false, "the pedal has the new loader");
    const note = [...computer.notes.values()][0];
    assert.deepEqual([note.job, note.state], ["upgrade", "written"]);
  }

  test("an update that needs the new loader goes through the original once; the presets stay", async () => {
    const computer = new Computer(), { before, pedal, played } = await olderWithPresets(computer);
    const run = computer.program(pedal, { own: { ...assets, ...WIDE_ASSETS } });
    await run.installer.home();
    assert.deepEqual([run.last().title, run.last().actions[0].label], ["An update is ready", "Update HyperRig"]);
    assert.match(run.last().actions[0].ask.text, /original firmware comes back for a moment/);
    pedal.set.hrid = "HRID 1 0.6.0 ffff456789abcdef banks=3";
    await run.installer.act("install");
    await upgraded(pedal, before, played, computer, run);
    assert.ok(run.lines.some(l => /the original comes back for a moment/.test(l)) && pedal.log.includes("stock"), run.lines.join("\n"));
    assert.ok(run.views.some(v => v.title === "Putting the original back for a moment") && run.views.some(v => v.over === "Updating"));
    /* the next update is a plain one */
    const next = computer.program(pedal, { own: { ...assets, ...WIDE_ASSETS, version: "0.6.1", build: "eeee456789abcdef" } });
    await next.installer.home();
    assert.doesNotMatch(next.last().actions[0].ask.text, /original/);
  });

  test("an update through the original that the original does not take: it says so, and Install goes on with the presets", async () => {
    const computer = new Computer(), { before, pedal, played } = await olderWithPresets(computer);
    const run = computer.program(pedal, { own: { ...assets, ...WIDE_ASSETS } });
    await run.installer.home();
    pedal.set.hrid = "HRID 1 0.6.0 ffff456789abcdef banks=3";
    pedal.faults.refuse = true;                       // the original's update service does not take the new loader
    await run.installer.act("install");
    assert.deepEqual([run.last().screen, run.last().title], ["trouble", V.TROUBLE.refused[0]], run.lines.join("\n"));
    assert.match(run.last().safe, /original firmware for the moment.*presets are in the copy on this computer/);
    assert.equal(pedal.mode, "stock");
    assert.deepEqual([[...computer.notes.values()][0].job, [...computer.notes.values()][0].state], ["upgrade", "original"]);
    pedal.faults.refuse = false;
    await run.installer.act("again");
    assert.equal(run.last().title, "Ready for HyperRig");
    await run.installer.act("install");
    await upgraded(pedal, before, played, computer, run);
    /* the same, with the program closed in between: another start of it goes on as well */
    const second = new Computer(), older = await olderWithPresets(second), first = second.program(older.pedal, { own: { ...assets, ...WIDE_ASSETS } });
    await first.installer.home();
    older.pedal.set.hrid = "HRID 1 0.6.0 ffff456789abcdef banks=3";
    older.pedal.faults.refuse = true;
    await first.installer.act("install");
    older.pedal.faults.refuse = false;
    const later = second.program(older.pedal, { own: { ...assets, ...WIDE_ASSETS } });
    await later.installer.home();
    await later.installer.act("install");
    await upgraded(older.pedal, older.before, older.played, second, later);
  });

  test("an update through the original without the copies on this computer: nothing is changed", async () => {
    const computer = new Computer(), { pedal, played } = await olderWithPresets(computer);
    for (const k of [...computer.files.keys()]) if (computer.files.get(k).about.kind === "stock") computer.files.delete(k);
    const run = computer.program(pedal, { own: { ...assets, ...WIDE_ASSETS } });
    await run.installer.home();
    await run.installer.act("install");
    assert.deepEqual([run.last().screen, run.last().title], ["trouble", V.TROUBLE.through[0]], run.lines.join("\n"));
    assert.match(run.last().safe, /Nothing was changed/);
    assert.ok(W.same(await pedal.flash(), played));
  });

  test("an update through the original, the power gone in either loader: it goes on, and the presets stay", async () => {
    let cuts = 0;
    for (const [session, at] of [[1, 1], [1, 1100], [1, 2250], [2, 1], [2, 1300], [2, 2550]]) {
      const computer = new Computer(), { before, pedal, played } = await olderWithPresets(computer);
      const run = computer.program(pedal, { own: { ...assets, ...WIDE_ASSETS } });
      await run.installer.home();
      pedal.set.hrid = "HRID 1 0.6.0 ffff456789abcdef banks=3";
      pedal.set.cutIn = [pedal.loaderStarts + session, at];
      pedal.cut = false;
      await run.installer.act("install");
      pedal.set.cutIn = null;
      if (!pedal.cut) { await upgraded(pedal, before, played, computer, run); continue; }
      assert.equal(run.last().screen, "trouble", `${session} ${at}`);
      cuts++;
      await pedal.powerCycle();
      assert.equal(pedal.mode, "loader", `${session} ${at}: the pedal is ${pedal.mode}`);
      const later = computer.program(pedal, { own: { ...assets, ...WIDE_ASSETS } });
      await later.installer.home();
      assert.deepEqual([later.last().screen, later.last().actions[0].id], ["resume", "continue"], `${session} ${at}`);
      assert.match(later.last().text, /finish updating HyperRig/);
      await later.installer.act("continue");
      await upgraded(pedal, before, played, computer, later);
    }
    assert.equal(cuts, 6, "every one of them was cut");
  });

  test("a pedal with a newer HyperRig is not offered an older one", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer();
    await installed(computer, pedal);
    for (const [there, here, title, labels] of [["0.3.0", "0.2.0", "Your pedal is ahead of this program", ["Open the editor", "Restore the original"]],
      ["0.2.0", "0.2.0-dev.6", "Your pedal is ahead of this program", ["Open the editor", "Restore the original"]],
      ["0.2.0-dev.6", "0.2.0", "An update is ready", ["Update HyperRig", "Open the editor", "Restore the original"]],
      ["0.2.0", "0.2.0", "An update is ready", ["Update HyperRig", "Open the editor", "Restore the original"]],
      ["odd", "0.2.0", "An update is ready", ["Update HyperRig", "Open the editor", "Restore the original"]]]) {
      pedal.set.hrid = `HRID 1 ${there} aaaa456789abcdef banks=3`;
      const run = computer.program(pedal, { own: { ...assets, version: here, build: "ffff456789abcdef" } });
      await run.installer.home();
      assert.deepEqual([run.last().title, run.last().actions.map(a => a.label)], [title, labels], there + " " + here);
    }
    assert.deepEqual([["0.2.0-dev.2", "0.2.0-dev.12"], ["0.2.0", "0.2.0-beta.1"], ["1.0.0", "0.9.9"], ["0.2", "0.2.0"]].map(([a, b]) => order(a, b)), [-1, 1, 1, null]);
  });
  test("an update keeps the presets; the same build is not written again", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer();
    await installed(computer, pedal);
    const played = await pedal.flash();
    played.fill(0x77, 0xc0000, 0xce000);
    await engine.talk("F", played);
    const image = area({ text: "HyperRig auth", size: 0x76000 });
    const run = computer.program(pedal, { own: { ...assets, image, version: "0.3.0", build: "ffff456789abcdef" } });
    await run.installer.home();
    assert.deepEqual([run.last().title, run.last().actions[0].label], ["An update is ready", "Update HyperRig"]);
    pedal.set.hrid = "HRID 1 0.3.0 ffff456789abcdef banks=3";
    await run.installer.act("install");
    assert.equal(run.last().screen, "done", run.lines.join("\n"));
    const after = await pedal.flash();
    assert.ok(W.same(after.subarray(F.USER), played.subarray(F.USER)) && W.same(after.subarray(F.APP, F.APP_END), F.areaFor(image, before.subarray(F.APP))));
    const count = (await engine.talk("O"))[0];
    await run.installer.home();
    await run.installer.act("install");
    assert.equal(run.last().screen, "done");
    const state = await engine.talk("O");
    assert.equal(state[0] | state[1] << 8, 0, "nothing was erased or programmed");
    assert.ok(count > 0);
  });

  test("a HyperRig that is a MIDI device too is known by its serial port, updated, and gives the original back", async () => {
    for (const midi of ["Tank-M HyperRig", "USB-Midi"]) {
      const before = stockFlash(), pedal = await pedalWith(before, { midi }), computer = new Computer();
      const first = await installed(computer, pedal);
      assert.equal(first.last().screen, "done", first.lines.join("\n"));
      const image = area({ text: "HyperRig auth", size: 0x76000 }), run = computer.program(pedal, { own: { ...assets, image, version: "0.3.0", build: "ffff456789abcdef" } });
      await run.installer.home();
      assert.deepEqual([run.last().title, run.last().actions.map(a => a.id)], ["An update is ready", ["install", "editor", "restore"]], run.lines.join("\n"));
      pedal.set.hrid = "HRID 1 0.3.0 ffff456789abcdef banks=3";
      await run.installer.act("install");
      assert.equal(run.last().screen, "done", run.lines.join("\n"));
      assert.ok(W.same((await pedal.flash()).subarray(F.APP, F.APP_END), F.areaFor(image, before.subarray(F.APP))));
      await run.installer.home();
      await run.installer.act("restore");
      assert.equal(run.last().title, "The original is back", run.lines.join("\n"));
      assert.equal(pedal.mode, "stock");
    }
  });

  for (const [name, fault] of Object.entries({ "to the pedal are lost": { loseEvery: 43 }, "from the pedal are lost": { loseTo: 43 }, "from the pedal come twice": { doubleEvery: 5 }, "from the pedal are damaged": { damageEvery: 43 } }))
    test(`messages ${name}, in the loader`, async () => {
      const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
      await run.installer.home();
      /* from the moment the loader runs */
      const power = pedal.power.bind(pedal);
      pedal.power = async request => { await power(request); Object.assign(pedal.faults, pedal.mode === "loader" ? fault : { loseEvery: 0, loseTo: 0, doubleEvery: 0, damageEvery: 0 }); };
      await run.installer.act("install");
      assert.equal(run.last().screen, "done", run.lines.slice(-3).join("\n"));
      expected(before, await pedal.flash());
    });

  test("the cable is pulled at any message, and it goes on from there", async () => {
    for (const at of [1, 2, 3, 5, 20, 46, 60, 300, 1200, 1300, 1400, 1500, 1800, 1900]) {
      const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
      await run.installer.home();
      pedal.taken = 0;
      pedal.faults.pullAt = at;
      await run.installer.act("install");
      if (pedal.plugged) { assert.ok(at > 1700 && run.last().screen === "done", `at ${at} of ${pedal.taken}`); continue; }
      assert.deepEqual([run.last().screen, run.last().title.includes("HyperRig")], ["trouble", false], `at ${at}`);
      const open = F.bootDecision(await pedal.flash()).outcome !== "application";
      assert.equal(/waits in update mode/.test(run.last().safe), open || run.installer.changed, `at ${at}`);
      if (pedal.mode === "stock") pedal.update = null;
      pedal.plug();
      await run.installer.home();
      const offered = run.last().actions.map(a => a.id);
      assert.ok(offered.includes(open ? "continue" : "install"), `at ${at}: ${offered} in ${pedal.mode}`);
      await run.installer.act(open ? "continue" : "install");
      assert.equal(run.last().screen, "done", `at ${at}: ${run.lines.slice(-4).join("\n")}`);
      expected(before, await pedal.flash());
    }
  });

  test("the power goes at flash operations all along; the pedal comes back and the job is finished, or undone", async () => {
    for (const [n, at] of [1, 2, 3, 17, 18, 19, 200, 1000, 1500, 2000, 2080, 2090, 2095, 2100, 2110].entries()) {
      const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
      await run.installer.home();
      await pedal.cutAt(at);
      pedal.cut = false;
      await run.installer.act("install");
      if (!pedal.cut) { assert.equal(run.last().screen, "done"); assert.ok(at > 1500, `only ${at} operations`); continue; }
      assert.equal(run.last().screen, "trouble", `at ${at}`);
      const left = await pedal.flash();
      assert.ok(W.same(left.subarray(0, 0x4000), before.subarray(0, 0x4000)) && W.same(left.subarray(0xbe000), before.subarray(0xbe000)));
      await pedal.powerCycle();
      assert.equal(pedal.mode, "loader", `at ${at}: the pedal is ${pedal.mode}`);
      /* the program was closed meanwhile */
      const later = computer.program(pedal);
      await later.installer.home();
      assert.deepEqual([later.last().screen, later.last().actions[0].id], ["resume", "continue"]);
      if (n % 2) {
        const note = [...computer.notes.entries()][0];
        computer.notes.set(note[0], { ...note[1], job: "restore" });            // the person wants the original after all
      }
      await later.installer.home();
      await later.installer.act("continue");
      assert.equal(later.last().screen, "done", `at ${at}: ${later.lines.slice(-4).join("\n")}`);
      const end = await pedal.flash();
      if (n % 2) { assert.ok(W.same(end.subarray(F.APP, 0x95000), before.subarray(F.APP, 0x95000)) && W.same(end.subarray(0xbe000), before.subarray(0xbe000))); assert.equal(pedal.mode, "stock"); }
      else expected(before, end);
      assert.equal([...computer.files.values()].length, 1, "one backup, the original");
    }
  });

  test("the program is closed while it writes, and opened again", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
    await run.installer.home();
    pedal.taken = 0;
    pedal.faults.pullAt = 1600;
    await run.installer.act("install");
    pedal.plug();
    assert.equal(pedal.mode, "loader", "only the cable was pulled");
    const later = computer.program(pedal);
    await later.installer.home();
    assert.equal(later.last().screen, "resume");
    await later.installer.act("continue");
    assert.equal(later.last().screen, "done", later.lines.join("\n"));
    expected(before, await pedal.flash());
  });

  test("the pedal does not take the loader, or stops half way: nothing was changed", async () => {
    for (const [fault, kind] of [[{ refuse: true }, "refused"], [{ stopAfter: 2 }, "refused"], [{ stopAfter: 20 }, "refused"]]) {
      const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
      await run.installer.home();
      Object.assign(pedal.faults, fault);
      await run.installer.act("install");
      assert.deepEqual([run.last().screen, run.last().title], ["trouble", V.TROUBLE[kind][0]]);
      assert.match(run.last().safe, /Nothing was changed/);
      assert.ok(W.same(await pedal.flash(), before) && pedal.mode === "stock");
      assert.equal(computer.files.size, 0);
    }
  });

  test("without a way back nothing is written, and the pedal goes back to its firmware", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
    await run.installer.home();
    const power = pedal.power.bind(pedal);
    pedal.power = async request => {
      if (request !== null && request !== undefined) { const f = await pedal.flash(); f[0xbcf06] ^= 1; await engine.talk("F", f); }
      await power(request);
    };
    await run.installer.act("install");
    assert.equal(run.last().title, V.TROUBLE.noway[0], run.lines.join("\n"));
    const after = await pedal.flash();
    assert.ok(W.same(after.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(after.subarray(0xbe000), before.subarray(0xbe000)));
    await pedal.work;
    await new Promise(done => setTimeout(done, 120));
    assert.equal(pedal.mode, "stock");
  });

  test("an older update record that would be found first is made void", async () => {
    const before = stockFlash();
    stored(before, random("an old loader", 900), { place: 0xb0000, record: 0xbdf00, name: "ota-TANK MINI_007" });
    const pedal = await pedalWith(before), computer = new Computer(), run = await installed(computer, pedal);
    assert.equal(run.last().screen, "done", run.lines.join("\n"));
    const after = await pedal.flash();
    assert.deepEqual([...after.subarray(0xbdf06, 0xbdf08)], [0, 0]);
    expected(before, after);
    assert.equal(F.bootDecision(F.withoutApplication(after)).outcome, "loader");
  });

  test("a full disk, a disk that lies, a damaged copy of the program", async () => {
    for (const [spoil, kind, own] of [[c => { c.full = true; }, "disk"], [c => { c.bad = true; }, "disk"], [() => {}, "damaged", { ...assets, image: (() => { const b = HYPERRIG.slice(); b[0x6000] ^= 1; return b; })() }]]) {
      const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer();
      spoil(computer);
      const run = await installed(computer, pedal, { own: own || assets });
      assert.equal(run.last().title, V.TROUBLE[kind][0], run.lines.join("\n"));
      const after = await pedal.flash();
      assert.ok(W.same(after.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(after.subarray(0xbe000), before.subarray(0xbe000)));
      await new Promise(done => setTimeout(done, 120));
      assert.equal(pedal.mode, "stock");
    }
  });

  test("another computer: no backup there", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
    await run.installer.home();
    await pedal.cutAt(900);
    await run.installer.act("install");
    await pedal.powerCycle();
    const other = new Computer().program(pedal);
    await other.installer.home();
    assert.equal(other.last().screen, "resume");
    await other.installer.act("continue");
    assert.equal(other.last().title, V.TROUBLE.elsewhere[0]);
    assert.equal(pedal.mode, "loader");
    /* and restoring there, with HyperRig whole on the pedal */
    const pedal2 = await pedalWith(stockFlash()), first = new Computer();
    await installed(first, pedal2);
    const second = new Computer().program(pedal2);
    await second.installer.home();
    await second.installer.act("restore");
    assert.equal(second.last().title, V.TROUBLE.backup[0], second.lines.join("\n"));
    await new Promise(done => setTimeout(done, 150));
    assert.equal(pedal2.mode, "hyperrig", "it went back by itself");
  });

  test("two pedals keep their own backups and notes", async () => {
    const computer = new Computer();
    for (const unit of [1, 2]) { const pedal = await pedalWith(stockFlash("011", unit)); await installed(computer, pedal); }
    assert.equal(computer.notes.size, 2);
    assert.equal(new Set([...computer.files.keys()].map(k => k.split("/")[0])).size, 2);
  });

  test("only a copy: nothing but the loader in the settings store is written, and the pedal goes on as it was", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
    await run.installer.home();
    assert.deepEqual(run.last().actions.map(a => a.id), ["install", "save"]);
    await run.installer.act("save");
    assert.equal(run.last().title, "Your pedal is saved", run.lines.join("\n"));
    const after = await pedal.flash(), state = await engine.talk("O");
    assert.equal(state[0] | state[1] << 8, 0, "the loader erased and programmed nothing");
    assert.ok(W.same(after.subarray(0, 0x95000), before.subarray(0, 0x95000)) && W.same(after.subarray(0xbe000), before.subarray(0xbe000)));
    assert.equal(pedal.mode, "stock");
    const copy = [...computer.files.values()];
    assert.deepEqual([copy.length, copy[0].about.kind], [1, "stock"]);
    assert.ok(W.same(copy[0].bytes, after));
    assert.equal(computer.notes.size, 0);
    assert.ok(run.lines.some(l => l.includes('way back: {"ok":true')), "the log says whether there is a way back");
    const progress = run.views.filter(v => v.screen === "work").map(v => v.progress);
    assert.ok(progress.every((p, i) => !i || p >= progress[i - 1] - 1e-9) && progress.at(-1) > 0.9);
  });

  test("the loader under whatever name the system gives its port", async () => {
    for (const name of ["USB Audio Device", "USB-Midi", "TANK-MINI"]) {
      const before = stockFlash(), pedal = await pedalWith(before, { loaderName: name }), computer = new Computer(), run = await installed(computer, pedal);
      assert.equal(run.last().screen, "done", `${name}: ${run.lines.slice(-3).join("\n")}`);
      expected(before, await pedal.flash());
    }
  });

  test("the loader's port changes between finding and opening it", async () => {
    for (const times of [1, 2]) {
      const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal), open = pedal.open.bind(pedal);
      let left = times;
      pedal.open = async id => {
        if (pedal.mode === "loader" && left > 0) { left--; pedal.serial++; }       // the port comes back under another number
        return open(id);
      };
      await run.installer.home();
      await run.installer.act("save");
      assert.equal(run.last().title, "Your pedal is saved", run.lines.slice(-4).join("\n"));
      assert.equal(pedal.mode, "stock");
    }
  });

  test("a loader that waits, and leaving it alone", async () => {
    const before = stockFlash(), pedal = await pedalWith(before), computer = new Computer(), run = computer.program(pedal);
    await run.installer.home();
    const s = run.installer.situation;
    await run.installer.enter(s, () => {});
    await run.installer.home();
    assert.deepEqual([run.last().title, run.last().actions.map(a => a.id)], ["Your pedal waits", ["install", "save", "leave"]]);
    await run.installer.act("leave");
    await new Promise(done => setTimeout(done, 150));
    assert.equal(pedal.mode, "stock");
    const after = await pedal.flash();
    assert.ok(W.same(after.subarray(0, 0x95000), before.subarray(0, 0x95000)));
  });

  test("what is connected, as it comes and goes", async () => {
    const pedal = await pedalWith(stockFlash()), computer = new Computer(), run = computer.program(pedal);
    pedal.plugged = false;
    const watching = run.installer.watch();
    const until = async right => { for (let i = 0; i < 300 && !right(); i++) await new Promise(done => setTimeout(done, 10)); assert.ok(right(), JSON.stringify(run.last())); };
    await until(() => run.last() && run.last().screen === "search");
    pedal.plug();
    await until(() => run.last().title === "Ready for HyperRig" && run.last().pedal === "Original 011");
    pedal.pull();
    await until(() => run.last().screen === "search");
    pedal.mode = "updater";
    pedal.plug();
    await until(() => run.last().title === "M-Upgrade is at work");
    pedal.pull();
    pedal.mode = "stock";
    pedal.version = "012";
    pedal.plug();
    await until(() => run.last().title === "This version is not known yet" && !run.last().actions.length);
    pedal.pull();
    pedal.mode = "hyperrig";
    pedal.set.stage = false;
    pedal.plug();
    await until(() => run.last().title === "HyperRig is on your pedal" && !run.last().actions.some(a => a.id === "restore"));
    run.installer.stopped = true;
    await watching;
  });

  test("a port in use by another program", async () => {
    const pedal = await pedalWith(stockFlash()), computer = new Computer(), run = computer.program(pedal);
    await run.installer.home();
    pedal.set.taken = true;
    await run.installer.act("install");
    assert.equal(run.last().screen, "trouble");
    assert.match(run.last().safe, /Nothing was changed/);
  });
}

(async () => {
  if (ENGINE) engine = new Engine(ENGINE);
  let failed = 0;
  for (const [name, body] of tests) {
    if (ONLY && !name.includes(ONLY)) continue;
    const start = Date.now();
    try { await body(); console.log(`ok   ${name} (${Date.now() - start} ms)`); } catch (e) { failed++; console.log(`FAIL ${name}\n${e && e.stack || e}`); }
  }
  if (engine) engine.close();
  console.log(failed ? `${failed} of ${tests.length} failed` : `${tests.length} tests passed${ENGINE ? "" : " (without the engine)"}`);
  process.exit(failed ? 1 : 0);
})();
