"""Build the joined parameter/resource lifecycle and its unchanged dependencies."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from verify_effect_parameter_lifecycle import SOURCES
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--distro',default='Ubuntu')
    parser.add_argument('--build-only',action='store_true');parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):parser.error('use a fresh directory under build/')
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',
        *SOURCES,'-o',relative+'/libhyperrig_effect_parameter_lifecycle.so'])
    for source in SOURCES:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
            *common,'-Os','-ffreestanding','-fno-builtin','-c',source,
            '-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    if args.build_only:
        print('Development host and pi32v2 builds complete; comparison verification is separate.');return
    tests=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_parameter_lifecycle_machine.py','-v'],capture_output=True,text=True)
    (output/'focused-tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*SOURCES,
        'tests/effect_parameter_lifecycle_sanitize.c','-o',relative+'/effect_parameter_lifecycle_sanitize'])
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):parser.error('MINI image must be inside the workspace')
        mini=['--mini-image',path.relative_to(ROOT).as_posix()]
    run(['python3','-B','tools/verify_effect_parameter_lifecycle.py','--library',relative+'/libhyperrig_effect_parameter_lifecycle.so',
        '--output',relative+'/verification.json','--sanitizer-corpus',relative+'/original-comparison-replay.bin',*mini])
    replay=run([relative+'/effect_parameter_lifecycle_sanitize',relative+'/original-comparison-replay.bin'],capture_output=True,text=True)
    result=json.loads(replay.stdout);assert result['result']=='pass'
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'joined-effect-parameter-lifecycle','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Joined parameter/resource callers, scene/stage comparisons, target build and sanitizer replay passed offline.')

if __name__=='__main__':main()
