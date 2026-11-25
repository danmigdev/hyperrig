/* The same volume for every preset and scene (docs/MINI_LOUDNESS.md): the numbers. The pedal plays strokes of a guitar into its own input and
 * measures what comes out (firmware/ultrarig/mini/product/loudness.c); this part makes the strokes and works out the gains. It sends nothing
 * and shows nothing: that is product-loudness-ui.js. */
(function (root) {
  "use strict";
  const RATE = 48077, LOW = RATE / 4;                           // the pedal's rate, and that of the strokes
  const SLICE = 512, WINDOW = 0.4 * RATE / SLICE;               // 400 ms, in slices
  const STROKE = 5632, BEFORE = 16, AFTER = 4;                  // codes; slices of silence before a run, and after it
  const PLAYED = STROKE / 128;                                  // slices of a play
  const FULL = 2 ** 26, LOWEST = -30, HIGHEST = 12;             // full scale at the end of the chain; output gains in dB
  const LARGEST = 30000, LAST = 87, SIZES = [16, 17, 19, 21, 23, 25, 27, 29], MOVES = [-1, -1, -1, -1, 2, 4, 6, 8];

  /* The codes of a stroke: four bits a sample, as in the firmware. */
  function coder() {
    let guess = 0, step = 0;
    const size = () => SIZES[step & 7] << (step >> 3);
    const sample = code => {
      const d = size() * (2 * (code & 7) + 1) >> 3;
      guess = Math.max(-LARGEST, Math.min(LARGEST, guess + (code & 8 ? -d : d)));
      step = Math.max(0, Math.min(LAST, step + MOVES[code & 7]));
      return guess;
    };
    const code = value => {
      const d = value - guess, c = (d < 0 ? 8 : 0) | Math.min(7, Math.floor(Math.abs(d) * 4 / size()));
      sample(c);
      return c;
    };
    return { sample, code };
  }
  const decode = (codes, c = coder()) => Float32Array.from(codes, v => c.sample(v) / 32768);
  function encode(samples) {
    const c = coder();
    return Uint8Array.from(samples, v => c.code(Math.max(-32768, Math.min(32767, Math.round(v * 32768)))));
  }
  const hexOf = codes => Array.from(codes, v => v.toString(16)).join("");
  const codesOf = text => Uint8Array.from(text, c => parseInt(c, 16));
  const bytesOf = text => text.replace(/(.)(.)/g, "$2$1");       // two codes a byte, the first in its low half

  /* BS.1770 gives its two filters for 48 kHz: the same at another rate, by way of the bilinear transform. */
  const GIVEN = [[[1.53512485958697, -2.69169618940638, 1.19839281085285], [1, -1.69065929318241, 0.73248077421585]], [[1, -2, 1], [1, -1.99004745483398, 0.99007225036621]]];
  function atRate([b, a], rate) {
    const k = rate / 48000, plus = [1 + k, 1 - k], minus = [1 - k, 1 + k];
    const times = (p, q) => [p[0] * q[0], p[0] * q[1] + p[1] * q[0], p[1] * q[1]], terms = [times(plus, plus), times(plus, minus), times(minus, minus)];
    const put = c => [0, 1, 2].map(i => c[0] * terms[0][i] + c[1] * terms[1][i] + c[2] * terms[2][i]);
    const B = put(b), A = put(a);
    return [B.map(v => v / A[0]), A.map(v => v / A[0])];
  }
  function weighted(x, rate) {
    let out = x;
    for (const [b, a] of GIVEN.map(f => atRate(f, rate))) {
      const y = new Float64Array(out.length);
      for (let i = 0, x1 = 0, x2 = 0, y1 = 0, y2 = 0; i < out.length; i++) {
        const v = out[i], w = b[0] * v + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2;
        x2 = x1; x1 = v; y2 = y1; y1 = w; y[i] = w;
      }
      out = y;
    }
    return out;
  }
  const lufs = mean => -0.691 + 10 * Math.log10(mean + 1e-20);

  /* The loudest 400 ms that begin in the slices first to last: whole slices, and a part of the one before or after. */
  function loudest(energies, first, last) {
    const whole = Math.floor(WINDOW), part = WINDOW - whole;
    let best = -Infinity;
    for (let i = first; i <= last; i++) {
      let sum = 0;
      for (let k = 0; k < whole; k++) sum += energies[i + k];
      sum += part * Math.max(i ? energies[i - 1] : 0, i + whole < energies.length ? energies[i + whole] : 0);
      best = Math.max(best, lufs(sum / WINDOW));
    }
    return best;
  }
  /* A run of so many plays of a stroke: the loudness of the last one, how far it is from the one before, and what was still heard before the first. */
  function result(energies, plays) {
    const of = n => { const from = BEFORE + n * PLAYED; return loudest(energies, from - 1, Math.min(from + PLAYED - Math.floor(WINDOW) + AFTER, energies.length - Math.floor(WINDOW) - 1)); };
    const level = of(plays - 1), tail = energies.slice(BEFORE - 4, BEFORE).reduce((a, b) => a + b, 0) / 4;
    return { level, apart: Math.abs(level - of(plays - 2)), before: lufs(tail) };
  }
  const slices = plays => BEFORE + plays * PLAYED + AFTER;
  const mean = list => list.length ? list.reduce((a, b) => a + b, 0) / list.length : NaN;
  const median = list => { const v = list.slice().sort((a, b) => a - b), n = v.length; return n ? n % 2 ? v[(n - 1) / 2] : (v[n / 2 - 1] + v[n / 2]) / 2 : NaN; };

  /* The strokes of a recording, samples of full scale 1 at LOW: where each begins, its loudest 400 ms, and the time to the next. */
  function strokes(x) {
    const H = Math.round(0.005 * LOW), n = Math.floor(x.length / H), e = new Float64Array(n);
    for (let f = 0, last = 0; f < n; f++) {
      let sum = 0;
      for (let i = f * H; i < (f + 1) * H; i++) { const d = x[i] - 0.97 * last; last = x[i]; sum += d * d; }
      e[f] = 10 * Math.log10(sum / H + 1e-12);
    }
    const top = e.reduce((a, b) => Math.max(a, b), -Infinity), at = [];
    for (let f = 8, prev = -1e9; f < n - 6; f++) {
      let before = 0, now = -Infinity, soon = -Infinity;
      for (let k = f - 8; k < f - 1; k++) before += e[k] / 7;
      for (let k = f; k < f + 3; k++) now = Math.max(now, e[k]);
      for (let k = f; k < f + 6; k++) soon = Math.max(soon, e[k]);
      if (now - before > 8 && soon > top - 30 && soon > -75 && (f - prev) * H > 0.25 * LOW) { at.push(f * H); prev = f; }
    }
    const w = weighted(x, LOW), sums = new Float64Array(x.length + 1), N = Math.round(0.4 * LOW);
    for (let i = 0; i < w.length; i++) sums[i + 1] = sums[i] + w[i] * w[i];
    return at.filter(i => i + STROKE <= x.length).map((i, k) => {
      const next = at[k + 1] === undefined ? x.length : at[k + 1];
      let level = -Infinity;
      for (let a = i; a <= Math.max(i, Math.min(next - N, i + N / 2)) && a + N <= x.length; a += H) level = Math.max(level, lufs((sums[a + N] - sums[a]) / N));
      let peak = 0;
      for (let a = i; a < Math.min(next, i + N); a++) peak = Math.max(peak, Math.abs(x[a]));
      return { at: i, level, gap: (next - i) / LOW, peak };
    });
  }
  /* Three of them, in the middle of how they are played, of those that are let ring if there are enough. The mean of what is measured with
   * them is nearer to the median over all strokes than the median of the three (docs/MINI_LOUDNESS.md). */
  function choose(list) {
    const ringing = list.filter(s => s.gap >= 0.36), from = ringing.length >= 3 ? ringing : list, sorted = from.slice().sort((a, b) => a.level - b.level), out = [];
    for (const q of [0.5, 0.4, 0.6]) {
      const rest = sorted.filter(s => !out.includes(s));
      if (!rest.length) break;
      const want = sorted[Math.round(q * (sorted.length - 1))].level;
      out.push(rest.reduce((a, b) => Math.abs(b.level - want) < Math.abs(a.level - want) ? b : a));
    }
    return out;
  }
  /* What the way through the pedal takes from the top, given before: a of 0.02 for the play alone, 0.03 with the recording. */
  function brighter(x, a) {
    return Float32Array.from(x, (v, i) => (1 + 2 * a) * v - a * ((i ? x[i - 1] : 0) + (i + 1 < x.length ? x[i + 1] : 0)));
  }
  function cut(x, at) {
    const from = Math.max(0, at - Math.round(0.01 * LOW)), out = x.slice(from, from + STROKE), up = Math.round(0.004 * LOW), down = Math.round(0.03 * LOW);
    for (let i = 0; i < up; i++) out[i] *= i / up;
    for (let i = 0; i < down; i++) out[out.length - 1 - i] *= i / down;
    return encode(brighter(out, 0.03));
  }
  /* Strokes that nobody played, for who does not want to: two chords and a note of partials that fall, the higher the faster, and the pick. How
   * they are was fitted to a guitar recorded directly (docs/MINI_LOUDNESS.md); the level is that of the pickups, soft, medium or hot. */
  const BUILT = { tilt: 1.2, fall: 25, more: 3, at: 0.17, pick: 0.25, notes: [[98, 123.5, 196, 293.7], [110, 164.8, 220, 261.6], [220]] };
  const LEVELS = { soft: -28, medium: -23, hot: -18 };
  function built(level = LEVELS.medium, o = BUILT) {
    let seed = 20251125;
    const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
    return o.notes.map(chord => {
      const x = new Float32Array(STROKE), start = Math.round(0.01 * LOW);
      for (const hertz of chord) {
        let top = 0;
        const y = new Float32Array(STROKE);
        for (let k = 1; k < 64; k++) {
          const f = hertz * k * Math.sqrt(1 + 4e-5 * k * k), a = Math.abs(Math.sin(Math.PI * k * o.at)) / k ** o.tilt, phase = 2 * Math.PI * random(), fall = (o.fall + o.more * k) * Math.LN10 / 20 / LOW;
          if (f > 5000) break;
          for (let i = 0; i < STROKE - start; i++) y[start + i] += a * Math.exp(-fall * i) * Math.sin(2 * Math.PI * f * i / LOW + phase);
        }
        for (const v of y) top = Math.max(top, Math.abs(v));
        for (let i = 0; i < STROKE; i++) x[i] += y[i] / top;
      }
      const up = Math.round(0.003 * LOW);
      for (let i = 0; i < up; i++) x[start + i] *= i / up;
      let last = 0;
      for (let i = 0; i < 0.03 * LOW; i++) { const v = o.pick * (random() * 2 - 1) * Math.exp(-i / (0.004 * LOW)); x[start + i] += v - last; last = v; }
      const down = Math.round(0.03 * LOW);
      for (let i = 0; i < down; i++) x[STROKE - 1 - i] *= i / down;
      const w = weighted(x, LOW), N = Math.round(0.4 * LOW);
      let sum = 0;
      for (let i = start; i < start + N; i++) sum += w[i] * w[i];
      const gain = 10 ** ((level - lufs(sum / N)) / 20);
      return encode(brighter(x, 0.02).map(v => v * gain));
    });
  }

  /* One sound that was measured: {levels, peak, out}. The gain that brings it to a volume, and the most it may have before the limiter holds it. */
  const decibels = peak => 20 * Math.log10(Math.max(peak, 1) / FULL);
  const gainFor = (item, volume) => Math.max(LOWEST, Math.min(HIGHEST, Math.round(volume - item.level)));
  const roomOf = (item, limit) => Math.floor(limit - decibels(item.peak) + 1e-6);
  /* The volume to begin with: what they have now, in the middle; not more than what all can reach before the limiter, nor than the gains allow. */
  function start(items, limit) {
    const now = median(items.map(i => i.level + i.out));
    return Math.floor(1e-6 + Math.min(now, ...items.map(i => i.level + Math.min(HIGHEST, roomOf(i, limit)))));
  }

  root.HyperRigLoudness = Object.freeze({ RATE, LOW, STROKE, BEFORE, AFTER, PLAYED, FULL, coder, decode, encode, hexOf, codesOf, bytesOf, weighted, lufs, loudest, result, slices, mean, median, strokes, choose, cut, brighter, built, LEVELS,
    decibels, gainFor, roomOf, start });
})(globalThis);
