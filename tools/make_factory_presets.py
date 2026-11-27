"""HyperRig's three factory presets, Clean, Crunch and Lead, and the cab IR they carry: made here, from filters, so that they
are HyperRig's own and ship with it. No recording of anybody else is in them.

The cab is the response of a few second-order filters, the shape of a guitar speaker in a closed cabinet: a resonance near
100 Hz below which it falls, less of the low mids, a presence near 2.5 kHz, a dip of cone break-up near 4.2 kHz, and a steep
fall above 5.5 kHz (RBJ's cookbook filters at 48 kHz, applied to an impulse). 1,024 samples (21 ms) are kept, faded and put
into the pedal's form as the editor does it (prepIr in its page): normalized, 16 bits, and the gain in thousandths of a dB.

Usage, from the repository root:
    python -B tools/make_factory_presets.py            writes app/mini/factory/
    python -B tools/make_factory_presets.py --check    says whether the files there are the ones this makes
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'app/mini/factory'
RATE, LENGTH = 48000, 1024
STAMP = '2026-11-26T00:00:00Z'          # one time, so that the files are the same when they are made again
CAB_NAME = 'HyperRig Cab'

# (kind, hertz, Q, gain in dB): the speaker's shape
SHAPE = [('highpass', 85, 1.3, 0), ('peak', 110, 1.2, 2.5), ('peak', 400, 1.0, -3), ('peak', 1200, 1.0, 2),
         ('peak', 2500, 1.2, 5), ('peak', 4200, 3.0, -6), ('lowpass', 5500, 0.7, 0), ('lowpass', 5500, 1.0, 0)]


def biquad(kind, hz, q, db):
    w = 2 * math.pi * hz / RATE
    cw, sw = math.cos(w), math.sin(w)
    alpha, a = sw / (2 * q), 10 ** (db / 40)
    if kind == 'peak':
        b, c = [1 + alpha * a, -2 * cw, 1 - alpha * a], [1 + alpha / a, -2 * cw, 1 - alpha / a]
    elif kind == 'lowpass':
        b, c = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2], [1 + alpha, -2 * cw, 1 - alpha]
    else:
        b, c = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2], [1 + alpha, -2 * cw, 1 - alpha]
    return [v / c[0] for v in b], [1.0, c[1] / c[0], c[2] / c[0]]


def impulse():
    x = [1.0] + [0.0] * (LENGTH - 1)
    for kind, hz, q, db in SHAPE:
        (b0, b1, b2), (_, a1, a2) = biquad(kind, hz, q, db)
        y, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
        for v in x:
            w = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1, y2, y1 = x1, v, y1, w
            y.append(w)
        x = y
    return x


def pedal_form(x):
    """As the editor's prepIr: a fade over the last eighth (at most 256), energy 1, then 16 bits at full scale, and the gain."""
    x = list(x)
    fade = min(len(x) >> 3, 256)
    for i in range(fade):
        x[len(x) - fade + i] *= 0.5 * (1 + math.cos(math.pi * i / (fade - 1 or 1)))
    e = math.sqrt(sum(v * v for v in x))
    x = [v / e for v in x]
    peak = max(abs(v) for v in x)
    q = [int(math.floor(v / peak * 32767 + 0.5)) for v in x]
    while len(q) > 1 and q[-1] == 0:
        q.pop()
    gain = int(math.floor(20000 * math.log10(peak * 32768 / 32767) + 0.5))
    return struct.pack(f'<{len(q)}h', *q), gain


def wav(q_bytes):
    n = len(q_bytes)
    return (b'RIFF' + struct.pack('<I', 36 + n) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, 1, RATE, RATE * 2, 2, 16) +
            b'data' + struct.pack('<I', n) + q_bytes)


def attachment(data, gain):
    return {'kind': 'ir', 'format': 'tkgj', 'name': CAB_NAME, 'bytes': len(data), 'rate_khz': 48, 'gain_mdb': gain,
            'sha256': hashlib.sha256(data).hexdigest(), 'data': base64.b64encode(data).decode('ascii')}


def block(n, kind, **params):
    b = {'id': f'b{n}', 'type': kind, 'on': True, 'params': params}
    if kind == 'ir':
        b['ir'] = None                   # the preset's cab: cab_ir below
    return b


CAB = lambda low, high: ('ir', {'mezcla_pct': 100, 'nivel_db': 0, 'ir_slot': 0, 'largo_ms': 21, 'lowcut_hz': low, 'hicut_hz': high})
PRESETS = [
    ('HyperRig Clean', '#4aa3c7', ['clean', 'plate', 'compressor'],
     'A glassy clean for chords and arpeggios. A light compressor evens out the picking, the Clean Amp sits just below '
     'break-up, and a short plate adds space without washing it out. Turn the amp\'s gain up a little for an edge-of-break-up sound.',
     [('comp', {'umbral_db': -28, 'ratio_x10': 25, 'ataque_ms': 12, 'release_ms': 150, 'nivel_db': 3, 'mezcla_pct': 70}),
      ('amp_clean', {'ganancia_pct': 35, 'graves_pct': 55, 'medios_pct': 45, 'agudos_pct': 60, 'presencia_pct': 45, 'nivel_db': -6, 'os_n': 1}),
      CAB(70, 10000),
      ('plate', {'tamano_pct': 55, 'decay_pct': 45, 'amort_pct': 30, 'predelay_ms': 15, 'mezcla_pct': 22, 'nivel_db': 0, 'mod_pct': 30})]),
    ('HyperRig Crunch', '#d9a441', ['crunch', 'british', 'rock'],
     'A British amp just breaking up: chords stay clear, harder picking bites. A short hall reverb, kept small, adds a little air. Roll back '
     'your guitar\'s volume and it cleans up.',
     [('amp_brit', {'ganancia_pct': 55, 'graves_pct': 50, 'medios_pct': 65, 'agudos_pct': 55, 'presencia_pct': 50, 'nivel_db': -6, 'os_n': 1}),
      CAB(90, 8500),
      ('reverb2', {'tamano_pct': 35, 'decay_pct': 30, 'amort_pct': 45, 'predelay_ms': 10, 'mezcla_pct': 15, 'nivel_db': 0, 'mod_pct': 20})]),
    ('HyperRig Lead', '#c4452f', ['lead', 'high gain', 'solo'],
     'A singing high-gain lead. A gate keeps it quiet between phrases, a Tube Screamer tightens the low end into the Hi-Gain Amp, '
     'then a 420 ms delay and a light plate.',
     [('sgate', {'umbral_db': -56, 'rango_att': 60, 'release_ms': 200, 'hush_pct': 40}),
      ('ts9', {'drive_pct': 20, 'tono_pct': 55, 'nivel_db': -2, 'os_n': 1, 'limpio_pct': 0}),
      ('amp_hi', {'ganancia_pct': 65, 'graves_pct': 50, 'medios_pct': 55, 'agudos_pct': 55, 'presencia_pct': 50, 'nivel_db': -8, 'os_n': 3}),
      CAB(100, 7500),
      ('delay', {'tiempo_ms': 420, 'realim_pct': 30, 'mezcla_pct': 22, 'amort_pct': 40, 'sync': 0, 'lowcut_hz': 150, 'mono': 1}),
      ('plate', {'tamano_pct': 60, 'decay_pct': 50, 'amort_pct': 30, 'predelay_ms': 20, 'mezcla_pct': 18, 'nivel_db': 0, 'mod_pct': 40})]),
]
NOTE = ' Built-in blocks only, no capture; its cab is HyperRig\'s own IR, which comes with it.'


def preset(name, color, tags, description, blocks, cab):
    chain = [{'amp': True}] + [block(i + 1, kind, **params) for i, (kind, params) in enumerate(blocks)]
    ref = {'name': cab['name'], 'bytes': cab['bytes'], 'rate_khz': 48, 'sha256': cab['sha256'], 'attachment': 'cab'}
    sound = {'chain': chain, 'amp': {'present': False, 'on': True, 'capture': None}, 'cab_ir': ref, 'gain_db': {'in': 0, 'out': 0},
             'tempo_bpm_x10': 1200, 'color': color, 'scenes': [], 'active_scene': None}
    meta = {'name': name, 'description': description + NOTE, 'tags': tags, 'genre': '', 'author': 'HyperRig', 'created': STAMP,
            'modified': STAMP, 'id': ''}
    compat = {'source': {}, 'needs': {'effects': sorted({k for k, _ in blocks}), 'captures': [], 'irs': [ref]}}
    return {'meta': meta, 'compat': compat, 'sound': sound}


def document(kind, presets, cab):
    return {'format': 'hyperrig-preset', 'version': 1, 'min_reader': 1, 'kind': kind, 'exported': STAMP, 'app': 'HyperRig',
            'presets': presets, 'attachments': {'cab': cab}}


def made():
    data, gain = pedal_form(impulse())
    cab = attachment(data, gain)
    presets = [preset(name, color, tags, text, blocks, cab) for name, color, tags, text, blocks in PRESETS]
    files = {'HyperRig-Cab.wav': wav(data)}
    for p in presets:
        files[p['meta']['name'].replace(' ', '-') + '.hyperrig.json'] = (json.dumps(document('preset', [p], cab), indent=1) + '\n').encode()
    bank = [{**p, 'meta': {**p['meta'], 'slot': slot}} for p, slot in zip(presets, ('1A', '1B', '1C'))]
    files['HyperRig-Factory.hyperrig.json'] = (json.dumps(document('bank', bank, cab), indent=1) + '\n').encode()
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    files = made()
    if args.check:
        wrong = [n for n, raw in files.items() if not (OUT / n).is_file() or (OUT / n).read_bytes() != raw]
        print(json.dumps({'result': 'fail' if wrong else 'pass', 'differ': wrong}))
        return 1 if wrong else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for n, raw in files.items():
        (OUT / n).write_bytes(raw)
    print(json.dumps({'written': sorted(files), 'cab_samples': len(files['HyperRig-Cab.wav']) // 2 - 22}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
