"""Build and verify actual constructor and signal handoffs without device access."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from verify_effect_configured_signal import SOURCES,source_paths,EffectConfiguredSignalProgram
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mini-image',type=Path);parser.add_argument('--distro',default='Ubuntu');args=parser.parse_args()
    output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):parser.error('choose a fresh directory under build/')
    # Load exactly the verifier's transitive models and guard schema before the
    # first compiler call, closing the compilation-to-verification edit window.
    from verify_effect_construction import IO as ConstructionIO
    EffectConfiguredSignalProgram()
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths()}
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=['wsl.exe','--distribution',args.distro,'--exec'] if os.name=='nt' else []
    def run(command,**kwargs):return subprocess.run(prefix+command,cwd=ROOT,check=True,**kwargs)
    common=['-std=c11','-Wall','-Wextra','-Werror','-Ifirmware/include']
    run(['gcc',*common,'-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all',*SOURCES,'-o',relative+'/libhyperrig_effect_configured_signal.so'])
    compiler='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    for source in SOURCES:
        run([compiler,'-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin','-c',source,
            '-o',relative+'/'+Path(source).stem+'.pi32v2.o'])
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*SOURCES,
        'tests/effect_configured_signal_sanitize.c','-o',relative+'/effect_configured_signal_sanitize'])
    focused=run(['python3','-B','-m','unittest','discover','-s','tests','-p','test_effect_configured_signal_machine.py','-v'],capture_output=True,text=True)
    (output/'focused-tests.txt').write_text(focused.stdout+focused.stderr,encoding='utf-8')
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):parser.error('MINI image must be within the workspace')
        mini=['--mini-image',path.relative_to(ROOT).as_posix()]
    run(['python3','-B','tools/verify_effect_configured_signal.py','--library',relative+'/libhyperrig_effect_configured_signal.so',
        '--output',relative+'/verification.json','--sanitizer-corpus',relative+'/retained-state-replay.bin',*mini])
    report=json.loads((output/'verification.json').read_text())
    if report['source_sha256']!=before:raise ValueError('configured-signal inputs changed during compilation/comparison')
    sanitizer=run([relative+'/effect_configured_signal_sanitize',relative+'/retained-state-replay.bin'],capture_output=True,text=True)
    result=json.loads(sanitizer.stdout);assert result['result']=='pass'
    assert result['cases']==report['total_comparisons']
    assert result['retained_allocation_chains']==report['retained_allocation_chains']
    (output/'sanitizers.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    manifest={'component':'reconstructed-effect-configured-signal','flashable':False,'device_access':False,
        'files':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Configured signal host/pi32v2 build, original instruction comparisons, and sanitizer replay passed.')

if __name__=='__main__':main()
