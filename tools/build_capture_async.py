"""Build asynchronous capture reconstruction and offline instruction evidence."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from verify_capture_async import SOURCES
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mini-image',type=Path);parser.add_argument('--distro',default='Ubuntu');parser.add_argument('--development',action='store_true')
    args=parser.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):parser.error('use a fresh directory under build/')
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix();prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    sources=[f'firmware/src/hyperrig_{name}.c' for name in SOURCES];common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*sources,'-o',relative+'/libhyperrig_capture_async.so'])
    if args.development:return
    compiler='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    for source in sources:run([compiler,'-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*sources,'tests/capture_async_sanitize.c','-o',relative+'/capture_async_sanitize'])
    result=subprocess.run(prefix+[relative+'/capture_async_sanitize'],cwd=ROOT,capture_output=True,text=True,check=True)
    sanitizer=json.loads(result.stdout);assert sanitizer['result']=='pass'
    (output/'sanitizers.json').write_text(json.dumps(sanitizer,indent=2)+'\n',encoding='utf-8')
    run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_capture_async_machine.py','-v'])
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):parser.error('MINI image must be in workspace')
        mini=['--mini-image',path.relative_to(ROOT).as_posix()]
    run(['python3','-B','tools/verify_capture_async.py','--library',relative+'/libhyperrig_capture_async.so','--output',relative+'/verification.json',*mini])
    manifest={'component':'reconstructed-capture-async','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Asynchronous capture reconstruction verified.')
if __name__=='__main__':main()
