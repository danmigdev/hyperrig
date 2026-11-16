"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const {transformHtml, parse, canonical} = require("../tools/editor/derive.cjs");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "build/hyperrig-mini-fx-editor/app/web/tankmini.html"), "utf8");
const config = JSON.parse(fs.readFileSync(path.join(root, "app/project.json"), "utf8"));
const result = transformHtml(source, config);
function main(html) {
  return [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
    .map(m => m[2]).find(s => /const SerialTransport\s*=/.test(s));
}
function declarations(text) {
  const result = new Map();
  for (const node of parse(text).body) {
    if (node.type === "VariableDeclaration") for (const value of node.declarations) result.set(value.id.name, value);
    if (node.type === "FunctionDeclaration") result.set(node.id.name, node);
  }
  return result;
}
const before = declarations(main(source)), after = declarations(main(result.html));

test("USB, Bluetooth and command dispatch retain the same parsed implementation", () => {
  for (const name of ["SerialTransport", "BleTransport", "Pedal"]) {
    assert.ok(before.has(name), name);
    assert.equal(canonical(after.get(name)), canonical(before.get(name)), name);
  }
});
test("reporting opens only the configured GitHub issue form", async () => {
  for (const name of ["reportOpen", "reportSend"]) {
    const node = after.get(name), code = main(result.html).slice(node.start, node.end), opened = [];
    const context = {window: {open: (...args) => opened.push(args)}};
    vm.runInNewContext(code, context);
    await context[name]({secret: "must not appear in the URL"});
    assert.deepEqual(opened, [[config.issues, "_blank", "noopener,noreferrer"]]);
  }
});
test("disconnect reason translation preserves connection control flow", () => {
  const original = before.get("connect"), translated = JSON.parse(JSON.stringify(after.get("connect")));
  function normalize(node) {
    if (!node || typeof node !== "object") return;
    if (node.type === "Literal") {
      if (node.value === "user") node.value = "usuario";
      if (node.value === "another tab") node.value = "otra pestaña";
    }
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) value.forEach(normalize);
      else if (value && typeof value === "object") normalize(value);
    }
  }
  normalize(translated);
  assert.equal(canonical(original), canonical(translated));
});
test("guide links open the project's maintained documentation", () => {
  const node = after.get("guideLink"), context = {};
  vm.runInNewContext(main(result.html).slice(node.start, node.end), context);
  assert.equal(context.guideLink("02").href, config.documentation);
  assert.equal(context.guideLink("04").label, "HyperRig documentation");
});
test("language and startup behavior cannot select another locale", () => {
  assert.equal(after.get("LANG").init.value, "en");
  assert.equal(after.get("LANG_ASK").init.value, false);
  assert.deepEqual(after.get("LANGS").init.properties.map(p => p.key.name), ["en"]);
  assert.equal(after.get("I18N_ES").init.properties.length, 0);
  assert.doesNotMatch(result.html, /id="(?:langSel|langPick)"/);
});
test("donations, old endpoints and embedded service keys are absent", () => {
  assert.doesNotMatch(result.html, /buy me a coffee|mercado pago|sb_publishable_|hyperrig\.invalid|manuaguirre9|id="support"/i);
  assert.doesNotMatch(result.html, /id="updChk"/);
  assert.equal(after.get("REPORT_KEY").init.value, "");
});
test("unexpected upstream layout fails instead of applying partial branding", () => {
  assert.throws(() => transformHtml(source.replace('id="support"', 'id="unexpected-support"'), config), /donation controls/);
});
