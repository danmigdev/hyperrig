/* The amp that plays has no slot in the library (the pedal's own capture, or one that was only loaded): a preset cannot bring it
 * back. Says which one it is, and keeps it in a free slot if the person wants it. The preset is saved either way. */
async function hrKeepCapture() {
  const what = S.model ? `"${S.model}"` : "the capture that plays";
  const lib = pioLib(await Pedal.cmd("CLIST", l => /^CLIST (?:end|fin)\b/.test(l) || /^ERR/.test(l), 2000), true);
  const used = new Set(lib.list.map(x => x.slot)), slots = lib.slots || 15;
  let free = 0;
  while (free < slots && used.has(free)) free++;
  const body = `The preset plays with the capture ${what}, which is not in your library. Without it, the preset will not bring this sound back.`;
  if (free >= slots) {
    await uiAlert({ title: "The capture is not kept", body: body + " All the slots of the library are in use: delete one, then save the preset again." });
    return;
  }
  if (!await uiConfirm({ title: "Keep the capture too?", body, okLabel: `Save it in slot ${free + 1}`, cancelLabel: "Only the preset" })) return;
  const label = pioAscii(S.model, 23) || "Capture";                       // the pedal's names are plain letters
  const r = reply(await Pedal.cmd(`CSAVE ${free} ${label}`, "CSAVE", 8000), "CSAVE");
  Log.act("capture_kept", { slot: free, name: label, ok: r.startsWith("CSAVE ok") });
  if (!r.startsWith("CSAVE ok")) { toast(`The capture was not kept: ${r || "no answer"}`, "err"); return; }
  S.capSlot = free;
  toast(`Capture "${label}" kept in slot ${free + 1}.`, "ok");
}

/* The name of a preset that has no slot yet, a new one or one from a file: it is saved with it. */
function hrNamePending() {
  inlineEdit(() => $("presetLbl").querySelector("span") || $("presetLbl"), { value: S.pendName || "", max: 23, label: "Name of the preset", placeholder: "Name", clean: v => pioAscii(v, 23),
    save: v => { S.pendName = v; renderPresets(); }, focusEl: () => $("presetBtn"), minW: 240 });
}

/* The tuner takes 7 KB of the pedal's memory while it is open, and beside a full preset there may be none. */
let hrTunerFull = false;
function hrTunerRoom(none) {
  if (none) {
    TU.tgt = null;
    const say = "No memory for the tuner beside this preset. Remove a block or shorten a delay, then open it again.";
    if (!hrTunerFull) { $("tuSay").textContent = say; $("tuLvl").textContent = "–"; }
    $("tuStat").textContent = say;
  } else if (hrTunerFull) { $("tuStat").textContent = "Play a string"; TU.drawn = ""; }
  hrTunerFull = none;
}

/* The places of the chain. The firmware holds ten blocks before the AMP block and ten after it, sixteen in all. Without a capture nothing stands between
 * the two sections and a block sounds the same in both (tools/check_mini_places.py), so one chain is shown and both are used for it. Two things are not the
 * same, and decide where they meet: only the second is in stereo, so a chain of more than ten has ten there and the first ones in the other; and neither a
 * split nor drives with oversampling that stand side by side, which the firmware works as one, are divided. */
const HR_SECTION = 10, HR_CHAIN = 16;
const HR_LEAD = new Set([3, 9, 10, 16, 17, 18, 19, 20, 21, 22, 23]), HR_FOLLOW = new Set([9, 10, 17, 18, 19, 20, 22, 23]);      // the effects of the firmware's group_first and group_length
let hrNew = null;                                                                                                                // a block that was just added, before the chain is read again
const hrIds = s => s.k === "fx" ? [s.id] : s.k === "grp" ? [...s.A, ...s.B] : [];
const hrCount = segs => segs.reduce((n, s) => n + hrIds(s).length, 0);
const hrSplits = segs => segs.filter(s => s.k === "grp").length;
function hrDrive(id) {
  const it = instOf(id) || (hrNew && hrNew.id === id ? hrNew : null), t = it && S.types[it.type], q = t && t.params.find(x => x.name === PIO_OS_P);
  return q ? { id: t.id, os: it.p ? it.p[q.idx] : q.def } : null;
}
const hrTogether = (a, b) => !!(a && b && HR_LEAD.has(a.id) && (a.os === 1 || a.os === 3) && HR_FOLLOW.has(b.id) && b.os === 1);

/* The chain as the page shows it: an amp that is not there is before everything. Two splits that meet where it was stay two, with it between them. */
function hrView(segs) {
  const a = ampIdx(segs);
  if (S.ampPresent || a <= 0 || (segs[a - 1].k === "grp" && segs[a + 1] && segs[a + 1].k === "grp")) return segs;
  return [segs[a], ...segs.slice(0, a), ...segs.slice(a + 1)];
}

/* Where the two sections of a list of parts {n, split} can meet: the place with the least cost, or -1. only: the one place it may be. */
function hrMeet(parts, only, cost) {
  const n = parts.reduce((t, x) => t + x.n, 0), splits = parts.filter(x => x.split).length;
  let best = -1, least = null, p = 0, g = 0;
  for (let k = 0; k <= parts.length; k++) {
    if (k) { p += parts[k - 1].n; g += parts[k - 1].split ? 1 : 0; }
    if (p > HR_SECTION || n - p > HR_SECTION || g > FX_MAXGRP || splits - g > FX_MAXGRP || (only != null && k !== only)) continue;
    const c = cost(k, p);
    if (!least || c[0] < least[0] || (c[0] === least[0] && c[1] < least[1])) { best = k; least = c; }
  }
  return best;
}

/* The chain as it goes to the pedal; null when its sections can meet nowhere. Without a capture the first section has no more blocks than it must. */
function hrArrange(segs) {
  segs = normalize(segs);
  if (S.ampPresent) return segs;
  const a = ampIdx(segs), bare = segs.filter(s => s.k !== "amp"), drive = bare.map(s => s.k === "fx" ? hrDrive(s.id) : null);
  const held = a > 0 && a < bare.length && bare[a - 1].k === "grp" && bare[a].k === "grp" ? a : null;      // two splits that stay two
  const divides = k => k > 0 && k < bare.length && hrTogether(drive[k - 1], drive[k]) ? 1 : 0;
  const k = hrCount(bare) > HR_CHAIN ? -1 : hrMeet(bare.map(s => ({ n: hrIds(s).length, split: s.k === "grp" })), held, (k, p) => [divides(k), p]);
  return k < 0 ? null : normalize([...bare.slice(0, k), { k: "amp" }, ...bare.slice(k)]);
}

/* The section a block is added to before it is moved to its place: that of what follows there, or the other when it is full. */
function hrBank(segs, loc) {
  loc = loc || { t: "serial", si: segs.length };
  if (S.ampPresent) return locBank(segs, loc);
  const next = segs[loc.si], bank = !next ? "Q" : next.k === "amp" ? "P" : next.k === "grp" ? next.bank : (findInst(next.id) || { bank: "Q" }).bank;
  return S.chain[bank].length < HR_SECTION ? bank : bank === "P" ? "Q" : "P";
}

/* Whether the sections can meet somewhere with one block more, and if not why. A chain of sixteen is refused by the rules. */
function hrFits(loc) {
  const segs = cloneSegs(curSegs());
  loc = loc || { t: "serial", si: segs.length };
  if (S.ampPresent || (hrCount(segs) >= HR_CHAIN && !DEMO)) return true;
  if (!placeNode(segs, -1, loc) || hrArrange(segs)) return true;
  hrNoPlace(segs);
  return false;
}
function hrNoPlace(segs) {
  segs = normalize(segs);
  const n = hrCount(segs), splits = hrSplits(segs);
  Log.ev("chain_refused", { blocks: n, splits, said: "places" });
  if (n > HR_CHAIN) toast("16 blocks are the most the pedal can hold. Remove one to add another.", "err", { title: "This preset is full" });
  else if (splits > 2 * FX_MAXGRP) toast(`A chain holds ${2 * FX_MAXGRP} splits at most. Merge one first.`, "err", { title: "Too many splits" });
  else toast("A split cannot be divided, and this one is too large for this place. Choose another place, or take a block out of the split.", "err", { title: "No room here" });
}

/* The order in which blocks are moved: the page's own, but one that goes into a full section waits until there is a place. */
function* hrMoves(sim, tid, placed) {
  const left = PQ.flatMap(b => tid[b].filter(id => !placed.has(id)).map(id => [b, id]));
  while (left.length) yield left.splice(Math.max(0, left.findIndex(([b, id]) => sim[b].includes(id) || sim[b].length < HR_SECTION)), 1)[0];
}

/* After a block was taken away, or the capture: the sections meet where they should again. */
async function hrSettle() {
  if (S.ampPresent || !S.chain.P.length) return;
  const cur = flatCurrent(S.chain), segs = hrArrange(curSegs());
  if (!segs || !planCommands(cur, flatten(segs, cur)).length) return;
  const g = /^grp:([PQ]):(\d+)$/.exec(String(S.sel)), at = g ? findGrp(curSegs(), g[1], +g[2]) : -1, id = at < 0 ? null : hrIds(curSegs()[at])[0];
  await commitSegs(segs);
  const s = id == null ? null : curSegs().find(x => x.k === "grp" && hrIds(x).includes(id));
  if (s) { S.sel = `grp:${s.bank}:${s.ord}`; render(true); }
}

/* A capture is added to a chain that had none: how many of its parts stand before that place; null, and why, when the sections do not hold what would be
 * before and after it. Nothing is sent then. */
function hrAmpPlace(loc) {
  const segs = curSegs(), before = segs.slice(0, loc.si).filter(s => s.k !== "amp"), after = segs.slice(loc.si).filter(s => s.k !== "amp");
  const p = hrCount(before), q = hrCount(after), many = p > HR_SECTION ? "before" : "after", touch = x => x.some((s, i) => i && s.k === "grp" && x[i - 1].k === "grp");
  if (p > HR_SECTION || q > HR_SECTION) toast(`At most 10 blocks fit ${many} it, and here there would be ${Math.max(p, q)}. Add it nearer the ${p > HR_SECTION ? "start" : "end"} of the chain.`, "err", { title: `No room ${many} the AMP block` });
  else if (Math.max(hrSplits(before), hrSplits(after)) > FX_MAXGRP) toast(`At most ${FX_MAXGRP} splits fit on each side of the AMP block. Add it between them.`, "err", { title: "Too many splits on one side" });
  else if (touch(before) || touch(after)) toast("Two splits side by side would become one. Add the capture between them.", "err", { title: "No room here" });
  else return before.length;
  return null;
}
const hrAmpLoc = n => ({ t: "serial", si: n <= ampIdx(curSegs()) ? n : n + 1 });

/* One step of a block to the left or right; none before the first place that is shown. */
function hrStep(segs, id, dir) {
  const loc = moveStepLoc(segs, id, dir);
  return loc && !S.ampPresent && loc.t === "serial" && loc.si === 0 && segs[0].k === "amp" ? null : loc;
}

/* The first blocks of a chain of more than ten, without a capture, are in the section that is not in stereo: said when it comes to that, and in the block. */
function hrMono() {
  if (S.ampPresent || S.chain.P.length + S.chain.Q.length <= HR_SECTION || !stOn()) return [];
  const v = stImage([...S.chain.P, ...S.chain.Q], S.types, { on: true, geq: !!(S.geq && S.geq.some(x => +x)) });
  return S.chain.P.filter(x => x.on && v.blk[x.id].outv === 1 && v.blk[x.id].cls !== "pass").map(x => x.id);
}
function hrMonoSay(before) {
  const now = hrMono().filter(id => !before.includes(id));
  if (now.length) toast(`In a chain of more than 10 blocks only the last ten are in stereo. Now in mono: ${[...new Set(now.map(id => lookOf(instOf(id).type).name))].join(", ")}.`, "info", { title: "Mono at the start of the chain" });
}
function hrMonoHint(h, it) {
  if (!hrMono().includes(it.id)) return;
  const p = el("p", "stnl");
  p.textContent = "Mono here: without a capture, the last ten blocks of a chain are in stereo.";
  h.appendChild(p); h.hidden = false;
}

/* A preset from a file, without a capture: the place of the amp says where the sections meet. Where they cannot, another place where they can. */
function hrImportChain(chain, amp, types) {
  if (!pioObj(amp) || amp.present !== false) return chain;
  const known = b => pioObj(b) && typeof b.type === "string" && types[b.type] && types[b.type].params;
  const bare = chain.filter(x => !(pioObj(x) && x.amp === true)), at = chain.findIndex(x => pioObj(x) && x.amp === true), was = at < 0 ? bare.length : at;
  let left = HR_CHAIN;
  const take = list => { const n = Math.min(left, list.filter(known).length); left -= n; return n; };
  const drive = b => { const t = types[b.type], q = t.params.find(x => x.name === PIO_OS_P), v = q && pioObj(b.params) ? pioInt(b.params[PIO_OS_P]) : null; return q ? { id: t.id, os: v == null ? q.def : v } : null; };
  const parts = bare.map(x => pioObj(x) && pioObj(x.split) ? { n: take([...pioArr(x.split.a), ...pioArr(x.split.b)]), split: true, drive: null } : { n: take([x]), split: false, drive: known(x) ? drive(x) : null });
  if (hrMeet(parts, was, () => [0, 0]) === was) return chain;
  const k = hrMeet(parts, null, (k, p) => [k > 0 && k < parts.length && hrTogether(parts[k - 1].drive, parts[k].drive) ? 1 : 0, p]);
  return k < 0 ? chain : [...bare.slice(0, k), { amp: true }, ...bare.slice(k)];
}

/* How many places are left, and a change of the chain that is not sent: why, in words one can act on. */
const hrRoom = () => Math.max(0, HR_CHAIN - S.chain.P.length - S.chain.Q.length);
function hrNoRoom(command, reason) {
  const m = hrOther.kind ? null : /^FX(A|M \d+) ([PQ]) /.exec(String(command || ""));
  if (hrOther.kind) return toast("ERR MINI_APP " + reason, "err");
  const p = S.chain.P.length, q = S.chain.Q.length, add = m && m[1] === "A", after = m && m[2] === "Q";
  let title = "", text = "";
  if (add && p + q >= HR_CHAIN) { title = "This preset is full"; text = "16 blocks are the most the pedal can hold. Remove one to add another."; }
  else if (m && S.ampPresent && (add ? (after ? q : p) >= HR_SECTION : (findInst(+m[1].slice(2)) || { bank: m[2] }).bank !== m[2])) {
    title = `No room ${after ? "after" : "before"} the AMP block`;
    text = `At most 10 blocks fit ${after ? "after" : "before"} it. Remove one${add ? `, or add this one ${after ? "before" : "after"} it` : " there first"}.`;
  }
  Log.ev("chain_refused", { command: String(command || "").slice(0, 40), reason: String(reason || "").slice(0, 80), said: title });
  return title ? toast(text, "err", { title }) : toast(reason, "err");
}

/* Another block in the place of one, in one command of the pedal (mini/product/replace.c): with its place, its branch and its switch, in every scene too. The command names
 * the preset and the block that the page shows: after a footswitch the pedal does nothing. What does not fit leaves the old block as it was.
 * from: the block and the preset that it was meant for, when an IR was picked first. */
async function hrReplace(id, type, from) {
  const f = findInst(id);
  if (!f || f.inst.type === type || from && (from.preset !== curPreset || from.type !== f.inst.type)) return null;
  const old = f.inst, was = lookOf(old.type).name, name = lookOf(type).name, stays = `${was} stays as it was.`, line = `FXC ${curPreset} ${id} ${old.type} ${type}`;
  const gate = HyperRigMini.preflight([line], Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");
  const moved = () => toast("The pedal has another preset now. Nothing was replaced.", "err", { title: "Not replaced" });
  if (!gate.allowed) { if (!hrOther.kind && (refreshing || S.curPre != null && S.curPre !== curPreset)) moved(); else hrNoRoom(line, gate.reason); return null; }
  Log.act("fx_replace", { id, from: old.type, to: type, preset: curPreset });
  const before = [ED.other, ED.otherQ, ED.otherT], ep = ED.ep, q = edQ();
  let now = null;
  txn++; fxGone.add(id);
  edMark("other", null, q);                            // before it is sent: when its answer is lost, the block may be another
  try {
    const lines = await Pedal.cmd(line, l => l.startsWith("FX cpu") || l.startsWith("ERR"), 4000);
    const ok = lines.map(l => /^FXC id=(\d+) /.exec(l)).find(Boolean), err = lines.find(l => l.startsWith("ERR")) || "";
    if (ok) { now = +ok[1]; edDropBlock(id); S.sel = now; }
    else {
      if (err && ED.ep === ep && ED.otherQ === q) { [ED.other, ED.otherQ, ED.otherT] = before; renderSaveBar(); }
      if (/another (?:preset|block)/.test(err)) { moved(); await edFresh(); }
      else if (isCpuErr(err)) cpuToast(`Not enough CPU for ${name}. ${stays}`);
      else if (isMemErr(err)) { await memNeed(); memToast(`Not enough memory for ${name}. ${stays}` + memWhy(type, err, old)); }
      else if (isIrErr(err)) { toast(`Pick one from the library, or load a .wav. Until then ${stays}`, "err", { title: "No cab IR yet" }); irLoc = { t: "replace", id, type: old.type, preset: curPreset }; openLib("ir"); }
      else if (err) toast(`${stays} ${errText(err)}.`, "err", { title: "Not replaced" });
      else toast("The chain shows what is on it.", "err", { title: "The pedal did not answer" });
    }
    await loadChain();
  } catch (e) { toast("Pedal not connected.", "err"); }
  finally { txn--; fxGone.delete(id); }
  return now;
}

/* A choice of many names for a parameter of a block, as a list. */
function hrList(host, { list, val, label, onChange }) {
  const el = document.createElement("label"), name = document.createElement("span"), select = document.createElement("select");
  el.className = "segsel hrlist"; el.title = list.tip;
  name.className = "lbl"; name.textContent = label;
  select.className = "irsel"; select.setAttribute("aria-label", label);
  list.names.forEach((text, i) => { const o = document.createElement("option"); o.value = list.first + i; o.textContent = text; select.appendChild(o); });
  let shown = val;
  const show = v => { shown = v; select.value = String(v); };
  select.onchange = async () => {
    select.disabled = true;
    try { show(await onChange(+select.value)); } catch (e) { show(shown); } finally { select.disabled = false; }
  };
  el.append(name, select);
  host.appendChild(el);
  show(val);
  return { set: show, el };
}

/* Saving, in one line under the preset's name, always there: the state of the preset in words, and where Save writes.
 * "Saved" is said once a preset was loaded or saved since the pedal connected; before that the editor only knows that nothing was changed here. */
let hrKnown = false, hrSaving = false;
function hrState() {
  const fresh = curPreset < 0, slot = !fresh ? slotTxt(curPreset) : hrSlot >= 0 ? slotTxt(hrSlot) : "";
  if (fresh) return { kind: "new", text: "<b>Not saved</b> · " + (slot ? `new preset for ${slot}` : "new preset, without a slot yet"), go: slot ? `Save to ${slot}` : "Save to…", as: slot ? "Other slot…" : "" };
  if (edCount()) return { kind: "changed", text: `<b>Not saved</b> · changes in ${S.snap >= 0 && !ED.other ? `scene ${S.snap + 1} of ` : ""}${slot}${ED.other ? ", for all its scenes" : ""}`, go: `Save to ${slot}`, as: "Save as…", undo: true };
  return { kind: "saved", text: hrKnown ? `<b>Saved</b> in ${slot}` : `<b>No changes</b> in ${slot}`, as: "Save as…" };
}
function hrSaveBar() {
  const bar = $("saveBar"), go = $("saveGo"), undo = $("saveDiscard"), as = $("hrSaveAs"), text = $("saveTxt");
  if (!bar || !as || DEMO) return false;
  if (PH) {                                             // the phone's layout has the page's own bar
    if (bar.dataset.hr) { delete bar.dataset.hr; bar.classList.remove("hrnew", "hrchanged", "hrsaved"); go.textContent = "Save…"; go.hidden = undo.hidden = false; text.dataset.h = ""; }
    return false;
  }
  if (!S.connected) hrKnown = false;
  const on = !!S.connected && !hrOther.kind && !(globalThis.hrTry && hrTry.on), s = hrState(), set = (b, label) => { b.hidden = !label; if (label && b.textContent !== label) b.textContent = label; };
  bar.hidden = !on;
  document.body.classList.toggle("dirty", on && s.kind !== "saved");
  for (const row of document.querySelectorAll("#pList .pslot")) row.classList.toggle("hrchg", on && s.kind !== "saved" && row.classList.contains("cur"));
  if (!on) return true;
  if (bar.dataset.hr !== s.kind) { bar.dataset.hr = s.kind; for (const k of ["new", "changed", "saved"]) bar.classList.toggle("hr" + k, k === s.kind); }
  if (text.dataset.h !== s.text) { text.innerHTML = s.text; text.dataset.h = s.text; }
  text.title = s.kind === "changed" ? edSummary() : "";
  set(go, s.go || ""); set(as, s.as); set(undo, s.undo ? "Discard" : "");
  go.disabled = saveRun || hrSaving; go.title = s.go ? "Ctrl+S" : "";
  return true;
}
async function hrSave() {
  if (globalThis.hrTry && hrTry.state !== "off") return hrTry.keep();          // a sound that is tried (product-try.js)
  if (hrSaving || saveRun || pioBusy || !S.connected || hrOther.kind) return;
  hrSaving = true;
  try {
    if (curPreset >= 0) { if (edCount()) await saveFlow(); }
    else if (hrSlot >= 0) await savePreset(hrSlot);
    else await hrSaveTo();
  } finally { hrSaving = false; hrSaveBar(); }
}
/* Where to save, and with which name: the first empty slot is offered. A preset that is there is replaced only after the question of the save itself. */
async function hrSaveTo() {
  let r = null;
  try { r = await readPlist(); } catch (e) { /* below */ }
  if (!r || !r.ok) { toast("Couldn't read the presets of the pedal. Try again.", "err"); return; }
  plist = r.list; plistHave = true; renderPresets();
  const held = new Map(plist.map(p => [p[0], p[1]])), order = [...Array(PRESET_N).keys()], from = Math.max(0, curPreset >= 0 ? curPreset : bank * PRESETS_PER_BANK);
  const free = [...order.slice(from), ...order.slice(0, from)].find(n => !held.has(n)), first = curPreset < 0 && hrSlot >= 0 ? hrSlot : free !== undefined ? free : from;
  const mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  let name = null, slot = null;
  const pick = await uiForm({
    title: "Save this preset", okLabel: "Save",
    build: box => {
      name = mk("input"); name.type = "text"; name.maxLength = 23; name.autocomplete = "off"; name.value = S.pendName || (/^Preset \d+[A-C]$/.test(presetName()) ? "" : presetName());
      slot = mk("select", "mdlg-sel");
      for (let b = 0; b * PRESETS_PER_BANK < PRESET_N; b++) {
        const g = mk("optgroup"); g.label = `Bank ${b + 1}`;
        for (const n of order.slice(b * PRESETS_PER_BANK, (b + 1) * PRESETS_PER_BANK)) { const o = mk("option", "", `${slotTxt(n)} · ${held.get(n) || "empty"}`); o.value = String(n); g.append(o); }
        slot.append(g);
      }
      slot.value = String(first);
      const note = mk("p", "hrnote"), say = () => { const n = +slot.value; note.textContent = held.has(n) ? `Replaces "${held.get(n)}".` : ""; name.placeholder = `Preset ${slotTxt(n)}`; };
      slot.onchange = say; say();
      const field = (label, e) => { const w = mk("label", "mdlg-fld"); w.append(mk("span", "", label), e); return w; };
      box.append(field("Name", name), field("Slot", slot), note);
      return { first: name };
    },
    submit: async () => ({ n: +slot.value, name: pioAscii(name.value, 23) || `Preset ${slotTxt(+slot.value)}` }),
  });
  if (!pick) return;
  const was = S.pendName;
  S.pendName = pick.name;
  await savePreset(pick.n, plist.find(p => p[0] === pick.n));
  if (curPreset !== pick.n || S.pendName) { S.pendName = was; renderPresets(); }      // not saved: it was answered no
}

/* The battery, as the pedal reads it (HRST): asked when it connects and every half minute, between other commands. Before its first mean the pedal says
 * -1, and nothing is shown. Whether it charges it does not say. */
let hrBattery = null, hrBatteryNext = 0;
async function hrBatteryAsk() {
  if (!S.connected) { hrBattery = null; hrBatteryNext = 0; return; }
  if (DEMO || performance.now() < hrBatteryNext || txn || saveRun || edSaving || refreshing || (globalThis.hrTry && hrTry.on)) return;
  hrBatteryNext = performance.now() + 30000;
  let said = "";
  try { said = reply(await Pedal.cmd("HRST", "HRST "), "HRST "); } catch (e) { /* asked again in half a minute */ }
  const m = /\bbattery=(\d{1,3})\b/.exec(said);
  hrBattery = m && +m[1] <= 100 ? { pct: +m[1], mv: null, usb: false, chg: false, note: `Battery: ${+m[1]} %, as the pedal reads it` } : null;
  if (S.connected) battShow(hrBattery);
}
setInterval(hrBatteryAsk, 1730);

/* The pedal had no time for all of it and switched a block off by itself: which one it says, and here it can be switched on again. */
function hrOverloadAction(m) {
  if (!m || m[4] !== "off") return undefined;
  const id = +m[2], type = m[3];
  return { label: "Turn it on", fn: async () => {
    const f = findInst(id);
    if (S.connected && f && f.inst.type === type && !f.inst.on) await toggle(id);
  } };
}

/* The cab that a block plays, as its parameter says it: 0 for the preset's, or one more than the slot of its own. */
const hrIrSlot = (it, types) => { const t = types[it.type], q = it.type === "ir" && t ? t.params.find(x => x.name === "ir_slot") : null; return q ? it.p[q.idx] || 0 : 0; };

/* What A, B and C do: one choice of three, in the footswitches' window. Presets is the pedal's own layout, with the pairs for the banks and the tuner. Stomp and
 * Scenes are actions of each switch, with pairs of their own (mini/product/pairs.c). Custom is any other set of actions, without pairs. */
const HR_HOLD = { 1: [4, 0, 3], 8: [0, 0, 0] };               // held, in Scenes: the preset before and the next; the pairs do the rest (mini/product/pairs.c)
const hrTab = kind => [0, 1, 2].map(f => [[kind, f, 255], [HR_HOLD[kind][f], 0, 255], [0, 0, 255]]).concat([[[0, 0, 255], [0, 0, 255], [0, 0, 255]]]);
/* The scene of a switch: in Scenes the taps are the three of the group that the pedal is on. */
const hrScene = a => S.fm && S.fm.layout !== 0 && a < 3 && hrSetup() === "snaps" ? a + 3 * Math.min(2, Math.max(0, S.fm.bank - 1)) : a;
const HR_SETUPS = { stomps: { name: "Stomp", tab: () => hrTab(8) }, snaps: { name: "Scenes", tab: () => hrTab(1) } };
const HR_SAY = {
  factory: "Tap: a preset of the bank, again for bypass. Hold one second: save there. A+B and B+C: the bank. B+C held: the tuner.",
  stomps: "Tap: its block on and off. A+B and B+C: the preset before and the next. B+C held: the tuner.",
  snaps: "Tap: three scenes. A+B and B+C: the three before and the next three. B+C held: the tuner. A or C held: the preset before and the next, after its scene.",
  kept: "Your own actions. A+B and B+C do nothing here.",
  live: "The pedal is in live mode: A turns the first reverb on and off, B the first delay, C the first modulation. Choose one of these to leave it.",
};
const hrOwn = () => !!fsTab && !Object.values(HR_SETUPS).some(s => fsSameTab(s.tab(), fsTab)) && !fsSameTab(fsDefault(), fsTab);      // actions that are nobody else's
function hrSetup() {
  if (!S.fm) return null;
  if (S.fm.layout === 0) return S.fm.live ? "live" : "factory";
  if (!fsTab || !stFsReady) return "kept";
  return Object.keys(HR_SETUPS).find(k => fsSameTab(HR_SETUPS[k].tab(), fsTab)) || "kept";
}
const hrStored = () => { try { return JSON.parse(localStorage.getItem("hyperrig.footswitches") || "{}") || {}; } catch (e) { return {}; } };
/* The blocks that were chosen for Stomp, when they were left for another choice. */
function hrTabOf(k) {
  const std = HR_SETUPS[k].tab(), t = hrStored()[k];
  const right = Array.isArray(t) && t.length === 4 && t.every(r => Array.isArray(r) && r.length === 3 && r.every(x => Array.isArray(x) && x.length === 3 && x.every(v => Number.isInteger(v) && v >= 0 && v <= 255)));
  if (!right || !fsSameTab(std, t)) return std;
  // a switch that had no block, in a preset with fewer, takes the one of its place again
  return t.map((r, f) => r.map((x, g) => x[0] === 8 && !x[1] && !x[2] ? std[f][g].slice() : x.slice()));
}
function hrSetups(el) {
  const now = hrSetup();
  if (!fsTab || !now) { el.innerHTML = ""; return; }
  if (HR_SETUPS[now]) try { localStorage.setItem("hyperrig.footswitches", JSON.stringify({ ...hrStored(), [now]: fsTab })); } catch (e) { /* only a convenience */ }
  const list = [["factory", "Presets"], ...Object.entries(HR_SETUPS).map(([k, s]) => [k, s.name]), ...(now === "kept" || hrOwn() ? [["kept", "Custom"]] : [])];
  el.innerHTML = `<h3 class="hrq" id="fsQl">What do A, B and C do?</h3><span class="fseg" role="group" aria-labelledby="fsQl">` +
    list.map(([k, name]) => `<button type="button" class="${k === now ? "on" : ""}" data-fq="${k}" aria-pressed="${k === now}">${name}</button>`).join("") + `</span><p class="hrsay">${HR_SAY[now]}</p>`;
  hrModes($("fmChip"));
}
async function hrApply(k) {
  if (!S.connected) { toast("Connect the pedal first.", "err"); return; }
  const now = hrSetup();
  if (fsQuickBusy || !now || k === now) return;
  const own = hrOwn(), setup = HR_SETUPS[k];
  if (setup && own && !await uiConfirm({ title: `Use ${setup.name}?`, body: "Your own actions are replaced.", okLabel: "Use it" })) return;
  Log.act("fs_setup", { k, from: now });
  fsQuickBusy = true;
  const old = fsTab;
  try {
    if (setup) {
      const tab = hrTabOf(k);
      fsTab = tab;
      for (let f = 0; f < 4; f++) for (let g = 0; g < 3; g++) if (String(tab[f][g]) !== String(old[f][g])) await fsSendA(f, g);
    }
    if (k === "factory" && S.fm.live && fsLay === 0) await fmSetMode(false);
    else if (!await fsSetLayout(k === "factory" ? 0 : 2)) toast("Couldn't change it. Try again.", "err");
  } finally { fsQuickBusy = false; }
  if (!S.connected) { fsTab = old; toast("The pedal disconnected: it was not changed.", "err"); return; }
  fsRender(); fsDots(); snapTitles(); stSig = ""; stRender();
  if (hrSetup() === k) toast(`${k === "factory" ? "Presets" : setup ? setup.name : "Custom"}. Save to pedal keeps it.`, "ok");
}
/* The pedal's own layout, in the window: nothing to choose. */
function hrFactory(el) {
  el.innerHTML = `<section class="fsfac" aria-label="What A, B and C do"><div class="fsfg"><span></span>${["A", "B", "C"].map(x => `<b class="fsk">${x}</b>`).join("")}` +
    `<span class="fsfl">Tap</span>${(S.fm && S.fm.live ? ["First reverb", "First delay", "First modulation"] : [0, 1, 2].map(f => `Preset ${slotTxt(((S.fm && S.fm.bank) || 1) * 3 - 3 + f)}`)).map(x => `<span class="fsfv">${x}</span>`).join("")}</div>` +
    `<p class="fsfx"><span>Bluetooth: hold A+B 3 s on, 6 s off</span></p></section>`;
}
/* Beside the preset's name: a mark when the switches do not do the usual. */
function hrModes(mark) {
  const now = hrSetup(), bypass = !!(S.fm && S.fm.bypass), text = bypass ? "Bypass" : { live: "Live", stomps: "Stomp", snaps: "Scenes", kept: "Custom" }[now] || "";
  mark.hidden = !text;
  if (text && mark.textContent !== text) mark.textContent = text;
  mark.title = bypass ? "The pedal is bypassed. The footswitch of the preset ends it." : text ? `What A, B and C do: ${text}. Click to change it.` : "";
  if (text) mark.setAttribute("aria-label", mark.title);
}

/* A footswitch pressed during an import loads another preset: a scene or a preset written then would go over it, or be it under another name. */
async function hrStillNew(send) {
  if (!/ p=-1(?: |$)/.test(pioFind(await send("LVL", "LVL", 1500), "LVL"))) throw new Error("another preset was chosen on the pedal");
}

/* A delay longer than the memory of the pedal takes. The pedal says only which time it keeps: the longest that fits is looked for, a few steps between
 * that and the one that was asked, and said. A drag of the knob asks again and again: the answer is remembered for a moment, and a new turn of the knob
 * stops the search. */
const hrTime = { turn: 0, last: null };
function hrTimeTurned() { return ++hrTime.turn; }
async function hrLongest(id, want, refused, turn) {
  const keep = +(/kept (-?\d+)/.exec(refused) || [])[1], now = performance.now();
  if (!(keep >= 1) || want - keep < 2) return refused;
  if (hrTime.last && hrTime.last.id === id && hrTime.last.ms === keep && now < hrTime.last.until) { hrTime.last.until = now + 1500; return "FXP ok " + keep; }
  let low = keep, high = want;
  while (high - low > 10 && turn === hrTime.turn && S.connected) {
    const mid = Math.round((low + high) / 2), r = reply(await Pedal.cmd(`FXP ${id} 0 ${mid}`, "FXP"), "FXP");
    if (r.startsWith("FXP ok")) low = mid;
    else if (isMemErr(r)) high = mid;
    else break;
  }
  if (turn !== hrTime.turn) return "FXP ok " + low;                // another turn of the knob follows, with its own answer
  hrTime.last = { id, ms: low, until: performance.now() + 1500 };
  memToast(`The longest delay that fits here is ${(low / 1000).toFixed(2)} s. A capture and the other blocks share the pedal's memory.`);
  return "FXP ok " + low;
}

/* Every preset of a file, one after the other, each in the slot it was exported from, or in the next that is free. The captures and IRs that the
 * file brings go to the pedal once, where there is room. A preset that is there is replaced only after the question. */
function hrPlaces(presets, held) {
  const taken = new Set(), out = presets.map(pre => {
    const m = /^([1-9]|1[01])([ABC])$/.exec(String(pre && pre.meta && pre.meta.slot || "")), n = m ? (m[1] - 1) * 3 + "ABC".indexOf(m[2]) : -1;
    const at = n >= 0 && n < 32 && !taken.has(n) ? n : -1;
    if (at >= 0) taken.add(at);
    return { pre, n: at };
  });
  let free = 0;
  for (const x of out) {
    if (x.n >= 0) continue;
    while (free < 32 && (taken.has(free) || held.has(free))) free++;
    if (free < 32) { x.n = free; taken.add(free); }
  }
  return out;
}
async function hrFiles(pre, doc, ctx, note) {
  const atts = pioAttsOf(pre, doc), chk = atts.map(x => pioAttCheck(x.a)), ups = [];
  if (!atts.length) return ups;
  if (chk.some(c => !c.ok)) { note("the files inside are damaged, and were not loaded"); return ups; }
  atts.forEach((x, i) => { x.data = chk[i].data; });
  const pl = await pioAttPlace(atts, pioSendLive, ctx);
  for (const x of atts) {
    const p = pl.place[x.key];
    if (!p) { note(`no free slot for "${pioText(x.a.name, 40)}"`); continue; }
    ctx.att[x.key] = p.slot;
    if (p.up) ups.push({ x, slot: p.slot });
  }
  return ups;
}
/* One preset of a file, built on the pedal and saved in slot n. */
async function hrPutPreset(pre, n, ctx, note, on) {
  const plan = pioPlan(pre, ctx), res = await pioRun(plan, pioSendLive, ctx, on);
  await hrStillNew(pioSendLive);
  const name = pioAscii(plan.name, 23) || "Preset " + slotTxt(n), w = reply(await Pedal.cmd(`PSAVE ${n} ${name}`, "PSAVE", 8000), "PSAVE");
  if (!w.startsWith("PSAVE ok")) throw new Error(`${slotTxt(n)} was not saved: ${w || "no answer"}`);
  if (!plan.scenes.length) await sceneAOnSave(n);
  for (const x of [...plan.warn, ...res.warn]) note(T(x.k, { ...x, why: x.why ? T(x.why) : "" }));
}
async function hrImportAll(r) {
  if (pioBusy) return false;
  try { const p = await readPlist(); if (!p.ok) throw new Error(p.why || "no answer"); plist = p.list; plistHave = true; } catch (e) { toast("Couldn't read the presets of the pedal. Try again.", "err"); return false; }
  const held = new Map(plist.map(p => [p[0], p[1]])), go = hrPlaces(r.presets, held).filter(x => x.n >= 0), over = go.filter(x => held.has(x.n));
  const left = r.presets.length - go.length;
  if (!await uiConfirm({ title: `Import ${go.length} presets?`, okLabel: "Import all", danger: over.length > 0,
    body: (over.length ? "Replaced on the pedal: " + over.map(x => `${slotTxt(x.n)} "${held.get(x.n)}"`).join(", ") + "." : "No preset on the pedal is replaced.") +
      (left ? ` ${left} find no free slot and are left out.` : "") + " What plays now and is not saved is lost." })) return false;
  const files = new Map();
  for (const x of go) for (const a of pioAttsOf(x.pre, r.doc)) files.set(a.key, a);
  const load = files.size > 0 && await uiConfirm({ title: "Load the presets' files?", okLabel: "Load them", cancelLabel: "Not now",
    body: [...files.values()].map(a => (a.role === "ir" ? "Cab IR: " : "Amp capture: ") + pioText(a.a.name, 40)).join("\n") });
  Log.act("preset_import_all", { n: go.length, over: over.length, files: files.size, load });
  const notes = [];
  let done = 0, tun = null, err = "";
  pioBusy = true; txn++; edClear();
  try {
    tun = await pioMute();
    await aeqSettle();
    for (let i = 0; i < go.length; i++) {
      const { pre, n } = go[i], note = text => notes.push(`${slotTxt(n)}: ${text}`), say = `Preset ${i + 1} of ${go.length}…`;
      busy(true, say, i / go.length);
      const libs = [pioLib(await pioSendLive("CLIST", PIO_LIBEND("CLIST"), 3000), true), pioLib(await pioSendLive("ILIST", PIO_LIBEND("ILIST"), 3000), false)];
      if (!libs.every(l => l.full)) throw new Error("the slots could not be read");
      const ctx = pioCtxOf(libs[0], libs[1]);
      ctx.att = {};
      const ups = load ? await hrFiles(pre, r.doc, ctx, note) : [];
      if (ups.length) {
        const pn = pioFind(await pioSendLive("PNEW", "PNEW", 3000), "PNEW");
        if (!/^PNEW ok/.test(pn)) throw new Error(pn || "no answer");
        for (const u of ups) {
          try { await pioAttUpload(pioSendLive, u.x, u.slot, { maxLine: Pedal.tr.maxLine, audioOn: S.audio === 2 }, fr => busy(true, say, (i + fr / 2) / go.length)); }
          catch (e) { delete ctx.att[u.x.key]; note(`"${pioText(u.x.a.name, 40)}" could not be saved (${errText(String(e && e.message || e))})`); }
        }
      }
      await hrPutPreset(pre, n, ctx, note, (k, of) => busy(true, say, (i + .5 + k / of / 2) / go.length));
      done++;
    }
  } catch (e) { err = String(e && e.message || e); }
  finally {
    await pioUnmute(tun).catch(() => {}); busy(false);
    curPreset = -1; S.curPre = -1; S.sel = null; S.pendName = ""; hrSlot = -1;
    if (S.connected) {
      await evPoll({ own: true });
      for (const read of [loadPresets, loadChain, stwLoad, () => loadAmpEq(true), loadMem, loadModelName, loadSnaps]) await Promise.resolve().then(read).catch(() => {});
    }
    txn--; pioBusy = false;
  }
  Log.act("preset_import_all_done", { done, of: go.length, err: err || undefined, notes: notes.length });
  if (done && S.connected) await loadPreset(go[0].n).catch(() => {});
  if (err) toast(`${done} of ${go.length} presets were imported, then it stopped: ${errText(err)}. Import the file again.`, "err");
  else toast(`${done} presets imported.`, "ok");
  if (notes.length) await uiAlert({ title: "Imported, with some changes", body: [...new Set(notes)].join("\n") });
  return !err;
}

/* The pedal has another HyperRig than the one this page is for: the page reads it and changes nothing. Says so in plain words, with
 * the way to the update where the program has an installer, and keeps a bar as long as it lasts. The versions go to the log only. */
const hrOther = { kind: null, installer: false };
/* -1 when version a comes before b, 1 after, 0 the same, null when one of them is not a version of HyperRig. */
function hrVersions(a, b) {
  const of = v => { const m = /^(\d+)\.(\d+)\.(\d+)(?:-dev\.(\d+))?$/.exec(String(v)); return m && [+m[1], +m[2], +m[3], m[4] === undefined ? Infinity : +m[4]]; };
  const x = of(a), y = of(b);
  if (!x || !y) return null;
  for (let i = 0; i < 4; i++) if (x[i] !== y[i]) return x[i] < y[i] ? -1 : 1;
  return 0;
}
async function hrUpdate() {
  try { await Pedal.disconnect(); } catch (e) { /* it was gone already */ }
  location.href = "hyperrig://installer/index.html";
}
function hrOtherBar() {
  let bar = document.getElementById("hrOther");
  if (!hrOther.kind) { if (bar) bar.remove(); return; }
  if (!bar) {
    bar = document.createElement("div"); bar.id = "hrOther"; bar.setAttribute("role", "status");
    const top = document.querySelector(".top");
    if (top) top.after(bar); else document.body.prepend(bar);
  }
  const text = document.createElement("span");
  text.textContent = hrOther.kind === "newer" ? "Your pedal has a newer HyperRig than this program. You can look, but not change anything."
    : "Your pedal needs an update. Until then you can look, but not change anything.";
  bar.replaceChildren(text);
  if (hrOther.kind === "older" && hrOther.installer) {
    const go = document.createElement("button");
    go.type = "button"; go.className = "btn mini"; go.textContent = "Update now"; go.onclick = hrUpdate;
    bar.append(go);
  }
}
async function hrOtherBuild(b, mine) {
  hrOther.kind = !b ? null : b.known && mine && hrVersions(b.version, mine.version) === 1 ? "newer" : "older";
  hrOtherBar();
  if (!hrOther.kind) return;
  if (hrOther.kind === "newer") {
    await uiAlert({ title: "Your pedal is ahead of this program", body: "It has a newer HyperRig. Open the newest HyperRig program to change your presets. Here you can only look at them." });
    return;
  }
  const body = "A newer HyperRig is ready for it. Until you update, you can look at your presets but not change them.";
  if (!hrOther.installer) { await uiAlert({ title: "Your pedal needs an update", body: body + " The update is made with the HyperRig program." }); return; }
  if (await uiConfirm({ title: "Update your pedal?", body: body + " It takes about two minutes, and your presets stay.", okLabel: "Update now", cancelLabel: "Not now" })) await hrUpdate();
}

/* HyperRig for TANK-MINI, product builds: what the page adds to itself. The size of everything (in the desktop program, which
 * answers at "zoom"), the way to the installer when the program has it, and the bar that goes away when a pedal is connected.
 * No command reaches the pedal from here. */
(function () {
  "use strict";
  const note = document.getElementById("miniPortStatus");
  setInterval(() => {
    const on = typeof S !== "undefined" && !!S.connected;
    if (note && note.hidden !== on) note.hidden = on;
    const bar = document.getElementById("hrOther");        // the bar of another build is there while its pedal is
    if (bar && bar.hidden === on) bar.hidden = !on;
  }, 500);
  // What the page refuses to send, said as a person would: while it only reads, and what its rules do not know.
  const said = toast;
  const PLAIN = [
    [/outside the current FXT\/FXS\/PLIST\/SNAPS data|malformed command|empty command operation/, "The editor and the pedal are out of step. Disconnect, connect again and retry."],
    [/MINI firmware identity\/build not accepted/, "The pedal was not recognized. Disconnect, connect again and retry."],
    [/MINI switch\/LED mapping is not validated/, "This setting of the footswitches is not available on this pedal."],
  ];
  toast = function (message, kind, act) {
    const text = String(message);
    if (hrOther.kind && /ERR MINI_APP/.test(text)) {
      message = hrOther.kind === "newer" ? "Not changed: your pedal has a newer HyperRig than this program." : "Not changed: update your pedal first.";
      kind = "err"; act = { title: "Only looking" };
    } else {
      const plain = PLAIN.find(([re]) => re.test(text));
      if (plain) { Log.ev("refused", { text: text.slice(0, 160) }); message = plain[1]; kind = "err"; act = { title: "Nothing was changed" }; }
    }
    return said(message, kind, act);
  };

  // The names: a pencil beside the preset's and one beside the scenes. The page has both edits, behind a double click and a menu.
  const pencil = (id, after, go) => {
    const b = document.createElement("button");
    b.type = "button"; b.id = id; b.className = "btn mini ico hrname"; b.hidden = true;
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 20 1-4.500L16.500 4a2.100 2.100 0 0 1 3 0l.500.500a2.100 2.100 0 0 1 0 3L8.500 19 4 20Z M14.500 6l3.500 3.500" fill="none" stroke="currentColor" stroke-width="1.700" stroke-linejoin="round"/></svg>';
    b.onclick = go;
    after.after(b);
    return b;
  };
  const titleOf = (b, text) => { if (b.title !== text) { b.title = text; b.setAttribute("aria-label", text); } };
  const presetAt = document.getElementById("presetBtn"), scenesAt = document.getElementById("snapSave");
  if (presetAt && scenesAt) {
    const unsaved = () => curPreset < 0;
    const preset = pencil("hrNameP", presetAt, () => { if (curPreset >= 0) presetEdit(curPreset, true); else if (unsaved()) hrNamePending(); });
    const scene = pencil("hrNameS", scenesAt, () => { if (S.snap >= 0 && S.snaps[S.snap]) snapEdit(S.snap); });
    setInterval(() => {
      const on = !!S.connected && !hrOther.kind;
      preset.hidden = !(on && (curPreset >= 0 ? plist.some(p => p[0] === curPreset) : unsaved()));
      scene.hidden = !(on && S.snap >= 0 && S.snaps && S.snaps[S.snap]);
      if (!preset.hidden) titleOf(preset, curPreset >= 0 ? "Rename preset " + slotTxt(curPreset) : "Name this preset");
      if (!scene.hidden) titleOf(scene, "Rename scene " + (S.snap + 1));
      hrSaveBar();
      // with actions of the switches' own, the mark says which setup they are: read once
      if (on && S.fm && S.fm.layout !== 0 && !stFsReady && !stFsLoading && !Pedal.busy && !txn && !refreshing) { stFsLoading = true; fsLoad().catch(() => {}).finally(() => { stFsLoading = false; hrModes(document.getElementById("fmChip")); }); }
    }, 300);
  }
  // The serial port that is asked for: the pedal's USB numbers, and those of the builds before the released 0.2.0.
  if (navigator.serial && typeof navigator.serial.requestPort === "function") {
    const ask = navigator.serial.requestPort.bind(navigator.serial);
    Object.defineProperty(navigator.serial, "requestPort", { configurable: true, value: () => ask({ filters: [{ usbVendorId: 0x4c4a, usbProductId: 0x5155 }, { usbVendorId: 0x3654 }] }) });
  }
  // The choice of what the switches do is between the drawing of the pedal and the switches.
  const choiceAt = document.getElementById("fsQuick"), colsAt = document.getElementById("fsCols");
  if (choiceAt && colsAt) colsAt.before(choiceAt);
  // The line of the saving goes to the top of the board, with a button to save elsewhere; Ctrl+S saves.
  const saveAt = document.getElementById("saveBar"), boardAt = document.querySelector(".mainc > .board"), goAt = document.getElementById("saveGo");
  if (saveAt && boardAt && goAt) {
    boardAt.prepend(saveAt);
    const as = document.createElement("button");
    as.type = "button"; as.id = "hrSaveAs"; as.className = "btn mini"; as.hidden = true;
    as.onclick = async () => { if (hrSaving || saveRun || pioBusy) return; hrSaving = true; try { await hrSaveTo(); } finally { hrSaving = false; hrSaveBar(); } };
    goAt.before(as);
    document.addEventListener("keydown", e => {
      if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey || (e.key !== "s" && e.key !== "S")) return;
      e.preventDefault();
      if (!PH && !document.querySelector(".mdlg, input.ied, #fsm.on, #settings.on, #lib.on, #tuner.on, #stage.on")) void hrSave();      // not under a panel, where the line is not seen
    });
    const send = Pedal.cmd;
    Pedal.cmd = function (line, ...more) {              // what was loaded or saved, as the pedal answered
      const out = send.call(this, line, ...more);
      if (/^(?:PLOAD|PSAVE|SNAPSAVE) /.test(line)) out.then(ls => { if ((ls || []).some(l => /^(?:PLOAD|PSAVE) ok |^SNAPSAVE ok \d preset=\d/.test(l))) hrKnown = true; }, () => {});
      return out;
    };
  }

  if (location.protocol !== "hyperrig:") return;
  document.body.classList.add("hrdesk");
  const box = document.createElement("div");
  box.className = "hrzoom"; box.setAttribute("role", "group"); box.setAttribute("aria-label", "Size of everything");
  const button = (text, title, by, cls) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = text; b.title = title; b.setAttribute("aria-label", title); if (cls) b.className = cls;
    b.onclick = () => ask(by); box.append(b); return b;
  };
  const smaller = button("−", "Smaller (Ctrl −)", "out");
  const shown = button("100 %", "Fit to the window (Ctrl 0)", "auto", "hrz");
  const larger = button("+", "Larger (Ctrl +)", "in");
  const before = document.getElementById("setBtn");
  if (before) before.before(box);
  function show(state) {
    if (!state || !Number.isFinite(state.percent)) return;
    shown.textContent = state.percent + " %";
    shown.classList.toggle("auto", !!state.auto);
    shown.title = state.auto ? "This size fits the window by itself" : "Fit to the window (Ctrl 0)";
    smaller.disabled = !state.out; larger.disabled = !state.in;
    if (state.installer) { firmware(); if (!hrOther.installer) { hrOther.installer = true; hrOtherBar(); } }
  }
  function firmware() {
    if (document.getElementById("hrFirmware")) return;
    const section = document.createElement("section"), title = document.createElement("h3"), text = document.createElement("p"), go = document.createElement("button");
    section.id = "hrFirmware";
    title.textContent = "Firmware";
    text.className = "spill";
    text.textContent = "Put HyperRig on a pedal, update it, or put back the original firmware.";
    go.type = "button"; go.className = "btn mini"; go.textContent = "Install, update or restore";
    go.onclick = hrUpdate;
    section.append(title, text, go);
    const sections = document.querySelectorAll("#settings .dbox > section");
    if (sections.length) sections[sections.length - 1].before(section);
    if (note && note.parentElement) {                    // and beside the line that asks for a pedal
      const way = document.createElement("button");
      way.type = "button"; way.className = "btn mini hrinst"; way.textContent = "Install HyperRig on a pedal"; way.onclick = go.onclick;
      note.append(" ", way);
    }
  }
  async function ask(by) {
    try { const r = await fetch("zoom" + (by ? "?by=" + by : ""), { method: by ? "POST" : "GET", cache: "no-store" }); if (r.ok) show(await r.json()); } catch (e) { /* the keys still work */ }
  }
  // Ctrl and +, − or 0, on any keyboard, and Ctrl with the wheel.
  const mac = /Mac/.test(navigator.platform);
  addEventListener("keydown", e => {
    if (e.altKey || !(mac ? e.metaKey : e.ctrlKey)) return;
    const by = e.key === "+" || e.key === "=" || e.code === "NumpadAdd" ? "in" : e.key === "-" || e.key === "_" || e.code === "NumpadSubtract" ? "out" :
      e.key === "0" || e.code === "Numpad0" ? "auto" : "";
    if (by) { e.preventDefault(); e.stopPropagation(); ask(by); }
  }, true);
  let turned = 0;
  addEventListener("wheel", e => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    turned += e.deltaY;
    if (Math.abs(turned) >= 60) { ask(turned < 0 ? "in" : "out"); turned = 0; }
  }, { passive: false, capture: true });
  let wait = 0;
  addEventListener("resize", () => { clearTimeout(wait); wait = setTimeout(() => ask(""), 120); });
  ask("");
})();
