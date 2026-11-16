"""Build and verify complete integer IR runtime for host and pi32v2."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from build_ir_convolution import SOURCES as CONSTRUCTION_SOURCES

ROOT=Path(__file__).resolve().parents[1]
SOURCES=CONSTRUCTION_SOURCES+['firmware/src/hyperrig_ir_processing.c']

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--distro',default='Ubuntu');parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):parser.error('choose a fresh directory under build/')
    mini=[]
    if args.mini_image:
        image=args.mini_image.resolve(strict=True)
        if not image.is_relative_to(ROOT):parser.error('MINI image must be inside the workspace')
        mini=['--mini-image',image.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',
         *SOURCES,'-o',relative+'/libhyperrig_ir_processing.so'])
    compiler='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    for source in SOURCES:
        run([compiler,'-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin',
             '-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',
         *SOURCES,'tests/ir_processing_sanitize.c','-o',relative+'/ir_processing_sanitize'])
    sanitizer=subprocess.run(prefix+[relative+'/ir_processing_sanitize'],cwd=ROOT,capture_output=True,text=True,check=True)
    (output/'sanitizers.json').write_text(json.dumps(json.loads(sanitizer.stdout),indent=2)+'\n',encoding='utf-8')
    run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_ir_processing_machine.py','-v'])
    run(['python3','-B','tools/verify_ir_processing.py','--library',relative+'/libhyperrig_ir_processing.so',
         '--output',relative+'/verification.json',*mini])
    manifest={'component':'reconstructed-ir-processing','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Complete software IR processing verified for host and pi32v2. All accelerator transactions were synthetic.')
if __name__=='__main__':main()
