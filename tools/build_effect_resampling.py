"""Build and verify complete effect resampling on host and pi32v2, offline."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mini-image',type=Path,required=True);p.add_argument('--distro',default='Ubuntu');args=p.parse_args()
    output=args.output.resolve();mini=args.mini_image.resolve(strict=True)
    if output.exists() or not output.is_relative_to(ROOT/'build'):p.error('use a fresh output directory under build/')
    if not mini.is_relative_to(ROOT):p.error('MINI image must be inside workspace')
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include'];source='firmware/src/hyperrig_effect_resampling.c'
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',source,
        '-o',relative+'/libhyperrig_effect_resampling.so'])
    run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',*common,
        '-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/hyperrig_effect_resampling.pi32v2.o'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',source,
        'tests/effect_resampling_sanitize.c','-o',relative+'/effect_resampling_sanitize'])
    run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_resampling_machine.py','-v'])
    run(['python3','-B','tools/verify_effect_resampling.py','--library',relative+'/libhyperrig_effect_resampling.so',
        '--output',relative+'/verification.json','--mini-image',mini.relative_to(ROOT).as_posix(),
        '--sanitizer-corpus',relative+'/sanitizer-corpus.bin'])
    checked=subprocess.run(prefix+[relative+'/effect_resampling_sanitize',relative+'/sanitizer-corpus.bin'],
        cwd=ROOT,capture_output=True,text=True,check=True)
    result=json.loads(checked.stdout);assert result['result']=='pass'
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'reconstructed-effect-resampling','flashable':False,'device_access':False,
        'files':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Complete resampling kernels and wrappers verified without hardware access.')

if __name__=='__main__':main()
