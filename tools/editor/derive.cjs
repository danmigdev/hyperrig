/* Derive presentation-only changes with parsed JavaScript boundaries. */
"use strict";
const fs = require("node:fs");
const crypto = require("node:crypto");
const acorn = require("acorn");

const sha = text => crypto.createHash("sha256").update(text).digest("hex");
const parse = source => acorn.parse(source, {ecmaVersion: "latest"});
const canonical = tree => JSON.stringify(tree, (key, value) =>
  ["start", "end", "loc", "raw"].includes(key) ? undefined : value);
function walk(node, visit) {
  if (!node || typeof node !== "object") return;
  if (node.type) visit(node);
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) value.forEach(item => walk(item, visit));
    else if (value && typeof value === "object") walk(value, visit);
  }
}
function apply(source, patches) {
  let last = source.length;
  for (const patch of patches.sort((a, b) => b.start - a.start)) {
    if (patch.end > last) throw Error("Overlapping presentation patches");
    source = source.slice(0, patch.start) + patch.text + source.slice(patch.end);
    last = patch.start;
  }
  return source;
}
function stripComments(source) {
  const comments = [];
  const before = acorn.parse(source, {ecmaVersion: "latest", onComment: comments});
  const result = apply(source, comments.map(c => ({...c,
    text: source.slice(c.start, c.end).replace(/[^\r\n]/g, " ")})));
  if (canonical(before) !== canonical(parse(result))) throw Error("Comment removal changed JavaScript semantics");
  return result;
}
function declaration(tree, name) {
  let found = null;
  for (const statement of tree.body) {
    if (statement.type === "VariableDeclaration") {
      for (const item of statement.declarations) if (item.id.name === name) found = item;
    }
  }
  return found;
}
function serialMethod(source) {
  const node = declaration(parse(source), "SerialTransport");
  const property = node && node.init.properties.find(p => p.key.name === "open");
  if (!property || !property.method) throw Error("Expected SerialTransport.open method");
  return source.slice(property.start, property.end);
}
function transformScript(source, config) {
  const tree = parse(source), patches = [], changes = [];
  const main = !!declaration(tree, "SerialTransport");
  const boot = source.includes('format: "boot-guard-1"');
  const add = (node, text, reason) => {patches.push({start: node.start, end: node.end, text}); changes.push(reason);};
  const issue = `window.open(${JSON.stringify(config.issues)}, "_blank", "noopener,noreferrer");`;
  const functions = {
    langStored: 'function langStored() { return "en"; }',
    langGuess: 'function langGuess() { return "en"; }',
    setLang: 'function setLang(language) { return language === "en"; }',
    noteClick: 'function noteClick() {}',
    reportSend: `async function reportSend() { ${issue} return "github"; }`,
    reportOpen: `async function reportOpen() { ${issue} }`,
    updFetch: 'async function updFetch() { return null; }',
    updStart: 'function updStart() { return false; }',
    updRun: 'async function updRun() { return false; }',
    updBoot: 'function updBoot() {}',
    guideLink: `function guideLink(section, label) { return {href: ${JSON.stringify(config.documentation)}, label: label || "HyperRig documentation"}; }`,
    updUrlOk: `function updUrlOk(url) { return typeof url === "string" && (url === ${JSON.stringify(config.releases)} || url.startsWith(${JSON.stringify(config.releases + "/")})); }`,
  };
  const initializers = {
    LANGS: '{en: "English"}', I18N_ES: '{}', I18N: '{en: null}', GUIDES: '{}',
    LANG: '"en"', LANG_ASK: 'false', numL: 'value => value',
    REPORT_URL: JSON.stringify(config.issues), REPORT_KEY: '""',
    CLICK_URL: '""', CLICK_KINDS: '[]', UPD_URL: '""', UPD_LINK: JSON.stringify(config.releases),
    DEMO_APP_URL: JSON.stringify(config.releases), FW_DL_URL: JSON.stringify(config.documentation),
  };
  if (main) {
    for (const statement of tree.body) {
      if (statement.type === "FunctionDeclaration" && functions[statement.id.name]) {
        add(statement, functions[statement.id.name], statement.id.name);
      }
      if (statement.type === "VariableDeclaration") for (const item of statement.declarations) {
        if (Object.hasOwn(initializers, item.id.name)) add(item.init, initializers[item.id.name], item.id.name);
      }
      if (statement.type === "IfStatement" && source.slice(statement.start, statement.end).includes("noteClick(CLICK_KINDS")) {
        add(statement, "", "remove donation click listener");
      }
    }
    for (const expected of ["LANGS", "I18N_ES", "LANG", "LANG_ASK", "reportOpen", "reportSend", "updStart", "noteClick"])
      if (!changes.includes(expected)) throw Error("Missing expected presentation boundary: " + expected);
  }
  if (boot) walk(tree, node => {
    if (node.type === "VariableDeclarator" && node.id.name === "es") add(node.init, "false", "English boot guard");
    if (node.type === "VariableDeclarator" && node.id.name === "TX") {
      if (node.init.type !== "ConditionalExpression") throw Error("Boot guard language boundary changed");
      add(node.init, source.slice(node.init.alternate.start, node.init.alternate.end), "English boot messages");
    }
    if (node.type === "FunctionDeclaration" && node.id.name === "send")
      add(node, `function send(btn, note) { ${issue} note.nodeValue = "Review and submit your issue on GitHub."; }`, "GitHub boot report");
  });
  let result = apply(source, patches);
  // These are local diagnostic/scene labels, not wire protocol identifiers.
  // Rename both disconnect reason values and their matching comparisons.
  const labels = {"usuario": "user", "otra pestaña": "another tab", "vacía": "empty"};
  const labelPatches = [];
  walk(parse(result), node => {
    if (node.type === "Literal" && typeof node.value === "string" && Object.hasOwn(labels, node.value))
      labelPatches.push({start: node.start, end: node.end, text: JSON.stringify(labels[node.value])});
  });
  result = apply(result, labelPatches);
  if (labelPatches.length) changes.push("English disconnect and scene labels");
  result = stripComments(result);
  if (main) {
    const after = parse(result);
    for (const name of ["SerialTransport", "BleTransport", "Pedal"]) {
      const beforeNode = declaration(tree, name), afterNode = declaration(after, name);
      if (beforeNode && (!afterNode || canonical(beforeNode) !== canonical(afterNode)))
        throw Error("Presentation changes modified device transport: " + name);
    }
  }
  return {source: result, changes, main};
}
function transformHtml(html, config) {
  const changes = [];
  html = html.replace(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi, (all, attrs, source) => {
    if (/\bsrc\s*=/.test(attrs) || !source.trim()) return all;
    const derived = transformScript(source, config);
    changes.push(...derived.changes);
    return `<script${attrs}>${derived.source}</script>`;
  });
  const once = (pattern, replacement, reason) => {
    let count = 0;
    html = html.replace(pattern, () => {count++; return replacement;});
    if (count !== 1) throw Error(`Expected one ${reason}, found ${count}`);
    changes.push(reason);
  };
  once(/<div class="langpick"[^>]*>[\s\S]*?<\/div><\/div>/g, "", "language picker");
  once(/<label class="spill langrow">[\s\S]*?<\/label>/g, "", "language setting");
  once(/<div class="support" id="support">[\s\S]*?<\/div>/g, "", "donation controls");
  once(/<div class="support" id="community">[\s\S]*?<\/div>/g,
    `<div class="support" id="community"><p><a href="${config.repository}" target="_blank" rel="noopener noreferrer">HyperRig on GitHub</a></p><p><a href="${config.releases}" target="_blank" rel="noopener noreferrer">HyperRig releases</a></p></div>`, "project links");
  once(/<label class="spill"[^>]*><input type="checkbox" id="updChk"[^>]*> Check for updates<\/label>/g, "", "automatic update setting");
  html = html.replace(/<!--[^]*?-->/g, "").replace(/<style([^>]*)>([\s\S]*?)<\/style>/gi,
    (_, attrs, css) => `<style${attrs}>${css.replace(/\/\*[\s\S]*?\*\//g, "")}</style>`);
  for (const [from, to] of [
    ["Send report to the developer…", "Report an issue on GitHub…"],
    ["Send report…", "Report an issue…"], ["Send a report", "Open GitHub issues"],
    ["Send the error to the developer", "Report this error on GitHub"],
    ["https://hyperrig.invalid/source/releases/latest", config.releases],
    ["https://hyperrig.invalid/source/", config.repository + "/"],
    ["https://hyperrig.invalid/#download", config.documentation],
    ["https://hyperrig.invalid", config.repository],
    ["hyperrig.invalid/source/issues", config.repository + "/issues"],
    ["hyperrig.app", config.repository],
  ]) html = html.split(from).join(to);
  html = html.replace(/<html\s+lang="[^"]*"/i, '<html lang="en"');
  const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m => !/\bsrc\s*=/.test(m[1]));
  scripts.forEach(m => parse(m[2]));
  const main = scripts.find(m => declaration(parse(m[2]), "SerialTransport"));
  if (!main) throw Error("No editor script after derivation");
  if (/buy me a coffee|mercado pago|sb_publishable_|hyperrig\.invalid|https?:\/\/ultrarig\.app|github\.com\/manuaguirre9\/ultrarig/i.test(html))
    throw Error("Obsolete product link, donation, or telemetry remains");
  return {html, changes, serialMethod: serialMethod(main[2]), sha256: sha(html)};
}

module.exports = {transformHtml, stripComments, transformScript, canonical, parse, serialMethod};
if (require.main === module) {
  const [input, output, configPath, reportPath] = process.argv.slice(2);
  if (!reportPath) throw Error("Usage: node derive.cjs INPUT OUTPUT CONFIG REPORT");
  const result = transformHtml(fs.readFileSync(input, "utf8"), JSON.parse(fs.readFileSync(configPath, "utf8")));
  fs.writeFileSync(output, result.html, "utf8");
  delete result.html;
  fs.writeFileSync(reportPath, JSON.stringify(result, null, 2) + "\n", "utf8");
}
