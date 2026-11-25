/* The strict reading of a preset file from somebody else (product-presetfile.js). Run: node app/mini/test_presetfile.js */
"use strict";
const assert = require("node:assert");
require("./product-presetfile.js");
const { clean, needs, MAX } = globalThis.HyperRigPresetFile;
const HIDDEN = String.fromCharCode(0x202e, 0x200b), hidden = s => Array.from(s).some(c => c.charCodeAt(0) < 32 || HIDDEN.includes(c));
const file = (presets, more) => JSON.stringify({ format: "hyperrig-preset", version: 1, min_reader: 1, presets, ...more });
const block = (type, id, more) => ({ type, id, on: true, params: {}, ...more });
const preset = (chain, more, meta) => ({ meta: { name: "One", ...meta }, sound: { chain, ...more } });
const only = (p, more) => { const r = clean(file([p], more)); assert.ok(r.ok, r.err); return r.presets[0]; };

// what is not a preset is refused, whatever it is
for (const raw of [undefined, null, 5, "", "  ", "{", "[]", "null", "5", '"x"', "{}", '{"format":"hyperrig-preset"}', '{"format":"hyperrig-preset","version":"1","presets":[]}',
  '{"format":"hyperrig-preset","version":0,"presets":[{}]}', '{"format":"other","version":1,"presets":[]}', file([]), file([{}]), file([{ sound: {} }]), file([null, 5, "x", []]), "[".repeat(200000)]) {
  const r = clean(raw);
  assert.ok(!r.ok && r.err && !r.presets.length, String(raw).slice(0, 40));
}
assert.match(clean(" ".repeat(10) + "x".repeat(MAX.bytes)).err, /too large/);
assert.match(clean(file([preset([])], { min_reader: 2 })).err, /newer/);
assert.ok(clean(file([preset([])], { version: 2 })).warn[0].includes("newer"));
assert.ok(clean(String.fromCharCode(0xfeff) + file([preset([])])).ok);

// limits
assert.strictEqual(clean(file(Array(80).fill(preset([])))).presets.length, 64);
const many = only(preset([...Array(30)].map((_, i) => block("gate", "b" + i))));
assert.strictEqual(many.sound.chain.length, MAX.blocks);
assert.strictEqual(many.left, 14);
const nested = only(preset([{ split: { a: [...Array(12)].map(() => block("gate")), b: [...Array(12)].map(() => block("boost")) }, mix_db: [1e9, "x"], crossover_hz: -5 }]));
assert.strictEqual(nested.sound.chain[0].split.a.length + nested.sound.chain[0].split.b.length, MAX.blocks);
assert.deepStrictEqual([nested.sound.chain[0].mix_db, nested.sound.chain[0].crossover_hz, nested.sound.chain[0].even_gain], [[0, 0], 0, false]);
const lots = only(preset([block("gate", "a", { params: Object.fromEntries([...Array(50)].map((_, i) => ["p" + i, i])) })]));
assert.strictEqual(Object.keys(lots.sound.chain[0].params).length, MAX.params);

// names and texts: no control characters, no lines, nothing that hides; types and keys only in their form
const bad = only(preset([block("gate\nPSAVE 1 x", "a"), block("gate", "a b"), block("__proto__", "c"), block("constructor", "d"), block("Gate", "e"), block("gate", "f"), block("gate", "f"), block("gate", "toString")],
  { scenes: [{ index: 0, name: "a\r\nPDEL 0", blocks: { f: { on: false, params: { x: 1, "y z": 2 } }, zz: {} } }, { index: 0 }, { index: 9 }, { index: "1" }, null] }, { name: "x\r\nPSAVE 0 y" + HIDDEN + " z", tags: ["a\nb", 5, ""], slot: "12A" }));
assert.deepStrictEqual(bad.sound.chain.map(b => [b.type, b.id]), [["gate", undefined], ["constructor", "d"], ["gate", "f"], ["gate", undefined], ["gate", undefined]]);
assert.ok(![bad.meta.name, bad.sound.scenes[0].name, ...bad.meta.tags].some(hidden));
assert.deepStrictEqual([bad.meta.name, bad.meta.tags, bad.meta.slot], ["x PSAVE 0 y z", ["a b"], undefined]);
assert.deepStrictEqual([bad.sound.scenes.length, Object.keys(bad.sound.scenes[0].blocks), { ...bad.sound.scenes[0].blocks.f.params }], [1, ["f"], { x: 1 }]);
assert.strictEqual(bad.sound.scenes[0].blocks.f.on, false);

// numbers only, whole, within reason; the rest is as if it were not there
const odd = only(preset([block("gate", "a", { on: "no", params: { a: "5", b: null, c: 1e400, d: 2.4, e: NaN, f: -100001, g: true, __proto__: 3 } })],
  { gain_db: { in: "1", out: 5000 }, tempo_bpm_x10: "900", color: "#12345", stereo: "yes", active_scene: 8, amp: { present: "x", on: false, tone: { bass: 5, other: 1, mid: "2" } } }));
assert.deepStrictEqual([{ ...odd.sound.chain[0].params }, odd.sound.chain[0].on], [{ d: 2 }, true]);
assert.deepStrictEqual([{ ...odd.sound.gain_db }, odd.sound.tempo_bpm_x10, odd.sound.color, odd.sound.stereo, odd.sound.active_scene], [{}, undefined, undefined, undefined, undefined]);
assert.deepStrictEqual([odd.sound.amp.present, odd.sound.amp.on, { ...odd.sound.amp.tone }], [true, false, { bass: 5 }]);

// nothing of the prototype
const proto = clean('{"format":"hyperrig-preset","version":1,"presets":[{"meta":{"name":"p","__proto__":{"polluted":1}},"sound":{"chain":[{"type":"gate","id":"__proto__","params":{"__proto__":5,"constructor":6}}],"scenes":[{"index":1,"blocks":{"__proto__":{"on":false}}}]}}],"attachments":{"__proto__":{"kind":"ir"},"constructor":{}}}');
assert.ok(proto.ok && ({}).polluted === undefined && proto.presets[0].sound.chain[0].id === undefined);
assert.deepStrictEqual(Object.keys(proto.doc.attachments), []);

// files: their size, their form and their place
const data = Buffer.alloc(300, 7), hash = "a".repeat(64);
const att = more => ({ kind: "ir", format: "tkgj", name: "V30", bytes: 300, sha256: hash, data: data.toString("base64"), rate_khz: 48, gain_mdb: -1500, ...more });
const kept = list => Object.keys(clean(file([preset([])], { attachments: list })).doc.attachments);
assert.deepStrictEqual(kept({ ir1: att(), "a b": att(), long: att({ data: data.toString("base64") + "AAAA" }), big: att({ bytes: 8153 }), kind: att({ kind: "exe" }), hash: att({ sha256: "x" }), text: att({ data: "*".repeat(400) }), n: 5, none: null }), ["ir1"]);
assert.strictEqual(kept(Object.fromEntries([...Array(60)].map((_, i) => ["k" + i, att()]))).length, MAX.files);
const cap = clean(file([preset([])], { attachments: { c: att({ kind: "capture", format: "a2l1", trim_db: 40, in_dbu: 12.5 }) } })).doc.attachments.c;
assert.deepStrictEqual([cap.kind, cap.trim_db, cap.in_dbu, cap.gain_mdb], ["capture", 0, 12.5, undefined]);

// where it came from: the places it can come from, and no other address
const from = origin => only(preset([], {}, { origin })).meta.origin;
assert.deepStrictEqual({ ...from({ title: "T", creator: "c", license: "CC BY", address: "https://patchstorage.com/x-y/", other: 1 }) }, { title: "T", creator: "c", license: "CC BY", address: "https://patchstorage.com/x-y/" });
for (const address of ["http://patchstorage.com/x", "https://evil.com/patchstorage.com/", "https://patchstorage.com.evil.com/", "javascript:alert(1)", "https://patchstorage.com/x?y=1", "https://u:p" + "@patchstorage.com/"])
  assert.strictEqual(from({ creator: "c", address }).address, undefined, address);
assert.strictEqual(from({ address: "x" }), undefined);

// what it needs
const p = only(preset([block("gate", "a"), block("newfx", "b"), { split: { a: [block("ir", "c", { ir: { name: "Own", bytes: 10 } })], b: [block("ir", "d")] } }, block("ir", "e")],
  { amp: { capture: { name: "Plexi", bytes: 4892 } }, cab_ir: { name: "V30" } }));
const lacks = needs(p, { type: t => t !== "newfx", capture: () => false, ir: r => r.name === "Own" });
assert.deepStrictEqual(lacks, { effects: ["newfx"], captures: ["Plexi"], irs: ["V30"] });
assert.deepStrictEqual(needs(p, { type: () => true, capture: () => true, ir: () => true }), { effects: [], captures: [], irs: [] });
assert.deepStrictEqual(needs(only(preset([], { amp: { present: false, capture: { name: "x" } } })), { type: () => true, capture: () => false, ir: () => false }).captures, []);
console.log("all tests passed");
