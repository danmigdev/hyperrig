/* node app/desktop/test_store.js: the installer's copies and notes, in a folder of its own. */
"use strict";
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { store, SIZE } = require("./store.js");

const folder = fs.mkdtempSync(path.join(os.tmpdir(), "hyperrig-store-"));
try {
  let clock = Date.UTC(2026, 10, 24, 1, 2, 3, 4);
  const s = store(path.join(folder, "pedals"), { now: () => new Date(clock += 1000) });
  const unit = "0123456789abcdef", other = "fedcba9876543210", raw = crypto.randomBytes(SIZE), hash = crypto.createHash("sha256").update(raw).digest("hex");
  assert.deepEqual([s.backups(unit), s.note(unit)], [[], null]);
  const name = s.save(unit, "stock", raw, { version: "011", sha256: hash });
  assert.equal(name, "20261124-010204-004-stock.bin");
  assert.deepEqual(s.backups(unit), [{ name, kind: "stock", version: "011", sha256: hash, time: "2026-11-24T01:02:04.004Z" }]);
  assert.ok(s.load(unit, name).equals(raw));
  assert.deepEqual(s.backups(other), []);
  const second = s.save(unit, "hyperrig", raw, {});
  assert.deepEqual(s.backups(unit).map(b => b.name), [name, second]);
  /* nothing is overwritten */
  clock -= 1000;
  assert.throws(() => s.save(unit, "hyperrig", raw, {}), /name/);
  /* what is not a pedal's */
  for (const bad of ["", "..", "0123456789ABCDEF", "../0123456789abcdef", "0123456789abcdef/..", unit + "0"]) {
    for (const f of [() => s.backups(bad), () => s.note(bad), () => s.save(bad, "stock", raw, {}), () => s.load(bad, name), () => s.keep(bad, '{"job":"install","state":"writing"}')]) assert.throws(f, /unit/, bad);
  }
  for (const bad of ["", "note.json", "../" + name, name + ".json", name.replace(".bin", ".json"), "a.bin"]) assert.throws(() => s.load(unit, bad), /name/, bad);
  assert.throws(() => s.save(unit, "other", raw, {}), /kind/);
  assert.throws(() => s.save(unit, "stock", raw.subarray(1), {}), /size/);
  assert.throws(() => s.save(unit, "stock", raw, { sha256: "00" }), /sha256/);
  /* the note */
  s.keep(unit, JSON.stringify({ job: "install", state: "writing", backup: name }));
  assert.deepEqual(s.note(unit), { job: "install", state: "writing", backup: name });
  s.keep(unit, JSON.stringify({ job: "install", state: "written" }));
  assert.equal(s.note(unit).state, "written");
  for (const bad of ["", "null", "{}", '{"job":"format","state":"writing"}', '{"job":"install","state":"x"}', JSON.stringify({ job: "install", state: "writing", x: "y".repeat(5000) })]) assert.throws(() => s.keep(unit, bad), undefined, bad);
  assert.equal(s.note(unit).state, "written");
  /* a copy that was cut short, or lost its description, is not offered */
  fs.writeFileSync(path.join(folder, "pedals", unit, second), raw.subarray(0, 1000));
  assert.throws(() => s.load(unit, second), /size/);
  fs.rmSync(path.join(folder, "pedals", unit, second.replace(".bin", ".json")));
  assert.deepEqual(s.backups(unit).map(b => b.name), [name]);
  assert.ok(!fs.readdirSync(path.join(folder, "pedals", unit)).some(n => n.endsWith(".new")));
  console.log("store tests passed");
} finally { fs.rmSync(folder, { recursive: true, force: true }); }
