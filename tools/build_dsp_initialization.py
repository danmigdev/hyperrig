"""Build and compare DSP initialization with explicit synthetic startup services."""
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
    parser.add_argument("--output", type=Path, required=True)
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
            parser.error("MINI image must be inside workspace")
        mini_argument = ["--mini-image", mini.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True)
    relative = output.relative_to(ROOT).as_posix()
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []
    def run(command):
        subprocess.run(prefix + command, cwd=ROOT, check=True)
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/include"]
    sources = ["firmware/src/hyperrig_biquad_coefficients.c", "firmware/src/hyperrig_biquad_generator.c",
               "firmware/src/hyperrig_dsp_initialization.c"]
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined", "-fno-sanitize-recover=all",
         *sources, "-o", relative + "/libhyperrig_dsp_initialization.so"])
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    for source in sources:
        run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin",
             "-c", source, "-o", relative + "/" + Path(source).stem + ".pi32v2.o"])
    run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
         *sources, "tests/dsp_initialization_sanitize.c", "-o", relative + "/dsp_initialization_sanitize"])
    result = subprocess.run(prefix + [relative + "/dsp_initialization_sanitize"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    sanitizer = json.loads(result.stdout)
    (output / "sanitizers.json").write_text(json.dumps(sanitizer, indent=2)+"\n", encoding="utf-8")
    run(["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_dsp_initialization_machine.py", "-v"])
    run(["python3", "-B", "tools/verify_dsp_initialization.py", "--library", relative + "/libhyperrig_dsp_initialization.so",
         "--output", relative + "/verification.json", *mini_argument])
    manifest = {"component": "reconstructed-dsp-initialization", "flashable": False, "device_access": False,
        "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()}}
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(f"DSP initialization verified, including {sanitizer['exact_buffer_cases']} ASan/UBSan exact-buffer cases.")


if __name__ == "__main__":
    main()
