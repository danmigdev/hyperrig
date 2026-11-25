/* The installer's page: it shows what the core says and gives it what it works with, the pedal's MIDI and serial ports, the
 * backups that the desktop program keeps, and the firmware. It decides nothing about the pedal. */
"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const EDITOR = "hyperrig://editor/tank-mini.html";
  let view = null, asking = null, installer = null;

  /* ---- the screen ---- */
  function act(name) {
    if (name === "editor") { location.href = EDITOR; return; }
    if (installer) installer.act(name).catch(e => log("act: " + (e && e.stack || e)));
  }
  function button(a, first) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = a.label;
    b.className = a.weight === "quiet" ? "quiet" : first ? "big" : "big plain";
    b.dataset.act = a.id;
    b.onclick = () => a.ask ? ask(a) : act(a.id);
    return b;
  }
  function ask(a) {
    asking = a.id;
    $("askTitle").textContent = a.ask.title;
    $("askText").textContent = a.ask.text;
    $("askYes").textContent = a.ask.yes;
    $("ask").showModal();
    $("askYes").focus();
  }
  $("askYes").onclick = () => { const id = asking; $("ask").close(); if (id) act(id); };
  $("askNo").onclick = () => $("ask").close();
  $("ask").addEventListener("close", () => { asking = null; });

  function show(v) {
    const before = view;
    view = v;
    document.body.dataset.screen = v.screen;
    $("over").textContent = v.over || "";
    $("title").textContent = v.title;
    $("text").textContent = v.text || "";
    $("safe").textContent = v.safe || "";
    $("pedalFw").textContent = v.pedal || "";
    const working = v.screen === "work", step = working ? v.step : v.screen === "done" ? 3 : -1;
    $("work").hidden = $("keep").hidden = !working;
    for (const list of [document.querySelectorAll("#steps li"), document.querySelectorAll("#pedal .led")])
      list.forEach((e, n) => { e.classList.toggle("now", working && n === step); e.classList.toggle("done", n < step); });
    if (working) {
      const p = Math.round(100 * (v.progress || 0));
      $("meterFill").style.width = p + "%";
      $("meter").setAttribute("aria-valuenow", p);
    }
    if (!before || JSON.stringify(before.actions) !== JSON.stringify(v.actions)) {
      if ($("ask").open) $("ask").close();
      $("actions").replaceChildren(...(v.actions || []).map((a, i) => button(a, i === 0)));
    }
  }
  function details(open) { $("details").hidden = !open; $("detailsBtn").setAttribute("aria-expanded", String(open)); }
  $("detailsBtn").onclick = () => details($("details").hidden);
  $("detailsX").onclick = () => details(false);
  $("copyBtn").onclick = () => navigator.clipboard.writeText($("log").textContent);
  $("folderBtn").onclick = () => fetch("store/open", { method: "POST" });
  $("editorBtn").onclick = () => { if (!installer || !installer.busy) location.href = EDITOR; };
  addEventListener("keydown", e => { if (e.key === "Escape" && !$("ask").open) details(false); });
  addEventListener("beforeunload", e => { if (installer && installer.busy) e.preventDefault(); });

  let rows = [], later = 0;
  function log(text) {
    const line = new Date().toISOString().slice(11, 19) + " " + text;
    $("log").textContent += line + "\n";
    $("log").scrollTop = $("log").scrollHeight;
    rows.push({ t: new Date().toISOString(), kind: "installer", text: String(text) });
    clearTimeout(later);
    later = setTimeout(() => { const some = rows; rows = []; fetch("log", { method: "POST", body: JSON.stringify(some) }).catch(() => {}); }, 200);
  }

  /* ---- what the core works with ---- */
  const { midiOf } = HrWebMidi;
  const serial = navigator.serial ? HrSerial.serialOf(navigator.serial, { log }) : null;

  const good = async r => { if (!r.ok) throw new Error(`${r.url}: ${r.status}`); return r; };
  const bytes = async r => new Uint8Array(await (await good(r)).arrayBuffer());
  const at = (what, q) => "store/" + what + "?" + new URLSearchParams(q);
  const store = {
    backups: async unit => (await good(await fetch(at("backups", { unit }), { cache: "no-store" }))).json(),
    note: async unit => (await good(await fetch(at("note", { unit }), { cache: "no-store" }))).json(),
    load: async (unit, name) => bytes(await fetch(at("load", { unit, name }), { cache: "no-store" })),
    save: async (unit, kind, data, about) => (await (await good(await fetch(at("save", { unit, kind, about: JSON.stringify(about) }), { method: "POST", body: data }))).json()).name,
    keep: async (unit, note) => { await good(await fetch(at("keep", { unit }), { method: "POST", body: JSON.stringify(note) })); },
  };
  const sha256 = async data => Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", data)), b => b.toString(16).padStart(2, "0")).join("");
  async function firmware() {
    const about = await (await good(await fetch("firmware/firmware.json", { cache: "no-store" }))).json(), out = { version: about.version, build: about.build, stored: about.stored };
    for (const [name, key] of [["image.bin", "image"], ["stage-package.bin", "pack"], ["stage-code.bin", "code"]]) {
      out[key] = await bytes(await fetch("firmware/" + name, { cache: "no-store" }));
      if (await sha256(out[key]) !== about.sha256[name]) throw new Error("firmware/" + name);
    }
    return out;
  }

  (async () => {
    show(HrViews.search());
    let assets;
    try { assets = await firmware(); } catch (e) { log("firmware: " + e.message); show(HrViews.trouble("damaged", { again: false })); return; }
    log(`HyperRig ${assets.version} ${assets.build}, loader package of ${assets.pack.length} bytes`);
    let access;
    try { access = await navigator.requestMIDIAccess({ sysex: true }); } catch (e) { log("MIDI: " + e.message); show(HrViews.trouble("busy")); return; }
    const env = { midi: midiOf(access), serial, store, sha256, now: () => Date.now(), sleep: ms => new Promise(done => setTimeout(done, ms)) };
    installer = new HrFlow.Installer(env, assets, { show, log, times: window.HYPERRIG_TIMES || {} });
    await installer.watch();
  })();
})();
