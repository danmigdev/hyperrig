/* The bytes between the computer and the pedal: SysEx of the stock firmware's update service and of HyperRig's loader, and the
 * checksums and the scrambling of the flash. No I/O; for the page and for node. */
"use strict";
(function (root) {
  /* CRC-32 as zlib's; the loader's. */
  const TABLE = new Uint32Array(256);
  for (let i = 0; i < 256; i++) { let c = i; for (let k = 0; k < 8; k++) c = c & 1 ? c >>> 1 ^ 0xedb88320 : c >>> 1; TABLE[i] = c >>> 0; }
  function crc32(data, crc = 0) {
    let c = ~crc >>> 0;
    for (let i = 0; i < data.length; i++) c = c >>> 8 ^ TABLE[(c ^ data[i]) & 255];
    return ~c >>> 0;
  }
  /* CRC-16, 0x1021 from 0; of the records in the flash and in packages. */
  const TABLE16 = new Uint16Array(256);
  for (let i = 0; i < 256; i++) { let c = i << 8; for (let k = 0; k < 8; k++) c = c & 0x8000 ? (c << 1 ^ 0x1021) & 0xffff : c << 1 & 0xffff; TABLE16[i] = c; }
  function crc16(data) {
    let c = 0;
    for (let i = 0; i < data.length; i++) c = (c << 8 ^ TABLE16[(c >>> 8 ^ data[i]) & 255]) & 0xffff;
    return c;
  }
  /* The scrambling of a record, and of the application area (32 bytes at a time, with the place in the key). */
  function enc(data, key) {
    const out = new Uint8Array(data.length);
    for (let i = 0; i < data.length; i++) { out[i] = data[i] ^ key & 255; key = (key << 1 ^ (key & 0x8000 ? 0x1021 : 0)) & 0xffff; }
    return out;
  }
  function sfc(data, key, from = 0) {
    const out = new Uint8Array(data.length);
    for (let at = 0; at < data.length; at += 32) out.set(enc(data.subarray(at, at + 32), (key ^ from + at >>> 2) & 0xffff), at);
    return out;
  }
  const u16 = (b, at) => b[at] | b[at + 1] << 8;
  const u32 = (b, at) => (b[at] | b[at + 1] << 8 | b[at + 2] << 16 | b[at + 3] << 24) >>> 0;
  const put = (b, at, v, n) => { for (let i = 0; i < n; i++) b[at + i] = Math.floor(v / 2 ** (8 * i)) & 255; };
  const join = (...parts) => {
    const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
    let at = 0;
    for (const p of parts) { out.set(p, at); at += p.length; }
    return out;
  };
  const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
  const ascii = text => Uint8Array.from(text, c => c.charCodeAt(0));

  /* Eight bits into seven, lowest first; nothing more when they come out even, as M-Upgrade sends them. */
  function pack7(raw, flush) {
    const out = [];
    let hold = 0, bits = 0;
    for (const b of raw) {
      hold |= b << bits;
      bits += 8;
      while (bits >= 7) { out.push(hold & 127); hold >>= 7; bits -= 7; }
    }
    if (bits || flush) out.push(hold & 127);
    return Uint8Array.from(out);
  }
  function unpack7(packed) {
    const out = [];
    let hold = 0, bits = 0;
    for (const b of packed) {
      if (b > 127) return null;
      hold |= b << bits;
      bits += 7;
      if (bits >= 8) { out.push(hold & 255); hold >>= 8; bits -= 8; }
    }
    return Uint8Array.from(out);
  }
  const isSysex = m => m.length >= 2 && m[0] === 0xf0 && m[m.length - 1] === 0xf7;

  /* The stock firmware: 00 59, command, length (24 bits), body, the complement of the sum of the body. */
  const IDENTITY = 0x11, PACKAGE = 0x30;
  const ENTER = Uint8Array.from([0xf0, 0x22, 0x24, 0x35, 0x7f, 0xf7]);     // "install what I give you"
  const FINISHED = 0xe0000000, SUCCESS = ascii("success\0");
  function stockFrame(command, body = new Uint8Array(0)) {
    const raw = new Uint8Array(7 + body.length);
    raw[1] = 0x59;
    raw[2] = command;
    put(raw, 3, body.length, 3);
    raw.set(body, 6);
    raw[raw.length - 1] = ~body.reduce((n, b) => n + b, 0) & 255;
    return join([0xf0], pack7(raw, false), [0xf7]);
  }
  function stockParse(message) {
    if (!isSysex(message)) return null;
    const raw = unpack7(message.subarray(1, message.length - 1));
    if (!raw || raw.length < 7 || raw[0] || raw[1] !== 0x59) return null;
    const n = raw[3] | raw[4] << 8 | raw[5] << 16;
    if (raw.length < 7 + n) return null;
    const body = raw.subarray(6, 6 + n);
    return (~body.reduce((s, b) => s + b, 0) & 255) === raw[6 + n] ? { command: raw[2], body } : null;
  }
  /* The name the pedal answers with: TANK MINI_011, ota-TANK MINI_011. */
  function identityOf(message) {
    const f = stockParse(message);
    if (!f || f.command !== IDENTITY) return null;
    const end = f.body.indexOf(0), text = String.fromCharCode(...f.body.subarray(0, end < 0 ? f.body.length : end));
    return /^[\x20-\x7e]{1,40}$/.test(text) ? text : null;
  }
  /* A block of the package the pedal asks for, and the answer to it. */
  function packageRequest(message) {
    const f = stockParse(message);
    if (!f || f.command !== PACKAGE || f.body.length !== 8) return null;
    return { head: f.body.slice(), address: u32(f.body, 1), length: f.body[5] | f.body[6] << 8 | f.body[7] << 16 };
  }
  const packageAnswer = (request, data) => stockFrame(PACKAGE, join(request.head, data));

  /* HyperRig's loader: 'H' 'R' 1 op seq:u16 length:u16 body crc32:u32 (firmware/mini_stage/README.md). */
  const OPS = { HELLO: 0x01, READ: 0x02, CRC: 0x03, BEGIN: 0x10, DATA: 0x11, WRITE: 0x12, OPEN: 0x13, FINISH: 0x14, RETIRE: 0x15, LEAVE: 0x20 };
  const PREFIX = [0x7d, 0x48, 0x52];
  function loaderFrame(op, sequence, body = new Uint8Array(0)) {
    const raw = new Uint8Array(12 + body.length);
    raw.set([0x48, 0x52, 1, op]);
    put(raw, 4, sequence, 2);
    put(raw, 6, body.length, 2);
    raw.set(body, 8);
    put(raw, 8 + body.length, crc32(raw.subarray(0, 8 + body.length)), 4);
    return join([0xf0], PREFIX, pack7(raw, false), [0xf7]);
  }
  function loaderParse(message) {
    if (!isSysex(message) || message.length < 6 || !same(message.subarray(1, 4), PREFIX)) return null;
    const raw = unpack7(message.subarray(4, message.length - 1));
    if (!raw || raw.length < 12 || raw[0] !== 0x48 || raw[1] !== 0x52 || raw[2] !== 1) return null;
    const n = u16(raw, 6);
    if (raw.length < 12 + n || crc32(raw.subarray(0, 8 + n)) !== u32(raw, 8 + n)) return null;
    return { op: raw[3], sequence: u16(raw, 4), body: raw.slice(8, 8 + n) };
  }
  function helloOf(data) {
    if (data.length < 47 || String.fromCharCode(...data.subarray(0, 4)) !== "HRS1") return null;
    const end = data.subarray(26, 42).indexOf(0);
    return { chunk: u16(data, 4), capacity: u32(data, 6), jedec: u32(data, 10), key: u16(data, 14), status1: data[16], status2: data[17], fast: data[18],
      application: !!data[19], whole: !!data[19] && !data[24], done: u16(data, 20), sectors: u16(data, 22), touched: !!data[24], windows: data[25],
      build: String.fromCharCode(...data.subarray(26, 26 + (end < 0 ? 16 : end))), returns: !!data[42], record: u32(data, 43) };
  }
  const PHASES = ["ready", "armed", "opened", "done", "failed"];
  const STATUS = ["ok", "message", "range", "order", "checksum", "backup", "preimage", "no application", "no way back", "flash", "another flash", "protected", "busy", "write enable", "too long", "read back"];

  const api = { crc32, crc16, enc, sfc, u16, u32, put, join, same, ascii, pack7, unpack7, IDENTITY, PACKAGE, ENTER, FINISHED, SUCCESS, stockFrame, stockParse, identityOf,
    packageRequest, packageAnswer, OPS, loaderFrame, loaderParse, helloOf, PHASES, STATUS };
  if (typeof module === "object" && module.exports) module.exports = api; else root.HrWire = api;
})(typeof globalThis === "object" ? globalThis : this);
