"""The installer's core (app/installer): its own tests in node, and that its numbers are the loader's."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'app/installer'


@pytest.mark.skipif(not shutil.which('node'), reason='no node')
def test_wire_formats_and_flash_rules():
    done = subprocess.run(['node', 'app/installer/test_installer.js'], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and 'tests passed' in done.stdout, done.stdout + done.stderr


def test_numbers_are_the_loaders():
    header = (ROOT / 'firmware/mini_stage/engine.h').read_text(encoding='utf-8')
    flash, wire = ((CORE / n).read_text(encoding='utf-8') for n in ('flash.js', 'wire.js'))

    def number(text, name):
        return int(re.search(rf'\b{name} = (0x[0-9a-f]+|\d+)', text).group(1), 0)

    def define(name):
        return int(re.search(rf'#define {name} (?:UINT32_C\()?(0x[0-9a-f]+|\d+)', header).group(1), 0)
    for name in ('CAPACITY', 'SECTOR', 'APP', 'APP_END', 'USER', 'USER_END', 'JEDEC', 'LOADER_AT', 'LOADER_MAX', 'LOADER_CRC', 'RECORD_MARK'):
        assert number(flash, name) == define('HRS_' + name), name
    ops = dict(re.findall(r'HRS_([A-Z]+) = (0x[0-9a-f]+)', header))
    mine = dict(re.findall(r'([A-Z]+): (0x[0-9a-f]+)', re.search(r'const OPS = \{(.*?)\}', wire).group(1)))
    assert {k: int(v, 16) for k, v in mine.items()} == {k: int(v, 16) for k, v in ops.items() if k != 'REPLY'}
    errors = re.search(r'enum \{ HRS_OK, (.*?)\};', header, re.S).group(1)
    names = [n for n in re.findall(r'HRS_E_[A-Z_]+', re.sub(r'HRS_LAST_NOTE = HRS_E_[A-Z_]+,', '', errors))]
    status = re.findall(r'"([^"]*)"', re.search(r'const STATUS = \[(.*?)\];', wire).group(1))
    assert len(status) == len(names) + 1 and status[names.index('HRS_E_NO_RETURN') + 1] == 'no way back' and names.index('HRS_E_NO_RETURN') + 1 == 8


def test_no_stock_code_and_no_outside_address():
    for path in [*CORE.glob('*.js'), *CORE.glob('page/*.js'), *CORE.glob('page/*.html')]:
        text = path.read_text(encoding='utf-8')
        # the check of the built program speaks with its own window, and tries what must be refused
        assert path.name == 'check_program.js' or 'https://' not in text and 'http://' not in text, path.name
        assert '\r' not in text and text.endswith('\n'), path.name


def test_every_trouble_that_can_be_raised_has_its_words():
    flow, views = ((CORE / n).read_text(encoding='utf-8') for n in ('flow.js', 'views.js'))
    known = set(re.findall(r'^    ([a-z]+): \["', views, re.M))
    raised = set(re.findall(r'new Trouble\("([a-z]+)"', flow)) | set(re.findall(r'(?:[a-z]+|\d): "([a-z]+)"', re.search(r'const KINDS = \{(.*?)\}', flow).group(1)))
    assert raised <= known, raised - known
