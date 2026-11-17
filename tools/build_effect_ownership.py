"""Build complete effect ownership bodies and replay original state/call evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from verify_effect_ownership import SOURCES,source_paths,EffectOwnershipProgram
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mini-image',type=Path);p.add_argument('--distro',default='Ubuntu');args=p.parse_args()
    output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):p.error('use a fresh directory under build/')
    mini=[]
    if args.mini_image:
        image=args.mini_image.resolve(strict=True)
        if not image.is_relative_to(ROOT):p.error('MINI image must be inside the workspace')
        mini=['--mini-image',image.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    EffectOwnershipProgram()
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    library=relative+'/libhyperrig_effect_ownership.so'
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*SOURCES,'-o',library])
    for source in SOURCES:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
            *common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    focused=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_ownership_machine.py','-v'],capture_output=True,text=True)
    (output/'focused-tests.txt').write_text(focused.stdout+focused.stderr,encoding='utf-8')
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*SOURCES,
        'tests/effect_ownership_sanitize.c','-o',relative+'/effect_ownership_sanitize'])
    fixtures=relative+'/original-fixtures.bin'
    run(['python3','-B','tools/verify_effect_ownership.py','--library',library,
        '--fixtures',fixtures,'--output',relative+'/verification.json',*mini])
    report=json.loads((output/'verification.json').read_text())
    if report['source_sha256']!=before:raise ValueError('ownership source set or bytes changed during build')
    sanitizer=run([relative+'/effect_ownership_sanitize',fixtures],capture_output=True,text=True)
    result=json.loads(sanitizer.stdout)
    if result.get('result')!='pass':raise ValueError('ownership sanitizer replay failed')
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'reconstructed-effect-ownership','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Complete ownership, routing, callback, host, target and sanitizer evidence passed.')
if __name__=='__main__':main()
