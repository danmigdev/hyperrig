/* NAM captures that keep some knobs of what they were made of (docs/PARAMETRIC_NAM.md): from the .nam of a knob-conditioned A2-Lite
 * network to what the pedal loads, the plain capture at the knobs' middle and, behind it, how its numbers move with the knobs.
 *
 * Read: ConcatWaveNet (the knobs beside the audio), HyperWaveNet and HyperA2 (the knobs make the weights), with 3 channels. These are the
 * published forms of neural-amp-modeler-parametric; the code is HyperRig's. The engine of the pedal is the plain one:
 * - with the knobs at rest every term they add is a constant, and the constants of the residual move forward into the biases of the
 *   convolutions, which the engine adds as 32-bit words: exactly the same network;
 * - of a network whose weights follow the knobs, the numbers that move (388 at most) follow a few directions of them, found here by what
 *   each number weighs in the output. How far along each direction, a hidden layer of at most 24 units says, for any place of the knobs.
 * convert() gives the same as Nam2Chip.convert, with what the knobs are called and how near the pedal's form is to the model. */
(function (root) {
  "use strict";
  const C = 3, TAPS = 16, CONTROLS = 6, LAYERS = 23, MAX_DIRECTIONS = 8, MAX_UNITS = 24, SLOT = 8152, Q14 = 16384, HEADER = 12, KNOB = 26;
  const CB = 1, MIX = 2, L1 = 4, RECH = 8, HEAD = 16, HB = 32;
  const MAGIC = 0x31503241, TAIL = 0x5041;                                   // "A2P1", and "AP" in the last words

  function make(Chip) {
    const bad = msg => { throw new Chip.NamError(msg); };
    const ARCH = ["HyperA2", "HyperWaveNet", "ConcatWaveNet"];
    const parse = text => { try { const d = JSON.parse(text); return d && typeof d === "object" ? d : null; } catch (e) { return null; } };
    const handles = text => /"architecture"\s*:\s*"(?:HyperA2|HyperWaveNet|ConcatWaveNet)"/.test(text) && ARCH.includes((parse(text) || {}).architecture);

    /* ---- the knobs ---- */
    function specsOf(list) {
      if (!Array.isArray(list) || !list.length) bad("This parametric capture does not say which knobs it has.");
      return list.map(s => {
        const n = { name: String(s.name || "Knob"), min: +s.min, max: +s.max, def: +s.default, kind: s.type === "switch" ? "switch" : "knob", names: s.enum_names || null };
        if (![n.min, n.max, n.def].every(Number.isFinite) || !(n.max > n.min)) bad(`The knob "${n.name}" of this capture has no usable range.`);
        if (n.kind === "switch" && (!Array.isArray(n.names) || n.names.length < 2)) bad(`The switch "${n.name}" of this capture has no positions.`);
        return n;
      });
    }
    const widthOf = s => (s.kind === "switch" ? s.names.length : 1);
    /* What the network is given for values of the knobs in their own numbers. */
    function encode(specs, values) {
      const out = [];
      specs.forEach((s, i) => {
        if (s.kind === "switch") for (let k = 0; k < s.names.length; k++) out.push(k === Math.round(values[i]) ? 1 : 0);
        else out.push(-1 + 2 * (values[i] - s.min) / (s.max - s.min));
      });
      return out;
    }
    /* Which control of the amp moves which knob: by the name, the others in the order of the panel. The amp's volume stays a volume, so five
     * knobs are the most; a switch, and a knob that finds no control, keeps its usual place. */
    const WORDS = [[5, /gain|drive|pre-?amp|dist|fuzz|boost|input|crunch/i], [1, /bass|\blow|depth|resonance|bottom/i], [2, /mid|contour|body/i],
                   [3, /treble|\bhigh|tone|bright|\bcut/i], [4, /presence|pres\b|air|edge|master|volume|level|output/i]];
    function assign(specs) {
      const control = specs.map(() => 0), free = new Set([1, 2, 3, 4, 5]);
      for (const [c, re] of WORDS) {
        const i = specs.findIndex((s, k) => s.kind === "knob" && !control[k] && re.test(s.name));
        if (i >= 0 && free.has(c)) { control[i] = c; free.delete(c); }
      }
      specs.forEach((s, i) => {
        if (s.kind !== "knob" || control[i]) return;
        const c = [5, 3, 2, 1, 4].find(k => free.has(k));
        if (c) { control[i] = c; free.delete(c); }
      });
      return control;
    }

    /* ---- the model ---- */
    /* -> { specs, at(encoded): the plain engine (in the form of Nam2Chip) at that place of the knobs, with rb the constant of the residual } */
    function model(d) {
      let cfg = d.config || {}, weights = d.weights, arch = d.architecture;
      if (!Array.isArray(weights)) bad("This parametric capture has no weights.");
      const specs = specsOf(cfg.params);
      if (arch === "HyperA2") {
        const sub = (cfg.submodels || []).find(s => s && s.name === "lite");
        if (!sub || !sub.config) bad("This parametric capture has no A2-Lite network: the pedal plays that one.");
        weights = weights.slice(sub.weight_offset, sub.weight_offset + sub.weight_count); cfg = sub.config; arch = "HyperWaveNet";
      }
      const L = (cfg.layers || [])[0];
      if (!L || (cfg.layers || []).length !== 1) bad("This parametric capture is not an A2 network.");
      if (L.channels !== C) bad(`This parametric capture has ${L.channels} channels: the pedal plays A2-Lite, with 3.`);
      const E = specs.reduce((n, s) => n + widthOf(s), 0);
      return arch === "ConcatWaveNet" ? concat(cfg, L, weights, specs, E, d) : hyper(cfg, weights, specs, E, d);
    }
    const plainConfig = (cfg, L) => ({ ...cfg, layers: [{ ...L, input_size: 1, condition_size: 1 }] });

    function concat(cfg, L, weights, specs, E, d) {
      const inputs = 1 + E;
      if ((L.input_size != null && L.input_size !== inputs) || (L.condition_size != null && L.condition_size !== inputs)) bad("The inputs of this parametric capture do not agree with its knobs.");
      const w = Float64Array.from(Float32Array.from(weights)), n = L.kernel_sizes.length, hk = L.head && L.head.kernel_size, flat = [];
      const size = C * inputs + L.kernel_sizes.reduce((s, K) => s + C * C * K + C + C * inputs + C * C + C, 0) + C * hk + (L.head.bias !== false ? 1 : 0) + 1;
      if (w.length !== size) bad(`Unexpected number of weights in this parametric capture: ${w.length}, not ${size}.`);
      let o = 0;
      const take = k => { const a = w.subarray(o, o + k); o += k; return a; };
      const knobs = { rech: null, mix: [] };
      const first = m => [0, 1, 2].map(c => m[c * inputs]);                  // the column of the audio
      const m0 = take(C * inputs); knobs.rech = m0; flat.push(...first(m0));
      for (const K of L.kernel_sizes) {
        flat.push(...take(C * C * K + C));
        const m = take(C * inputs); knobs.mix.push(m); flat.push(...first(m));
        flat.push(...take(C * C + C));
      }
      flat.push(...take(w.length - o));
      const sub = { architecture: "WaveNet", config: plainConfig(cfg, L), weights: flat };
      Chip.checkSupported(sub);
      const of = (m, c, x) => { let s = 0; for (let e = 0; e < E; e++) s += m[c * inputs + 1 + e] * x[e]; return s; };
      return { specs, d, linear: true, units: null, at(x) {
        const e = Chip.buildEngine(sub);
        e.rb = Float64Array.from([0, 1, 2], c => of(knobs.rech, c, x));
        for (let i = 0; i < n; i++) for (let c = 0; c < C; c++) e.layers[i].convB[c] += of(knobs.mix[i], c, x);
        return e;
      } };
    }

    function activation(a) {
      const name = typeof a === "string" ? a : a && (a.name || a.type), slope = a && typeof a === "object" ? a.negative_slope : undefined;
      if (name === "LeakyReLU") return { slope: slope != null ? +slope : 0.01, f: v => (v >= 0 ? v : (slope != null ? +slope : 0.01) * v) };
      if (name === "ReLU") return { slope: 0, f: v => Math.max(0, v) };
      const other = { Tanh: Math.tanh, Sigmoid: v => 1 / (1 + Math.exp(-v)), SiLU: v => v / (1 + Math.exp(-v)),
                      Hardswish: v => (v <= -3 ? 0 : v >= 3 ? v : v * (v + 3) / 6), Softsign: v => v / (1 + Math.abs(v)) }[name];
      if (!other) bad(`The network of the knobs of this capture uses "${name}", which is not known here.`);
      return { slope: null, f: other };
    }
    function hyper(cfg, weights, specs, E, d) {
      const h = cfg.hypernet || {}, map = h.delta_map;
      if (!Array.isArray(map) || !map.length) bad("This parametric capture does not say which of its weights follow the knobs.");
      const { params, hypernet, ...plain } = cfg;
      const w = Float64Array.from(Float32Array.from(weights)), L = cfg.layers[0];
      let baseCount = C + 1 + C * L.head.kernel_size + (L.head.bias !== false ? 1 : 0);
      for (const K of L.kernel_sizes) baseCount += C * C * K + C + C + C * C + C;
      const base = w.subarray(0, baseCount), rest = w.subarray(baseCount), hidden = h.hidden_sizes || [], act = activation(h.activation || "ReLU");
      const width = t => (t.mode === "low_rank" ? t.rank * (t.out_features + t.rest_features) : t.numel);
      const outs = map.reduce((s, t) => s + width(t), 0), trunk = [];
      let o = 0, ins = E;
      for (const n of hidden) { trunk.push({ n, ins, W: rest.subarray(o, o + n * ins), b: rest.subarray(o + n * ins, o + n * ins + n) }); o += n * ins + n; ins = n; }
      const FW = rest.subarray(o, o + outs * ins), Fb = rest.subarray(o + outs * ins, o + outs * ins + outs), anchor = rest.subarray(o + outs * ins + outs, o + outs * ins + 2 * outs);
      if (rest.length !== o + outs * ins + 2 * outs) bad(`Unexpected number of weights in this parametric capture: ${w.length}.`);
      /* The base has the trailing scale of the head, which no knob moves; the convolutions must stay, the pedal has no room to make them anew. */
      const convs = []; { let at = C; for (const K of L.kernel_sizes) { convs.push([at, at + C * C * K]); at += C * C * K + C + C + C * C + C; } }
      for (const t of map) if (convs.some(([a, b]) => t.export_offset < b && t.export_offset + t.numel > a))
        bad("In this parametric capture the knobs change the convolutions: the pedal plays the usual form, in which they do not.");
      const at = x => {
        let v = Float64Array.from(x);
        for (const l of trunk) { const y = new Float64Array(l.n); for (let i = 0; i < l.n; i++) { let s = l.b[i]; for (let k = 0; k < l.ins; k++) s += l.W[i * l.ins + k] * v[k]; y[i] = act.f(s); } v = y; }
        const flat = Float64Array.from(base);
        let p = 0;
        for (const t of map) {
          const n = width(t), f = new Float64Array(n);
          for (let i = 0; i < n; i++) { let s = Fb[p + i]; for (let k = 0; k < ins; k++) s += FW[(p + i) * ins + k] * v[k]; f[i] = s; }
          if (t.mode === "low_rank") {
            const R = t.rank, O = t.out_features, Z = t.rest_features;
            for (let i = 0; i < n; i++) f[i] += anchor[p + i];
            for (let a = 0; a < O; a++) for (let b = 0; b < Z; b++) { let s = 0; for (let r = 0; r < R; r++) s += f[a * R + r] * f[O * R + r * Z + b]; flat[t.export_offset + a * Z + b] += s; }
          } else for (let i = 0; i < n; i++) flat[t.export_offset + i] += f[i];
          p += n;
        }
        return Chip.buildEngine({ architecture: "WaveNet", config: plainConfig(plain, L), weights: Array.from(flat) });
      };
      Chip.checkSupported({ architecture: "WaveNet", config: plainConfig(plain, L), weights: Array.from(base) });
      const units = trunk.length === 1 && act.slope != null && trunk[0].n <= MAX_UNITS ? { slope: act.slope, n: trunk[0].n, W: trunk[0].W, b: trunk[0].b, ins: E } : null;
      return { specs, d, linear: false, units, at };
    }

    /* The constants of the residual forward into the biases of the convolutions: every l1B is 0 afterwards and the output is the same. */
    function push(e) {
      const off = Float64Array.from(e.rb || [0, 0, 0]);
      for (const l of e.layers) {
        for (let o = 0; o < C; o++) { let s = 0; for (let i = 0; i < C; i++) for (let k = 0; k < l.K; k++) s += l.convW[(o * C + i) * l.K + k] * off[i]; l.convB[o] += s; }
        for (let o = 0; o < C; o++) { off[o] += l.l1B[o]; l.l1B[o] = 0; }
      }
      e.rb = null;
      return e;
    }

    /* ---- the numbers that move, in the order the pedal takes them ---- */
    const lay = (() => {
      const groups = [];
      let n = 0;
      const add = (kind, layer, count) => { groups.push({ kind, layer, from: n, count }); n += count; };
      for (let i = 0; i < LAYERS; i++) {
        add(CB, i, C); add(MIX, i, C);
        if (i < LAYERS - 1) add(L1, i, C * C);                               // what the last layer gives the residual goes nowhere
      }
      add(RECH, 0, C); add(HEAD, 0, C * TAPS); add(HB, 0, 1);
      return { groups, n };
    })();
    function read(e) {
      const out = new Float64Array(lay.n);
      for (const g of lay.groups) {
        const l = e.layers[g.layer], a = g.kind === CB ? l.convB : g.kind === MIX ? l.mixW : g.kind === L1 ? l.l1W : g.kind === RECH ? e.rech : null;
        if (a) for (let i = 0; i < g.count; i++) out[g.from + i] = a[i];
        else if (g.kind === HEAD) for (let t = 0; t < TAPS; t++) for (let c = 0; c < C; c++) out[g.from + t * C + c] = e.hW[c * TAPS + t] * e.headScale;
        else out[g.from] = e.hB * e.headScale;
      }
      return out;
    }
    function write(e, v) {
      const layers = e.layers.map(l => ({ ...l, convB: l.convB.slice(), mixW: l.mixW.slice(), l1W: l.l1W.slice() })), n = { ...e, layers, rech: e.rech.slice(), hW: e.hW.map(x => x * e.headScale), hB: e.hB * e.headScale, headScale: 1 };
      for (const g of lay.groups) {
        const l = layers[g.layer], a = g.kind === CB ? l.convB : g.kind === MIX ? l.mixW : g.kind === L1 ? l.l1W : g.kind === RECH ? n.rech : null;
        if (a) for (let i = 0; i < g.count; i++) a[i] = v[g.from + i];
        else if (g.kind === HEAD) for (let t = 0; t < TAPS; t++) for (let c = 0; c < C; c++) n.hW[c * TAPS + t] = v[g.from + t * C + c];
        else n.hB = v[g.from];
      }
      return n;
    }

    /* ---- the network, forward and backward, for what each number weighs ---- */
    function forward(e, x, keep) {
      const T = x.length, rs = [], as = [];
      let r = [0, 1, 2].map(c => { const a = new Float64Array(T), w = e.rech[c]; for (let t = 0; t < T; t++) a[t] = w * x[t]; return a; });
      const s = [0, 1, 2].map(() => new Float64Array(T));
      for (const l of e.layers) {
        if (keep) rs.push(r);
        const z = [0, 1, 2].map(o => {
          const a = new Float64Array(T).fill(l.convB[o]), mw = l.mixW[o];
          for (let k = 0; k < l.K; k++) {
            const sh = (l.K - 1 - k) * l.dil, w0 = l.convW[o * 3 * l.K + k], w1 = l.convW[(o * 3 + 1) * l.K + k], w2 = l.convW[(o * 3 + 2) * l.K + k], a0 = r[0], a1 = r[1], a2 = r[2];
            for (let t = sh; t < T; t++) a[t] += w0 * a0[t - sh] + w1 * a1[t - sh] + w2 * a2[t - sh];
          }
          for (let t = 0; t < T; t++) { const v = a[t] + mw * x[t]; a[t] = v; }
          return a;
        });
        const a = z.map(q => { const y = new Float64Array(T); for (let t = 0; t < T; t++) { const v = q[t]; y[t] = v >= 0 ? v : l.slope * v; } return y; });
        if (keep) as.push(a);
        for (let c = 0; c < C; c++) { const sc = s[c], ac = a[c]; for (let t = 0; t < T; t++) sc[t] += ac[t]; }
        r = [0, 1, 2].map(o => { const y = new Float64Array(T), w0 = l.l1W[o * 3], w1 = l.l1W[o * 3 + 1], w2 = l.l1W[o * 3 + 2], b = l.l1B[o], p = r[o], a0 = a[0], a1 = a[1], a2 = a[2];
          for (let t = 0; t < T; t++) y[t] = p[t] + w0 * a0[t] + w1 * a1[t] + w2 * a2[t] + b; return y; });
      }
      const y = new Float64Array(T).fill(e.hB * e.headScale);
      for (let c = 0; c < C; c++) for (let k = 0; k < e.hk; k++) { const sh = e.hk - 1 - k, w = e.hW[c * e.hk + k] * e.headScale, sc = s[c]; for (let t = sh; t < T; t++) y[t] += w * sc[t - sh]; }
      return { y, s, as, rs };
    }
    /* The derivative of sum(dy * y) by each number of the layout. */
    function backward(e, x, f, dy, g) {
      const T = x.length, ds = [0, 1, 2].map(() => new Float64Array(T));
      for (let c = 0; c < C; c++) for (let k = 0; k < e.hk; k++) { const sh = e.hk - 1 - k, w = e.hW[c * e.hk + k] * e.headScale, a = ds[c]; for (let t = sh; t < T; t++) a[t - sh] += w * dy[t]; }
      const at = {};
      for (const q of lay.groups) at[q.kind + ":" + q.layer] = q.from;
      if (at[HB + ":0"] != null) { let s = 0; for (let t = 0; t < T; t++) s += dy[t]; g[at[HB + ":0"]] = s; }
      if (at[HEAD + ":0"] != null) for (let k = 0; k < TAPS; k++) for (let c = 0; c < C; c++) { const sh = TAPS - 1 - k, sc = f.s[c]; let s = 0; for (let t = sh; t < T; t++) s += dy[t] * sc[t - sh]; g[at[HEAD + ":0"] + k * C + c] = s; }
      let dr = [0, 1, 2].map(() => new Float64Array(T));
      for (let i = e.layers.length - 1; i >= 0; i--) {
        const l = e.layers[i], a = f.as[i], l1 = at[L1 + ":" + i], cb = at[CB + ":" + i], mx = at[MIX + ":" + i];
        if (l1 != null) for (let o = 0; o < C; o++) for (let c = 0; c < C; c++) { let s = 0; const d = dr[o], ac = a[c]; for (let t = 0; t < T; t++) s += d[t] * ac[t]; g[l1 + o * C + c] = s; }
        const dz = [0, 1, 2].map(c => { const y = new Float64Array(T), w0 = l.l1W[c], w1 = l.l1W[3 + c], w2 = l.l1W[6 + c], d0 = dr[0], d1 = dr[1], d2 = dr[2], sc = ds[c], ac = a[c];
          for (let t = 0; t < T; t++) y[t] = (sc[t] + w0 * d0[t] + w1 * d1[t] + w2 * d2[t]) * (ac[t] >= 0 ? 1 : l.slope); return y; });
        for (let c = 0; c < C; c++) { let s = 0, m = 0; const d = dz[c]; for (let t = 0; t < T; t++) { s += d[t]; m += d[t] * x[t]; } if (cb != null) g[cb + c] = s; if (mx != null) g[mx + c] = m; }
        const n = [0, 1, 2].map(c => dr[c].slice());
        for (let o = 0; o < C; o++) for (let k = 0; k < l.K; k++) {
          const sh = (l.K - 1 - k) * l.dil, d = dz[o];
          for (let c = 0; c < C; c++) { const w = l.convW[(o * 3 + c) * l.K + k], y = n[c]; for (let t = sh; t < T; t++) y[t - sh] += w * d[t]; }
        }
        dr = n;
      }
      if (at[RECH + ":0"] != null) for (let c = 0; c < C; c++) { let s = 0; const d = dr[c]; for (let t = 0; t < T; t++) s += d[t] * x[t]; g[at[RECH + ":0"] + c] = s; }
      return g;
    }

    /* ---- small linear algebra ---- */
    function solve(A, B, n, m) {                                             // symmetric positive: A n*n, B n*m, by Cholesky; the answer in B
      const Lw = Float64Array.from(A);
      for (let i = 0; i < n; i++) for (let j = 0; j <= i; j++) { let s = Lw[i * n + j]; for (let k = 0; k < j; k++) s -= Lw[i * n + k] * Lw[j * n + k]; Lw[i * n + j] = i === j ? Math.sqrt(Math.max(s, 1e-30)) : s / Lw[j * n + j]; }
      for (let c = 0; c < m; c++) {
        for (let i = 0; i < n; i++) { let s = B[i * m + c]; for (let k = 0; k < i; k++) s -= Lw[i * n + k] * B[k * m + c]; B[i * m + c] = s / Lw[i * n + i]; }
        for (let i = n - 1; i >= 0; i--) { let s = B[i * m + c]; for (let k = i + 1; k < n; k++) s -= Lw[k * n + i] * B[k * m + c]; B[i * m + c] = s / Lw[i * n + i]; }
      }
      return B;
    }
    /* The directions (rows, orthonormal) along which the rows of A (G*n) spread most, by subspace iteration. */
    function directions(A, G, n, r) {
      const k = Math.min(r + 4, G, n), R = Chip.rng(7);
      let Q = Array.from({ length: k }, () => Float64Array.from({ length: n }, () => R.g()));
      const ortho = q => { const out = []; for (const v of q) { for (let pass = 0; pass < 2; pass++) for (const u of out) { let s = 0; for (let i = 0; i < n; i++) s += u[i] * v[i]; for (let i = 0; i < n; i++) v[i] -= s * u[i]; }
        let s = 0; for (let i = 0; i < n; i++) s += v[i] * v[i]; s = Math.sqrt(s); if (s > 1e-200) { for (let i = 0; i < n; i++) v[i] /= s; out.push(v); } } return out; };
      const apply = q => q.map(v => { const u = new Float64Array(G); for (let g = 0; g < G; g++) { let s = 0, o = g * n; for (let i = 0; i < n; i++) s += A[o + i] * v[i]; u[g] = s; }
        const y = new Float64Array(n); for (let g = 0; g < G; g++) { const s = u[g], o = g * n; if (s) for (let i = 0; i < n; i++) y[i] += s * A[o + i]; } return { y, u }; });
      Q = ortho(Q);
      for (let it = 0; it < 60; it++) Q = ortho(apply(Q).map(a => a.y));
      /* within the subspace: the symmetric matrix of the spreads, by Jacobi */
      const m = Q.length, U = apply(Q).map(a => a.u), S = new Float64Array(m * m), V = new Float64Array(m * m);
      for (let i = 0; i < m; i++) { V[i * m + i] = 1; for (let j = 0; j < m; j++) { let s = 0; for (let g = 0; g < G; g++) s += U[i][g] * U[j][g]; S[i * m + j] = s; } }
      for (let sweep = 0; sweep < 60; sweep++) for (let p = 0; p < m; p++) for (let q = p + 1; q < m; q++) {
        const apq = S[p * m + q];
        if (Math.abs(apq) < 1e-300) continue;
        const th = (S[q * m + q] - S[p * m + p]) / (2 * apq), t = Math.sign(th || 1) / (Math.abs(th) + Math.sqrt(th * th + 1)), c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let i = 0; i < m; i++) { const a = S[i * m + p], b = S[i * m + q]; S[i * m + p] = c * a - s * b; S[i * m + q] = s * a + c * b; }
        for (let i = 0; i < m; i++) { const a = S[p * m + i], b = S[q * m + i]; S[p * m + i] = c * a - s * b; S[q * m + i] = s * a + c * b; }
        for (let i = 0; i < m; i++) { const a = V[i * m + p], b = V[i * m + q]; V[i * m + p] = c * a - s * b; V[i * m + q] = s * a + c * b; }
      }
      const order = [...Array(m).keys()].sort((a, b) => S[b * m + b] - S[a * m + a]).slice(0, r).filter(i => S[i * m + i] > 1e-24);
      return order.map(i => { const v = new Float64Array(n); for (let j = 0; j < m; j++) for (let k2 = 0; k2 < n; k2++) v[k2] += V[j * m + i] * Q[j][k2]; return v; });
    }

    /* ---- the places of the knobs that are looked at ---- */
    function places(P, R) {
      const out = [];
      if (P === 0) return [[]];
      if (P <= 2) { const n = P === 1 ? 61 : 21; for (let a = 0; a < n; a++) for (let b = 0; b < (P === 1 ? 1 : n); b++) out.push(P === 1 ? [-1 + 2 * a / (n - 1)] : [-1 + 2 * a / (n - 1), -1 + 2 * b / (n - 1)]); return out; }
      out.push(Array(P).fill(0));
      for (let c = 0; c < 1 << P; c++) out.push([...Array(P).keys()].map(k => (c >> k & 1 ? 1 : -1)));
      for (let k = 0; k < P; k++) for (let v = -1; v <= 1.001; v += .25) { const x = Array(P).fill(0); x[k] = v; out.push(x); }
      while (out.length < 420) out.push([...Array(P).keys()].map(() => (R.u() < .2 ? (R.u() < .5 ? -1 : 1) : 2 * R.u() - 1)));
      return out;
    }

    /* ---- how the pedal goes from the controls to the numbers: whole numbers, so that it is the same here and there ---- */
    const down = (v, s) => Math.floor(v / Math.pow(2, s));
    const rows = (list, x) => list.map(q => { let t = q.bias * Q14 + Math.pow(2, q.shift - 1); for (let k = 0; k < x.length; k++) t += q.w[k] * x[k]; return down(t, q.shift); });
    const xOf = (k, v) => { v = Math.max(-120, Math.min(120, v)); return k.mid + Math.trunc((v < 0 ? k.mid - k.lo : k.hi - k.mid) * v / 120); };
    const bent = (units, slope, x) => rows(units, x).map(v => (v < 0 ? down(v * slope, 10) : v));
    const coefficients = (ext, x) => rows(ext.far, bent(ext.units, ext.slope, x));
    /* The change of every number, in steps of the engine's words, for the amp's controls as AMPEQ has them (tenths). */
    const change = (ext, tone) => changeAt(ext, ext.knobs.map(k => xOf(k, tone[k.control])));
    function changeAt(ext, x) {
      const c = coefficients(ext, x), out = new Float64Array(lay.n);
      lay.groups.forEach((g, j) => { for (let i = g.from; i < g.from + g.count; i++) { let t = 0; for (let k = 0; k < ext.r; k++) t += c[k] * ext.B[i * ext.r + k]; out[i] = ext.shift[j] > 0 ? down(t, ext.shift[j]) : t * Math.pow(2, -ext.shift[j]); } });
      return out;
    }

    /* ---- what is stored behind the capture ---- */
    const sizeOf = (P, U, r) => HEADER + KNOB * P + lay.groups.length + U * (3 + 2 * P) + r * (3 + 2 * U + lay.n) + 8;
    function pack(ext, plain) {
      const P = ext.knobs.length, U = ext.units.length, size = sizeOf(P, U, ext.r), total = plain.length + size, u8 = new Uint8Array(total), dv = new DataView(u8.buffer);
      u8.set(plain);
      let o = plain.length;
      dv.setUint32(o, MAGIC, true);
      u8.set([1, P, U, ext.r], o + 4);
      dv.setUint16(o + 8, ext.slope, true);
      o += HEADER;
      for (const k of ext.knobs) {
        u8[o] = k.control;
        u8.set(new TextEncoder().encode(k.name.normalize("NFD").replace(/[^\x20-\x7e]/g, "")).slice(0, 11), o + 1);
        dv.setFloat32(o + 12, k.min, true); dv.setFloat32(o + 16, k.max, true);
        dv.setInt16(o + 20, k.lo, true); dv.setInt16(o + 22, k.mid, true); dv.setInt16(o + 24, k.hi, true);
        o += KNOB;
      }
      for (const v of ext.shift) dv.setInt8(o++, v);
      for (const q of [...ext.units, ...ext.far]) { u8[o++] = q.shift; for (const v of [q.bias, ...q.w]) { dv.setInt16(o, v, true); o += 2; } }
      for (const v of ext.B) dv.setInt8(o++, v);
      dv.setUint16(o, size, true); dv.setUint16(o + 2, TAIL, true);
      dv.setUint32(o + 4, Chip.crc32(u8.subarray(0, total - 4)), true);
      return u8;
    }
    function unpack(u8) {
      const dv = new DataView(u8.buffer, u8.byteOffset, u8.length), n = u8.length;
      if (n < 60 || dv.getUint16(n - 6, true) !== TAIL) return null;
      const size = dv.getUint16(n - 8, true), at = n - size, P = u8[at + 5], U = u8[at + 6], r = u8[at + 7];
      if (at < 44 || dv.getUint32(at, true) !== MAGIC || u8[at + 4] !== 1 || size !== sizeOf(P, U, r)) return null;
      const ext = { r, slope: dv.getUint16(at + 8, true), knobs: [], plain: at };
      let o = at + HEADER;
      for (let k = 0; k < P; k++, o += KNOB) {
        let name = ""; for (let i = 1; i < 12 && u8[o + i]; i++) name += String.fromCharCode(u8[o + i]);
        ext.knobs.push({ control: u8[o], name, min: dv.getFloat32(o + 12, true), max: dv.getFloat32(o + 16, true), lo: dv.getInt16(o + 20, true), mid: dv.getInt16(o + 22, true), hi: dv.getInt16(o + 24, true) });
      }
      const i8 = c => { const a = []; for (let i = 0; i < c; i++) a.push(dv.getInt8(o++)); return a; };
      const row = c => { const q = { shift: u8[o++], w: [] }; for (let i = 0; i <= c; i++, o += 2) q.w.push(dv.getInt16(o, true)); q.bias = q.w.shift(); return q; };
      ext.shift = i8(lay.groups.length);
      ext.units = Array.from({ length: U }, () => row(P)); ext.far = Array.from({ length: r }, () => row(U));
      ext.B = i8(lay.n * r);
      return ext;
    }

    /* ---- the conversion ---- */
    function convert(text, opts) {
      opts = opts || {};
      const prog = opts.onProgress || (() => {}), t0 = Date.now(), d = parse(text);
      if (!d || !ARCH.includes(d.architecture)) bad("This is not a parametric NAM capture.");
      prog(.01, "Reading the network");
      const mod = model(d), specs = mod.specs, control = assign(specs), fs = d.sample_rate || 48000;
      if (fs !== 48000) bad(`This capture is ${fs} Hz; the pedal runs at 48 kHz.`);
      const moved = specs.map((s, i) => i).filter(i => control[i]), P = moved.length;
      /* The middle of a control is the knob's usual place, unless that is at an end: then it is the middle of the knob. */
      const knobs = moved.map(i => { const s = specs[i], e = -1 + 2 * (s.def - s.min) / (s.max - s.min), mid = Math.abs(e) > .9 ? 0 : e;
        return { i, control: control[i], name: s.name, min: s.min, max: s.max, lo: -Q14, mid: Math.round(mid * Q14), hi: Q14 }; });
      const encodeAt = x => { const v = specs.map(s => s.def); moved.forEach((i, k) => { v[i] = specs[i].min + (x[k] + 1) / 2 * (specs[i].max - specs[i].min); }); return encode(specs, v); };
      const engineAt = x => push(mod.at(encodeAt(x)));
      const x0 = knobs.map(k => k.mid / Q14), e0 = engineAt(x0);
      if (e0.layers.length !== LAYERS || e0.hk !== TAPS) bad("This parametric capture is not of the A2 shape: 23 layers and a head of 16.");
      const R = Chip.rng(99), spots = places(P, R), V = spots.map(x => read(engineAt(x))), v0 = read(e0), moves = V.some(v => v.some((y, i) => Math.abs(y - v0[i]) > 1e-9));

      /* the levels, over the whole range of the knobs */
      const sigs = Chip.embeddedSignals(fs), short = [sigs[1].subarray(0, 24000), sigs[2].subarray(0, 48000), sigs[4].subarray(0, 36000)];
      const sites = [x0];
      for (let c = 0; c < 1 << P && P; c++) if (P <= 3 || c === 0 || c === (1 << P) - 1 || R.u() < 8 / (1 << P)) sites.push([...Array(P).keys()].map(k => (c >> k & 1 ? 1 : -1)));
      for (let k = 0; k < P; k++) for (const v of [-1, 1]) { const x = x0.slice(); x[k] = v; sites.push(x); }
      const rs = [];
      sites.forEach((x, j) => { const e = j ? engineAt(x) : e0; for (const s of j ? short : sigs) rs.push(Chip.measure(e, s)); prog(.02 + .4 * (j + 1) / sites.length, "Calibrating levels"); });
      const ranges = Chip.mergeRanges(rs);
      for (const k of ["rech", "head", "out"]) ranges[k] *= 1.5;
      ranges.z = ranges.z.map(v => v * 1.5); ranges.x3 = ranges.x3.map(v => v * 1.5);

      const plainBytes = 36 + 1 + 2 * C + 4 + 1 + 2 * C * TAPS + 8 + e0.layers.reduce((s, l) => s + 13 + 2 * C * C * l.K + 16 * C + 2 * C + 2 * C * C, 0);
      const ext = P && moves ? extension({ mod, P, knobs, spots, V, v0, engineAt, x0, e0, R, room: SLOT - plainBytes, prog }) : null;

      /* the words of the engine at the middle, with room in every one of them for the whole range, as the model has it and as it is stored */
      const stored = ext ? spots.map(x => reals(ext, x, v0)) : [];
      const ceiling = (kind, layer) => { let m = 0; const g = lay.groups.find(q => q.kind === kind && q.layer === layer); for (const v of [...V, ...stored]) for (let i = g.from; i < g.from + g.count; i++) m = Math.max(m, Math.abs(v[i])); return m * 1.01; };
      const F = (m, most) => Math.min(Chip.fbits(m, 16), most), maxOf = a => a.reduce((m, v) => Math.max(m, Math.abs(v)), 0);
      const meta = d.metadata || {}, name = opts.name != null ? opts.name : typeof meta.name === "string" && meta.name ? meta.name : "NAM";
      const q = (v, f, bits) => { const s = Math.pow(2, f); return Array.from(v, a => { let y = Math.round(a * s); if (bits === 64) return BigInt(y); const lim = Math.pow(2, bits - 1); return Math.max(-lim, Math.min(lim - 1, y)); }); };
      const m = { wbits: 16, abits: 32, fs, C, head_K: TAPS, name, Fin: Chip.fbits(1, 32), Fx3_0: Chip.fbits(ranges.rech * 2, 32), Fh: Chip.fbits(ranges.head * 2, 32), Fout: Chip.fbits(ranges.out * 2, 32), layers: [] };
      m.rech_F = F(Math.max(maxOf(e0.rech), ceiling(RECH, 0)), m.Fx3_0 - m.Fin + 31); m.rech_W = q(e0.rech, m.rech_F, 16);
      let prev = m.Fx3_0;
      e0.layers.forEach((l, i) => {
        const Fz = Chip.fbits(ranges.z[i] * 2, 32), Fx3 = Chip.fbits(ranges.x3[i] * 2, 32), cF = F(maxOf(l.convW), Fz - prev + 31);
        const mF = F(Math.max(maxOf(l.mixW), ceiling(MIX, i)), Fz - m.Fin + 31), lF = F(i < LAYERS - 1 ? Math.max(maxOf(l.l1W), ceiling(L1, i)) : maxOf(l.l1W), Fx3 - Fz + 31);
        m.layers.push({ K: l.K, dil: l.dil, Fz, Fx3, lmul: Math.round(l.slope * (1 << 24)), cF, cW: q(l.convW, cF, 16), cB: q(l.convB, cF + prev, 64), mF, mW: q(l.mixW, mF, 16), lF, lW: q(l.l1W, lF, 16), lB: q(l.l1B, lF + Fz, 64) });
        prev = Fx3;
      });
      m.Fh = Math.min(m.Fh, Math.min(...m.layers.map(l => l.Fz)) - 1);
      const hW = Float64Array.from(e0.hW, v => v * e0.headScale);
      m.hF = F(Math.max(maxOf(hW), ceiling(HEAD, 0)), m.Fout - m.Fh + 31); m.hW = q(hW, m.hF, 16); m.hB = q([e0.hB * e0.headScale], m.hF + m.Fh, 64)[0];
      const plain = Chip.pack(m);
      Chip.validateBlob(plain);

      let blob = plain, fit = null;
      if (ext) {
        ext.shift = lay.groups.map((q, j) => {
          const l = m.layers[q.layer], f = q.kind === CB ? l.Fz : q.kind === MIX ? l.mF : q.kind === L1 ? l.lF : q.kind === RECH ? m.rech_F : q.kind === HEAD ? m.hF : m.Fout;
          return ext.cexp + ext.eg[j] - f;
        });
        const wide = lay.groups.some(g => g.kind === CB && ceiling(CB, g.layer) * Math.pow(2, m.layers[g.layer].Fz) >= Math.pow(2, 30));      // a step of the way there must fit
        if (wide || ext.shift.some(s => s < -16 || s > 30)) bad("The levels of this parametric capture are too extreme for the pedal.");
        blob = pack(ext, plain);
        fit = check({ ext, m, engineAt, e0, P, R, prog, sig: sigs[2] });
      }
      prog(1, "Done");
      const macs = C + e0.layers.reduce((s, l) => s + l.convW.length + l.mixW.length + l.l1W.length, 0) + e0.hW.length;
      return { blob, name, ranges, knobs: ext ? ext.knobs.map(k => ({ name: k.name, control: k.control, min: k.min, max: k.max })) : [],
        fixed: specs.filter((s, i) => !control[i]).map(s => ({ name: s.name, at: s.kind === "switch" ? s.names[Math.round(s.def)] : s.def })), fit,
        stats: { layers: LAYERS, channels: C, macs, headK: TAPS, sampleRate: fs, bytes: blob.length, directions: ext ? ext.r : 0, calibSamples: sigs.reduce((s, a) => s + a.length, 0), calibPeak: ranges.out, ms: Date.now() - t0, headScale: e0.headScale,
                 meta: { name: meta.name, modeledBy: meta.modeled_by, gear: meta.gear_model || meta.gear_make, tone: meta.tone_type, gearType: typeof meta.gear_type === "string" ? meta.gear_type : null,
                         inputLevelDbu: typeof meta.input_level_dbu === "number" && isFinite(meta.input_level_dbu) ? meta.input_level_dbu : null } } };
    }

    /* The hidden layer: the model's own when it has one, for a linear model the knobs themselves, else bends along every knob and pair of knobs. */
    function hiddenLayer(mod, P, knobs, encodeRow) {
      const rows = [];
      let slope = 1024;
      if (mod.linear) for (let k = 0; k < P; k++) rows.push([...Array(P).keys()].map(j => (j === k ? 1 : 0)).concat(0));
      else if (mod.units) { slope = Math.round(mod.units.slope * 1024); for (let u = 0; u < mod.units.n; u++) rows.push(encodeRow(u)); }
      else {
        slope = 0;
        const bends = P <= 2 ? [-.9, -.5, -.15, .15, .5] : P === 3 ? [-.7, 0, .6] : [-.4, .5];
        for (let k = 0; k < P; k++) { rows.push([...Array(P).keys()].map(j => (j === k ? 1 : 0)).concat(1)); for (const b of bends) rows.push([...Array(P).keys()].map(j => (j === k ? 1 : 0)).concat(-b)); }
        for (let a = 0; a < P; a++) for (let b = a + 1; b < P; b++) for (const s of [1, -1]) if (rows.length < MAX_UNITS) rows.push([...Array(P).keys()].map(j => (j === a ? .5 : j === b ? .5 * s : 0)).concat(0));
        rows.length = Math.min(rows.length, MAX_UNITS);
      }
      return { rows, slope };
    }

    function extension(o) {
      const { mod, P, knobs, spots, V, v0, engineAt, x0, e0, R, room, prog } = o, n = lay.n, G = spots.length;
      /* what each number weighs in the output: its effect on the sum of the output with random signs, at the middle and the ends of the knobs */
      const w = new Float64Array(n), T = 6346 + 6000, x = new Float64Array(T);
      { const src = Chip.strum(48000, [82.41, 123.47, 164.81, 207.65, 246.94, 329.63], T / 48000 + .01, .5, R, .998); for (let t = 0; t < T; t++) x[t] = src[t]; }
      const sites = [x0, ...[...Array(P).keys()].flatMap(k => [-.8, .8].map(v => { const a = x0.slice(); a[k] = v; return a; }))], sum = new Float64Array(n), g = new Float64Array(n);
      sites.forEach((site, j) => {
        const e = engineAt(site), f = forward(e, x, true);
        let p = 0; for (let t = 6346; t < T; t++) p += f.y[t] * f.y[t];
        for (let k = 0; k < 2; k++) {
          const dy = new Float64Array(T); for (let t = 6346; t < T; t++) dy[t] = R.u() < .5 ? -1 : 1;
          backward(e, x, f, dy, g);
          for (let i = 0; i < n; i++) sum[i] += g[i] * g[i] / Math.max(p, 1e-12);
        }
        prog(.44 + .3 * (j + 1) / sites.length, "Weighing the knobs");
      });
      const top = Math.sqrt(Math.max(...sum));
      for (let i = 0; i < n; i++) w[i] = Math.max(Math.sqrt(sum[i]), top * 1e-6);
      const A = new Float64Array(G * n);
      for (let k = 0; k < G; k++) for (let i = 0; i < n; i++) A[k * n + i] = (V[k][i] - v0[i]) * w[i];

      const { rows: rows0, slope } = hiddenLayer(mod, P, knobs, u => {              // the model's unit over the knobs that move: the others are constants
        const W = mod.units.W, ins = mod.units.ins, row = Array(P).fill(0);
        let b = mod.units.b[u], e = 0;
        mod.specs.forEach((s, i) => {
          const k = knobs.findIndex(q => q.i === i), wide = widthOf(s);
          if (k >= 0) row[k] = W[u * ins + e];
          else { const c = encode([s], [s.def]); for (let j = 0; j < wide; j++) b += W[u * ins + e + j] * c[j]; }
          e += wide;
        });
        return row.concat(b);
      });
      const U = rows0.length, whole = v => Math.max(-32768, Math.min(32767, Math.round(v)));
      const units = rows0.map(row => { const e = Math.max(1, Math.min(14, Chip.fbits(Math.max(1e-6, ...row.map(Math.abs)), 16))), q = row.map(v => whole(v * Math.pow(2, e))); return { shift: e, bias: q[P], w: q.slice(0, P) }; });

      let r = mod.linear ? P : MAX_DIRECTIONS;
      while (r && sizeOf(P, U, r) > room) r--;
      if (!r || (mod.linear && r < P)) bad("This parametric capture has too many knobs for a slot of the pedal.");
      let dirs;
      if (mod.linear) {                                                      // each knob is one direction, exactly
        dirs = [...Array(P).keys()].map(k => { const a = x0.slice(); a[k] = 1; const b = x0.slice(); b[k] = -1; const va = read(engineAt(a)), vb = read(engineAt(b));
          return Float64Array.from(va, (v, i) => (v - vb[i]) / 2 * w[i]); });
      } else dirs = directions(A, G, n, r);
      r = dirs.length;

      /* 8 bits for each direction: one scale for each tensor of each layer, what its numbers weigh; nothing is clipped */
      const eg = lay.groups.map(q => { let s = 0; for (let i = q.from; i < q.from + q.count; i++) s += w[i] * w[i]; return Math.round(Math.log2(Math.sqrt(s / q.count))); });
      const groupOf = new Int32Array(n); lay.groups.forEach((q, j) => { for (let i = q.from; i < q.from + q.count; i++) groupOf[i] = j; });
      const B = new Int8Array(n * r);
      dirs.forEach((v, k) => {
        let mx = 0; for (let i = 0; i < n; i++) mx = Math.max(mx, Math.abs(v[i] / w[i] * Math.pow(2, eg[groupOf[i]])));
        for (let i = 0; i < n; i++) B[i * r + k] = Math.max(-127, Math.min(127, Math.round(v[i] / w[i] * Math.pow(2, eg[groupOf[i]]) * 127 / mx)));
      });
      /* how far along each stored direction every place is (least squares with the stored directions), and the hidden layer that says it */
      const gram = new Float64Array(r * r), right = new Float64Array(r * G), real = i => Math.pow(2, -eg[groupOf[i]]) * w[i];
      for (let i = 0; i < n; i++) for (let a = 0; a < r; a++) for (let b = 0; b < r; b++) gram[a * r + b] += B[i * r + a] * B[i * r + b] * real(i) * real(i);
      for (let k = 0; k < G; k++) for (let i = 0; i < n; i++) { const t = A[k * n + i] * real(i); if (t) for (let a = 0; a < r; a++) right[a * G + k] += t * B[i * r + a]; }
      const coef = solve(gram, right, r, G);                                 // coef[a*G + k]
      const phi = x2 => bent(units, slope, x2.map(v => Math.round(v * Q14))).map(v => v / Q14);
      const N = U + 1, AtA = new Float64Array(N * N), AtB = new Float64Array(N * r);
      spots.forEach((sp, k) => { const f = [1, ...phi(sp)]; for (let a = 0; a < N; a++) { for (let b = 0; b < N; b++) AtA[a * N + b] += f[a] * f[b]; for (let c = 0; c < r; c++) AtB[a * r + c] += f[a] * coef[c * G + k]; } });
      for (let a = 0; a < N; a++) AtA[a * N + a] += 1e-6 * G;
      const M = solve(AtA, AtB, N, r), most = k => { let mx = 1e-9; for (let a = 0; a < N; a++) mx = Math.max(mx, Math.abs(M[a * r + k])); return mx; };
      const mexp = Array.from({ length: r }, (_, k) => Chip.fbits(most(k), 16));
      /* The way along each direction, in whole numbers of 16 bits, and 0 at the middle of the knobs to the last digit: there the capture is the stored one. */
      const cexp = Math.min(Chip.fbits(Math.max(...coef.map(Math.abs)) * 1.1, 16), ...mexp.map(e => e - 1)), middle = bent(units, slope, x0.map(v => Math.round(v * Q14)));
      const far = mexp.map((e, k) => {
        const w = Array.from({ length: U }, (_, a) => whole(M[(a + 1) * r + k] * Math.pow(2, e))), at = w.reduce((t, v, a) => t + v * middle[a], 0);
        return { shift: Math.min(e + 14 - cexp, 60), bias: whole(-at / Q14), w };
      });
      if (far.some((q, k) => rows([q], middle)[0] !== 0)) bad("The levels of this parametric capture are too extreme for the pedal.");
      return { r, slope, cexp, knobs, eg, units, far, B };
    }
    /* The numbers as stored, in their own units, at a place of the knobs. */
    function reals(ext, x, v0) {
      const c = coefficients(ext, x.map(v => Math.round(v * Q14))).map(v => v / Math.pow(2, ext.cexp)), out = v0.slice();
      lay.groups.forEach((g, j) => { for (let i = g.from; i < g.from + g.count; i++) { let t = 0; for (let k = 0; k < ext.r; k++) t += c[k] * ext.B[i * ext.r + k]; out[i] += t * Math.pow(2, -ext.eg[j]); } });
      return out;
    }

    /* How near the stored form is to the model, at places between those that were looked at: the error of the sound, in dB below it. */
    function check(o) {
      const { ext, m, engineAt, e0, P, R, prog, sig } = o, T = 6346 + 16000, x = sig.subarray(0, T), spots = [];
      for (let k = 0; k < 8; k++) spots.push([...Array(P).keys()].map(() => 2 * R.u() - 1));
      for (const v of [-1, 1]) spots.push(Array(P).fill(v));
      const db = spots.map((s, j) => {
        const tone = new Array(CONTROLS).fill(0);
        ext.knobs.forEach((k, i) => { const e = s[i] * Q14, v = e < k.mid ? (e - k.mid) / (k.mid - k.lo || 1) : (e - k.mid) / (k.hi - k.mid || 1); tone[k.control] = Math.round(v * 120); });
        const at = ext.knobs.map(k => xOf(k, tone[k.control]) / Q14), y = forward(engineAt(at), x, false).y, z = forward(played(ext, m, e0, tone), x, false).y;
        let ma = 0, mb = 0; for (let t = 6346; t < T; t++) { ma += (y[t] - z[t]) / (T - 6346); mb += y[t] / (T - 6346); }
        let a = 0, b = 0; for (let t = 6346; t < T; t++) { a += (y[t] - z[t] - ma) ** 2; b += (y[t] - mb) ** 2; }
        prog(.76 + .22 * (j + 1) / spots.length, "Checking the knobs");
        return 10 * Math.log10((a + 1e-15) / (b + 1e-15));
      }).sort((a, b) => a - b);
      return { median: db[db.length >> 1], worst: db[db.length - 1] };
    }
    /* The engine as the pedal has it for these controls: the words of the capture, changed. */
    function played(ext, m, e0, tone) {
      const dv = change(ext, tone), e = { ...e0, headScale: 1, layers: [] }, back = (a, f) => Float64Array.from(a, v => Number(v) / Math.pow(2, f));
      let prev = m.Fx3_0;
      m.layers.forEach(l => { e.layers.push({ K: l.K, dil: l.dil, slope: l.lmul / (1 << 24), convW: back(l.cW, l.cF), convB: back(l.cB, l.cF + prev), mixW: back(l.mW, l.mF), l1W: back(l.lW, l.lF), l1B: back(l.lB, l.lF + l.Fz) }); prev = l.Fx3; });
      e.rech = back(m.rech_W, m.rech_F); e.hW = back(m.hW, m.hF); e.hB = Number(m.hB) / Math.pow(2, m.hF + m.Fh);
      for (const g of lay.groups) {
        const l = e.layers[g.layer], ml = m.layers[g.layer];
        for (let i = 0; i < g.count; i++) {
          const d = dv[g.from + i];
          if (g.kind === CB) l.convB[i] += d / Math.pow(2, ml.Fz);
          else if (g.kind === MIX) l.mixW[i] += d / Math.pow(2, ml.mF);
          else if (g.kind === L1) l.l1W[i] += d / Math.pow(2, ml.lF);
          else if (g.kind === RECH) e.rech[i] += d / Math.pow(2, m.rech_F);
          else if (g.kind === HEAD) e.hW[(i % C) * TAPS + Math.floor(i / C)] += d / Math.pow(2, m.hF);
          else e.hB += d / Math.pow(2, m.Fout);
        }
      }
      return e;
    }

    return { handles, convert, unpack, change, model, push, forward, assign, NamError: Chip.NamError };
  }

  /* In a worker, so that the page goes on; without one, here. */
  const SELF = (typeof document !== "undefined" && document.currentScript && document.currentScript.src) || "product-parametric.js";
  if (typeof module !== "undefined" && module.exports) { module.exports = make; return; }
  if (typeof WorkerGlobalScope !== "undefined" && root instanceof WorkerGlobalScope) {
    root.importScripts("nam2chip.js");
    const api = make(root.Nam2Chip);
    root.onmessage = ev => {
      try { const r = api.convert(ev.data.text, { name: ev.data.name, onProgress: (f, s) => root.postMessage({ t: "p", f, s }) }); root.postMessage({ t: "ok", r }, [r.blob.buffer]); }
      catch (err) { root.postMessage({ t: "err", msg: err.message, user: err instanceof root.Nam2Chip.NamError }); }
    };
    return;
  }
  const api = make(root.Nam2Chip);
  api.convertAsync = (text, opts) => new Promise((resolve, reject) => {
    const o = opts || {}, direct = () => setTimeout(() => { try { resolve(api.convert(text, o)); } catch (err) { if (err instanceof api.NamError) err.user = true; reject(err); } }, 30);
    let w = null;
    try { w = new Worker(SELF); } catch (err) { direct(); return; }
    w.onmessage = ev => {
      const m = ev.data;
      if (m.t === "p") { if (o.onProgress) o.onProgress(m.f, m.s); }
      else if (m.t === "ok") { w.terminate(); resolve(m.r); }
      else { w.terminate(); const er = new Error(m.msg); er.user = m.user; reject(er); }
    };
    w.onerror = () => { w.terminate(); direct(); };
    w.postMessage({ text, name: o.name });
  });
  root.HyperRigParametric = api;
})(typeof self !== "undefined" ? self : globalThis);
