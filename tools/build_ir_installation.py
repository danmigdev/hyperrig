"""Build IR installation recovery for host/pi32v2 and verify it without hardware."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCES=[f'firmware/src/hyperrig_{name}.c' for name in ('controls','control_actions','selection',
    'preset_storage','preset_assets','ir_loader','biquad_coefficients','biquad_generator','ir_installation')]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='fresh directory under build/')
    parser.add_argument('--distro',default='Ubuntu');parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'): parser.error('use a new directory under build/')
    mini=[]
    if args.mini_image:
        image=args.mini_image.resolve(strict=True)
        if not image.is_relative_to(ROOT): parser.error('MINI image must be inside workspace')
        mini=['--mini-image',image.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command): subprocess.run(prefix+command,cwd=ROOT,check=True)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',
         *SOURCES,'-o',relative+'/libhyperrig_ir_installation.so'])
    compiler='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    for source in SOURCES:
        run([compiler,'-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin',
             '-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',
         *SOURCES,'tests/ir_installation_sanitize.c','-o',relative+'/ir_installation_sanitize'])
    sanitizer=subprocess.run(prefix+[relative+'/ir_installation_sanitize'],cwd=ROOT,capture_output=True,text=True,check=True)
    (output/'sanitizers.json').write_text(json.dumps(json.loads(sanitizer.stdout),indent=2)+'\n',encoding='utf-8')
    run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_ir_installation_machine.py','-v'])
    run(['python3','-B','tools/verify_ir_installation.py','--library',relative+'/libhyperrig_ir_installation.so',
         '--output',relative+'/verification.json',*mini])
    manifest={'component':'reconstructed-ir-installation','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('IR preparation, installation and slot reads verified for host and pi32v2. No firmware produced or installed.')
if __name__=='__main__': main()
