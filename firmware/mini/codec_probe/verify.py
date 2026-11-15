"""Offline compiler + independent edge decoder checks. No device access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.verify_mini_codec import target_metadata


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prefix = ['wsl.exe', '--distribution', 'Ubuntu', '--exec'] if os.name == 'nt' else []
    out = ROOT / 'build/mini-codec-probe'
    out.mkdir(parents=True, exist_ok=True)

    def run(args):
        result = subprocess.run(prefix + args, cwd=ROOT, check=True,
                                capture_output=True, text=True, encoding='utf-8')
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.stdout

    source = 'firmware/mini/codec_probe/read16.c'
    common = ['-std=c11', '-Wall', '-Wextra', '-Werror']
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined',
         '-fno-sanitize-recover=all', source,
         'firmware/mini/codec_probe/test_read16.c', '-o', 'build/mini-codec-probe/test-read16'])
    counts = json.loads(run(['build/mini-codec-probe/test-read16']))
    compiler = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    run([compiler, '-target', 'pi32v2', '-mcpu=r3', *common, '-Os', '-ffreestanding',
         '-fno-builtin', '-c', source, '-o', 'build/mini-codec-probe/read16.pi32v2.o'])
    object_path = out / 'read16.pi32v2.o'
    target, _ = target_metadata(object_path.read_bytes())
    if target['undefined_symbols']:
        raise AssertionError('unexpected target externals: ' + str(target['undefined_symbols']))
    report = {
        'project': 'HyperRig', 'scope': 'Finite diagnostic register reads; no codec data writes',
        'sources': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in [
            ROOT / source, Path(__file__), ROOT / 'firmware/mini/codec_probe/read16.h',
            ROOT / 'firmware/mini/codec_probe/test_read16.c',
            ROOT / 'tools/verify_mini_codec.py',
            ROOT / 'firmware/mini/codec/hyperrig_mini_codec.h']},
        'target': target, 'object_sha256': sha(object_path), 'host_asan_ubsan': counts,
        'wire': ['START', '0x36', 'reg_hi', 'reg_lo', 'repeated START', '0x37',
                 'read_hi', 'master ACK', 'read_lo', 'master NACK (SDA released)', 'STOP'],
        'register_allowlist': [hex(r) for r in (1,3,0x1c,0x1d,0x2b,0x2c,0x31,0x32,0x58,0x59)],
        'slave_acks': 4, 'read_bytes': 2, 'maximum_sample_calls': 20,
        'maximum_delay_calls': 193,
        'references_documentary_only': [
            {'url': 'https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.1.pdf',
             'scope': 'section7.4 page35, Figure23: repeated START, register16BE, value16BE, final NACK'},
            {'url': 'https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.6.pdf',
             'scope': 'page69: register0x58 ID/status; register0x59 read-only RAM/analog-mute status'},
            {'url': 'https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.h',
             'scope': 'register0x58 has KEYDET bit7, MICDET bit6, softwareID mask3'},
        ],
        'limitations': ['Callbacks must terminate; no calibrated electrical timing or clock stretching.',
            'A NACK in ROM does not establish codec absence: power/reset/MCLK are inherited.',
            'No ID read by this verifier; no exclusive chip/revision identification.',
            'Failed timing callbacks only permit best-effort STOP and line-latch cleanup.',
            'Reading clock register fields does not measure physical MCLK/BCLK/LRCK.',
            'ROM wrapper, GPIO save/restore, USB commands and hardware execution are external.'],
        'hardware_accessed': False,
    }
    (out / 'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
