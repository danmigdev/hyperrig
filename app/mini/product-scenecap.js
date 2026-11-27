/* HyperRig for TANK-MINI, product builds: a capture for each scene (firmware: mini/product/scenes.c, SNAPCAP). The amp's panel says whether the capture that
 * plays is for all scenes or for this one. While it is for this one, a capture that is chosen, uploaded or kept is for this scene too, and the preset's own
 * stays what it is. A firmware that does not know the word has one capture for all, as before. */
const hrCap = { of: null, own: -1, touched: false };
function hrCapParse(line) {
  const m = /^SNAPCAP((?: -?\d+){8}) preset=(-?\d+)$/.exec(line || "");
  return m ? { of: m[1].trim().split(" ").map(Number), own: +m[2] } : null;
}
const hrCapAny = () => !!hrCap.of && hrCap.of.some(v => v >= 0);
/* The capture of the scene that is on, or -1. */
const hrCapMine = () => hrCap.of && S.snap >= 0 && S.snaps[S.snap] ? hrCap.of[S.snap] : -1;
async function hrCapAsk(line) {
  const v = hrCapParse(reply(await Pedal.cmd(line, "SNAPCAP", 8000), "SNAPCAP"));
  if (v) { hrCap.of = v.of; hrCap.own = v.own; }
  return v;
}
/* With the scenes, when they are read. */
async function hrCapRead() {
  if (DEMO || !S.connected) { hrCap.of = null; return; }
  if (!await hrCapAsk("SNAPCAP")) { hrCap.of = null; hrCap.own = -1; }
  if (hrCapAny()) await hrCapShown();
}
/* What plays, after it may be another. */
async function hrCapShown() { await loadModel(); await loadModelName(); }
/* A capture of the library, for this scene when it has one of its own, for the preset else; what the pedal says. */
async function hrCapUse(slot) {
  const k = S.snap;
  if (hrCapMine() < 0) return reply(await Pedal.cmd(`CLOAD ${slot}`, "CLOAD", 8000), "CLOAD");
  const v = await hrCapAsk(`SNAPCAP ${k} ${slot}`);
  if (!v || v.of[k] !== slot) return "ERR the pedal did not take it";
  hrCap.touched = true;
  return (await libList(true)).cur === slot ? "SNAPCAP ok" : "ERR the capture could not be loaded";
}
/* A capture came from a file and is in the library now, while the scene has one of its own: it is for this scene. The one it had is loaded again first, so
 * that the pedal knows what the preset's is. */
async function hrCapCame() {
  const k = S.snap, had = hrCapMine(), now = S.capSlot;
  if (had < 0 || now < 0) return;
  if (now !== had) await Pedal.cmd(`CLOAD ${had}`, "CLOAD", 8000);
  const v = await hrCapAsk(`SNAPCAP ${k} ${now}`);
  hrCap.touched = true;
  if (!v || v.of[k] !== now) toast("It plays, but it is not kept for this scene. Choose it in the library.", "warn");
}
async function hrCapScope(mine) {
  const k = S.snap, q = edQ(), to = mine ? S.capSlot : -1;
  if (!hrCap.of || k < 0 || !S.snaps[k] || txn || saveRun || pioBusy) return false;
  if (mine && to < 0) { toast("Save this capture to the library first: a scene takes its capture from there.", "warn"); return false; }
  const v = await hrCapAsk(`SNAPCAP ${k} ${to}`);
  if (!v || v.of[k] !== to) { toast("The pedal did not take the change. Try again.", "err"); return false; }
  Log.act("scene_capture", { k, slot: to });
  hrCap.touched = true;
  edMark("other", null, q);
  await hrCapShown();
  toast(mine ? `Choose the capture of scene ${k + 1} now. The others keep theirs.` : `Scene ${k + 1} has the preset's capture again.`, "ok");
  return true;
}
/* In the amp's panel, in place of the page's "Same in all scenes". */
const hrCapCan = () => !!hrCap.of && !DEMO && S.snap >= 0 && !!S.snaps[S.snap];
const hrCapSig = () => hrCapCan() ? `${S.snap}/${hrCapMine()}` : "";
function hrCapPanel() {
  const host = document.getElementById("hrCapSeg");
  if (!host || !hrCapCan()) return;
  segSel(host, { opts: ["All scenes", "This scene"], val: hrCapMine() >= 0 ? 1 : 0, label: "Capture for", titles: ["Every scene plays this capture", `Only scene ${S.snap + 1} plays this capture`],
    onChange: async v => { await hrCapScope(v === 1); return hrCapMine() >= 0 ? 1 : 0; } });
}
const hrCapLib = () => hrCapMine() >= 0 ? `<span>For scene ${S.snap + 1} only</span>` : "";
/* For the files of presets: what the pedal says, and the captures of the scenes that a file names. */
async function hrCapOf(send) {
  if (!hrCap.of) return null;
  return hrCapParse(pioFind(await send("SNAPCAP", "SNAPCAP"), "SNAPCAP"));
}
const hrCapUsed = st => st.scap ? [...new Set(st.scap.of.filter((v, k) => v >= 0 && st.scenes[k]))] : [];
