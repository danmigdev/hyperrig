"""The presets to start with and HyperRig's cab (tools/make_factory_presets.py): the files in the tree are the ones it makes, the
editor's own reader keeps all of them, and the cab is what the editor makes of an IR."""
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import make_factory_presets as factory  # noqa: E402

READ = r'''
require(require("path").resolve(process.argv[1]));
const out = {};
for (const file of process.argv.slice(2)) {
  const r = HyperRigPresetFile.clean(require("fs").readFileSync(file, "utf8"));
  out[require("path").basename(file)] = r.ok ? r.presets.map(p => [p.meta.name, p.meta.slot || null, p.sound.chain.filter(b => !b.amp).map(b => [b.type, Object.keys(b.params).length]), !!p.sound.cab_ir]).concat([r.warn]) : r.err;
}
console.log(JSON.stringify(out));
'''


def test_the_files_are_the_ones_made():
    for name, raw in factory.made().items():
        assert (factory.OUT / name).read_bytes() == raw, name


def test_the_editor_reads_them_whole():
    files = sorted(str(p) for p in factory.OUT.glob('*.hyperrig.json'))
    done = subprocess.run(['node', '-e', READ, str(ROOT / 'app/mini/product-presetfile.js'), *files], capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0, done.stderr
    got = json.loads(done.stdout)
    bank = got['HyperRig-Factory.hyperrig.json']
    assert [p[:2] for p in bank[:3]] == [['HyperRig Clean', '1A'], ['HyperRig Crunch', '1B'], ['HyperRig Lead', '1C']] and bank[3] == []
    for (name, _, blocks, cab), (title, _, _, _, given) in zip(bank[:3], factory.PRESETS):
        assert name == title and cab
        assert blocks == [[kind, len(params)] for kind, params in given]
    for one in ('HyperRig-Clean', 'HyperRig-Crunch', 'HyperRig-Lead'):
        assert got[one + '.hyperrig.json'][0][1] is None and got[one + '.hyperrig.json'][1] == []


def test_the_cab_is_in_the_editors_form():
    doc = json.loads((factory.OUT / 'HyperRig-Factory.hyperrig.json').read_bytes())
    cab = doc['attachments']['cab']
    assert cab['format'] == 'tkgj' and cab['rate_khz'] == 48 and cab['bytes'] % 2 == 0 and cab['bytes'] // 2 <= 4076
    wav = (factory.OUT / 'HyperRig-Cab.wav').read_bytes()
    assert wav[:4] == b'RIFF' and wav[8:16] == b'WAVEfmt ' and struct.unpack('<IHHIIHH', wav[16:36])[1:4] == (1, 1, 48000)
    assert len(wav) - 44 == cab['bytes']
