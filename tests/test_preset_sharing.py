"""Trying without saving and presets from others: the strict reading of a file, what is refused while a sound is tried, the cab IR that is heard at once."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tools import build_mini_dev_editor as editor

ROOT = Path(__file__).resolve().parents[1]
TRY = (ROOT / 'app/mini/product-try.js').read_text(encoding='utf-8')
needs_node = pytest.mark.skipif(not shutil.which('node'), reason='no node')


@needs_node
def test_a_preset_file_is_read_strictly():
    done = subprocess.run(['node', 'app/mini/test_presetfile.js'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0 and 'all tests passed' in done.stdout, done.stderr


@needs_node
def test_the_scripts_are_whole():
    for name in editor.PRODUCT_FILES:
        if name.endswith('.js'):
            done = subprocess.run(['node', '--check', 'app/mini/' + name], cwd=ROOT, capture_output=True, text=True)
            assert done.returncode == 0, done.stderr


@needs_node
def test_what_writes_to_the_pedal_is_refused_while_a_sound_is_tried():
    stores = re.search(r'const STORES = (/.+?/), send', TRY).group(1)
    writes = ['PSAVE 0 x', 'PSAVE 31 x', 'SNAPSAVE 0', 'SNAPDEL 7', 'SNAPNAME 0 x', 'SNAPNAME 3', 'PNAME 0 x', 'PNAME 31 x', 'PDEL 12', 'PCOLOR ff0000', 'PCOLOR none', 'CSAVE 14 x', 'CDEL 0', 'CTRIM 3 0', 'CTRIM 14 -1.5', 'ISAVE 0 x', 'IDEL 7']
    reads = ['PLIST', 'PLOAD 0', 'PNEW', 'SNAP 0', 'SNAPS', 'SNAPNAME', 'PNAME', 'PCOLOR', 'CLIST', 'ILIST', 'CLOAD 0', 'ILOAD 0', 'CREAD 0', 'IREAD 0', 'CTRIM live 0 65', 'GAIN 0 0', 'FXP 0 0 1', 'FXA Q 99 gate', 'LDBEGIN 4', 'IREND 00000000', 'GSAVE']
    out = subprocess.run(['node', '-e', f'const r = {stores}; console.log(JSON.stringify(JSON.parse(process.argv[1]).map(c => r.test(c))))', json.dumps(writes + reads)], capture_output=True, text=True)
    assert json.loads(out.stdout) == [True] * len(writes) + [False] * len(reads), out.stdout + out.stderr


def test_a_try_sends_nothing_that_is_kept():
    """In the code of the try the words that write to the flash are sent by Keep and by Save it first, and nowhere else."""
    body = lambda name: re.search(rf'\n  async function {name}\(.*?\n  }}\n', TRY, re.S).group(0)
    keeping = ''.join(body(n) for n in ('saveFirst', 'keepPreset', 'beforeSave', 'keepFile'))
    rest = TRY.replace('\n', '\n')
    for name in ('saveFirst', 'keepPreset', 'beforeSave', 'keepFile'):
        rest = rest.replace(body(name), '')
    sent = re.findall(r'(?:Pedal\.cmd|line|pioSendLive|careful|send)\([^;]*?[`"](PSAVE|SNAPSAVE|CSAVE|ISAVE|PDEL|CDEL|IDEL|PNAME|GSAVE|SNAPNAME)', rest)
    assert not sent, sent
    assert 'CSAVE' in keeping and 'ISAVE' in keeping


def test_the_names_of_a_file_are_plain_before_they_are_in_a_command():
    for command in re.findall(r'`(?:\$\{word\}|CSAVE|ISAVE|PSAVE|SNAPNAME) [^`]*`', TRY):
        for value in re.findall(r'\$\{([^}]*)\}', command):
            assert value in ('word', 'slot', 'pick.slot', 'pick.name') or 'pioAscii(' in value, command
    assert re.search(r'name: pioAscii\(name\.value, 23\)', TRY), 'the name that is typed'


def test_the_uploaded_cab_is_heard_through_the_applications_own_steps():
    source = (ROOT / 'firmware/ultrarig/flash/020112f8_console_dispatch.s').read_text(encoding='ascii')
    assert source.count('    call ir_installation_attach\n.if MINI_PRODUCT\n    call hyperrig_ir_heard  ; @call.xl\n.endif\n') == 1
    code = (ROOT / 'firmware/ultrarig/mini/product/irlive.c').read_text(encoding='ascii')
    for name in ('audio_pause_pause_audio', 'audio_pause_resume_audio', 'preset_application_chain_read', 'preset_application_effect_type', 'ir_effect_lifecycle_owns', 'ir_effect_lifecycle_refresh'):
        assert code.count(name) >= 2, name
