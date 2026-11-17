"""Build, replay and bind complete storage platform evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from verify_storage_platform import SOURCES,source_paths,StoragePlatformProgram
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mini-image',type=Path,required=True);p.add_argument('--distro',default='Ubuntu');a=p.parse_args()
    out=a.output.resolve();mini=a.mini_image.resolve(strict=True)
    if out.exists() or not out.is_relative_to(ROOT/'build'):p.error('use a fresh output directory under build/')
    if not mini.is_relative_to(ROOT):p.error('MINI input must be workspace-local')
    StoragePlatformProgram()
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    out.mkdir(parents=True);relative=out.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',a.distro,'--exec'] if os.name=='nt' else []
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    library=relative+'/libhyperrig_storage_platform.so'
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*SOURCES,'-o',library])
    for source in SOURCES:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
            *common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    focused=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_storage_platform_machine.py','-v'],capture_output=True,text=True)
    (out/'focused-tests.txt').write_text(focused.stdout+focused.stderr,encoding='utf-8')
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*SOURCES,
        'tests/storage_platform_sanitize.c','-o',relative+'/storage_platform_sanitize'])
    fixtures=relative+'/original-fixtures.bin'
    run(['python3','-B','tools/verify_storage_platform.py','--library',library,'--fixtures',fixtures,
        '--output',relative+'/verification.json','--mini-image',mini.relative_to(ROOT).as_posix()])
    report=json.loads((out/'verification.json').read_text())
    if report['source_sha256']!=before:raise ValueError('platform source set/bytes changed after pre-compilation capture')
    replay=run([relative+'/storage_platform_sanitize',fixtures],capture_output=True,text=True)
    result=json.loads(replay.stdout)
    if result.get('result')!='pass':raise ValueError('storage sanitizer replay failed')
    (out/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'storage-platform','flashable':False,'physical_storage_access':False,'CPU_events_are_synthetic':True,
        'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file()}}
    (out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Storage platform host, target, original and sanitizer checks passed.')
if __name__=='__main__':main()
