"""Build model construction and local original-byte evidence without devices."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from verify_effect_model_construction import SOURCES,source_paths,EffectModelConstructionProgram
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path);p.add_argument('--mini-image',required=True,type=Path)
    p.add_argument('--distro',default='Ubuntu');args=p.parse_args()
    output=args.output.resolve();mini=args.mini_image.resolve(strict=True)
    if output.exists()or not output.is_relative_to(ROOT/'build'):p.error('use a fresh directory under build/')
    if not mini.is_relative_to(ROOT):p.error('MINI input must be inside the workspace')
    EffectModelConstructionProgram()
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()for name in source_paths()}
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec']if os.name=='nt'else[]
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    library=relative+'/libhyperrig_effect_model_construction.so'
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*SOURCES,'-o',library])
    for source in SOURCES:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
            *common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    focused=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_model_construction_machine.py','-v'],capture_output=True,text=True)
    (output/'focused-tests.txt').write_text(focused.stdout+focused.stderr,encoding='utf-8')
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*SOURCES,
        'tests/effect_model_construction_sanitize.c','-o',relative+'/effect_model_construction_sanitize'])
    fixtures=relative+'/original-fixtures.bin'
    run(['python3','-B','tools/verify_effect_model_construction.py','--library',library,'--fixtures',fixtures,
         '--output',relative+'/verification.json','--mini-image',mini.relative_to(ROOT).as_posix()])
    report=json.loads((output/'verification.json').read_text())
    if report['source_sha256']!=before:raise ValueError('source set or bytes changed during build')
    sanitized=run([relative+'/effect_model_construction_sanitize',fixtures],capture_output=True,text=True)
    evidence=json.loads(sanitized.stdout)
    if evidence.get('result')!='pass'or evidence['exact_allocation_replays']!=report['comparisons']:
        raise ValueError('sanitizer replay result/count')
    (output/'sanitizers.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'reconstructed-effect-model-construction','flashable':False,'device_access':False,
      'files':{file.name:hashlib.sha256(file.read_bytes()).hexdigest()for file in sorted(output.iterdir())if file.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('All model-construction, native numerical, host/target and sanitizer checks passed.')

if __name__=='__main__':main()
