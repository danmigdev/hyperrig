"""Build and verify preset preflight on the host and pi32v2 without hardware."""
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
    parser.add_argument("--mini-image", type=Path)
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
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/include"]
    sources = [f"firmware/src/hyperrig_{name}.c" for name in
               ("controls", "control_actions", "selection", "preset_storage", "preset_preflight")]
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined",
         "-fno-sanitize-recover=all", *sources, "-o", relative + "/libhyperrig_preset_preflight.so"])
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    for source in sources:
        run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding",
             "-fno-builtin", "-c", source, "-o", relative + "/" + Path(source).stem + ".pi32v2.o"])
    run(["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_preset_preflight_machine.py", "-v"])
    run(["python3", "-B", "tools/verify_preset_preflight.py", "--library", relative + "/libhyperrig_preset_preflight.so",
         "--output", relative + "/verification.json", *mini_argument])
    manifest = {"component": "reconstructed-preset-preflight", "flashable": False, "device_access": False,
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Preset preflight host library and pi32v2 objects verified. No firmware produced or installed.")


if __name__ == "__main__":
    main()
