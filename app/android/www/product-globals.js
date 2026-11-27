/* HyperRig for TANK-MINI, product builds: the settings for every preset, in Settings, and the calibration of the input. The page has both; what may be sent
 * is in mini-dev-rules.js, and what the firmware does with it is checked by tools/check_mini_globals.py. Here: the global EQ on, off and flat, the room it
 * takes, what the pedal did not take shown as it is, and one step of calibration. */

/* The EQ has five bands at fixed frequencies and no switch: a band at 0 dB is not computed. S.geq is what the pedal has. Switched off, the pedal has five
 * zeros, and the values stay on this computer. */
const HR_EQ = { kept: null, knobs: [], busy: false };
const hrEqNone = v => !v || v.every(x => x === 0);
function hrEqKept(v) {
  try {
    if (v) localStorage.setItem("hyperrig.eq", JSON.stringify(v)); else if (v === null) localStorage.removeItem("hyperrig.eq");
    const k = JSON.parse(localStorage.getItem("hyperrig.eq") || "null");
    return Array.isArray(k) && k.length === 5 && k.every(x => Number.isInteger(x) && x >= -12 && x <= 12) && !hrEqNone(k) ? k : null;
  } catch (e) { return null; }                                   // only a convenience
}
/* The firmware counts 580 ticks for a band, 55 more for the first and a sixteenth on top of what it measures, and takes a band even without room for it:
 * then blocks are let by. */
const hrEqRoom = bands => DEMO || !S.connected || !S.cpu || !S.cpu[1] || S.cpu[0] + 640 * bands <= S.cpu[1];
const hrEqFull = () => toast("This preset leaves no room for it. Switch a block off first, or take one away.", "err", { title: "No room for the global EQ" });

/* One band, as the pedal then has it. After an answer that is not one the pedal is asked again: the page shows what is there. */
async function hrEqSend(b, v) {
  if (DEMO || !S.connected) { S.geq = S.geq.map((x, i) => i === b ? v : x); return true; }
  const of = lines => { const m = /^GEQ (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)$/.exec(reply(lines, "GEQ")); return m && m.slice(1).map(Number); };
  const was = S.geq[b], now = of(await Pedal.cmd(`GEQ ${b} ${v}`, "GEQ")) || of(await Pedal.cmd("GEQ", "GEQ"));
  if (now) S.geq = now;
  if (!was && now && now[b] && S.cpu) S.cpu = [S.cpu[0] + 640, S.cpu[1]];      // until the pedal says it
  return !!now && now[b] === v;
}
const hrEqRefused = () => toast("The pedal did not take the change. Try again.", "err", { title: "Global EQ" });
async function hrEqTurn(b, v) {
  const k = HR_EQ.knobs[b];
  if (!S.geq[b] && v && !hrEqRoom(1)) { k.show(0); hrEqFull(); return; }
  if (!await hrEqSend(b, v)) { k.show(S.geq[b]); hrEqRefused(); }
  hrEqShow();
  if (!DEMO && S.connected) await syncGen();
}
/* All five: those that go off first, which makes room for the others. */
async function hrEqPut(values, kept) {
  if (HR_EQ.busy) return false;
  HR_EQ.busy = true; hrEqShow();
  let ok = true;
  try { for (const b of [0, 1, 2, 3, 4].sort((x, y) => !!values[x] - !!values[y])) if (ok && S.geq[b] !== values[b]) ok = await hrEqSend(b, values[b]); } catch (e) { ok = false; }
  HR_EQ.busy = false;
  hrEqKept(ok ? kept : null);
  hrEq();
  if (!ok && S.connected) hrEqRefused();
  if (!DEMO && S.connected) await syncGen();
  return ok;
}
async function hrEqSwitch(on) {
  const kept = HR_EQ.kept;
  if (on && kept && !hrEqRoom(kept.filter(Boolean).length)) { hrEqShow(); hrEqFull(); return; }
  Log.act("geq_switch", { on });
  if (on && kept) await hrEqPut(kept, null);
  else if (!on) await hrEqPut([0, 0, 0, 0, 0], S.geq.slice());
}
async function hrEqFlat() {
  const was = S.geq.slice(), kept = HR_EQ.kept;
  Log.act("geq_flat", {});
  if (!await hrEqPut([0, 0, 0, 0, 0], null)) return;
  toast("The global EQ is flat.", "ok", { action: { label: "Undo", fn: () => { if (kept) { hrEqKept(kept); hrEq(); } else void hrEqPut(was, null); } } });
}
function hrEqShow() {
  const on = !hrEqNone(S.geq), off = !!HR_EQ.kept, say = $("hrEqSay");
  if (!say) return;
  $("hrEqOn").checked = on;
  $("hrEqOn").disabled = $("hrEqFlat").disabled = HR_EQ.busy || !on && !off;
  for (const k of HR_EQ.knobs) { k.el.inert = off || HR_EQ.busy; k.el.classList.toggle("hroff", off); }
  say.textContent = off ? "Off. Its values are kept." : on && S.stw && S.stw.w > 0 ? "Stereo is paused: the EQ is mono." : "";
}
/* In place of the page's five knobs. */
function hrEq() {
  const host = $("geq"), row = document.createElement("div");
  S.geq = S.geq || [0, 0, 0, 0, 0];
  HR_EQ.kept = hrEqNone(S.geq) ? hrEqKept() : hrEqKept(null);
  host.innerHTML = "";
  HR_EQ.knobs = GEQ_HZ.map((hz, b) => knob(host, { min: -12, max: 12, val: (HR_EQ.kept || S.geq)[b], def: 0, unit: "dB", label: hz + " Hz", onChange: v => hrEqTurn(b, v) }));
  for (const k of HR_EQ.knobs) k.el.classList.add("small");
  row.className = "hreq";
  row.innerHTML = '<label class="spill"><input type="checkbox" id="hrEqOn"> On</label><button type="button" class="btn mini" id="hrEqFlat">Set flat</button><span class="hrsay" id="hrEqSay" role="status"></span>';
  host.append(row);
  $("hrEqOn").onchange = () => void hrEqSwitch($("hrEqOn").checked);
  $("hrEqFlat").onclick = () => void hrEqFlat();
  hrEqShow();
}

/* The calibration: the suggestion comes from the loudest of all readings, so one step is enough; the page's second one, a held note, has no part in it. While
 * the pedal listens the bar is the level of the input. What the pedal found for another capture is not for this one. */
function hrCalOther(c) {
  if (!Cal.open || c.slot === Cal.slot) return false;
  toast("Another capture plays now. Calibrate again for this one.", "warn", { title: "Calibration stopped" });
  closeCalib(true);
  return true;
}
function hrCal() {
  const c = Cal.fin || Cal.last, done = Cal.phase >= 2, res = $("calRes"), dB = v => numL((v > 0 ? "+" : "") + v.toFixed(1));
  if (Cal.fin && hrCalOther(Cal.fin)) return;
  document.querySelectorAll("#calSteps li").forEach(li => { const i = +li.dataset.i; li.classList.toggle("on", i === +done); li.classList.toggle("done", i < +done); });
  $("calPk").textContent = c && c.win && c.hold != null && c.hold > -60 ? dB(c.hold) : "–";
  $("calWin").textContent = c ? c.win : 0;
  $("calNext").textContent = "Show the suggestion";
  $("calNext").disabled = done || !(c && c.win >= 1);
  $("calNext").style.display = done ? "none" : "";
  $("calApply").style.display = "none";
  $("calX").textContent = done ? "Close" : "Cancel";
  document.querySelector("#calm .calread").hidden = done;
  if (!done) {
    res.textContent = !c || c.win < 1 ? "Listening: the first reading takes three seconds." : c.suggest == null ? "Nothing is heard yet. Check the cable and the guitar's volume." : "Keep playing, and play your loudest.";
    return;
  }
  const f = Cal.fin;
  if (!f) { res.textContent = "The pedal did not answer. Try again."; return; }
  if (f.suggest == null) { res.innerHTML = '<span class="warn">No sound was heard.</span> Check the cable and the guitar\'s volume, then try again.'; return; }
  const now = f.trim || 0, same = Math.abs(f.suggest - now) < 0.25;
  res.innerHTML = `<div class="big">Input trim ${dB(f.suggest)} dB</div>` + (same ? "That is what it is now: nothing to change." : `Now it is ${dB(now)} dB.`) +
    ` Your loudest chord comes in at ${dB(f.hold + f.gain)} dB${f.gain ? `, with the input gain of ${dB(f.gain)} dB` : ""}; ${S.model ? `"${esc(S.model)}"` : "this capture"} is meant for ${dB(f.target)} dB.` +
    (f.clamped ? ' <span class="warn">The trim goes no further: change the input gain too.</span>' : "");
  Cal.sugg = Math.round(f.suggest * 2);
  $("calApply").textContent = `Set it to ${dB(f.suggest)} dB`;
  $("calApply").style.display = same ? "none" : "";
}
setInterval(() => {
  if (typeof Cal === "undefined" || !Cal.open || Cal.phase >= 2 || !$("calNow")) return;
  const level = S.inDb10;
  $("calBar").style.width = (level == null ? 0 : dbBar(level)) + "%";
  $("calNow").textContent = level == null || level <= -600 ? "–" : numL((level / 10).toFixed(1));
}, 150);
