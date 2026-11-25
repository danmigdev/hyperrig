/* The two things the installer talks to over USB MIDI: the stock firmware's update service, which is given HyperRig's loader,
 * and that loader. A link is { send(bytes), onmessage, close() }, one whole SysEx message at a time. For the page and for node. */
"use strict";
(function (root) {
  const node = typeof module === "object" && module.exports;
  const W = node ? require("./wire.js") : root.HrWire, F = node ? require("./flash.js") : root.HrFlash;
  class PedalError extends Error { constructor(code, text) { super(text || code); this.code = code; } }
  const wait = ms => new Promise(done => setTimeout(done, ms));

  /* The messages of a link, one after the other, each once. */
  class Inbox {
    constructor(link) {
      this.link = link;
      this.kept = [];
      this.waiting = null;
      this.gone = false;
      link.onmessage = message => { if (this.waiting) { const w = this.waiting; this.waiting = null; w(message); } else if (this.kept.length < 256) this.kept.push(message); };
      link.ongone = () => { this.gone = true; if (this.waiting) { const w = this.waiting; this.waiting = null; w(null); } };
    }
    clear() { this.kept.length = 0; }
    /* The next message, or null when the time is over or the pedal has gone. */
    next(ms) {
      if (this.kept.length) return Promise.resolve(this.kept.shift());
      if (this.gone || ms <= 0) return Promise.resolve(null);
      return new Promise(done => {
        const timer = setTimeout(() => { if (this.waiting === take) this.waiting = null; done(null); }, ms);
        const take = message => { clearTimeout(timer); done(message); };
        this.waiting = take;
      });
    }
    send(message) {
      if (this.gone) throw new PedalError("gone", "the pedal has gone");
      try { this.link.send(message); } catch (e) { throw new PedalError("gone", "the pedal does not take messages: " + (e && e.message || e)); }
    }
  }

  /* The stock firmware (or M-VAVE's own loader, which answers the same question). */
  class Stock {
    constructor(link, { now = () => Date.now(), times = {} } = {}) {
      this.inbox = new Inbox(link);
      this.now = now;
      this.times = { answer: 1500, first: 15000, next: 8000, end: 4000, ...times };
    }
    async identity(tries = 2) {
      for (let i = 0; i < tries; i++) {
        this.inbox.clear();
        this.inbox.send(W.stockFrame(W.IDENTITY));
        const until = this.now() + this.times.answer;
        for (let left = this.times.answer; left > 0; left = until - this.now()) {
          const m = await this.inbox.next(left);
          if (!m) break;
          const name = W.identityOf(m);
          if (name) return name;
        }
        if (this.inbox.gone) break;
      }
      return null;
    }
    /* Offers the package; the pedal asks for its parts, stores the loader, and ends with a last question. After the answer it
     * restarts into the loader. Nothing of the application is changed by this. */
    async giveLoader(pack, stored, progress = () => {}) {
      const at = pack.length - (stored + 31 & ~31), taken = new Uint8Array(Math.ceil(pack.length / 512) + 4);
      this.inbox.clear();
      this.inbox.send(W.ENTER);
      let asked = 0, reached = 0;
      const other = [];           // what the pedal said that is not a request, for the log
      for (;;) {
        const m = await this.inbox.next(asked ? this.times.next : this.times.first);
        if (!m) {
          const heard = other.length ? "heard " + other.join(" ") : "heard nothing";
          throw new PedalError(this.inbox.gone ? "gone" : asked ? "stopped" : "refused", (asked ? "the pedal stopped asking for the loader" : "the pedal did not ask for the loader") + " (" + heard + ")");
        }
        const r = W.packageRequest(m);
        if (!r) { if (other.length < 4) other.push(Array.from(m.subarray(0, 24), v => v.toString(16).padStart(2, "0")).join("")); continue; }
        asked++;
        if (r.address === W.FINISHED && r.length === W.SUCCESS.length) {
          if (reached < at + stored) throw new PedalError("stopped", "the pedal ended before it had the whole loader");
          this.inbox.send(W.packageAnswer(r, W.SUCCESS));
          progress(1);
          return;
        }
        if (r.length < 1 || r.length > 1024 || r.address + r.length > pack.length + 512) throw new PedalError("stopped", `the pedal asked for ${r.length} bytes at ${r.address}`);
        const data = new Uint8Array(r.length);
        data.set(pack.subarray(Math.min(r.address, pack.length), Math.min(r.address + r.length, pack.length)));
        this.inbox.send(W.packageAnswer(r, data));
        taken[r.address >> 9] = 1;
        reached = Math.max(reached, r.address + r.length);
        progress(Math.min(0.99, Math.max(0, r.address + r.length - at) / stored));
        if (asked > 4000) throw new PedalError("stopped", "the pedal asks without end");
      }
    }
  }

  /* HyperRig's loader (firmware/mini_stage). The same message again is not carried out twice: what got no answer is sent again. */
  class Loader {
    constructor(link, { now = () => Date.now(), times = {} } = {}) {
      this.inbox = new Inbox(link);
      this.now = now;
      this.times = { answer: 1200, slow: 8000, tries: 5, ...times };
      this.sequence = Math.floor(Math.random() * 60000);
      this.phase = "ready";
    }
    async ask(op, body, { slow = false } = {}) {
      this.sequence = this.sequence + 1 & 0xffff;
      const frame = W.loaderFrame(op, this.sequence, body);
      for (let i = 0; i < this.times.tries; i++) {
        this.inbox.clear();
        this.inbox.send(frame);
        const limit = slow ? this.times.slow : this.times.answer, until = this.now() + limit;
        for (let left = limit; left > 0; left = until - this.now()) {
          const m = await this.inbox.next(left);
          if (!m) break;
          const r = W.loaderParse(m);
          if (!r || r.op !== (op | 0x80) || r.sequence !== this.sequence || r.body.length < 2) continue;
          this.phase = W.PHASES[r.body[1]] || "failed";
          return { status: r.body[0], data: r.body.subarray(2) };
        }
        if (this.inbox.gone) throw new PedalError("gone", "the pedal has gone");
      }
      throw new PedalError("silent", "the loader does not answer");
    }
    async must(op, body, options) {
      const r = await this.ask(op, body, options);
      if (r.status) throw Object.assign(new PedalError("loader", `the loader answered: ${W.STATUS[r.status] || r.status}`), { status: r.status });
      return r.data;
    }
    async hello() {
      const h = W.helloOf(await this.must(W.OPS.HELLO));
      if (!h) throw new PedalError("other", "another loader answered");
      return { ...h, whole: h.whole || this.phase === "done", phase: this.phase };       // the application as it is now
    }
    async read(address, length) {
      const b = new Uint8Array(6);
      W.put(b, 0, address, 4);
      W.put(b, 4, length, 2);
      const data = await this.must(W.OPS.READ, b);
      if (data.length !== length) throw new PedalError("mismatch", "a block came back with another length");
      return data;
    }
    async crc(address, length) {
      const b = new Uint8Array(8);
      W.put(b, 0, address, 4);
      W.put(b, 4, length, 4);
      return W.u32(await this.must(W.OPS.CRC, b, { slow: true }), 0);
    }
    /* A part of the flash, each stretch compared with what the chip itself computes for it. */
    async readChecked(address, length, progress = () => {}) {
      const out = new Uint8Array(length), stretch = 0x10000;
      for (let from = 0; from < length; from += stretch) {
        const n = Math.min(stretch, length - from);
        for (let attempt = 0; ; attempt++) {
          for (let k = 0; k < n; k += 1024) {
            const m = Math.min(1024, n - k);
            out.set(await this.read(address + from + k, m), from + k);
            progress((from + k + m) / length);
          }
          if (await this.crc(address + from, n) === W.crc32(out.subarray(from, from + n))) break;
          if (attempt) throw new PedalError("mismatch", "what was read is not what the chip says it holds");
        }
      }
      return out;
    }
    readAll(progress) { return this.readChecked(0, F.CAPACITY, progress); }
    async begin(plan) {
      const b = new Uint8Array(15);
      W.put(b, 0, plan.now, 4);
      W.put(b, 4, plan.then, 4);
      W.put(b, 8, plan.order.length, 2);
      b[10] = plan.windows;
      b.set(W.ascii("ARM!"), 11);
      await this.must(W.OPS.BEGIN, b, { slow: true });
    }
    async open(now) {
      const b = new Uint8Array(4);
      W.put(b, 0, W.crc32(now.subarray(F.APP, F.APP + F.SECTOR)), 4);
      await this.must(W.OPS.OPEN, b, { slow: true });
    }
    async writeSector(a, now, target) {
      for (let at = 0; at < F.SECTOR; at += 1024) {
        const b = new Uint8Array(1026);
        W.put(b, 0, at, 2);
        b.set(target.subarray(a + at, a + at + 1024), 2);
        await this.must(W.OPS.DATA, b);
      }
      const b = new Uint8Array(12);
      W.put(b, 0, a, 4);
      W.put(b, 4, W.crc32(now.subarray(a, a + F.SECTOR)), 4);
      W.put(b, 8, W.crc32(target.subarray(a, a + F.SECTOR)), 4);
      await this.must(W.OPS.WRITE, b, { slow: true });
    }
    /* From what the flash holds to what it shall hold; the whole flash is compared by the chip at the end. */
    async write(now, target, plan, progress = () => {}) {
      await this.begin(plan);
      if (plan.windows & 1) await this.open(now);
      let done = 0;
      for (const a of plan.order) { await this.writeSector(a, now, target); progress(++done / plan.order.length); }
    }
    async finish() { await this.must(W.OPS.FINISH, undefined, { slow: true }); }
    async retire(record) {
      const b = new Uint8Array(4);
      W.put(b, 0, record, 4);
      await this.must(W.OPS.RETIRE, b, { slow: true });
    }
    /* 1 the application, 2 the ROM's download mode, 3 a restart. The pedal may be gone before its answer arrives. */
    async leave(how) {
      try { await this.must(W.OPS.LEAVE, Uint8Array.of(how)); } catch (e) { if (e.code === "loader") throw e; }
    }
  }

  const api = { PedalError, Inbox, Stock, Loader, wait };
  if (node) module.exports = api; else root.HrPedal = api;
})(typeof globalThis === "object" ? globalThis : this);
