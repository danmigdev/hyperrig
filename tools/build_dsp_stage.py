"""Build stage/audio-task reconstruction and replay original comparisons under sanitizers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from verify_dsp_stage import SOURCES
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mini-image',type=Path);parser.add_argument('--distro',default='Ubuntu');args=parser.parse_args()
    output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):parser.error('use a fresh directory under build/')
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):parser.error('MINI image must be inside the workspace')
        mini=['--mini-image',path.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    sources=[f'firmware/src/hyperrig_{name}.c' for name in SOURCES]
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*sources,'-o',relative+'/libhyperrig_dsp_stage.so'])
    compiler='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    for source in sources:
        run([compiler,'-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*sources,'tests/dsp_stage_sanitize.c','-o',relative+'/dsp_stage_sanitize'])
    tests=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_dsp_stage_machine.py','-v'],capture_output=True,text=True)
    (output/'focused-tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    run(['python3','-B','tools/verify_dsp_stage.py','--library',relative+'/libhyperrig_dsp_stage.so','--output',relative+'/verification.json',
        '--sanitizer-corpus',relative+'/original-comparison-replay.bin',*mini])
    sanitizer=run([relative+'/dsp_stage_sanitize',relative+'/original-comparison-replay.bin'],capture_output=True,text=True)
    result=json.loads(sanitizer.stdout);assert result['result']=='pass'
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'reconstructed-dsp-stage','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Original stage/helper comparisons, joined task, host and pi32v2 builds, and sanitizer replay passed.')

if __name__=='__main__':main()
