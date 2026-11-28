/* What a TANK-MINI's flash holds, what the pedal's bootloader would do with it, and what it shall hold after an installation or
 * a restoration. No I/O; for the page and for node. */
"use strict";
(function (root) {
  const W = typeof module === "object" && module.exports ? require("./wire.js") : root.HrWire;
  const { crc16, crc32, enc, sfc, u16, u32, put, same } = W;
  const CAPACITY = 0x100000, SECTOR = 4096, APP = 0x4000, APP_END = 0x82000, USER = 0xbf000, USER_END = 0xff000, VM_END = 0xbe000;
  /* A loader since 022 may write the application up to the pedal's VM (0x95000 with M-VAVE's 011), never above APP_END_MAX; an
   * older one up to APP_END only. */
  const APP_END_MAX = 0xa0000;
  const JEDEC = 0xeb6014, KEY = 0x980f, LOADER_AT = 0x01c0a800, LOADER_MAX = 0x5b1c, LOADER_CRC = 0x4852, RECORD_MARK = 0x5441;
  const PARTITIONS = ["VM", "PRCT", "BTIF", "USR"];
  const NAMES = ["app_area_head", "app.bin", "cfg_tool.bin", ...PARTITIONS];
  class FlashError extends Error { constructor(code, text) { super(text); this.code = code; } }
  const need = (ok, code, text) => { if (!ok) throw new FlashError(code, text); };
  const hex = (b, n) => Array.from(b.subarray(0, n), v => v.toString(16).padStart(2, "0")).join("");

  /* The seven records of an application area (its plain first bytes), or null when they are not all there. */
  function records(plain) {
    const out = {};
    for (let i = 0; i < NAMES.length; i++) {
      const r = plain.subarray(32 * i, 32 * i + 32);
      if (r.length < 32 || crc16(r.subarray(2)) !== u16(r, 0)) return null;
      const end = r.subarray(16).indexOf(0), name = String.fromCharCode(...r.subarray(16, end < 0 ? 32 : 16 + end));
      if (name !== NAMES[i]) return null;
      out[name] = { raw: r.slice(), crc: u16(r, 2), offset: u32(r, 4), size: u32(r, 8) };
    }
    return out;
  }
  function find(data, text) {
    const wanted = W.ascii(text);
    outer: for (let i = data.indexOf(wanted[0]); i >= 0; i = data.indexOf(wanted[0], i + 1)) {
      for (let k = 1; k < wanted.length; k++) if (data[i + k] !== wanted[k]) continue outer;
      return i;
    }
    return -1;
  }
  /* The partitions as every TANK-MINI has them: VM up to 0xbe000, the radio data, the user area. */
  function layoutOf(r) {
    const vm = r.VM, at = vm.offset;
    const ok = at >= APP_END && at <= APP_END_MAX && at % SECTOR === 0 && at + vm.size === VM_END && r.PRCT.offset === 0 && r.PRCT.size === at &&
      r.BTIF.offset === VM_END && r.BTIF.size === SECTOR && r.USR.offset === USER && r.USR.size === USER_END - USER;
    return ok ? { vm: at } : null;
  }
  /* What is in the application area of a whole flash. */
  function describe(flash) {
    need(flash.length === CAPACITY, "size", "this is not a whole flash");
    const head = sfc(flash.subarray(APP, APP + SECTOR), KEY), r = records(head);
    const out = { kind: "none", version: null, layout: null, records: r, whole: false };
    if (!r) return out;
    out.layout = layoutOf(r);
    const size = r.app_area_head.size, limit = out.layout ? out.layout.vm - APP : APP_END - APP;
    out.kind = "other";
    if (size < 0x400 || size > limit || r["app.bin"].offset !== 0x120 || r["app.bin"].offset + r["app.bin"].size > size) return out;
    const plain = sfc(flash.subarray(APP, APP + size), KEY);
    out.whole = crc16(plain.subarray(32, size)) === r.app_area_head.crc && crc16(plain.subarray(0x120, 0x120 + r["app.bin"].size)) === r["app.bin"].crc;
    const stock = find(plain, "TANK MINI_0");
    if (find(plain, "HyperRig auth\0") >= 0) out.kind = "hyperrig";
    else if (stock >= 0) {
      const text = String.fromCharCode(...plain.subarray(stock, stock + 13));
      if (/^TANK MINI_\d{3}$/.test(text)) { out.kind = "stock"; out.version = text.slice(-3); }
    }
    return out;
  }
  /* Where a pedal's own numbers are; a name for it that says nothing about them. */
  const UNIT_PARTS = [[0xff000, SECTOR], [VM_END, SECTOR]];
  const unitBytes = flash => W.join(...UNIT_PARTS.map(([a, n]) => flash.subarray(a, a + n)));

  /* One LZ4 block after what came before; null when it is not right. */
  function unblock(data, size, before) {
    const out = new Uint8Array(before.length + size);
    out.set(before);
    let n = before.length, at = 0;
    for (;;) {
      if (at >= data.length) return null;
      const token = data[at++];
      let literals = token >> 4;
      if (literals === 15) for (let b = 255; b === 255;) { if (at >= data.length) return null; b = data[at++]; literals += b; }
      if (at + literals > data.length || n + literals > out.length) return null;
      out.set(data.subarray(at, at + literals), n);
      at += literals;
      n += literals;
      if (at === data.length) return n === out.length ? out : null;
      if (at + 2 > data.length) return null;
      const back = u16(data, at);
      at += 2;
      let length = token & 15;
      if (length === 15) for (let b = 255; b === 255;) { if (at >= data.length) return null; b = data[at++]; length += b; }
      length += 4;
      if (!back || back > n || n + length > out.length) return null;
      for (; length; length--, n++) out[n] = out[n - back];
    }
  }
  /* The code of a stored loader, as the bootloader unpacks and checks it; null when it would not start it. */
  function storedCode(flash, place) {
    if (place + 32 > flash.length) return null;
    const from = u32(flash, place + 4), size = u32(flash, place + 8);
    if (size < 64 || size > 0x10000 || from + size > flash.length) return null;
    const head = flash.subarray(from + 32, from + 64);
    if (crc16(head.subarray(2)) !== u16(head, 0) || u32(head, 8) !== LOADER_AT || u32(head, 4) > LOADER_MAX) return null;
    let out = new Uint8Array(0), at = from + 64;
    while (at < from + size) {
      if (at + 8 > from + size) return null;
      const packed = u32(flash, at), plain = u32(flash, at + 4);
      if (!packed || packed > 4096 || !plain || plain > 0x1000 || at + 8 + packed > from + size) return null;
      out = unblock(flash.subarray(at + 8, at + 8 + packed), plain, out);
      if (!out) return null;
      at += 8 + packed;
    }
    return out.length === u32(head, 4) && crc16(out) === u16(head, 2) ? out : null;
  }
  /* What the bootloader does when the pedal is switched on (tools/check_mini_boot.py runs the real one). */
  function bootDecision(flash) {
    const head = enc(flash.subarray(APP, APP + 32), KEY);
    if (crc16(head.subarray(2)) === u16(head, 0)) return { outcome: "application", record: null, place: null, code: null };
    const found = firstRecord(flash);
    if (!found) return { outcome: "reset", record: null, place: null, code: null };
    if (!found.crc || !found.type) return { outcome: "download mode", record: found.at, place: null, code: null };
    const code = storedCode(flash, found.place);
    return { outcome: code ? "loader" : "download mode", record: found.at, place: found.place, code };
  }
  function firstRecord(flash, top = CAPACITY - SECTOR) {
    for (let b = top; b > SECTOR; b -= SECTOR) {
      const r = flash.subarray(b - 256, b - 176);
      if (u16(r, 6) === RECORD_MARK && crc16(r.subarray(2)) === u16(r, 0)) return { at: b - 256, crc: u16(r, 0), type: u16(r, 2), place: u32(r, 72) };
    }
    return null;
  }
  /* The same flash with no application: what would happen if the power went while it is written. */
  function withoutApplication(flash) {
    const out = flash.slice();
    out.fill(0xff, APP, APP + SECTOR);
    return out;
  }
  /* Is there a way back to this loader, or to another one of HyperRig's; which record has to be made void first. */
  function wayBack(flash, code) {
    const bare = withoutApplication(flash), decision = bootDecision(bare);
    if (decision.outcome === "loader" && (code && same(decision.code, code) || crc16(decision.code) === LOADER_CRC)) return { ok: true, record: decision.record, retire: null };
    if (decision.record === null || decision.record < APP_END || decision.record >= USER) return { ok: false, record: decision.record, retire: null };
    const next = firstRecord(bare, decision.record + 256 - SECTOR), below = next && next.crc && next.type ? storedCode(bare, next.place) : null;
    return { ok: false, record: decision.record, retire: below && crc16(below) === LOADER_CRC ? decision.record : null };
  }

  /* HyperRig's application area for one pedal: its own partition records in HyperRig's directory, signed again. On a pedal whose
   * records are those of the image, the image comes out as it is. An image may be longer than APP_END (a build for the
   * application partition of 011); what it uses, as its directory says, has to fit this pedal's partition. The area ends at
   * APP_END, or past it where what it uses ends: an image that does not use the room installs as before, with any loader. */
  function areaFor(image, unitHead) {
    need(image.length >= APP_END - APP && image.length <= APP_END_MAX - APP && image.length % SECTOR === 0, "image", "the firmware image has another size");
    const plain = sfc(image, KEY), own = records(plain), unit = records(sfc(unitHead.subarray(0, SECTOR), KEY)), used = u32(plain, 8);
    need(own && used <= image.length && crc16(plain.subarray(32, used)) === u16(plain, 2), "image", "the firmware image is damaged");
    need(crc16(plain.subarray(0x120, 0x120 + own["app.bin"].size)) === own["app.bin"].crc, "image", "the firmware image is damaged");
    const layout = unit && layoutOf(unit);
    need(layout, "layout", "the pedal's partitions are not known");
    need(used <= layout.vm - APP, "size", "this firmware does not fit this pedal's application partition");
    const room = Math.min(image.length, Math.max(APP_END - APP, Math.ceil(used / SECTOR) * SECTOR));     // past APP_END only what it uses
    PARTITIONS.forEach((name, i) => plain.set(unit[name].raw, 32 * (3 + i)));
    put(plain, 2, crc16(plain.subarray(32, used)), 2);
    put(plain, 0, crc16(plain.subarray(2, 32)), 2);
    const out = sfc(plain, KEY).subarray(0, room);
    need(records(sfc(out.subarray(0, SECTOR), KEY)), "image", "the directory could not be made");
    return out;
  }
  /* Where the application of an image ends on the flash, as its directory says. */
  function imageEnd(image) {
    const plain = sfc(image.subarray(0, 32), KEY);
    return crc16(plain.subarray(2, 32)) === u16(plain, 0) ? APP + u32(plain, 8) : APP + image.length;
  }
  function installTarget(now, image, unitHead) {
    const out = now.slice();
    out.set(areaFor(image, unitHead), APP);
    return out;
  }
  /* The flash as it was: the application and the whole user area of the backup. The loader writes the application up to end (the
   * pedal's VM with a loader since 022, APP_END with an older one); from there to the VM the original must still be on the pedal. */
  function restoreTarget(now, backup, end = APP_END) {
    const was = describe(backup);
    need(was.kind === "stock" && was.whole && was.layout, "backup", "the backup does not hold a whole stock firmware");
    const to = Math.min(end, was.layout.vm);
    need(same(now.subarray(0, APP), backup.subarray(0, APP)) && same(now.subarray(to, was.layout.vm), backup.subarray(to, was.layout.vm)),
      "outside", "part of the original firmware is not on the pedal any more");
    const out = now.slice();
    out.set(backup.subarray(APP, to), APP);
    out.set(backup.subarray(USER, USER_END), USER);
    return out;
  }
  const writable = (a, end) => a >= APP && a < end || a >= USER && a < USER_END;
  /* Where the application's sectors that change end: past APP_END only a loader since 022 writes them. */
  function reach(now, target) {
    let end = APP_END;
    for (let a = APP_END; a < USER; a += SECTOR) if (!same(now.subarray(a, a + SECTOR), target.subarray(a, a + SECTOR))) end = a + SECTOR;
    return end;
  }
  /* The sectors to write, the header last; and that nothing else differs. The header is written whenever anything is, so that a
   * pedal that was interrupted comes back to the loader and not to an application with half of its data. end: where the
   * application's window ends, as the loader is told. */
  function plan(now, target, end = APP_END) {
    const order = [];
    let user = false;
    for (let a = 0; a < CAPACITY; a += SECTOR) {
      if (same(now.subarray(a, a + SECTOR), target.subarray(a, a + SECTOR))) continue;
      need(writable(a, end), "outside", "a sector outside the application and the user area would change");
      if (a >= USER) user = true;
      order.push(a);
    }
    const last = order.filter(a => a !== APP);
    if (order.length) last.push(APP);
    return { order: last, windows: last.length ? 1 | (user ? 2 : 0) : 0, now: crc32(now), then: crc32(target), end };
  }

  const api = { CAPACITY, SECTOR, APP, APP_END, APP_END_MAX, USER, USER_END, VM_END, JEDEC, KEY, LOADER_CRC, NAMES, UNIT_PARTS, FlashError, records, layoutOf, describe, unitBytes, unblock, storedCode,
    bootDecision, firstRecord, withoutApplication, wayBack, areaFor, imageEnd, installTarget, restoreTarget, reach, plan, hex };
  if (typeof module === "object" && module.exports) module.exports = api; else root.HrFlash = api;
})(typeof globalThis === "object" ? globalThis : this);
