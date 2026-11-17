"""Build exact resource/ownership/lifecycle derivatives and verify offline."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from verify_effect_resource_ownership import SOURCES,source_paths,check_derivatives,EffectResourceOwnershipProgram
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--distro',default='Ubuntu');parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):parser.error('use a fresh directory under build/')
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    check_derivatives();EffectResourceOwnershipProgram()
    inputs={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source_paths()}
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',
        *SOURCES,'-o',relative+'/libhyperrig_effect_resource_ownership.so'])
    for source in SOURCES:
        run(['tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang','-target','pi32v2','-mcpu=r3',
            *common,'-Os','-ffreestanding','-fno-builtin','-c',source,'-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    tests=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_resource_ownership_machine.py','-v'],capture_output=True,text=True)
    (output/'focused-tests.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*SOURCES,
        'tests/effect_resource_ownership_sanitize.c','-o',relative+'/effect_resource_ownership_sanitize'])
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):parser.error('MINI image must remain inside the workspace')
        mini=['--mini-image',path.relative_to(ROOT).as_posix()]
    run(['python3','-B','tools/verify_effect_resource_ownership.py','--library',relative+'/libhyperrig_effect_resource_ownership.so',
        '--output',relative+'/verification.json','--sanitizer-corpus',relative+'/original-comparison-replay.bin',*mini])
    verification=json.loads((output/'verification.json').read_text())
    if inputs!=verification['source_sha256']:raise ValueError('source provenance changed after compilation began')
    replay=run([relative+'/effect_resource_ownership_sanitize',relative+'/original-comparison-replay.bin'],capture_output=True,text=True)
    result=json.loads(replay.stdout);assert result['result']=='pass'
    assert result['original_comparison_replays']==verification['sanitizer_replay_cases']
    assert result['fourth_read_prefix_replays']==verification['original_fourth_read_prefix_comparisons']
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    assert inputs=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in inputs}
    manifest={'component':'joined-effect-resource-ownership','flashable':False,'device_access':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Resource/ownership/lifecycle host/pi32v2 builds, original comparisons and sanitizer replay passed.')

if __name__=='__main__':main()
