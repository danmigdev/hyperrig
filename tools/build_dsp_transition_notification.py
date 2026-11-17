"""Build and compare borrowed transition requests with their real notification."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
COMPONENTS=("biquad","biquad_coefficients","biquad_generator","dsp_initialization","dsp_dynamics",
    "dsp_audio_path","dsp_transition","controls","control_actions","selection","preset_storage",
    "preset_assets","capture_loader","dsp_transition_notification")
SOURCES=[f"firmware/src/hyperrig_{name}.c" for name in COMPONENTS]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--mini-image",type=Path);p.add_argument("--distro",default="Ubuntu");args=p.parse_args()
    output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/"build"):p.error("use a new output directory under build/")
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):p.error("MINI image must be inside workspace")
        mini=["--mini-image",path.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=["wsl.exe","--distribution",args.distro,"--exec"] if os.name=="nt" else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    common=["-std=c99","-Wall","-Wextra","-Werror","-Ifirmware/include"]
    run(["gcc",*common,"-O2","-fPIC","-shared","-fsanitize=undefined","-fno-sanitize-recover=all",*SOURCES,
        "-o",relative+"/libhyperrig_dsp_transition_notification.so"])
    compiler="tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    for source in SOURCES:
        run([compiler,"-target","pi32v2","-mcpu=r3",*common,"-Os","-ffreestanding","-fno-builtin",
            "-c",source,"-o",relative+"/"+Path(source).stem+".pi32v2.o"])
    run(["gcc",*common,"-O1","-g","-fsanitize=address,undefined","-fno-sanitize-recover=all",*SOURCES,
        "tests/dsp_transition_notification_sanitize.c","-o",relative+"/dsp_transition_notification_sanitize"])
    process=subprocess.run(prefix+[relative+"/dsp_transition_notification_sanitize"],cwd=ROOT,check=True,capture_output=True,text=True)
    result=json.loads(process.stdout);assert result["result"]=="pass"
    (output/"sanitizers.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    run(["python3","-B","-m","unittest","discover","-s","tests","-p","test_dsp_transition_notification_machine.py","-v"])
    run(["python3","-B","tools/verify_dsp_transition_notification.py","--library",relative+"/libhyperrig_dsp_transition_notification.so",
        "--output",relative+"/verification.json",*mini])
    manifest={"component":"reconstructed-dsp-transition-notification","flashable":False,"device_access":False,
        "files":{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output/"build-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("Real transition notification and borrowed state verified without hardware access.")


if __name__=="__main__":main()
