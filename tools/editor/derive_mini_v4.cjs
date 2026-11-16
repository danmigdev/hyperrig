/* Derive the MINI preset presentation without changing device slot IDs. */
"use strict";
const fs = require("node:fs");
const crypto = require("node:crypto");
const {parse, canonical} = require("./derive.cjs");
const sha = value => crypto.createHash("sha256").update(value).digest("hex");
function walk(node, visit) {
  if (!node || typeof node !== "object") return;
  if (node.type) visit(node);
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) value.forEach(child => walk(child, visit));
    else if (value && typeof value === "object") walk(value, visit);
  }
}
function declaration(tree, name) {
  let found;
  walk(tree, n => { if (n.type === "VariableDeclarator" && n.id.name === name) found = n; });
  return found;
}
function transform(html) {
  const original = html, changes = [];
  html = html.replace(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi, (all, attrs, source) => {
    if (/\bsrc\s*=/.test(attrs) || !source.includes('const SLOT =')) return all;
    const tree = parse(source), patches = [];
    const add = (node, text, reason) => {
      patches.push({start: node.start, end: node.end, text}); changes.push(reason);
    };
    const code = node => source.slice(node.start, node.end);
    const labels = new Set(["n", "pn", "a", "slot", "curPreset", "cp[0]"]);
    walk(tree, node => {
      if (node.type === "VariableDeclarator") {
        const initializers = {
          PAGE_RELEASE: '"mini-v4-preview"', FW_PUBLIC: '[]',
          relNum: '() => "v4 preview"',
          SLOT: 'i => "ABC"[i % PRESETS_PER_BANK]',
        };
        if (Object.hasOwn(initializers, node.id.name)) add(node.init, initializers[node.id.name], node.id.name);
      }
      if (node.type === "FunctionDeclaration" && node.id.name === "fwPublic")
        add(node, 'function fwPublic(m) { return /^tankm_fw /.test(String(m)) ? "MINI v4 preview" : String(m); }', "firmware display name");
      if (node.type === "BinaryExpression" && node.operator === "/" && node.right.value === 4 && labels.has(code(node.left)))
        add(node.right, "PRESETS_PER_BANK", "preset bank label");
      if (node.type === "BinaryExpression" && node.operator === ">>" && node.right.value === 2 && ["curPreset", "p[0]"].includes(code(node.left)))
        add(node, `Math.floor(${code(node.left)} / PRESETS_PER_BANK)`, "preset bank selection");
      if (node.type === "CallExpression" && node.callee.name === "SLOT") {
        const arg = node.arguments[0];
        if (arg && arg.type === "BinaryExpression" && arg.operator === "%" && arg.right.value === 4)
          add(arg, code(arg.left), "slot letter from device ID");
      }
      if (node.type === "MemberExpression" && node.object.value === "ABCD" && code(node.property) === "n % 4")
        add(node, "SLOT(n)", "diagnostic preset label");
      if (node.type === "Literal" && node.value === "New in alpha {n}")
        add(node, JSON.stringify("What's new in HyperRig"), "tour heading");
    });
    const render = tree.body.find(n => n.type === "FunctionDeclaration" && n.id.name === "renderPresets");
    if (!render) throw Error("Preset renderer is missing");
    walk(render, node => {
      if (node.type !== "BinaryExpression") return;
      if (code(node) === "i < 8") add(node, "i < Math.ceil(PRESET_N / PRESETS_PER_BANK)", "bank count");
      if (code(node) === "k < 4") add(node, "k < PRESETS_PER_BANK && bank * PRESETS_PER_BANK + k < PRESET_N", "three rows and final bank bound");
      if (code(node) === "bank * 4") add(node, "bank * PRESETS_PER_BANK", "device slot from bank and row");
    });
    const slot = tree.body.find(n => n.type === "VariableDeclaration" && n.declarations.some(d => d.id.name === "SLOT"));
    patches.push({start: slot.start, end: slot.start, text: "const PRESETS_PER_BANK = 3;\n"});
    let result = source, last = source.length;
    for (const p of patches.sort((a, b) => b.start - a.start || b.end - a.end)) {
      if (p.end > last) throw Error("Overlapping MINI presentation changes");
      result = result.slice(0, p.start) + p.text + result.slice(p.end); last = p.start;
    }
    const after = parse(result);
    for (const name of ["SerialTransport", "BleTransport", "Pedal", "fmSlot", "PRESET_N", "PLIST_PRE"]) {
      if (canonical(declaration(tree, name)) !== canonical(declaration(after, name)))
        throw Error("MINI presentation changed a protected protocol declaration: " + name);
    }
    return `<script${attrs}>${result}</script>`;
  });
  const brand = '<span class="alpha">Alpha</span>';
  if (html.split(brand).length !== 2) throw Error("Expected one upstream release badge");
  html = html.replace(brand, '<span class="alpha">MINI</span>');
  if (!changes.includes("three rows and final bank bound") || !changes.includes("firmware display name"))
    throw Error("MINI presentation anchors changed");
  return {html, report: {kind: "hyperrig-mini-v4-presentation", source_sha256: sha(original),
    derived_sha256: sha(html), presets_per_bank: 3, preset_capacity: 32, scene_capacity: 4,
    raw_preset_ids_preserved: true, physical_switch_dispatch_changed: false,
    device_io: false, changes}};
}
module.exports = {transform};
if (require.main === module) {
  const [input, output, report] = process.argv.slice(2);
  if (!report) throw Error("Usage: node derive_mini_v4.cjs INPUT OUTPUT REPORT");
  const result = transform(fs.readFileSync(input, "utf8"));
  fs.writeFileSync(output, result.html);
  fs.writeFileSync(report, JSON.stringify(result.report, null, 2) + "\n");
}
