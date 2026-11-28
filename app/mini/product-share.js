/* Patchstorage in the desktop program: presets that other players share there, looked at, tried on the pedal without saving, or saved as a file. The program asks
 * and fetches (app/desktop/patchstorage.js), only when a button here is pressed; this part shows. The creator, the licence and the address stay with a preset that
 * is kept, on this computer, and in a file that is saved. Publishing is on Patchstorage's own page, in the person's browser. In a browser this does nothing. */
(function () {
  "use strict";
  if (location.protocol !== "hyperrig:") return;
  const KEPT = "hr.share.presets";
  const read = () => { try { const v = JSON.parse(localStorage.getItem(KEPT)); return v && typeof v === "object" && !Array.isArray(v) ? v : {}; } catch (e) { return {}; } };
  const write = v => { try { localStorage.setItem(KEPT, JSON.stringify(v)); } catch (e) { /* it is only a note */ } };
  const el = (tag, attributes, ...children) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attributes || {})) if (k === "text") e.textContent = v; else if (k.startsWith("on")) e[k] = v; else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? "" : v);
    e.append(...children.filter(c => c !== null && c !== undefined));
    return e;
  };
  const link = (address, text, cls) => el("a", { href: address, target: "_blank", rel: "noopener noreferrer", text, class: cls });
  const size = n => (n >= 1024 * 1024 ? (n / 1024 / 1024).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB");
  let upload = "https://patchstorage.com/upload-a-patch/", open = null;

  async function ask(what) {
    let r;
    try { r = await fetch("patchstorage/" + what, { method: "POST", cache: "no-store" }); } catch (e) { throw new Error("Something went wrong with Patchstorage. Try again."); }
    if (r.ok) return r;
    let m = "Something went wrong with Patchstorage. Try again.";
    try { m = (await r.json()).error.message; } catch (e) { /* the usual words */ }
    throw new Error(m);
  }

  /* What came from there is noted beside the preset that is kept, as long as it has the name it was kept with. */
  function note(n, name, p) { write({ ...read(), [n]: { name, title: p.title, creator: p.creator, license: p.license, address: p.address } }); mark(); }
  let wanted = 0;
  function mark() {
    clearTimeout(wanted);
    wanted = setTimeout(() => {
      const kept = read();
      for (const row of document.querySelectorAll("#pList .pslot")) {
        const n = row.dataset.preset, i = kept[n], p = plist.find(x => x[0] === Number(n)), on = !!(i && p && p[1] === i.name && /^https:\/\/patchstorage\.com\//.test(i.address)), old = row.querySelector(".hrfrom");
        if (on && !old) { const a = link(i.address, `by ${i.creator} · ${i.license}`, "hrfrom"); a.title = "See it on Patchstorage: " + i.title; a.onclick = e => e.stopPropagation(); row.append(a); }
        else if (!on && old) old.remove();
      }
    }, 120);
  }
  const list = document.getElementById("pList");
  if (list) new MutationObserver(mark).observe(list, { childList: true });

  /* The presets of a file, read strictly, with where they come from; as a file again. */
  function fileOf(items, p) {
    const origin = { title: p.title, creator: p.creator, license: p.license, address: p.address }, first = items[0];
    return JSON.stringify({ format: "hyperrig-preset", version: 1, min_reader: 1, kind: items.length > 1 ? "bank" : "preset", exported: pioNow(), app: "", presets: items.map(x => ({ meta: { ...x.pre.meta, origin }, compat: {}, sound: x.pre.sound })),
      ...(Object.keys(first.doc.attachments).length ? { attachments: first.doc.attachments } : {}) }, null, 1);
  }

  function browse() {
    if (open) return;
    const d = open = el("dialog", { class: "t3k hrsh", "aria-label": "Presets on Patchstorage" }), words = el("input", { type: "search", maxlength: "60", placeholder: "Search", "aria-label": "Search" }), say = el("p", { class: "tsay", role: "status" });
    const rows = el("div", { class: "hrshl" }), more = el("button", { class: "btn", type: "button", text: "More", hidden: true }), where = el("span", { class: "hrshn" });
    const order = el("select", { "aria-label": "Sort", title: "Sort the list", onchange: () => void look(true) },
      ...[["new", "Newest"], ["downloads", "Most downloaded"], ["likes", "Most liked"]].map(([value, text]) => el("option", { value, text })));
    let page = 0, asked = "", sorted = "new", working = false;
    const close = () => { d.close(); d.remove(); open = null; };
    d.addEventListener("cancel", e => { e.preventDefault(); if (!d.querySelector(".hrshone")) close(); else back(); });
    const busyNow = on => { working = on; for (const b of d.querySelectorAll("button")) if (!b.dataset.out) b.disabled = on; };
    const tell = (text, bad) => { say.textContent = text; say.classList.toggle("bad", !!bad); };

    async function look(fresh) {
      if (working) return;
      busyNow(true); tell("Asking Patchstorage…");
      if (fresh) { page = 0; asked = words.value.trim(); sorted = order.value; rows.replaceChildren(); where.textContent = ""; }
      try {
        const got = await (await ask(`search?q=${encodeURIComponent(asked)}&page=${page + 1}&order=${encodeURIComponent(sorted)}`)).json();
        page = got.page;
        for (const p of got.list) rows.append(el("button", { type: "button", class: "hrshrow", onclick: () => void show(p) }, el("b", { text: p.title }), el("span", { text: ["by " + p.creator, p.day, p.downloads === 1 ? "1 download" : p.downloads + " downloads", p.likes === 1 ? "1 like" : p.likes + " likes"].filter(Boolean).join(" · ") }), p.about ? el("span", { text: p.about }) : null));
        tell(rows.children.length ? "" : asked ? "Nothing was found." : "There are no presets yet.");
        where.textContent = got.total !== null && rows.children.length ? `${rows.children.length} of ${got.total}` : "";
        more.hidden = !(got.page < got.pages);
      } catch (e) { tell(String(e.message || e), true); }
      busyNow(false);
      if (order.value !== sorted) void look(true);       // chosen while Patchstorage was answering
    }
    const first = el("div", { class: "tin" }, el("h2", { text: "Presets on Patchstorage" }), el("p", { text: "Presets that other players share. You can hear one on the pedal without saving it, or save its file." }),
      el("form", { class: "hrshq", onsubmit: e => { e.preventDefault(); void look(true); } }, words, order, el("button", { class: "btn", type: "submit", text: "Search" })), say, rows,
      el("div", { class: "tacts" }, where, more, el("button", { class: "btn", type: "button", text: "Share your own…", onclick: () => own() }), el("button", { class: "btn", type: "button", text: "Close", "data-out": "1", onclick: close })), el("div", { class: "tby" }, el("span", {}, "From ", link("https://patchstorage.com/", "Patchstorage"), ". Each preset is its creator's.")));
    more.onclick = () => void look(false);
    const back = () => { d.replaceChildren(first); tell(""); };

    /* One preset: who made it, under which licence, what it brings; tried or saved, and nothing is fetched before. */
    async function show(p) {
      if (working) return;
      busyNow(true); tell("Asking Patchstorage…");
      let got;
      try { got = await (await ask("patch?id=" + p.id)).json(); } catch (e) { tell(String(e.message || e), true); busyNow(false); return; }
      busyNow(false);
      const told = el("p", { class: "tsay", role: "status" }), radios = got.files.map((f, i) => { const input = el("input", { type: "radio", name: "hrshf", value: f.id }); input.checked = i === 0; return el("label", {}, input, el("span", { text: f.name }), el("span", { class: "sz", text: size(f.size) })); });
      const acts = el("div", { class: "tacts" });
      const one = el("div", { class: "tin hrshone" }, el("h2", { text: got.title }), el("div", { class: "tmeta" }, el("span", {}, "by ", el("b", { text: got.creator })), el("span", { text: "Licence: " + got.license }), got.day ? el("span", { text: got.day }) : null, link(got.address, "See it on Patchstorage")),
        got.about ? el("p", { class: "hrshabout", text: got.about }) : null, radios.length > 1 ? el("div", { class: "tlist", role: "radiogroup", "aria-label": "File" }, ...radios) : null, told, acts);
      const fetched = async () => {
        const id = radios.length > 1 ? one.querySelector("input:checked").value : got.files[0].id;
        for (const b of acts.children) b.disabled = true;
        told.textContent = "Fetching the preset…";
        try {
          const r = hrTry.presetItems(await (await ask(`file?id=${got.id}&file=${id}`)).text(), { by: got.creator, license: got.license, address: got.address, kept: (n, name) => note(n, name, got) });
          if (r.err) throw new Error(r.err);
          told.textContent = "";
          return r;
        } catch (e) { told.textContent = String(e.message || e); return null; }
        finally { for (const b of acts.children) b.disabled = false; }
      };
      acts.append(el("button", { class: "btn", type: "button", text: "To the list", onclick: back }));
      if (!got.files.length) told.textContent = "It has no HyperRig preset file.";
      else acts.append(el("button", { class: "btn", type: "button", text: "Save the file…", onclick: async () => { const r = await fetched(); if (r) { await pioSaveFile(pioFileName(got.title), fileOf(r.items, got)); told.textContent = "Saved, with its creator and its licence inside."; } } }),
        el("button", { class: "btn primary", type: "button", text: "Try it", onclick: async () => {
          if (!S.connected) { told.textContent = "Connect the pedal first."; return; }
          if (hrTry.on) { told.textContent = "You are trying a sound. Keep it or go back first."; return; }
          const r = await fetched();
          if (r) { close(); await hrTry.tryPresets(r.items, r.warn); }
        } }));
      d.replaceChildren(one);
      (acts.querySelector(".primary") || acts.firstChild).focus();
    }
    /* Publishing: the file from here, the rest on their page. */
    function own() {
      d.replaceChildren(el("div", { class: "tin hrshone" }, el("h2", { text: "Share a preset of yours" }), el("ol", { class: "hrshsteps" }, el("li", { text: "Export the preset to a file. Put a capture or a cab IR in it only when you may share it." }),
        el("li", {}, "Open ", link(upload, "Patchstorage's page"), " in your browser, sign in there with your own account, choose HyperRig and give it the file and a licence.")),
        el("p", { text: "HyperRig sends nothing and does not see your account." }),
        el("div", { class: "tacts" }, el("button", { class: "btn", type: "button", text: "To the list", onclick: back }), el("button", { class: "btn", type: "button", text: "Export this preset", onclick: () => { close(); void pioExport(false); } }), link(upload, "Open Patchstorage", "btn primary hrshgo"))));
    }
    d.append(first);
    document.body.append(d);
    d.showModal();
    words.focus();
    void look(true);
  }

  (async () => {
    try {
      const s = await (await fetch("patchstorage/status", { cache: "no-store" })).json();
      if (!s.available) return;
      if (/^https:\/\/patchstorage\.com\//.test(s.upload)) upload = s.upload;
    } catch (e) { return; }
    const ways = document.getElementById("hrWays");
    if (ways) ways.append(el("button", { type: "button", class: "btn mini hrshgo-way", id: "hrShare", "aria-label": "Browse Patchstorage", title: "Browse Patchstorage: presets that other players share", onclick: browse },
      el("img", { src: "patchstorage-logo.png", alt: "", class: "hrshlogo", draggable: "false" })));
    mark();
  })();
})();
