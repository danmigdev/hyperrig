"""Build and compare capture runtime orchestration without device access."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",required=True,type=Path)
    p.add_argument("--distro",default="Ubuntu");p.add_argument("--mini-image",type=Path)
    args=p.parse_args();output=args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/"build"):p.error("use a new directory under build/")
    mini=[]
    if args.mini_image:
        path=args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):p.error("MINI image must be inside workspace")
        mini=["--mini-image",path.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True);relative=output.relative_to(ROOT).as_posix()
    prefix=["wsl.exe","--distribution",args.distro,"--exec"] if os.name=="nt" else []
    def run(command):subprocess.run(prefix+command,cwd=ROOT,check=True)
    sources=[f"firmware/src/hyperrig_{name}.c" for name in ("dot","head","a2l","rechannel","capture_processing")]
    common=["-std=c99","-Wall","-Wextra","-Werror","-Ifirmware/include"]
    run(["gcc",*common,"-O2","-fPIC","-shared","-fsanitize=undefined","-fno-sanitize-recover=all",*sources,
        "-o",relative+"/libhyperrig_capture_processing.so"])
    compiler="tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    for source in sources:
        run([compiler,"-target","pi32v2","-mcpu=r3",*common,"-Os","-ffreestanding","-fno-builtin","-c",source,
            "-o",relative+"/"+Path(source).stem+".pi32v2.o"])
    run(["python3","-B","-m","unittest","discover","-s","tests","-p","test_capture_processing_machine.py","-v"])
    run(["python3","-B","tools/verify_capture_processing.py","--library",relative+"/libhyperrig_capture_processing.so",
        "--output",relative+"/verification.json",*mini])
    run(["gcc",*common,"-O1","-g","-fsanitize=address,undefined","-fno-sanitize-recover=all",*sources,
        "tests/capture_processing_sanitize.c","-o",relative+"/capture_processing_sanitize"])
    run([relative+"/capture_processing_sanitize"])
    manifest={"component":"reconstructed-capture-processing","flashable":False,"device_access":False,
        "sanitizer_exact_buffer_cases":189,"files":{q.name:hashlib.sha256(q.read_bytes()).hexdigest()
            for q in sorted(output.iterdir()) if q.is_file()}}
    (output/"build-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("Capture runtime host/target objects and 189 exact-buffer sanitizer cases verified.")


if __name__=="__main__":main()
