"""Build and verify native capture loading-to-processing integration offline."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
C_NAMES = ("controls", "control_actions", "selection", "preset_storage", "preset_assets",
    "capture_loader", "capture_container", "capture_dispatch", "capture_reset", "capture_parser",
    "capture_native", "dot", "head", "a2l", "rechannel", "capture_processing", "capture_warmup", "capture_live")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--distro", default="Ubuntu")
    parser.add_argument("--mini-image", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "build"):
        parser.error("use a new output directory under build/")
    mini_arguments = []
    if args.mini_image:
        path = args.mini_image.resolve(strict=True)
        if not path.is_relative_to(ROOT):
            parser.error("MINI image must be inside workspace")
        mini_arguments = ["--mini-image", path.relative_to(ROOT).as_posix()]
    output.mkdir(parents=True)
    relative = output.relative_to(ROOT).as_posix()
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []
    def run(command):
        subprocess.run(prefix + command, cwd=ROOT, check=True)
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/include"]
    sources = [f"firmware/src/hyperrig_{name}.c" for name in C_NAMES]
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined", "-fno-sanitize-recover=all",
         *sources, "-o", relative + "/libhyperrig_capture_live.so"])
    for source in sources:
        run(["tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang", "-target", "pi32v2", "-mcpu=r3",
             *common, "-Os", "-ffreestanding", "-fno-builtin", "-c", source,
             "-o", relative + "/" + Path(source).stem + ".pi32v2.o"])
    run(["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_capture_live_machine.py", "-v"])
    run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all", *sources,
         "tests/capture_live_sanitize.c", "-o", relative + "/capture_live_sanitize"])
    raw = subprocess.check_output(prefix + [relative + "/capture_live_sanitize",
        "analysis/firmware/m571_g_app/embedded-0.a2l"], cwd=ROOT, text=True)
    sanitizers = json.loads(raw)
    if sanitizers.get("result") != "pass":
        raise ValueError("live capture sanitizer failed")
    (output / "sanitizers.json").write_text(json.dumps(sanitizers, indent=2) + "\n", encoding="utf-8")
    run(["python3", "-B", "tools/verify_capture_live.py", "--library", relative + "/libhyperrig_capture_live.so",
         "--output", relative + "/verification.json", *mini_arguments])
    manifest = {"component": "native-capture-live-processing", "flashable": False, "device_access": False,
        "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(output.iterdir()) if path.is_file()}}
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Native capture loading and processing verified; no device accessed or firmware produced.")


if __name__ == "__main__":
    main()
