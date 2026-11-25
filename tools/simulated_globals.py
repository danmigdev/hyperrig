"""The settings that are the same for every preset, and the calibration of the input, as the firmware answers them: for the simulated pedal of
tools/check_mini_dev_editor.py. tools/check_mini_globals.py asks the firmware itself, in the simulator, and compares every line."""

GLOBALS = r'''
  /* GEQ, HPF, LIM, SPILL, GLIDE, SPUR and CALIB. Numbers in tenths of dB, as the firmware keeps them; -999 is none. */
  const makeGlobals = () => ({geq: [0, 0, 0, 0, 0], hpf: 55, lim: {on: 1, thr: -3, rel: 100}, spill: 1, glide: 16, snap: 1, spur: 1, sens: 120, pages: 0,
    cal: {running: 0, win: 0, peak: 0, rms: 0, hold: 0}});
  const tenths = (v, sign) => (sign && v >= 0 ? "+" : "") + (v < 0 ? "-" : "") + Math.trunc(Math.abs(v) / 10) + "." + Math.abs(v) % 10;
  const fifth = v => Math.trunc((v < 0 ? v - 2 : v + 2) / 5), halves = v => Math.max(-24, Math.min(24, v));
  /* live: what plays, {gain: of the input in dB, trim: in half dB, level: of the capture in tenths of dBu or null, slot}. */
  function calibLineOf(g, live) {
    const c = g.cal, target = live.level === null ? -180 : -30 - live.level, raw = fifth(target - c.hold - 10 * live.gain), heard = c.hold >= -599;
    return `CALIB running=${c.running} win=${c.win}` + (c.win ? ` peak=${tenths(c.peak)} rms=${tenths(c.rms)} hold=${tenths(c.hold)}` : "") + ` gain=${live.gain} sens=${tenths(g.sens)}` +
      (live.level === null ? "" : ` in=${tenths(live.level)}`) + ` target=${tenths(target)} suggest=${heard ? tenths(5 * halves(raw), true) : "none"}` +
      (heard && raw !== halves(raw) ? " clamped=1" : "") + (live.level === null ? "" : ` ref=${tenths(5 * halves(fifth(g.sens - live.level)), true)}`) +
      ` trim=${tenths(5 * live.trim)} slot=${live.slot}`;
  }
  /* A reading: three seconds of the input, as the firmware sees them; the line it sends by itself. */
  function calibWindow(g, live, peak, rms) {
    const c = g.cal;
    Object.assign(c, {win: c.win + 1, peak, rms, hold: Math.max(c.hold, peak)});
    return calibLineOf(g, live);
  }
  function globalAnswer(g, live, word, a) {
    const n = []; for (const x of a) { const m = /^-?\d+/.exec(x); if (!m) break; n.push(+m[0]); if (m[0] !== x) break; }
    const usage = [`ERR ${word} usage`];
    if (word === "GEQ") {
      if (n.length >= 2 && n[0] >= 0 && n[0] <= 4) g.geq[n[0]] = Math.max(-12, Math.min(12, n[1]));
      return ["GEQ " + g.geq.join(" ")];
    }
    if (word === "HPF") {
      if (a.length && (n.length !== 1 || a.length !== 1 || n[0] && (n[0] < 20 || n[0] > 120 || n[0] % 5))) return usage;
      if (a.length) g.hpf = n[0];
      return [`HPF hz=${g.hpf}`];
    }
    if (word === "LIM") {
      const thr = n.length > 1 ? n[1] : g.lim.thr, rel = n.length > 2 ? n[2] : g.lim.rel;
      if (n.length && (thr < -200 || thr > 0 || rel < 10 || rel > 2000)) return usage;
      if (n.length) g.lim = {on: n[0] ? 1 : 0, thr, rel};
      return [`LIM on=${g.lim.on} thr=${g.lim.thr} rel=${g.lim.rel} lat=48 samples=0`];
    }
    if (word === "SPILL") { if (a.length) g.spill = n[0] ? 1 : 0; return [`SPILL ${g.spill} tails=0`]; }
    if (word === "SPUR") { if (a.length) g.spur = n[0] ? 1 : 0; return [`SPUR ${g.spur} learned=0 blocks slow=0 pattern_rms=0 (Q30)`]; }
    if (word === "GLIDE") {
      if (a.length && (!n.length || n[0] < 0 || n[0] > 170 || n.length > 1 && (n[1] < 0 || n[1] > 1))) return usage;
      if (a.length) { g.glide = Math.max(1, Math.trunc((1000 * n[0] + 1331) / 2662)); if (n.length > 1) g.snap = n[1]; }
      return [`GLIDE ms=${g.glide > 1 ? Math.trunc(g.glide * 2662 / 1000) : 0} blocks=${g.glide} snap=${g.snap}`];
    }
    if (word === "CALIB" && a[0] === "sens") {
      const v = a[1] === undefined ? null : Math.round(10 * a[1]);
      if (v !== null && !(v >= -100 && v <= 300)) return ["ERR CALIB sens must be -10..30 dBu"];
      if (v !== null) g.sens = v;
      return [`CALIB sens=${tenths(g.sens)} dBu at 0 dBFS (GSAVE to keep)`];
    }
    if (word === "CALIB") {
      if (a.length > 1 || a.length && !["start", "stop", "status"].includes(a[0])) return ["ERR CALIB usage"];
      if (a[0] === "start" && live.audio !== 2) return ["ERR CALIB audio engine is not running (AUDIO A2L first)"];
      if (a[0] === "start") g.cal = {running: 1, win: 0, peak: -999, rms: -999, hold: -999};
      if (a[0] === "stop") g.cal.running = 0;
      return [calibLineOf(g, live)];
    }
    if (word === "GSAVE") { g.pages = g.pages % 30 + 1; return [`GSAVE ok slot=${g.pages}/30`]; }
  }
'''
