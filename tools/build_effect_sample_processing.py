"""Build complete sample engines and their joined callers without device access."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from verify_effect_sample_processing import SOURCES, source_paths, check_derivative, EffectSampleProcessingProgram
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--mini-image', required=True, type=Path)
    parser.add_argument('--distro', default='Ubuntu'); args = parser.parse_args()
    output = args.output.resolve(); mini = args.mini_image.resolve(strict=True)
    if output.exists() or not output.is_relative_to(ROOT/'build'): parser.error('choose a fresh directory under build/')
    if not mini.is_relative_to(ROOT): parser.error('MINI input must be inside the workspace')
    check_derivative(); EffectSampleProcessingProgram().audio
    before = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    output.mkdir(parents=True); relative = output.relative_to(ROOT).as_posix()
    prefix = ['wsl.exe', '--distribution', args.distro, '--exec'] if os.name == 'nt' else []
    def run(command, **kwargs): return subprocess.run(prefix+command, cwd=ROOT, check=True, **kwargs)
    common = ['-std=c11', '-Wall', '-Wextra', '-Werror', '-Ifirmware/include']
    library = relative+'/libhyperrig_effect_sample_processing.so'
    run(['gcc', *common, '-O2', '-fPIC', '-shared', '-fsanitize=undefined', '-fno-sanitize-recover=all', *SOURCES, '-o', library])
    for source in SOURCES:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang', '-target', 'pi32v2', '-mcpu=r3',
             *common, '-Os', '-ffreestanding', '-fno-builtin', '-c', source,
             '-o', relative+'/'+Path(source).stem+'.pi32v2.o'])
    focused = run(['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_effect_sample_processing_machine.py', '-v'],
                  capture_output=True, text=True)
    (output/'focused-tests.txt').write_text(focused.stdout+focused.stderr, encoding='utf-8')
    sanitizer = relative+'/effect_sample_processing_sanitize'
    run(['gcc', *common, '-O1', '-g', '-fsanitize=address,undefined', '-fno-sanitize-recover=all', *SOURCES,
         'tests/effect_sample_processing_sanitize.c', '-o', sanitizer])
    replay = relative+'/original-comparison-replay.bin'
    run(['python3', '-B', 'tools/verify_effect_sample_processing.py', '--library', library,
         '--output', relative+'/verification.json', '--sanitizer-corpus', replay,
         '--mini-image', mini.relative_to(ROOT).as_posix()])
    report = json.loads((output/'verification.json').read_text())
    if before != report['source_sha256']: raise ValueError('source set or bytes changed after the pre-compilation capture')
    sanitized = run([sanitizer, replay], capture_output=True, text=True)
    result = json.loads(sanitized.stdout)
    if result.get('result') != 'pass' or result.get('cases') != report['total_comparisons']:
        raise ValueError('sanitizer replay case count or result')
    (output/'sanitizers.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    if before != {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in before}:
        raise ValueError('source bytes changed during sanitizer replay')
    manifest = {'component': 'reconstructed-effect-sample-processing', 'flashable': False, 'device_access': False,
        'files': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print('Sample engines, exact original caller joins, host/target builds and sanitizer replay passed.')


if __name__ == '__main__': main()
