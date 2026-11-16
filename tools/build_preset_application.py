"""Build and compare complete preset application offline, without hardware access."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
C_NAMES=('controls','control_actions','selection','preset_storage','preset_assets','preset_application')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--distro',default='Ubuntu')
    p.add_argument('--mini-image',type=Path);args=p.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):p.error('use a new directory under build/')
    mini=[]
    if args.mini_image:
        image=args.mini_image.resolve(strict=True)
        if not image.is_relative_to(ROOT):p.error('MINI image must be within workspace')
        mini=['--mini-image',image.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    sources=[f'firmware/src/hyperrig_{name}.c' for name in C_NAMES]
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',
         *sources,'-o',relative+'/libhyperrig_preset_application.so'])
    for source in sources:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
             *common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_preset_application_machine.py','-v'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*sources,
         'tests/preset_application_sanitize.c','-o',relative+'/preset_application_sanitize'])
    result=json.loads(subprocess.check_output(prefix+[relative+'/preset_application_sanitize'],cwd=ROOT,text=True))
    if result.get('result')!='pass':raise ValueError('sanitizer verification failed')
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    run(['python3','-B','tools/verify_preset_application.py','--library',relative+'/libhyperrig_preset_application.so',
         '--output',relative+'/verification.json',*mini])
    manifest={'component':'reconstructed-preset-application','flashable':False,'device_access':False,
        'files':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Preset application verified offline. No hardware accessed or firmware image produced.')

if __name__=='__main__':main()
