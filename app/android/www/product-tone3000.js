/* TONE3000 in the desktop program: Browse TONE3000 in the libraries of captures and cab IRs. The program signs in and fetches
 * (app/desktop/tone3000.js); this part asks, shows what was chosen, and hands the file to the page's own upload. The creator, the
 * licence and the address of a tone stay with its slot, on this computer. In a browser this does nothing. */
(function () {
  "use strict";
  if (location.protocol !== "hyperrig:") return;
  const KEPT = "hr.t3k.slots", HELLO = "hr.t3k.hello";
  const read = (key, other) => { try { const v = JSON.parse(localStorage.getItem(key)); return v && typeof v === "object" ? v : other; } catch (e) { return other; } };
  const write = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* it is only a note */ } };
  const post = async what => { const r = await fetch("tone3000/" + what, { method: "POST", cache: "no-store" }); return r; };
  const el = (tag, attributes, ...children) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attributes || {})) if (k === "text") e.textContent = v; else if (k.startsWith("on")) e[k] = v; else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? "" : v);
    e.append(...children.filter(c => c !== null && c !== undefined));
    return e;
  };
  const logo = (cls, mark) => el("img", { src: mark ? "t3k-mark.svg" : "tone3000-logo.svg", alt: "TONE3000", class: cls });
  const link = (address, text) => el("a", { href: address, target: "_blank", rel: "noopener noreferrer", text });
  const LICENSES = { "t3k": "T3K licence", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc-by-nc": "CC BY-NC", "cc-by-nc-sa": "CC BY-NC-SA", "cc-by-nd": "CC BY-ND", "cc-by-nc-nd": "CC BY-NC-ND", "cco": "CC0", "cc0": "CC0" };
  const licence = v => LICENSES[String(v).toLowerCase()] || String(v || "see TONE3000");
  let available = false, signedIn = false, working = false;

  function ask(build) {
    return new Promise(resolve => {
      const d = el("dialog", { class: "t3k" });
      const done = value => { d.close(); d.remove(); resolve(value); };
      d.addEventListener("cancel", e => { e.preventDefault(); done(null); });
      d.append(build(done, d));
      document.body.append(d);
      d.showModal();
    });
  }
  const by = () => el("div", { class: "tby" }, el("span", {}, "Powered by ", link("https://www.tone3000.com", "TONE3000")), logo("", true));

  function hello() {
    return ask(done => el("div", { class: "tin" }, logo("tlogo"), el("h2", { text: "Captures and cab IRs from TONE3000" }),
      el("p", { text: "Browse the tones that players share on TONE3000 and load one straight into the pedal. You choose on TONE3000's own page and sign in there with your own account: HyperRig does not see your e-mail or your code." }),
      el("div", { class: "tacts" }, el("button", { class: "btn", type: "button", text: "Not now", onclick: () => done(false) }), el("button", { class: "btn primary", type: "button", text: "Continue to TONE3000", onclick: () => done(true) })), by()));
  }

  function choose(kind, got) {
    const { tone, models } = got;
    return ask(done => {
      const radios = models.map((m, i) => { const input = el("input", { type: "radio", name: "t3kmodel", value: m.id }); input.checked = i === 0; return el("label", {}, input, el("span", { text: m.name }), el("span", { class: "sz", text: m.size })); });
      const list = el("div", { class: "tlist", role: "radiogroup", "aria-label": "Model" }, ...radios);
      const head = el("div", { class: "thead" + (tone.picture ? "" : " nopic") }, tone.picture ? el("img", { class: "tpic", src: "tone3000/picture?id=" + tone.id, alt: "", onerror: e => { e.target.parentElement.classList.add("nopic"); e.target.remove(); } }) : null,
        el("div", { class: "tmeta" }, el("h2", { text: tone.title }), el("span", {}, "by ", el("b", { text: tone.creator })), el("span", { text: [tone.gear, tone.makes.join(", ")].filter(Boolean).join(" · ") }),
          el("span", { text: "Licence: " + licence(tone.license) }), link(tone.address, "See it on TONE3000")));
      return el("div", { class: "tin" }, logo("tlogo"), head, tone.description ? el("p", { text: tone.description }) : null, models.length > 1 ? list : null,
        el("div", { class: "tacts" }, el("button", { class: "btn", type: "button", text: "Cancel", onclick: () => done(null) }), el("button", { class: "btn", type: "button", text: "Choose another", onclick: () => done("again") }),
          el("button", { class: "btn", type: "button", text: "Load into the pedal", onclick: () => done(Number(models.length > 1 ? list.querySelector("input:checked").value : models[0].id)) }),
          el("button", { class: "btn primary", type: "button", text: "Try it", title: "Hear it on the pedal, without using a slot", onclick: () => done({ at: models.length > 1 ? radios.findIndex(r => r.querySelector("input").checked) : 0 }) })), by());
    });
  }

  async function thumbnail(tone) {
    if (!tone.picture) return null;
    try {
      const r = await fetch("tone3000/picture?id=" + tone.id); if (!r.ok) return null;
      const image = await createImageBitmap(await r.blob()), c = document.createElement("canvas"), side = Math.min(image.width, image.height);
      c.width = c.height = 96;
      c.getContext("2d").drawImage(image, (image.width - side) / 2, (image.height - side) / 2, side, side, 0, 0, 96, 96);
      return c.toDataURL("image/jpeg", 0.8);
    } catch (e) { return null; }
  }

  async function fetched(id) {
    const r = await post("model?id=" + id);
    if (!r.ok) { let m = "The file could not be fetched."; try { m = (await r.json()).error.message; } catch (e) { /* the usual words */ } throw new Error(m); }
    return new File([await r.arrayBuffer()], decodeURIComponent(r.headers.get("x-file-name") || "TONE3000"));
  }
  /* What came from TONE3000 is noted beside its slot. */
  function keepNote(lib, slot, name, tone, model, picture) {
    const slots = read(KEPT, {});
    slots[lib + ":" + slot] = { name, title: tone.title, creator: tone.creator, license: tone.license, gear: tone.gear, address: tone.address, model, picture };
    write(KEPT, slots);
    decorate();
  }
  /* The models of the tone are heard one after the other without a slot; each is fetched when it is asked for. */
  async function tryThem(kind, tone, models, at) {
    const lib = kind === "capture" ? "cap" : "ir";
    const items = models.map(m => {
      let file = null;
      return { kind, name: models.length > 1 ? `${tone.title} ${m.name}` : tone.title, by: tone.creator, license: licence(tone.license), address: tone.address, get: async () => file || (file = await fetched(m.id)),
        kept: (slot, name) => { keepNote(lib, slot, name, tone, m.name, null); void thumbnail(tone).then(p => { if (p) keepNote(lib, slot, name, tone, m.name, p); }); } };
    });
    await hrTry.start(kind, items, at);
  }
  /* A free slot, and the page's own upload into it. */
  async function load(kind, tone, models, id) {
    const cap = kind === "capture", lib = cap ? "cap" : "ir";
    let file;
    try { file = await fetched(id); } catch (e) { toast(String(e.message || e), "err", { title: "TONE3000" }); return; }
    if (!S.connected) { toast("Connect the pedal first.", "err"); return; }
    await openLib(lib, true);
    const used = new Set((window.libRows || []).map(x => x[0]));
    let slot = 0;
    while (slot < libSlots && used.has(slot)) slot++;
    if (slot >= libSlots) { toast("All slots are in use: delete one first.", "err"); return; }
    const picture = await thumbnail(tone);
    await (cap ? uploadCaptures([file], slot) : uploadIrs([file], slot));
    if (!S.connected) return;
    await openLib(lib, true);
    const row = (window.libRows || []).find(x => x[0] === slot);
    if (!row) return;
    keepNote(lib, slot, row[1], tone, (models.find(m => m.id === id) || {}).name || "", picture);
  }

  async function browse() {
    if (working) return;
    if (!S.connected && !DEMO) { toast("Connect the pedal first.", "err"); return; }
    if (capJobs) { toast("Wait for the current uploads to finish.", "err"); return; }
    if (hrTry.on) { toast("You are trying a sound. Keep it or go back first.", "err"); return; }
    working = true;
    update();
    try {
      const kind = libKind === "cap" ? "capture" : "ir";
      if (!signedIn && !read(HELLO, null)) { if (!await hello()) return; write(HELLO, { seen: true }); }
      for (;;) {
        const got = await (await post("select?kind=" + kind)).json();
        await status();
        if (got.canceled) return;
        if (got.error) { toast(got.error.message, "err", { title: "TONE3000" }); return; }
        const id = await choose(kind, got);
        if (id === "again") continue;
        if (id && typeof id === "object") await tryThem(kind, got.tone, got.models, Math.max(0, id.at));
        else if (id) await load(kind, got.tone, got.models, id);
        return;
      }
    } catch (e) { toast("Something went wrong with TONE3000. Try again.", "err"); Log.ev("tone3000", { err: String(e && e.message || e) }); }
    finally { working = false; update(); }
  }

  async function status() { try { const s = await (await fetch("tone3000/status", { cache: "no-store" })).json(); available = !!s.available; signedIn = !!s.signedIn; } catch (e) { available = false; } update(); }
  const button = el("button", { class: "btn t3kbtn", id: "t3kBrowse", type: "button", hidden: true, onclick: browse }, el("span", { text: "Browse" }), logo(""));
  const out = el("button", { class: "btn mini", id: "t3kOut", type: "button", text: "Sign out of TONE3000", onclick: async () => { await post("signout"); await status(); toast("Signed out of TONE3000.", "ok"); } });
  const section = el("section", { id: "t3kSection", hidden: true }, el("h3", { text: "TONE3000" }), el("p", { class: "spill" }, el("span", {}, "Powered by ", link("https://www.tone3000.com", "TONE3000"))), el("div", { class: "row wrap" }, out));
  function update() {
    button.hidden = !available; button.disabled = working || !!(typeof capJobs !== "undefined" && capJobs);
    section.hidden = !available; out.hidden = !signedIn;
  }
  const add = document.getElementById("libAdd");
  if (add) add.after(button);
  const sections = document.querySelectorAll("#settings .dbox > section");
  if (sections.length) sections[sections.length - 1].before(section);

  /* The mark, the creator and the licence, where the tone is listed and where it plays. */
  const infoOf = (lib, slot, name) => { const i = read(KEPT, {})[lib + ":" + slot]; return i && i.name === name ? i : null; };
  const line = i => el("a", { class: "t3kline", href: i.address, target: "_blank", rel: "noopener noreferrer", title: "See it on TONE3000" }, logo("", true), el("span", { text: `${i.title} · ${i.creator} · ${licence(i.license)}` }));
  let wanted = 0;
  function decorate() {
    clearTimeout(wanted);
    wanted = setTimeout(() => {
      for (const row of document.querySelectorAll("#libL .lslot")) {
        const r = (window.libRows || []).find(x => x[0] === Number(row.dataset.slot)), i = r ? infoOf(libKind, r[0], r[1]) : null, old = row.querySelector(".t3kline");
        if (i && !old) row.append(line(i)); else if (!i && old) old.remove();
      }
      const playing = typeof S !== "undefined" && S.capSlot >= 0 ? read(KEPT, {})["cap:" + S.capSlot] : null, shown = playing && playing.name === S.model ? playing : null;
      const amp = document.querySelector("#chain .amp"), mark = amp && amp.querySelector(".t3kmark");
      if (amp && shown && !mark) amp.append(el("span", { class: "t3kmark" }, logo("", true))); else if (mark && !shown) mark.remove();
      const head = document.getElementById("ampLoad") ? document.querySelector("#editor .ed-head") : null, card = document.querySelector("#editor .t3kcard");
      if (head && shown && !card) head.after(el("div", { class: "t3kcard" }, shown.picture ? el("img", { class: "tpic", src: shown.picture, alt: "" }) : logo("mk", true),
        el("span", { class: "tt" }, el("b", { text: shown.title }), el("span", { text: [shown.gear, "by " + shown.creator, licence(shown.license)].filter(Boolean).join(" · ") }), link(shown.address, "TONE3000"))));
      else if (card && !(head && shown)) card.remove();
      update();
    }, 120);
  }
  for (const id of ["libL", "chain", "editor"]) { const e = document.getElementById(id); if (e) new MutationObserver(decorate).observe(e, { childList: true, subtree: id === "libL" ? false : true }); }
  status();
})();
