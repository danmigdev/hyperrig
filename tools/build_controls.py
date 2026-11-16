"""Build the recovered controls component on the host and pi32v2, without hardware."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new directory under build/")
    parser.add_argument("--distro", default="Ubuntu")
    parser.add_argument("--mini-image", type=Path, help="optional reviewed v4 image inside the workspace")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build"):
        parser.error("use a new output directory under build/")
    mini_argument = []
    if args.mini_image:
        mini = args.mini_image.resolve(strict=True)
        if not mini.is_relative_to(ROOT):
            parser.error("the optional MINI image must be inside the workspace")
        mini_argument = ["--mini-image", mini.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True)
    relative = output.relative_to(ROOT).as_posix()
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []
    def run(command):
        subprocess.run(prefix + command, cwd=ROOT, check=True)
    source = "firmware/src/hyperrig_controls.c"
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/include"]
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined",
         "-fno-sanitize-recover=all", source, "-o", relative + "/libhyperrig_controls.so"])
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding",
         "-fno-builtin", "-c", source, "-o", relative + "/hyperrig_controls.pi32v2.o"])
    run(["python3", "-B", "tools/verify_controls.py", "--library", relative + "/libhyperrig_controls.so",
         "--output", relative + "/verification.json", *mini_argument])
    report = {"component": "reconstructed-controls", "flashable": False, "device_access": False,
              "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "build-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Host C and pi32v2 relocatable object verified. No firmware image was produced or installed.")


if __name__ == "__main__":
    main()
