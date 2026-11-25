/* A TANK-MINI for the installer's tests and checks: the stock firmware's update service, the bootloader's decision, the loader
 * with its real engine (or its messages, when no engine is given), and HyperRig's console. Its cable can be pulled, its messages
 * lost, doubled or damaged, and its power can go at a chosen flash operation. No device is opened. */
"use strict";
const { spawn } = require("node:child_process");
const path = require("node:path");
const W = require("./wire.js"), F = require("./flash.js");
const ROOT = path.resolve(__dirname, "../..");

/* The engine behind a pipe (firmware/mini_stage/host_server.c). */
class Engine {
  constructor(binary) {
    const command = process.platform === "win32" ? ["wsl.exe", "--distribution", "Ubuntu", "--exec", binary] : [path.join(ROOT, binary)];
    this.process = spawn(command[0], command.slice(1), { cwd: ROOT, stdio: ["pipe", "pipe", "inherit"], windowsHide: true });
    this.have = [];
    this.size = 0;
    this.waiting = [];
    this.process.stdout.on("data", data => { this.have.push(data); this.size += data.length; this.deliver(); });
    this.process.on("exit", () => { for (const w of this.waiting.splice(0)) w.fail(new Error("the engine ended")); });
  }
  deliver() {
    while (this.waiting.length && this.size >= 5) {
      let all = this.have.length === 1 ? this.have[0] : Buffer.concat(this.have);
      this.have = [all];
      const n = all.readUInt32LE(1);
      if (all.length < 5 + n) return;
      const answer = new Uint8Array(all.subarray(5, 5 + n));
      all = all.subarray(5 + n);
      this.have = all.length ? [all] : [];
      this.size = all.length;
      this.waiting.shift().done(answer);
    }
  }
  talk(kind, data = new Uint8Array(0)) {
    return new Promise((done, fail) => {
      this.waiting.push({ done, fail });
      const head = Buffer.alloc(5);
      head.write(kind, 0, "latin1");
      head.writeUInt32LE(data.length, 1);
      this.process.stdin.write(Buffer.concat([head, Buffer.from(data.buffer, data.byteOffset, data.length)]));
    });
  }
  close() { this.process.stdin.end(); }
}

const le = (v, n) => { const b = new Uint8Array(n); W.put(b, 0, v, n); return b; };

/* What the stock firmware leaves for its bootloader. */
function stored(flash, stream, { place = 0xb7000, record = 0xbcf00, name = "ota-TANK MINI_011" } = {}) {
  const head = new Uint8Array(32);
  W.put(head, 2, 0xffff, 2); W.put(head, 4, place, 4); W.put(head, 8, stream.length, 4);
  head.set([0x41, 0xff, 0xff, 0xff], 12);
  head.set(W.ascii("LOADER.BIN"), 16);
  W.put(head, 0, W.crc16(head.subarray(2)), 2);
  const body = new Uint8Array(80);
  W.put(body, 2, 0x5a0d, 2); W.put(body, 4, 0x5a01, 2); W.put(body, 6, 0x5441, 2);
  body.set(W.ascii(name), 8);
  W.put(body, 72, place, 4);
  W.put(body, 0, W.crc16(body.subarray(2)), 2);
  flash.fill(0xff, place, place + Math.ceil(stream.length / 4096) * 4096);
  flash.fill(0xff, record & ~4095, (record & ~4095) + 4096);
  flash.set(head, place);
  flash.set(stream.subarray(32), place + 32);
  flash.set(body, record);
}

class SimulatedPedal {
  /* engine: Engine; flash: the whole flash; options of the simulation in `set`. */
  constructor(engine, flash, set = {}) {
    this.engine = engine;
    this.set = { restart: 30, where: {}, hrid: null, stage: true, ...set };
    this.mode = "off";
    this.plugged = true;
    this.links = new Set();
    this.serial = 0;
    this.sent = 0;
    this.taken = 0;
    this.faults = { pullAt: 0, loseEvery: 0, loseTo: 0, doubleEvery: 0, damageEvery: 0, refuse: false, stopAfter: 0, mute: false };
    this.log = [];
    this.flash0 = flash;
    this.work = Promise.resolve();
  }
  async start() { await this.engine.talk("F", this.flash0); await this.engine.talk("X", le(0, 4)); await this.power(); return this; }
  flash() { return this.engine.talk("G"); }
  async cutAt(n) { await this.engine.talk("X", le(n, 4)); }

  /* The power comes: what the bootloader finds decides. */
  async power(request = null) {
    const flash = await this.flash();
    let outcome = F.bootDecision(flash), code = outcome.code;
    if (request !== null) { const c = F.storedCode(flash, request); if (c) { outcome = { outcome: "loader" }; code = c; } }
    this.version = null;
    this.serial++;              // the port comes back under another number, before anything can be seen on it
    if (outcome.outcome === "application") {
      const is = F.describe(flash);
      this.mode = is.kind === "stock" ? "stock" : is.kind === "hyperrig" ? "hyperrig" : "silent";
      this.version = is.version;
      if (!is.whole) this.mode = "silent";
    } else if (outcome.outcome === "loader") {
      this.mode = "loader";
      this.code = code;
      await this.engine.talk("P", Uint8Array.of(F.bootDecision(flash).outcome === "application" ? 1 : 0));
    } else this.mode = outcome.outcome === "download mode" ? "download" : "dead";
    this.log.push(this.mode);
  }
  /* The pedal goes away and comes back, after a moment. */
  restart(request = null) {
    this.vanish();
    this.mode = "off";
    this.work = this.work.then(() => new Promise(done => setTimeout(done, this.set.restart))).then(() => this.power(request));
    return this.work;
  }
  vanish() { for (const l of [...this.links]) { l.closed = true; if (l.ongone) l.ongone(); } this.links.clear(); }
  pull() { this.plugged = false; this.vanish(); }
  plug() { this.plugged = true; this.serial++; }
  async unplugged(ms) { this.pull(); await new Promise(done => setTimeout(done, ms)); this.plug(); }
  async powerCycle() { this.vanish(); await this.engine.talk("X", le(0, 4)); await this.power(); }

  /* ---- USB ---- */
  ports() {
    if (!this.plugged) return [];
    if (this.mode === "stock") return [{ id: `p${this.serial}`, name: "USB-Midi" }];
    if (this.mode === "loader") return [{ id: `p${this.serial}`, name: this.set.loaderName || "HyperRig Update" }];
    if (this.mode === "updater") return [{ id: `p${this.serial}`, name: "USB-Midi" }];
    if (this.mode === "hyperrig" && this.set.midi) return [{ id: `p${this.serial}`, name: this.set.midi }];      // its own MIDI port, which answers nothing
    return [];
  }
  async open(id) {
    if (!this.ports().some(p => p.id === id)) throw Object.assign(new Error("no such port"), { name: "NotFoundError", code: "gone" });
    if (this.set.taken) throw Object.assign(new Error("in use"), { name: "InvalidAccessError" });
    const link = { onmessage: null, ongone: null, closed: false, send: bytes => { if (link.closed) throw new Error("closed"); this.receive(link, Uint8Array.from(bytes)); },
      close: () => { link.closed = true; this.links.delete(link); } };
    this.links.add(link);
    return link;
  }
  deliver(link, message) {
    this.sent++;
    const f = this.faults;
    if (f.loseTo && this.sent % f.loseTo === 0) return;
    if (f.damageEvery && this.sent % f.damageEvery === 0) { message = message.slice(); message[Math.floor(message.length / 2)] ^= 1; }
    const times = f.doubleEvery && this.sent % f.doubleEvery === 0 ? 2 : 1;
    for (let i = 0; i < times; i++) setImmediate(() => { if (!link.closed && link.onmessage) link.onmessage(message); });
  }
  receive(link, message) {
    this.taken++;
    const f = this.faults;
    if (f.pullAt && this.taken >= f.pullAt) { f.pullAt = 0; this.pull(); return; }
    if (f.mute || f.loseEvery && this.taken % f.loseEvery === 0) return;
    this.work = this.work.then(() => this.act(link, message)).catch(e => { this.log.push("error " + e.message); });
  }
  async act(link, message) {
    if (link.closed) return;
    if (this.mode === "stock" || this.mode === "updater") return this.stock(link, message);
    if (this.mode === "loader") return this.loader(link, message);
  }
  /* ---- the stock firmware ---- */
  async stock(link, message) {
    const name = (this.mode === "updater" ? "ota-TANK MINI_" : "TANK MINI_") + (this.version || "011"), f = W.stockParse(message);
    if (f && f.command === W.IDENTITY) { const b = new Uint8Array(27); b.set(W.ascii(name)); this.deliver(link, W.stockFrame(W.IDENTITY, b)); return; }
    if (W.same(message, W.ENTER) && this.mode === "stock" && !this.update) {
      if (this.faults.refuse) return;
      this.update = { step: 0, parts: [], blocks: [[0, 512], [512, 512], [1024, 512]], next: 0, expect: null };
      setTimeout(() => this.request(link), 5);
      return;
    }
    const r = W.packageRequest(shorten(message));
    if (r && this.update && this.update.expect && r.address === this.update.expect[0] && r.length === this.update.expect[1]) {
      const body = f.body.subarray(8);
      if (body.length !== r.length) return;
      const u = this.update;
      u.expect = null;
      if (r.address === W.FINISHED) {
        this.update = null;
        if (W.same(body, W.SUCCESS) || u.tries >= 4) return void this.restart(u.place);
        u.tries++;
        this.update = u;
        return this.ask(link, [W.FINISHED, 8]);
      }
      u.parts[r.address] = body.slice();
      u.next++;
      this.request(link);
    }
  }
  ask(link, block) {
    this.update.expect = block;
    const b = new Uint8Array(8);
    W.put(b, 1, block[0], 4);
    W.put(b, 5, block[1], 3);
    this.deliver(link, W.stockFrame(W.PACKAGE, b));
  }
  request(link) {
    const u = this.update;
    if (!u || this.faults.stopAfter && u.next >= this.faults.stopAfter) return;
    if (u.next === 3 && u.blocks.length === 3) {
      /* the list names one file, ota.bin; its record names the loader */
      const head = W.enc(u.parts[0].subarray(0, 64), 0xffff), entry = W.enc(u.parts[0].subarray(64, 144), 0xffff);
      const ok = W.crc16(head.subarray(2)) === W.u16(head, 0) && W.u16(head, 8) === 1 && String.fromCharCode(...entry.subarray(64, 71)) === "ota.bin";
      const record = u.parts[1024].subarray(0, 32), name = String.fromCharCode(...record.subarray(16, 31));
      if (!ok || W.crc16(record.subarray(2)) !== W.u16(record, 0) || name !== "usb_hid_ota.bin") { this.update = null; return; }
      u.size = W.u32(record, 8);
      u.first = W.u32(entry, 8) + W.u32(record, 4);
      for (let at = 0; at < u.size; at += 512) u.blocks.push([u.first + at, Math.min(512, u.size - at)]);
      u.crc = W.u16(record, 2);
    }
    if (u.next < u.blocks.length) return this.ask(link, u.blocks[u.next]);
    if (u.expect) return;
    (async () => {
      const body = W.join(...u.blocks.slice(3).map(([a]) => u.parts[a]));
      if (W.crc16(body) !== u.crc) { this.update = null; return; }
      const flash = await this.flash();
      u.place = this.set.where.place || 0xb7000;
      stored(flash, W.join(new Uint8Array(32), body), { place: u.place, record: this.set.where.record || 0xbcf00, name: "ota-TANK MINI_" + this.version });
      await this.engine.talk("F", flash);
      u.tries = 0;
      this.ask(link, [W.FINISHED, 8]);
    })();
  }
  /* ---- the loader ---- */
  async loader(link, message) {
    const r = W.loaderParse(message);
    if (!r) return;
    const raw = new Uint8Array(12 + r.body.length);
    raw.set([0x48, 0x52, 1, r.op]);
    W.put(raw, 4, r.sequence, 2); W.put(raw, 6, r.body.length, 2);
    raw.set(r.body, 8);
    W.put(raw, 8 + r.body.length, W.crc32(raw.subarray(0, 8 + r.body.length)), 4);
    const reply = await this.engine.talk("M", raw), state = await this.engine.talk("O");
    if (reply.length) {
      const n = W.u16(reply, 6);
      this.deliver(link, W.loaderFrame(reply[3], W.u16(reply, 4), reply.subarray(8, 8 + n)));
    }
    if (state[4]) { this.cut = true; this.vanish(); this.mode = "off"; this.log.push("cut"); return; }        // the power is gone
    if (state[5]) this.leave(state[5]);
  }
  leave(how) {
    this.log.push("leave " + how);
    if (how === 2) { setTimeout(() => { this.vanish(); this.mode = "download"; }, 5); return; }
    setTimeout(() => this.restart(), 5);
  }
  /* ---- HyperRig's console ---- */
  console() {
    const ask = async line => {
        if (!this.plugged || this.mode !== "hyperrig") return null;
        this.log.push("> " + line);
        if (line === "HRID") return this.set.hrid;
        if (!this.set.stage) return null;
        const found = F.bootDecision(F.withoutApplication(await this.flash()));
        if (line === "STAGE") return found.outcome === "loader" ? `STAGE 1 ${found.record.toString(16)}` : "STAGE 0";
        if (line === "STAGE GO") {
          if (found.outcome !== "loader") return "STAGE ERR";
          setTimeout(() => this.restart(found.place), 5);
          return "STAGE GO";
        }
        return null;
      };
    return { present: async () => this.plugged && this.mode === "hyperrig", ask, talk: async task => task(ask) };
  }
}
/* An answer of the host carries the request's eight bytes first. */
function shorten(message) {
  const f = W.stockParse(message);
  return f && f.command === W.PACKAGE && f.body.length >= 8 ? W.stockFrame(W.PACKAGE, f.body.slice(0, 8)) : message;
}

module.exports = { Engine, SimulatedPedal, stored };
