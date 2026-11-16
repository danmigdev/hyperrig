"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const {parse} = require("../tools/editor/derive.cjs");
const {transform} = require("../tools/editor/derive_mini_v4.cjs");
const source = fs.readFileSync("build/hyperrig-mini-installer-one-switch-preview-04/editor/web/tankmini.html", "utf8");
const result = transform(source);
const script = [...result.html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
  .map(m => m[1]).find(s => s.includes("const PRESETS_PER_BANK"));
const tree = parse(script);
function extract(name) {
  for (const n of tree.body) {
    if (n.type === "FunctionDeclaration" && n.id.name === name) return script.slice(n.start, n.end);
    if (n.type === "VariableDeclaration") for (const d of n.declarations)
      if (d.id.name === name) return "const " + script.slice(d.start, d.end) + ";";
  }
  throw Error("Missing declaration: " + name);
}
function node() {
  return {children: [], dataset: {}, style: {}, parts: {}, setAttribute() {},
    appendChild(n) { this.children.push(n); },
    set innerHTML(value) { this.content = value; this.children = []; },
    get innerHTML() { return this.content; },
    querySelector(selector) { return this.parts[selector] ||= node(); }};
}
const elements = Object.fromEntries(["presetLbl", "presetBtn", "banks", "pList"].map(k => [k, node()]));
const loaded = [], saved = [];
const context = {
  bank: 0, plist: [[0, "One"], [3, "Two"], [31, "Last"]], curPreset: 3,
  S: {}, $: id => elements[id], document: {createElement: node},
  stRender() {}, T: text => text, esc: text => text, presetDots: () => "",
  MORE_ICO: "", ied: null, PH: false, lastPtr: "touch", PN_DBL_MS: 280,
  pnClickT: 0, pnFired: {}, clearTimeout() {},
  loadPreset(n) { loaded.push(n); }, newPedalboard() {}, refocusSoon() {},
  savePreset(n) { saved.push(n); },
};
vm.createContext(context);
vm.runInContext(["PRESETS_PER_BANK", "PRESET_N", "SLOT", "slotTxt", "renderPresets", "fwPublic", "relNum", "PAGE_RELEASE"].map(extract).join("\n"), context);
assert.equal(vm.runInContext("slotTxt(2)", context), "1C");
assert.equal(vm.runInContext("slotTxt(3)", context), "2A");
assert.equal(vm.runInContext("slotTxt(31)", context), "11B");
assert.equal(vm.runInContext('fwPublic("tankm_fw M5.71 rel ble")', context), "MINI v4 preview");
assert.equal(vm.runInContext("relNum(PAGE_RELEASE)", context), "v4 preview");
const ids = [];
for (let bank = 0; bank < 11; bank++) {
  context.bank = bank;
  vm.runInContext("renderPresets()", context);
  assert.equal(elements.banks.children.length, 11);
  assert.equal(elements.pList.children.length, bank === 10 ? 2 : 3);
  for (const row of elements.pList.children) {
    ids.push(row.dataset.preset);
    row.querySelector('[data-a="s"]').onclick();
    if ([0, 3, 31].includes(row.dataset.preset)) row.querySelector(".n").onclick();
  }
}
assert.deepEqual(ids, Array.from({length: 32}, (_, n) => n));
assert.deepEqual(saved, ids);
assert.deepEqual(loaded, [0, 3, 31]);
assert.match(elements.presetLbl.innerHTML, /2A/);
assert.match(result.html, /<span class="alpha">MINI<\/span>/);
assert.equal(result.report.scene_capacity, 4);
assert.equal(result.report.physical_switch_dispatch_changed, false);
assert.throws(() => transform(source.replace('const SLOT =', 'const REMOVED =')));
console.log("MINI presentation: all 32 raw preset IDs, A/B/C banks, final bank bounds and version labels passed (offline).");
