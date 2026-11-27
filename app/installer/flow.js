/* The installer's course: what is connected, what may be done, and the jobs, which can be taken up again at any point.
 *
 * Nothing is erased before all of this: the loader is HyperRig's, on the chip and flash it knows; the whole flash was read,
 * each stretch compared with the chip's own checksum, and kept on this computer, read back from the disk; the firmware to
 * write was checked; and the bootloader, as far as the flash shows, would come back to the loader without an application.
 * Only the application and the user area change, the header of the application first erased and last written; the chip
 * compares its whole flash with what was meant before the application is started. A job that was interrupted is found again
 * by its note on this computer and by the pedal's own numbers.
 *
 * env: midi { list() -> [{id, name}], open(id) -> link }, serial { present(), talk(task) -> what task(ask) gives } or null, where
 * ask(line, start, { ms, tries }) -> text or null,
 * store { backups(unit), save(unit, kind, bytes, about), load(unit, name), note(unit), keep(unit, note) }, sha256(bytes),
 * now(), sleep(ms). For the page and for node. */
"use strict";
(function (root) {
  const node = typeof module === "object" && module.exports;
  const F = node ? require("./flash.js") : root.HrFlash, P = node ? require("./pedal.js") : root.HrPedal, V = node ? require("./views.js") : root.HrViews;
  const KNOWN_STOCK = ["011"];       // what an installation was seen to work from, on a pedal
  /* Windows calls the stock firmware's port USB-Midi, and M-VAVE's updater's as well: who is there is found out by asking. */
  const LOADER_PORT = /^HyperRig Update/i, MAYBE = /TANK|HyperRig|USB[- ]?(?:MIDI|Audio)|ota-|MIDI function/i;
  const STOCK_NAME = /^TANK MINI_(\d{3})$/, UPDATER_NAME = /^ota-TANK MINI_/;
  const LOADER = Symbol("loader");
  const HRID = /^HRID 1 (\S+) ([0-9a-f]{16})\b/, STAGE = /^STAGE 1\b/;
  /* -1 when version a of HyperRig comes before b, 1 after, 0 the same, null when one of them is not a version. */
  function order(a, b) {
    const of = v => { const m = /^(\d+)\.(\d+)\.(\d+)(?:-(?:dev|beta)\.(\d+))?$/.exec(String(v)); return m && [+m[1], +m[2], +m[3], m[4] === undefined ? Infinity : +m[4]]; };
    const x = of(a), y = of(b);
    if (!x || !y) return null;
    for (let i = 0; i < 4; i++) if (x[i] !== y[i]) return x[i] < y[i] ? -1 : 1;
    return 0;
  }
  class Trouble extends Error { constructor(kind, text) { super(text || kind); this.kind = kind; } }
  const KINDS = { gone: "unplugged", silent: "unplugged", refused: "refused", stopped: "refused", mismatch: "mismatch", layout: "layout", image: "damaged", backup: "backup", outside: "layout", size: "damaged" };
  const REFUSALS = { 5: "mismatch", 6: "mismatch", 8: "noway" };          // what the loader itself answered
  const kindOf = e => e instanceof Trouble ? e.kind : e && e.code === "loader" ? REFUSALS[e.status] || "failed" : e && KINDS[e.code] || (e && e.name === "NotAllowedError" ? "busy" : "failed");

  class Installer {
    constructor(env, assets, { show, log = () => {}, times = {} }) {
      Object.assign(this, { env, assets, show, log });
      this.times = { look: 700, loader: 45000, back: 45000, settle: 400, pedal: {}, ...times };
      this.busy = false;
      this.stopped = false;
      this.seen = null;
      this.situation = { what: "none" };
      this.changed = false;
      this.holding = false;       // a screen that stays until the person answers
    }

    /* ---- what is connected ---- */
    async look() {
      const ports = await this.env.midi.list(), loader = ports.find(p => LOADER_PORT.test(p.name));
      if (loader) return { what: "loader", id: loader.id };
      for (const p of ports.filter(x => MAYBE.test(x.name))) {
        const name = await this.identity(p.id);
        if (name === LOADER) return { what: "loader", id: p.id };
        if (!name) continue;
        if (STOCK_NAME.test(name)) return { what: "stock", id: p.id, version: STOCK_NAME.exec(name)[1] };
        if (UPDATER_NAME.test(name)) return { what: "updater", id: p.id, name };
      }
      if (this.env.serial && await this.env.serial.present()) {
        const found = await this.env.serial.talk(async ask => {
          const line = await ask("HRID", "HRID", { tries: 5 }), m = line && HRID.exec(line);
          if (!m) return null;
          const stage = await ask("STAGE", "STAGE", { tries: 5 });
          return { what: "hyperrig", version: m[1], build: m[2], entry: !!stage && STAGE.test(stage) };
        });
        return found || { what: "hyperrig", version: "(older)", build: null, entry: false };
      }
      return { what: "none" };
    }
    /* The stock firmware's name, or that HyperRig's loader is there; null for anything else. */
    async identity(id) {
      let link = null;
      try {
        link = await this.env.midi.open(id);
        const options = { now: this.env.now, times: this.times.pedal };
        const name = await new P.Stock(link, options).identity();
        if (name) return name;
        return await new P.Loader(link, { ...options, times: { ...this.times.pedal, tries: 1 } }).hello().then(() => LOADER, () => null);
      } catch (e) { this.log(`port ${id}: ${e.message}`); return null; } finally { if (link) link.close(); }
    }
    async key() {
      const ports = await this.env.midi.list();
      return ports.map(p => p.id + "/" + p.name).sort().join("|") + "#" + (this.env.serial ? await this.env.serial.present() : "");
    }
    /* Looks again when something was plugged in or out; a screen that waits for an answer stays. */
    async watch() {
      for (; !this.stopped; await this.env.sleep(this.times.look)) {
        if (this.busy) continue;
        try {
          const key = await this.key();
          if (key === this.seen) continue;
          await this.env.sleep(this.times.settle);
          if (this.busy) continue;
          this.seen = await this.key();
          await this.home(true);
        } catch (e) { this.log("look: " + (e && e.stack || e)); }
      }
    }
    async home(plugged = false) {
      this.situation = await this.look();
      const s = this.situation;
      this.log("connected: " + JSON.stringify(s));
      if (this.holding && plugged && s.what !== "loader") return;
      this.holding = false;
      if (s.what === "none") return this.show(V.search());
      if (s.what === "updater") return this.show(V.updater(s.name));
      if (s.what === "stock") return this.show(KNOWN_STOCK.includes(s.version) ? V.stock(s.version) : V.untried(s.version));
      if (s.what === "hyperrig") {
        const other = s.build !== this.assets.build, ahead = other && order(s.version, this.assets.version) === 1;
        return this.show(V.hyperrig(s.version, { newer: other && !ahead ? this.assets.version : null, ahead: ahead ? this.assets.version : null, entry: s.entry }));
      }
      const found = await this.inLoader(s.id, async (loader, hello) => ({ hello, ...await this.noteOf(loader) }));
      if (!found.hello.whole) { this.show(V.resume(found.note && found.note.state === "writing" ? found.note.job : "install")); return; }
      this.show(V.waiting(found.backups.some(b => b.kind === "stock")));
    }

    /* ---- the buttons ---- */
    async act(action) {
      if (this.busy) return;
      if (action === "install" || action === "restore" || action === "save") return this.run(action);
      if (action === "continue") return this.run(null);
      if (action === "again" || action === "home") { this.holding = false; return this.home(); }
      if (action === "leave") return this.run("leave");
    }
    async run(job) {
      this.busy = true;
      this.changed = false;
      this.holding = true;
      let wanted = job;
      try {
        if (job === "leave") { const { id } = await this.look(); await this.inLoader(id, loader => loader.leave(1)); await this.gone(id); this.holding = false; }
        else {
          const s = await this.look();
          if (s.what === "loader" && !wanted) wanted = (await this.inLoader(s.id, loader => this.noteOf(loader))).note?.job || "install";
          if (!wanted) throw new Trouble("unplugged", "nothing is connected");
          const result = await this.perform(wanted, s);
          this.show(wanted === "save" ? V.saved({ came: result.came }) : V.done(wanted, result.version, { came: result.came, first: s.what !== "hyperrig" }));
        }
      } catch (e) {
        const kind = kindOf(e);
        this.log(`stopped (${kind}): ${e && e.stack || e}`);
        this.show(V.trouble(kind, { changed: this.changed, again: kind !== "layout" && kind !== "damaged" }));
      } finally {
        this.busy = false;
        this.seen = job === "leave" ? null : await this.key().catch(() => null);
      }
    }
    progress(job, step, from, to, title) {
      if (job === "save") { from = from / 0.4; to = Math.min(1, to / 0.4); }        // saving is the first two fifths of the others
      let last = -1;
      return part => {
        const p = from + (to - from) * part;
        if (p - last < 0.004 && part < 1) return;
        last = p;
        this.show(V.working(job, step, p, title));
      };
    }

    /* ---- a job ---- */
    async perform(job, situation) {
      const p = this.progress(job, "save", 0, 0.06, "Getting your pedal ready");
      p(0);
      const id = await this.enter(situation, p);
      return this.inLoader(id, (loader, hello) => this.work(job, loader, hello), { job });
    }
    /* Into the loader, from wherever the pedal is. */
    async enter(s, progress) {
      for (let attempt = 0; attempt < 3; attempt++) {
        if (s.what === "loader") {
          const phase = await this.inLoader(s.id, async (loader, hello) => hello.phase);
          if (phase === "ready") return s.id;
          this.log(`the loader is in the middle of something (${phase}): it starts anew`);
          await this.inLoader(s.id, loader => loader.leave(3));
          await this.gone(s.id);
          s = await this.appears(x => x.what === "loader" || x.what === "stock" || x.what === "hyperrig", this.times.loader);
          continue;
        }
        if (s.what === "stock") {
          if (!KNOWN_STOCK.includes(s.version)) throw new Trouble("refused", "stock " + s.version);
          const link = await this.env.midi.open(s.id).catch(e => { throw new Trouble("busy", e.message); });
          try {
            await new P.Stock(link, { now: this.env.now, times: this.times.pedal }).giveLoader(this.assets.pack, this.assets.stored, progress);
          } finally { link.close(); }
          this.log("the pedal has the loader and restarts");
        } else if (s.what === "hyperrig") {
          if (!s.entry) throw new Trouble("refused", "this HyperRig does not start the loader");
          /* Asked once, after a question that was answered. The answer may be lost when the pedal restarts at once. */
          const line = await this.env.serial.talk(async ask => await ask("HRID", "HRID", { tries: 5 }) ? ask("STAGE GO", "STAGE", { ms: 3000 }) : "silent");
          if (line === "silent" || line !== null && !/^STAGE GO\b/.test(line)) throw new Trouble("refused", "HyperRig did not start the loader: " + line);
          if (line === null) this.log("no answer to STAGE GO: perhaps the pedal is already restarting");
        } else throw new Trouble("unplugged", "nothing to start from");
        s = await this.appears(x => x.what === "loader", this.times.loader);
        return s.id;
      }
      throw new Trouble("failed", "the loader does not become ready");
    }
    async appears(right, ms) {
      const until = this.env.now() + ms;
      for (;;) {
        const ports = await this.env.midi.list();
        if (ports.some(p => LOADER_PORT.test(p.name) || MAYBE.test(p.name)) || this.env.serial && await this.env.serial.present()) {
          const s = await this.look().catch(() => ({ what: "none" }));
          if (right(s)) return s;
        }
        if (this.env.now() > until) throw new Trouble("unplugged", "the pedal did not come back in time");
        await this.env.sleep(this.times.settle);
      }
    }
    async gone(id) {
      const until = this.env.now() + 8000;
      while ((await this.env.midi.list()).some(p => p.id === id)) {
        if (this.env.now() > until) return;
        await this.env.sleep(150);
      }
    }
    /* The port of the loader can go and come back under another name between finding it and opening it. */
    async openLoader(id) {
      for (let i = 0; ; i++) {
        try { return await this.env.midi.open(id); } catch (e) {
          if (!e || e.code !== "gone") throw new Trouble("busy", e && e.message);
          if (i >= 2) throw new Trouble("unplugged", e.message);
          this.log("the loader's port changed: looking again");
          ({ id } = await this.appears(x => x.what === "loader", this.times.loader));
        }
      }
    }
    async inLoader(id, task) {
      if (!id) throw new Trouble("unplugged", "the loader is not there");
      const link = await this.openLoader(id);
      try {
        const loader = new P.Loader(link, { now: this.env.now, times: this.times.pedal }), hello = await loader.hello();
        if (hello.jedec !== F.JEDEC || hello.capacity !== F.CAPACITY || hello.key !== F.KEY || hello.chunk !== 1024) throw new Trouble("layout", "another chip or flash: " + JSON.stringify(hello));
        return await task(loader, hello);
      } finally { link.close(); }
    }
    async unitOf(loader) {
      const parts = [];
      for (const [a, n] of F.UNIT_PARTS) parts.push(await loader.readChecked(a, n));
      return this.unitName(parts);
    }
    async unitName(parts) { return (await this.env.sha256(parts.reduce((a, b) => { const o = new Uint8Array(a.length + b.length); o.set(a); o.set(b, a.length); return o; }, new Uint8Array(0)))).slice(0, 16); }
    async noteOf(loader) {
      const unit = await this.unitOf(loader);
      return { unit, note: await this.env.store.note(unit), backups: await this.env.store.backups(unit) };
    }
    /* The whole flash on the disk, read back from there. */
    async keepBackup(unit, kind, flash, about) {
      const hash = await this.env.sha256(flash), have = (await this.env.store.backups(unit)).find(b => b.sha256 === hash);
      if (have) return have.name;
      let name;
      try { name = await this.env.store.save(unit, kind, flash, { ...about, sha256: hash }); } catch (e) { throw new Trouble("disk", e.message); }
      const back = await this.env.store.load(unit, name).catch(() => null);
      if (!back || await this.env.sha256(back) !== hash) throw new Trouble("disk", "the backup does not read back");
      this.log(`backup ${name}: ${hash}`);
      return name;
    }
    async loadBackup(unit, name) {
      const about = (await this.env.store.backups(unit)).find(b => b.name === name), bytes = about && await this.env.store.load(unit, name).catch(() => null);
      if (!bytes || bytes.length !== F.CAPACITY || await this.env.sha256(bytes) !== about.sha256) return null;
      return bytes;
    }

    /* What stops before anything was changed leaves the pedal to its firmware again. */
    async work(job, loader, hello) {
      try { return await this.carryOut(job, loader, hello); } catch (e) {
        if (!this.changed && hello.whole) await loader.leave(1).catch(() => {});
        throw e;
      }
    }
    async carryOut(job, loader, hello) {
      this.log("loader: " + JSON.stringify(hello));
      let now = await loader.readAll(this.progress(job, "save", 0.06, 0.4));
      const unit = await this.unitName(F.UNIT_PARTS.map(([a, n]) => now.subarray(a, a + n)));
      const is = F.describe(now), note = await this.env.store.note(unit), interrupted = note && note.state === "writing" ? note : null;
      this.log(`unit ${unit}: ${is.kind} ${is.version || ""}, whole ${is.whole}, VM at ${is.layout && is.layout.vm.toString(16)}, note ${note && note.state}`);
      if (is.kind === "other" || is.records && !is.layout) throw new Trouble("layout", "the application or the partitions are not known");
      if (hello.application !== (F.bootDecision(now).outcome === "application")) throw new Trouble("mismatch", "the bootloader and the flash say different things about the application");
      /* the backup */
      const backups = await this.env.store.backups(unit);
      let kept = null;
      if (is.whole) kept = await this.keepBackup(unit, is.kind, now, { version: is.version, time: new Date(this.env.now()).toISOString() });
      else if (!backups.length) kept = await this.keepBackup(unit, "unfinished", now, { time: new Date(this.env.now()).toISOString() });
      if (job === "save") {
        this.log(`way back: ${JSON.stringify(F.wayBack(now, this.assets.code))}`);
        this.progress(job, "check", 0.9, 1, "Starting your pedal")(0.5);
        await loader.leave(1);
        return { version: is.version, came: await this.appears(x => x.what === "stock" || x.what === "hyperrig", this.times.back).then(() => true, () => false) };
      }
      /* what the flash shall hold */
      let target, version;
      if (job === "install") {
        let head = is.layout ? now.subarray(F.APP, F.APP + F.SECTOR) : null;
        for (const b of head ? [] : [interrupted && interrupted.backup, ...backups.filter(x => x.kind === "stock" || x.kind === "hyperrig").map(x => x.name)].filter(Boolean)) {
          const old = await this.loadBackup(unit, b);
          if (old && F.describe(old).layout) { head = old.subarray(F.APP, F.APP + F.SECTOR); break; }
        }
        if (!head) throw new Trouble("elsewhere", "no header and no backup to take the partitions from");
        target = F.installTarget(now, this.assets.image, head);
        version = this.assets.version;
      } else {
        const original = (await this.env.store.backups(unit)).filter(b => b.kind === "stock").sort((a, b) => a.time > b.time ? -1 : 1)[0], old = original && await this.loadBackup(unit, original.name);
        if (!old) throw new Trouble("backup", "no stock backup of this pedal");
        target = F.restoreTarget(now, old);
        version = F.describe(old).version;
      }
      let plan = F.plan(now, target);
      this.log(`${plan.order.length} sectors, windows ${plan.windows}`);
      if (plan.order.length) {
        /* the way back */
        let way = F.wayBack(now, this.assets.code);
        if (!way.ok && way.retire !== null) {
          this.log(`an older update record at ${way.retire.toString(16)} is made void`);
          await loader.retire(way.retire);
          const sector = way.retire & ~(F.SECTOR - 1);
          now = now.slice();
          now.set(await loader.readChecked(sector, F.SECTOR), sector);
          target = target.slice();
          target.set(now.subarray(sector, sector + F.SECTOR), sector);
          way = F.wayBack(now, this.assets.code);
          plan = F.plan(now, target);
        }
        if (is.records && !way.ok) throw new Trouble("noway", `no way back: ${JSON.stringify(way)}`);
        if (is.records && !(await loader.hello()).returns) throw new Trouble("noway", "the loader sees no way back");
        await this.env.store.keep(unit, { job, state: "writing", backup: kept || interrupted && interrupted.backup || null, version, loader: hello.build, time: new Date(this.env.now()).toISOString() })
          .catch(e => { throw new Trouble("disk", e.message); });
        const p = this.progress(job, "install", 0.4, 0.88);
        p(0);
        this.changed = true;
        await loader.write(now, target, plan, p);
        this.progress(job, "check", 0.88, 1)(0.1);
        await loader.finish();
        this.log("the chip holds exactly what was meant");
      }
      await this.env.store.keep(unit, { job, state: "written", version, time: new Date(this.env.now()).toISOString() }).catch(() => {});
      this.changed = false;
      this.progress(job, "check", 0.88, 1, "Starting your pedal")(0.7);
      await loader.leave(1);
      const came = await this.appears(x => job === "install" ? x.what === "hyperrig" : x.what === "stock", this.times.back).then(() => true, () => false);
      return { version, came };
    }
  }

  const api = { Installer, Trouble, KNOWN_STOCK, kindOf, order };
  if (node) module.exports = api; else root.HrFlow = api;
})(typeof globalThis === "object" ? globalThis : this);
