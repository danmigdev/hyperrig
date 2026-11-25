"""NAM captures that keep knobs: the page's conversion (app/mini/product-parametric.js) against a second form of its arithmetic
(tools/check_mini_parametric.py), and the fold against the network it was made from. No device, no browser."""
import json
import math
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_parametric as form  # noqa: E402

CHIP = ROOT / 'build/hyperrig-mini-installer-v4-fast-01/editor/web/nam2chip.js'
KERNELS, DILATIONS = [6] * 14 + [15, 15] + [6] * 7, [1, 3, 7, 17, 41, 101, 239] * 2 + [1, 13] + [1, 3, 7, 17, 41, 101, 239]
HEAD = f'''
const assert = require("node:assert"), fs = require("fs"), Chip = require({json.dumps(CHIP.as_posix())});
const api = require({json.dumps((ROOT / 'app/mini/product-parametric.js').as_posix())})(Chip);
const input = JSON.parse(fs.readFileSync(0, "utf8"));
'''
LAYER = {'channels': 3, 'kernel_sizes': KERNELS, 'dilations': DILATIONS, 'activation': [{'type': 'LeakyReLU', 'negative_slope': 0.01}] * 23, 'bottleneck': 3,
         'head': {'out_channels': 1, 'kernel_size': 16, 'bias': True}, 'head1x1': {'active': False}, 'layer1x1': {'active': True, 'groups': 1},
         'groups_input': 1, 'groups_input_mixin': 1, 'gating_mode': ['none'] * 23, 'secondary_activation': [None] * 23}


def node(script, payload):
    done = subprocess.run(['node', '-e', HEAD + script], input=json.dumps(payload), capture_output=True, text=True, timeout=300)
    if done.returncode:
        raise AssertionError(done.stderr[-2000:])
    return json.loads(done.stdout) if done.stdout.strip() else None


def knob(name, lo=0.0, hi=10.0, default=5.0, **more):
    return {'name': name, 'min': lo, 'max': hi, 'default': default, 'type': 'continuous', 'enum_names': None, **more}


def concat(params, seed=1):
    rng = random.Random(seed)
    inputs = 1 + sum(len(p['enum_names']) if p['type'] == 'switch' else 1 for p in params)
    g = lambda n, s: [rng.gauss(0, s) for _ in range(n)]
    w = [v for _ in range(3) for v in g(1, .8) + g(inputs - 1, .2)]
    for k in KERNELS:
        w += g(9 * k, .35 / math.sqrt(3 * k)) + g(3, .1)
        w += [v for _ in range(3) for v in g(1, .3) + g(inputs - 1, .12)]
        w += g(9, .25) + g(3, .05)
    w += g(48, .3) + [.02, .05]
    return {'version': '1.0.0', 'metadata': {'name': 'C'}, 'architecture': 'ConcatWaveNet', 'sample_rate': 48000,
            'config': {'layers': [dict(LAYER, input_size=inputs, condition_size=inputs)], 'head': None, 'head_scale': .05, 'params': params}, 'weights': w}


def hyper(params, seed=2, hidden=(16,), activation='LeakyReLU', convs=False, channels=3):
    rng = random.Random(seed)
    g = lambda n, s: [rng.gauss(0, s) for _ in range(n)]
    ins = sum(len(p['enum_names']) if p['type'] == 'switch' else 1 for p in params)
    base, targets, P = g(3, .8), [{'name': 'rech', 'mode': 'full', 'numel': 3, 'export_offset': 0}], 0
    for i, k in enumerate(KERNELS):
        o = len(base)
        base += g(9 * k, .35 / math.sqrt(3 * k)) + g(3, .1) + g(3, .3) + g(9, .25) + g(3, .05)
        if convs and i == 4:
            targets.append({'name': 'conv', 'mode': 'full', 'numel': 9 * k, 'export_offset': o})
        targets += [{'name': f'cb{i}', 'mode': 'full', 'numel': 3, 'export_offset': o + 9 * k}, {'name': f'mix{i}', 'mode': 'full', 'numel': 3, 'export_offset': o + 9 * k + 3},
                    {'name': f'l1{i}', 'mode': 'low_rank', 'numel': 9, 'export_offset': o + 9 * k + 6, 'rank': 2, 'out_features': 3, 'rest_features': 3},
                    {'name': f'lb{i}', 'mode': 'full', 'numel': 3, 'export_offset': o + 9 * k + 15}]
    o = len(base)
    base += g(48, .3) + [.02, .05]
    targets += [{'name': 'head', 'mode': 'full', 'numel': 48, 'export_offset': o}, {'name': 'hb', 'mode': 'full', 'numel': 1, 'export_offset': o + 48}]
    outs, state, last = sum(12 if t['mode'] == 'low_rank' else t['numel'] for t in targets), [], ins
    for n in hidden:
        state += g(n * last, .5) + g(n, .4)
        last = n
    state += g(outs * last, .04 / math.sqrt(last / 16)) + g(outs, .02) + g(outs, .02)
    sub = {'layers': [dict(LAYER, input_size=1, condition_size=1, channels=channels)], 'head': None, 'head_scale': .05, 'params': params,
           'hypernet': {'hidden_sizes': list(hidden), 'activation': activation, 'mode': 'low_rank', 'rank': 2, 'delta_map': targets}}
    w = base + state
    return {'version': '1.0.0', 'metadata': {'name': 'H'}, 'architecture': 'HyperA2', 'sample_rate': 48000,
            'config': {'params': params, 'size': 'full', 'submodels': [{'name': 'lite', 'config': sub, 'weight_offset': 7, 'weight_count': len(w), 'base_weight_count': len(base)}]},
            'weights': [9.0] * 7 + w}


@unittest.skipUnless(CHIP.exists(), 'the pinned editor is not here')
class Parametric(unittest.TestCase):
    TWO = [knob('Gain'), knob('Tone')]

    def converted(self, model):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'x.a2l'
            got = node('const r = api.convert(JSON.stringify(input.model), { name: "Test" }); fs.writeFileSync(input.out, r.blob);'
                       'console.log(JSON.stringify({ knobs: r.knobs, fixed: r.fixed, fit: r.fit, directions: r.stats.directions, bytes: r.blob.length }));',
                       {'model': model, 'out': str(out)})
            return out.read_bytes(), got

    def same_arithmetic(self, data, tones):
        theirs = node('const ext = api.unpack(Buffer.from(input.data, "hex")); console.log(JSON.stringify(input.tones.map(t => [...api.change(ext, t)])));',
                      {'data': data.hex(), 'tones': tones})
        ours = [form.change(form.unpack(data), t) for t in tones]
        self.assertEqual(theirs, ours)
        return ours

    def test_a_network_with_the_knobs_beside_the_audio(self):
        """Only the biases move, and in proportion to the knobs."""
        data, got = self.converted(concat([knob('Gain'), knob('Bass', -1.0, 1.0, 0.0), knob('Master'), knob('Bright', type='switch', min=0, max=1, default=1, enum_names=['Off', 'On'])]))
        self.assertEqual([k['name'] for k in got['knobs']], ['Gain', 'Bass', 'Master'])
        self.assertEqual([k['control'] for k in got['knobs']], [5, 1, 4])
        self.assertEqual(got['fixed'], [{'name': 'Bright', 'at': 'On'}])
        self.assertLess(got['fit']['worst'], -30)
        e = form.unpack(data)
        self.assertEqual((e['r'], e['slope'], e['plain']), (3, 1024, 4892))
        self.assertLessEqual(len(data), 8152)
        half, whole, _ = [[v for kind, _, first, count in form.GROUPS for v in d[first:first + count] if kind == form.CB] for d in self.same_arithmetic(data, [[0, 60, 0, 0, 0, 0], [0, 120, 0, 0, 0, 0], [0, -35, 0, 0, 120, -85]])]
        self.assertLess(max(abs(2 * a - b) for a, b in zip(half, whole)), max(map(abs, whole)) * .01)

    def test_a_network_that_makes_its_weights_of_the_knobs(self):
        data, got = self.converted(hyper(self.TWO))
        self.assertEqual([(k['name'], k['control']) for k in got['knobs']], [('Gain', 5), ('Tone', 3)])
        e = form.unpack(data)
        self.assertEqual((len(e['units']), e['slope'], e['plain']), (16, 10, 4892))
        self.assertLessEqual(len(data), 8152)
        self.assertLess(got['fit']['median'], -20)
        flat, _, _ = self.same_arithmetic(data, [[0] * 6, [0, 0, 0, 120, 0, -120], [0, 0, 0, -47, 0, 35]])
        self.assertFalse(any(flat))

    def test_another_hidden_layer(self):
        """Two hidden layers, or one of another kind, are followed by bends along the knobs."""
        data, got = self.converted(hyper([knob('Drive')], hidden=(8, 8), activation='Tanh'))
        self.assertEqual(got['knobs'][0]['control'], 5)
        self.assertLess(got['fit']['worst'], -15)
        self.same_arithmetic(data, [[0, 0, 0, 0, 0, 90], [0, 0, 0, 0, 0, -120]])

    def test_the_fold_is_the_network(self):
        """The knobs beside the audio, against the biases they become: the same output after the 6,346 samples a layer may look back."""
        worst = node('''
            const m = input.model, L = m.config.layers[0], n = 1 + 2, w = Float64Array.from(Float32Array.from(m.weights)), T = 6346 + 300;
            let o = 0, x = new Float64Array(T); const R = Chip.rng(3); for (let t = 0; t < T; t++) x[t] = R.g() * .3;
            const knobs = [-0.4, 0.9], u = [x, new Float64Array(T).fill(knobs[0]), new Float64Array(T).fill(knobs[1])], take = k => w.subarray(o, o += k);
            const at = (W, rows) => [0, 1, 2].map(c => { const y = new Float64Array(T); for (let t = 0; t < T; t++) for (let i = 0; i < n; i++) y[t] += W[c * n + i] * rows[i][t]; return y; });
            let r = at(take(3 * n), u), s = [0, 1, 2].map(() => new Float64Array(T));
            L.kernel_sizes.forEach((K, i) => {
              const W = take(9 * K), b = take(3), mix = at(take(3 * n), u), l1 = take(9), lb = take(3);
              const a = [0, 1, 2].map(c => { const y = mix[c].map(v => v + b[c]); for (let k = 0; k < K; k++) { const sh = (K - 1 - k) * L.dilations[i]; for (let j = 0; j < 3; j++) { const q = W[(c * 3 + j) * K + k]; for (let t = sh; t < T; t++) y[t] += q * r[j][t - sh]; } } return y.map(v => v >= 0 ? v : .01 * v); });
              s = s.map((q, c) => q.map((v, t) => v + a[c][t])); r = r.map((q, c) => q.map((v, t) => v + l1[c * 3] * a[0][t] + l1[c * 3 + 1] * a[1][t] + l1[c * 3 + 2] * a[2][t] + lb[c]));
            });
            const hw = take(48), hb = take(1)[0], scale = m.config.head_scale, y = new Float64Array(T).fill(hb);
            for (let c = 0; c < 3; c++) for (let k = 0; k < 16; k++) for (let t = 15 - k; t < T; t++) y[t] += hw[c * 16 + k] * s[c][t - 15 + k];
            const z = api.forward(api.push(api.model(m).at(knobs)), x, false).y;
            let worst = 0; for (let t = 6346; t < T; t++) worst = Math.max(worst, Math.abs(y[t] * scale - z[t]));
            console.log(JSON.stringify(worst));''', {'model': concat(self.TWO)})
        self.assertLess(worst, 1e-12)

    def test_which_control_moves_which_knob(self):
        got = node('console.log(JSON.stringify(input.map(names => api.assign(names.map(name => ({ name, kind: "knob" }))))));',
                   [['Gain', 'Bass', 'Middle', 'Treble', 'Presence', 'Master'], ['Volume', 'Tone'], ['Fuzz'], ['A', 'B'], ['Low', 'High', 'Pre-amp'], ['Level', 'Drive']])
        self.assertEqual(got, [[5, 1, 2, 3, 4, 0], [4, 3], [5], [5, 3], [1, 3, 5], [4, 5]])

    def test_what_cannot_be_played_is_refused_in_words(self):
        bad = {'channels': hyper(self.TWO, channels=8), 'convs': hyper(self.TWO, convs=True), 'activation': hyper(self.TWO, activation='Softmax'), 'rate': dict(hyper(self.TWO), sample_rate=44100),
               'weights': dict(hyper(self.TWO), weights=[0.0] * 50), 'knobs': dict(concat(self.TWO), config={'layers': []}), 'other': {'architecture': 'WaveNet', 'config': {}, 'weights': []}}
        got = node('const out = {}; for (const k in input) { try { api.convert(JSON.stringify(input[k]), {}); out[k] = null; } catch (e) { out[k] = [e instanceof api.NamError, e.message]; } } console.log(JSON.stringify(out));', bad)
        for name, seen in got.items():
            self.assertTrue(seen and seen[0], (name, seen))
        self.assertIn('8 channels', got['channels'][1])
        self.assertIn('convolutions', got['convs'][1])

    def test_only_these_captures_are_taken(self):
        got = node('console.log(JSON.stringify(input.map(d => api.handles(JSON.stringify(d)))));',
                   [{'architecture': 'WaveNet'}, {'architecture': 'SlimmableContainer', 'note': 'HyperA2'}, {'architecture': 'HyperA2'}, {'architecture': 'ConcatWaveNet'}, {'architecture': 'ConcatLSTM'}])
        self.assertEqual(got, [False, False, True, True, False])

    def test_the_panel_reads_what_the_pedal_says(self):
        script = (ROOT / 'app/mini/product-amp-knobs.js').read_text(encoding='utf-8') + '''
            hrKnobList = hrKnobParse(input);
            console.log(JSON.stringify([hrKnobList.length, hrKnobName(5), hrKnobName(1), [-120, 0, 60, 120].map(v => hrKnobText(5, v)), [-120, 0, 120].map(v => hrKnobText(3, v)), hrKnobText(1, 35), hrKnobNote()]));'''
        got = node('const DEMO = false, AEQ_NAMES = ["Volume", "Bass", "Mid", "Treble", "Presence", "Gain"], fmtVal = (v, u) => v + u, aeqTitle = () => "", clean = 0;\n' + script,
                   ['AMPK ' + struct.pack('<B11sffhhh', *k).hex() for k in ((5, b'Gain', 0, 10, -16384, 0, 16384), (3, b'My Tone', -12, 12, -16384, 3277, 16384), (0, b'x', 0, 1, 0, 0, 0))] + ['AMPK end'])
        self.assertEqual(got, [2, 'Gain', 'Bass', ['0.0', '5.0', '7.5', '10.0'], ['-12.0', '2.4', '12.0'], '35dB10', ' This capture has knobs of its own: Gain, My Tone.'])


if __name__ == '__main__':
    unittest.main()
