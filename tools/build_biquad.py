"""Build and verify recovered Q28 filters on the host and pi32v2, offline."""
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
    source = "firmware/src/hyperrig_biquad.c"
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined",
         "-fno-sanitize-recover=all", source, "-o", relative + "/libhyperrig_biquad.so"])
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding",
         "-fno-builtin", "-c", source, "-o", relative + "/hyperrig_biquad.pi32v2.o"])
    run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
         source, "tests/biquad_sanitize.c", "-o", relative + "/biquad_sanitize"])
    checked = subprocess.run(prefix + [relative + "/biquad_sanitize"], cwd=ROOT,
                             capture_output=True, text=True, check=True)
    sanitizer = json.loads(checked.stdout)
    (output / "sanitizers.json").write_text(json.dumps(sanitizer, indent=2) + "\n", encoding="utf-8")
    run(["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_biquad_machine.py", "-v"])
    run(["python3", "-B", "tools/verify_biquad.py", "--library", relative + "/libhyperrig_biquad.so",
         "--output", relative + "/verification.json", *mini_argument])
    manifest = {"component": "reconstructed-biquad-q28", "flashable": False, "device_access": False,
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Q28 filters verified, including {sanitizer['exact_buffer_cases']} ASan/UBSan exact-buffer cases.")


if __name__ == "__main__":
    main()
