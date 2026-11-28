/* What the installer keeps on this computer: for each pedal, by a name that says nothing about it, the copies of its flash and a
 * note about the job that is going on. A copy is written beside its place, flushed, and then put there; nothing is overwritten. */
"use strict";
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const SIZE = 0x100000, KINDS = ["stock", "hyperrig", "unfinished"];
const UNIT = /^[0-9a-f]{16}$/, NAME = /^\d{8}-\d{6}-\d{3}-(?:stock|hyperrig|unfinished)\.bin$/;
class StoreError extends Error {}
const need = (ok, text) => { if (!ok) throw new StoreError(text); };

function write(file, raw) {
  const beside = file + ".new", handle = fs.openSync(beside, "w");
  try { fs.writeFileSync(handle, raw); fs.fsyncSync(handle); } finally { fs.closeSync(handle); }
  fs.renameSync(beside, file);
}
function store(folder, { now = () => new Date() } = {}) {
  const place = (unit, name) => { need(UNIT.test(unit), "unit"); return path.join(folder, unit, ...(name ? [name] : [])); };
  function about(unit, name) {
    try {
      const a = JSON.parse(fs.readFileSync(place(unit, name.replace(/\.bin$/, ".json")), "utf8"));
      return { name, kind: String(a.kind), version: a.version === null || a.version === undefined ? null : String(a.version), sha256: String(a.sha256), time: String(a.time) };
    } catch (e) { return null; }
  }
  return {
    folder,
    backups(unit) {
      let names;
      try { names = fs.readdirSync(place(unit)); } catch (e) { if (e instanceof StoreError) throw e; return []; }
      return names.filter(n => NAME.test(n)).sort().map(n => about(unit, n)).filter(Boolean);
    },
    save(unit, kind, raw, more) {
      need(KINDS.includes(kind), "kind");
      need(raw.length === SIZE, "size");
      const hash = crypto.createHash("sha256").update(raw).digest("hex");
      need(!more || more.sha256 === undefined || more.sha256 === hash, "sha256");
      fs.mkdirSync(place(unit), { recursive: true });
      const time = now().toISOString(), stamp = time.replace(/[-:]/g, "").replace(/T/, "-").replace(/\.(\d{3})Z$/, "-$1");
      const name = `${stamp}-${kind}.bin`;
      need(NAME.test(name) && !fs.existsSync(place(unit, name)), "name");
      write(place(unit, name), raw);
      need(crypto.createHash("sha256").update(fs.readFileSync(place(unit, name))).digest("hex") === hash, "the copy does not read back");
      write(place(unit, name.replace(/\.bin$/, ".json")), JSON.stringify({ kind, version: more && more.version || null, sha256: hash, time }, null, 1) + "\n");
      return name;
    },
    load(unit, name) {
      need(NAME.test(name), "name");
      const raw = fs.readFileSync(place(unit, name));
      need(raw.length === SIZE, "size");
      return raw;
    },
    note(unit) {
      try { return JSON.parse(fs.readFileSync(place(unit, "note.json"), "utf8")); } catch (e) { if (e instanceof StoreError) throw e; return null; }
    },
    keep(unit, text) {
      need(typeof text === "string" && text.length < 4096, "note");
      const value = JSON.parse(text);
      need(noteOk(value), "note");
      fs.mkdirSync(place(unit), { recursive: true });
      write(place(unit, "note.json"), JSON.stringify(value) + "\n");
    },
  };
}
/* A note the installer may keep: its job and how far it got. An update that goes once through the original (flow.js,
 * throughOriginal) is "upgrade", and "original" while the original is on the pedal for a moment. */
function noteOk(value) {
  return !!value && typeof value === "object" && ["install", "restore", "upgrade"].includes(value.job) &&
    (["writing", "written"].includes(value.state) || value.state === "original" && value.job === "upgrade");
}
module.exports = { store, noteOk, StoreError, SIZE };
