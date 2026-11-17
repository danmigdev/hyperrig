"""Build and verify parameter primitives, actual division, copying and clearing."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mini-image',type=Path)
    p.add_argument('--distro',default='Ubuntu');args=p.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):p.error('use a fresh build directory')
    mini=[]
    if args.mini_image:
        image=args.mini_image.resolve(strict=True)
        if not image.is_relative_to(ROOT):p.error('MINI image must be in the workspace')
        mini=['--mini-image',image.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    sources=['firmware/src/hyperrig_effect_parameter_support.c','firmware/src/hyperrig_effect_enable.c']
    library=relative+'/libhyperrig_effect_parameter_support.so'
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*sources,'-o',library])
    for source in sources:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
             *common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_parameter_support_machine.py','-v'])
    fixtures=relative+'/original-fixtures.bin'
    run(['python3','-B','tools/verify_effect_parameter_support.py','--library',library,
         '--output',relative+'/verification.json','--fixtures',fixtures,*mini])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*sources,
         'tests/effect_parameter_support_sanitize.c','-o',relative+'/effect_parameter_support_sanitize'])
    result=json.loads(subprocess.check_output(prefix+[relative+'/effect_parameter_support_sanitize',fixtures],cwd=ROOT,text=True))
    if result.get('result')!='pass':raise ValueError('support sanitizer verification failed')
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'reconstructed-effect-parameter-support','flashable':False,'device_access':False,
        'files':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Complete parameter primitives, native division and memory bodies verified offline.')

if __name__=='__main__':main()
