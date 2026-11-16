"""Build and compare journal writes with synthetic storage only."""
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
    sources = [f"firmware/src/hyperrig_{name}.c" for name in
        ("controls", "control_actions", "selection", "preset_storage", "capture_metadata", "capture_journal")]
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined", "-fno-sanitize-recover=all",
         *sources, "-o", relative + "/libhyperrig_capture_journal.so"])
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    for source in sources:
        run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding", "-fno-builtin",
             "-c", source, "-o", relative + "/" + Path(source).stem + ".pi32v2.o"])
    run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
         *sources, "tests/capture_journal_sanitize.c", "-o", relative + "/capture_journal_sanitize"])
    run([relative + "/capture_journal_sanitize"])
    run(["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_capture_journal_machine.py", "-v"])
    run(["python3", "-B", "tools/verify_capture_journal.py", "--library", relative + "/libhyperrig_capture_journal.so",
         "--output", relative + "/verification.json", *mini_argument])
    manifest = {"component": "reconstructed-capture-journal", "flashable": False, "device_access": False, "physical_writes": False,
                "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Journal host/target objects verified using synthetic storage only.")


if __name__ == "__main__":
    main()
