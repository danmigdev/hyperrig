"""The HyperRig loader's files agree with each other; the engine's own tests run where gcc is (offline)."""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/mini_stage'


def define(name):
    text = (SOURCE / 'engine.h').read_text(encoding='utf-8')
    value = re.search(rf'#define {name} (?:UINT32_C\()?(0x[0-9a-f]+|\d+)', text).group(1)
    return int(value, 0)


def test_windows_are_the_application_and_the_user_area():
    assert (define('HRS_APP'), define('HRS_APP_END')) == (0x4000, 0x82000)
    assert (define('HRS_USER'), define('HRS_USER_END')) == (0xBF000, 0xFF000)
    assert define('HRS_JEDEC') == 0xEB6014 and define('HRS_CAPACITY') == 0x100000
    engine = (SOURCE / 'engine.c').read_text(encoding='utf-8')
    assert 'inside(a, n, HRS_APP, HRS_APP_END) || inside(a, n, HRS_USER, HRS_USER_END)' in engine
    # the flash driver asks the same rule
    assert 'int hyf_range(uint32_t a, uint32_t n) { return hrs_permits(a, n); }' in (SOURCE / 'stage.c').read_text(encoding='utf-8')
    assert 'return hrs_writable(a, n) || (s.retiring && a == s.retiring && n == HRS_PAGE); }' in engine


def test_an_application_is_where_the_bootloader_says():
    """The second word of the bootloader's context; its first is not zero without an application (tools/check_mini_boot.py)."""
    assert 'context && context[1] != 0' in (SOURCE / 'stage.c').read_text(encoding='utf-8')


def test_every_stored_loader_has_the_checksum_the_engine_looks_for():
    builder = (ROOT / 'tools/build_mini_stage.py').read_text(encoding='utf-8')
    assert define('HRS_LOADER_CRC') == 0x4852 and 'LOADER_CRC = 0x4852' in builder
    assert define('HRS_LOADER_AT') == 0x01C0A800 and define('HRS_LOADER_MAX') == 0x5B1C


def test_flash_driver_is_the_one_that_ran_on_the_pedal():
    """The loader uses firmware/mini_fast/nor.c as it is, with its eight commands."""
    nor = (ROOT / 'firmware/mini_fast/nor.c').read_text(encoding='utf-8')
    assert not (SOURCE / 'nor.c').exists()
    assert 'firmware/mini_fast/nor.c' in (ROOT / 'tools/build_mini_stage.py').read_text(encoding='utf-8')
    assert 'hyf_range' in nor


def test_stage_keeps_the_stored_record_and_clears_the_request():
    stage = (SOURCE / 'stage.c').read_text(encoding='utf-8')
    assert '0x01c7fd88u' in stage and '(uintptr_t)UPDATE_REQUEST = 0;' in stage
    for address in ('0xbcf00', '0xbc000', '0xb7000'):
        assert address not in stage.lower() and address not in (SOURCE / 'engine.c').read_text(encoding='utf-8').lower()


def test_linker_script_is_the_place_of_the_stock_loader():
    script = (SOURCE / 'stage.ld').read_text(encoding='utf-8')
    assert 'ORIGIN = 0x1c0a800' in script and '0x5b1c' in script


def test_the_usb_identity_is_not_the_private_one_and_not_the_running_pedals():
    """No device that is given to others may have 1209:0002; another product than the running pedal's keeps a computer from mixing their drivers."""
    source = (SOURCE / 'usb_midi.c').read_text(encoding='utf-8')
    row = re.search(r'device_descriptor\[18\] = \{\s*([^}]+)\}', source).group(1)
    values = [v.strip() for v in row.split(',')]
    vendor, product = (int(values[i], 16) | int(values[i + 1], 16) << 8 for i in (8, 10))
    assert (vendor, product) == (0x4C4A, 0x4852)
    assert (vendor, product) not in ((0x1209, 0x0002), (0x4C4A, 0x5155), (0x4C4A, 0xC755), (0x4C4A, 0x8057))
    assert f'{vendor:04X}:{product:04X}' in source and '1209' not in source
    for name in ('flow.js', 'webmidi.js', 'serial.js', 'pedal.js', 'flash.js'):
        text = (SOURCE.parents[1] / 'app/installer' / name).read_text(encoding='utf-8')
        assert '0x1209' not in text and '4852' not in text.replace('LOADER_CRC = 0x4852', ''), name


def test_readme_names_every_message():
    header = (SOURCE / 'engine.h').read_text(encoding='utf-8')
    readme = (SOURCE / 'README.md').read_text(encoding='utf-8')
    ops = dict(re.findall(r'HRS_(HELLO|READ|CRC|BEGIN|DATA|WRITE|OPEN|FINISH|RETIRE|LEAVE) = (0x[0-9a-f]+)', header))
    assert len(ops) == 10
    for name, value in ops.items():
        assert f'| {int(value, 16):02x} {name} |' in readme.lower().replace(name.lower(), name)


def test_text_is_english_and_has_lf_only():
    for path in SOURCE.iterdir():
        raw = path.read_bytes()
        assert raw and b'\r' not in raw and raw.endswith(b'\n'), path.name


@pytest.mark.skipif(os.name == 'nt' and not shutil.which('wsl.exe') or os.name != 'nt' and not shutil.which('gcc'),
                    reason='no gcc')
def test_engine(tmp_path):
    """Every message, refusal, fault, and power cut at every flash operation, with sanitizers."""
    binary = ROOT / 'build' / 'mini-stage-test'
    binary.mkdir(parents=True, exist_ok=True)
    out = 'build/mini-stage-test/test_engine'
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
    done = subprocess.run(prefix + ['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-Ifirmware/mini_stage', '-O1',
                                    '-fsanitize=address,undefined', '-fno-sanitize-recover=all', 'firmware/mini_stage/engine.c',
                                    'firmware/mini_stage/test_engine.c', '-o', out], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    done = subprocess.run(prefix + [out], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0 and 'engine tests passed' in done.stdout, done.stdout + done.stderr
