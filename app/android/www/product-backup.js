/* HyperRig for TANK-MINI, product builds: everything the pedal keeps in one file, and back. The file is one of presets, which Import reads as any other, with
 * more in it: every capture and every cab with the place it is in, and the settings. It is read strictly (product-presetfile.js). Nothing on the pedal is
 * changed by a backup. What a backup puts back is what was in it, place by place; the rest of the pedal stays, unless the person wants it erased. */

const hrBook = { busy: false };
function hrBookCan() {
  if (pioBusy || saveRun || hrSaving || hrBook.busy) return false;
  if (DEMO || !S.connected) { toast("Connect the pedal first.", "err"); return false; }
  if (hrOther.kind) { toast("This editor is for another HyperRig than the pedal's. Update first.", "err"); return false; }
  if (globalThis.hrTry && hrTry.on) { toast("A sound is being tried. Keep it, or put back what was playing, first.", "err"); return false; }
  return true;
}
const hrBookLibs = async () => {
  const libs = { capture: pioLib(await pioSendLive("CLIST", PIO_LIBEND("CLIST"), 3000), true), ir: pioLib(await pioSendLive("ILIST", PIO_LIBEND("ILIST"), 3000), false) };
  if (!libs.capture.full || !libs.ir.full) throw new Error("the captures and cabs could not be read");
  return libs;
};
const hrBookCount = (n, one, many) => n === 1 ? "1 " + one : n + " " + many;

/* The settings the pedal keeps, as the file has them. What the pedal does not say is left out. */
async function hrBookSettings() {
  const out = {}, all = (line, end) => Pedal.cmd(line, end ? doneBy(end) : line, 3000), one = async (line, said = line) => reply(await all(line), said);
  const nums = (re, s) => { const m = re.exec(s); return m ? m.slice(1).map(Number) : null; }, put = (k, v) => { if (v !== null && v !== undefined) out[k] = v; };
  put("eq", nums(/^GEQ (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)$/, await one("GEQ")));
  put("high_pass_hz", (nums(/^HPF hz=(\d+)/, await one("HPF")) || [])[0]);
  const bit = v => v === undefined ? undefined : v === 1;
  put("tails", bit((nums(/^SPILL ([01])/, await one("SPILL")) || [])[0]));
  const glide = nums(/^GLIDE ms=(\d+) blocks=\d+ snap=([01])/, await one("GLIDE"));
  put("glide", glide && { ms: glide[0], scenes: glide[1] === 1 });
  const spur = parseSpur(await one("SPUR")), lim = parseLim(await one("LIM", "LIM "));
  put("whine_filter", spur && spur.on);
  put("limiter", lim && { on: lim.on, threshold: lim.thr, release: lim.rel });
  const table = [0, 1, 2, 3].map(() => [null, null, null]);
  for (const l of await all("FSA", "FSA end")) { const m = /^FSA ([0-3]) ([0-2]) (\d+) (\d+) (\d+)$/.exec(l); if (m) table[+m[1]][+m[2]] = [+m[3], +m[4], +m[5]]; }
  if (!table.flat().includes(null)) out.switches = table;
  put("press", nums(/^FSPRESS ([01]) ([01]) ([01]) ([01])/, await one("FSPRESS")));
  const mode = parseFsMode(await one("FSMODE")), lights = parseFsLed(await all("FSLED", "FSLED end")), light = parseLedCfg(await one("LEDCFG"));
  put("layout", mode && FM_LAYOUTS[mode.layout]);
  put("switch_lights", lights && lights.map(x => x.custom ? [x.on, x.off] : "auto"));
  put("light", light && Object.fromEntries(Object.entries(light).map(([k, v]) => [k, String(v)])));
  const midi = hrMidiParse(await all("MIDI"));
  put("midi", midi && hrMidiHex(midi));
  return out;
}
/* To the pedal, and kept there: each line answered, then the same settings read again. What is not as it should be is said. */
async function hrBookSettingsPut(settings, note) {
  await hrBookSettings();                       // the pedal says them first: what it has not said may not be set
  for (const line of HyperRigPresetFile.lines(settings)) {
    const pre = line.startsWith("MIDI") ? "MIDI" : gdPre(line), r = reply(await Pedal.cmd(line, Array.isArray(pre) ? doneBy(...pre) : pre, 2500), pre);
    if (!r || /^ERR/.test(r)) note(`the setting "${line}" was not taken (${r || "no answer"})`);
  }
  const now = HyperRigPresetFile.settingsOf(await hrBookSettings()), left = Object.keys(settings).filter(k => JSON.stringify(settings[k]) !== JSON.stringify(now[k]));
  if (left.length) note("settings that are not as in the backup: " + left.map(k => k.replace(/_/g, " ")).join(", "));
  const kept = reply(await Pedal.cmd("GSAVE", "GSAVE", 5000), "GSAVE");
  if (!kept.startsWith("GSAVE ok")) note(`the settings are on, but could not be kept (${kept || "no answer"})`);
}

/* ---- the backup ---- */
async function hrBackup() {
  if (!hrBookCan()) return false;
  if (hrState().kind !== "saved" && (edCount() || S.chain.P.length + S.chain.Q.length > 0) &&
      !await uiConfirm({ title: "Back up without your changes?", okLabel: "Back up", danger: true, body: "What plays now is not saved. A backup loads each preset, so it would be lost." })) return false;
  hrBook.busy = pioBusy = true; txn++; edClear();
  const notes = [], files = {}, att = { cap: {}, ir: {} }, placed = { capture: [], ir: [] }, reads = [], now = pioNow(), src = pioSource();
  let tun = null, err = "", settings = {}, moved = false, back = -1, scene = -1;
  Log.act("backup", {});
  try {
    busy(true, "Reading the pedal…", 0);
    const p = await readPlist();
    if (!p.ok) throw new Error("the presets could not be read");
    plist = p.list; plistHave = true; back = p.cur; scene = S.snap;
    const libs = await hrBookLibs(), jobs = [...libs.capture.list.map(e => ["capture", "cap", e]), ...libs.ir.list.map(e => ["ir", "ir", e])];
    const list = plist.slice().sort((a, b) => a[0] - b[0]), steps = jobs.length + 2 * list.length + 1;
    for (let i = 0; i < jobs.length; i++) {
      const [role, short, e] = jobs[i], say = `Reading "${e.name}"…`;
      busy(true, say, i / steps);
      try {
        const a = pioAttOf(short, await pioSlotRead(pioSendLive, short, e.slot, fr => busy(true, say, (i + fr) / steps)), e), key = short + e.slot;
        if (!pioAttCheck(a).ok) throw new Error("it is not whole on the pedal");
        files[key] = a; att[short][e.slot] = { key, sha256: a.sha256 }; placed[role].push({ slot: e.slot, attachment: key });
      } catch (x) {
        if (!S.connected) throw x;
        notes.push(`${role === "ir" ? "Cab" : "Capture"} ${e.slot + 1} "${e.name}" could not be read and is not in the file (${errText(String(x && x.message || x))}).`);
      }
    }
    settings = await hrBookSettings();
    if (list.length) { tun = await pioMute(); moved = true; }
    for (let i = 0; i < list.length; i++) {
      const [n, name] = list[i];
      busy(true, `Reading preset ${slotTxt(n)}…`, (jobs.length + 2 * i) / steps);
      const r = reply(await Pedal.cmd(`PLOAD ${n}`, "PLOAD", 8000), "PLOAD");
      if (!r.startsWith("PLOAD ok")) { if (!S.connected) throw new Error("the pedal is gone"); notes.push(`Preset ${slotTxt(n)} "${name}" could not be read and is not in the file.`); continue; }
      const st = await pioReadPreset(pioSendLive, pioReadOpts());
      st.miss.forEach((m, k) => { if (m) notes.push(`Preset ${slotTxt(n)}, scene ${k + 1}: some blocks are kept as off.`); });
      reads.push({ st, n, o: { name, meta: {}, now, id: pioId(), source: src } });
    }
  } catch (e) { err = String(e && e.message || e); }
  finally {
    if (moved && S.connected && back >= 0) {
      const r = await Pedal.cmd(`PLOAD ${back}`, "PLOAD", 8000).catch(() => []);
      if (scene >= 0 && reply(r, "PLOAD").startsWith("PLOAD ok")) { await Pedal.cmd("SNAPS", "SNAPS").catch(() => {}); await Pedal.cmd(`SNAP ${scene}`, "SNAP ").catch(() => {}); }
    }
    await pioUnmute(tun).catch(() => {}); busy(false);
    await hrBookFresh(moved);
    txn--; hrBook.busy = pioBusy = false;
  }
  let text = "";
  if (!err) {
    const presets = reads.map(x => { const pre = pioPresetOut(x.st, S.types, { ...x.o, att }); pre.meta.slot = slotTxt(x.n); return pre; });
    const doc = pioDoc("backup", presets, { now, app: src.app, attachments: files, meta: { name: "HyperRig backup" } });
    doc.backup = { version: 1, captures: placed.capture, irs: placed.ir, settings };
    text = JSON.stringify(doc);
    // read as it will be read: a backup that could not be put back is none
    const r = HyperRigPresetFile.backup(text);
    if (!r.ok) err = r.err;
    else if (r.warn.length || r.presets.length !== presets.length || r.captures.length !== placed.capture.length || r.irs.length !== placed.ir.length ||
      JSON.stringify(r.settings) !== JSON.stringify(HyperRigPresetFile.settingsOf(settings)) || Object.keys(r.settings).length !== Object.keys(settings).length) err = "the file would not be whole";
  }
  if (err) { Log.act("backup_failed", { err }); toast(`No backup was made: ${errText(err)}. Try again.`, "err"); return false; }
  const file = pioFileName("HyperRig backup " + now.slice(0, 10)), how = await pioSaveFile(file, text);
  Log.act("backup_done", { presets: reads.length, captures: placed.capture.length, irs: placed.ir.length, bytes: text.length, notes: notes.length, how });
  const what = [hrBookCount(reads.length, "preset", "presets"), hrBookCount(placed.capture.length, "capture", "captures"), hrBookCount(placed.ir.length, "cab", "cabs"), "the settings"].join(", ");
  if (notes.length) await uiAlert({ title: "Backed up, with a note", body: `In the file: ${what}.\n` + notes.join("\n") });
  else toast(`In the file: ${what}.`, "ok", { title: "Backup" });
  return true;
}
/* What the page shows, read again after the pedal went through other presets. */
async function hrBookFresh(all) {
  if (!S.connected) return;
  if (!all) return;
  await evPoll({ own: true });
  for (const read of [loadPresets, loadChain, stwLoad, () => loadAmpEq(true), loadMem, loadModelName, loadSnaps, () => loadGlobal(false), fsLoad, () => hrMidiSay("")]) await Promise.resolve().then(read).catch(() => {});
}

/* ---- and back ---- */
function hrBookForm(r, full) {
  const mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }, f = {};
  const check = (key, text, on) => { const w = mk("label", "mdlg-chk"), c = mk("input"); c.type = "checkbox"; c.checked = on; f[key] = c; w.append(c, mk("span", "", text)); return w; };
  const files = [r.captures.length && hrBookCount(r.captures.length, "capture", "captures"), r.irs.length && hrBookCount(r.irs.length, "cab", "cabs")].filter(Boolean).join(" and ");
  const when = r.made ? new Date(r.made) : null;
  return uiForm({
    title: "Restore this backup?", okLabel: "Restore", danger: true,
    body: (when && !isNaN(when) ? `It was made on ${when.toLocaleString("en-GB", { dateStyle: "long", timeStyle: "short" })}. ` : "") + r.warn.join(" "),
    build: box => {
      if (r.presets.length) box.append(check("presets", hrBookCount(r.presets.length, "preset", "presets"), true));
      if (files) box.append(check("files", files, true));
      if (Object.keys(r.settings).length) box.append(check("settings", "Settings: footswitches, lights, MIDI, global EQ and the others", true));
      if (full) {
        box.append(mk("p", "mdlg-note", "What is in the same slots on the pedal is replaced, and what plays now and is not saved is lost."));
        box.append(check("first", "Back up the pedal as it is now, first", true));
        box.append(check("erase", "Erase what is on the pedal and not in the backup", false));
      }
      return { first: f.presets || f.files || f.settings };
    },
    submit: async () => Object.fromEntries(Object.entries(f).map(([k, c]) => [k, c.checked])),
  });
}
/* Whether the place holds just this: the bytes, the name and what goes with them. */
async function hrBookSame(x, list) {
  const a = x.a, e = list.find(y => y.slot === x.slot), cap = x.role === "capture";
  if (!e || e.bytes !== x.data.length || e.name !== x.name || cap && ((e.trim || 0) !== (a.trim_db || 0) || (e.inDbu ?? null) !== (a.in_dbu ?? null))) return false;
  const h = await pioSlotHead(pioSendLive, cap ? "cap" : "ir", x.slot);
  return !h.err && h.len === x.data.length && h.crc === pioCrc32(x.data) && (cap || h.aux === a.gain_mdb && h.fs === a.rate_khz);
}
async function hrRestore(text) {
  if (!hrBookCan()) return false;
  const r = HyperRigPresetFile.backup(text);
  if (!r.ok) { Log.act("restore", { ok: false, err: r.err }); toast(r.err, "err", { title: "Couldn't restore" }); return false; }
  const files = [];
  for (const [role, list] of [["capture", r.captures], ["ir", r.irs]]) for (const x of list) {
    const a = r.doc.attachments[x.key], c = pioAttCheck(a), name = pioAscii(a.name, 23) || (role === "ir" ? "Cab IR" : "Capture");
    if (c.ok) files.push({ role, slot: x.slot, key: x.key, a, data: c.data, name });
    else r.warn.push(`${role === "ir" ? "Cab" : "Capture"} ${x.slot + 1} "${name}" is damaged and left out.`);
  }
  r.captures = files.filter(x => x.role === "capture"); r.irs = files.filter(x => x.role === "ir");
  let p, libs;
  try { p = await readPlist(); if (!p.ok) throw new Error(); plist = p.list; plistHave = true; libs = await hrBookLibs(); } catch (e) { toast("Couldn't read the pedal. Try again.", "err"); return false; }
  const want = await hrBookForm(r, p.list.length + libs.capture.list.length + libs.ir.list.length > 0);
  if (!want || !(want.presets || want.files || want.settings)) return false;
  if (want.first && (!await hrBackup() || !await uiConfirm({ title: "Restore now?", okLabel: "Restore", danger: true, body: "Go on when the file of the pedal as it is now was saved." }))) return false;
  if (!hrBookCan()) return false;
  const notes = [], said = w => T(w.k, { ...w, why: w.why ? T(w.why) : "" }), done = { presets: 0, files: 0, same: 0, erased: 0 };
  let tun = null, err = "";
  hrBook.busy = pioBusy = true; txn++; edClear();
  Log.act("restore", { ok: true, want, presets: r.presets.length, files: files.length });
  try {
    tun = await pioMute();
    await aeqSettle();
    const steps = (want.files ? files.length : 0) + (want.presets ? r.presets.length : 0) + 1;
    let step = 0;
    const here = {};                                     // what of the backup is in its place: a preset takes it from there
    libs = await hrBookLibs();
    for (const x of files) {
      const list = libs[x.role].list, say = `Restoring "${x.name}"…`;
      if (want.files) busy(true, say, step / steps);
      if (await hrBookSame(x, list)) { here[x.key] = x.slot; if (want.files) { done.same++; step++; } continue; }
      if (!want.files) continue;
      try {
        const pn = pioFind(await pioSendLive("PNEW", "PNEW", 3000), "PNEW");
        if (!/^PNEW ok/.test(pn)) throw new Error(pn || "no answer");
        await pioAttUpload(pioSendLive, x, x.slot, { maxLine: Pedal.tr.maxLine, audioOn: S.audio === 2 }, fr => busy(true, say, (step + fr) / steps));
        if (!await hrBookSame(x, (await hrBookLibs())[x.role].list)) throw new Error("it does not read back as it was sent");
        here[x.key] = x.slot; done.files++;
      } catch (e) {
        if (!S.connected) throw e;
        notes.push(`${x.role === "ir" ? "Cab" : "Capture"} ${x.slot + 1} "${x.name}" was not restored (${errText(String(e && e.message || e))}).`);
      }
      step++;
    }
    if (want.presets) {
      libs = await hrBookLibs();
      for (const { n, pre } of r.presets) {
        const say = `Restoring preset ${slotTxt(n)}…`, ctx = pioCtxOf(libs.capture, libs.ir);
        ctx.att = { ...here };
        busy(true, say, step / steps);
        await hrPutPreset(pre, n, ctx, text => notes.push(`${slotTxt(n)}: ${text}`), (k, of) => busy(true, say, (step + k / of) / steps));
        done.presets++; step++;
      }
    }
    if (want.erase) {
      busy(true, "Erasing what is not in the backup…", step / steps);
      const gone = async (line, word) => { const a = reply(await Pedal.cmd(line, word, 5000), word); if (a.startsWith(word + " ok")) done.erased++; else notes.push(`"${line}" was not done (${a || "no answer"}).`); };
      if (want.presets) { const keep = new Set(r.presets.map(x => x.n)); for (const [n] of p.list) if (!keep.has(n)) await gone(`PDEL ${n}`, "PDEL"); }
      if (want.files) {
        for (const [role, word] of [["capture", "CDEL"], ["ir", "IDEL"]]) { const keep = new Set(files.filter(x => x.role === role).map(x => x.slot)); for (const e of libs[role].list) if (!keep.has(e.slot)) await gone(`${word} ${e.slot}`, word); }
      }
    }
    if (want.settings) { busy(true, "Restoring the settings…", step / steps); await hrBookSettingsPut(r.settings, text => notes.push(text[0].toUpperCase() + text.slice(1) + ".")); }
  } catch (e) { err = String(e && e.message || e); }
  finally {
    await pioUnmute(tun).catch(() => {}); busy(false);
    curPreset = -1; S.curPre = -1; S.sel = null; S.pendName = ""; hrSlot = -1;
    await hrBookFresh(true);
    txn--; hrBook.busy = pioBusy = false;
  }
  Log.act("restore_done", { ...done, err: err || undefined, notes: notes.length });
  const first = done.presets ? r.presets[0].n : want.presets || !plist.length ? -1 : plist[0][0];
  if (first >= 0 && S.connected) await loadPreset(first).catch(() => {});
  if (err) { toast(`The restore stopped: ${errText(err)}. Restore the file again: what is there already is not sent twice.`, "err"); if (notes.length) await uiAlert({ title: "Not everything was restored", body: notes.join("\n") }); return false; }
  const what = [want.presets && hrBookCount(done.presets, "preset", "presets"), want.files && hrBookCount(done.files + done.same, "capture or cab", "captures and cabs"), want.settings && "the settings",
    done.erased && hrBookCount(done.erased, "other erased", "others erased")].filter(Boolean).join(", ");
  if (notes.length) await uiAlert({ title: "Restored, with a note", body: `On the pedal: ${what}.\n` + [...new Set(notes)].join("\n") });
  else toast(`On the pedal: ${what}.`, "ok", { title: "Restored" });
  return !notes.length;
}
function hrRestorePick() {
  if (!hrBookCan()) return;
  const input = document.createElement("input");
  input.type = "file"; input.accept = ".json,application/json";
  input.onchange = async () => {
    const f = input.files && input.files[0];
    if (!f) return;
    if (f.size > HyperRigPresetFile.MAX.bytes) { toast("This is not a HyperRig backup.", "err", { title: "Couldn't restore" }); return; }
    let text;
    try { text = await f.text(); } catch (e) { toast("Couldn't read the file.", "err"); return; }
    await hrRestore(text);
  };
  input.click();
}
/* In Settings, before the last section. */
(function () {
  const sections = document.querySelectorAll("#settings .dbox > section");
  if (!sections.length) return;
  const section = document.createElement("section"), title = document.createElement("h3"), text = document.createElement("p"), row = document.createElement("div");
  section.id = "hrBook";
  title.textContent = "Backup";
  text.className = "spill";
  text.textContent = "Everything on the pedal in one file: presets, captures, cabs and settings.";
  row.className = "hrbook";
  for (const [id, label, go] of [["hrBookMake", "Back up the pedal…", () => void hrBackup()], ["hrBookPut", "Restore a backup…", () => hrRestorePick()]]) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "btn mini"; b.id = id; b.textContent = label; b.onclick = go;
    row.append(b);
  }
  section.append(title, text, row);
  sections[sections.length - 1].before(section);
})();
