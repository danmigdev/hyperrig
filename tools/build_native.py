"""Compile recovered DSP C on the host and for pi32v2; no firmware flashing."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distro", default="Ubuntu", help="WSL distribution on Windows")
    args = parser.parse_args()
    prefix = ["wsl.exe", "--distribution", args.distro, "--exec"] if os.name == "nt" else []

    def run(command):
        subprocess.run(prefix + command, cwd=ROOT, check=True)

    directory = ROOT / "build/native"
    directory.mkdir(parents=True, exist_ok=True)
    sources = ["firmware/src/hyperrig_dot.c", "firmware/src/hyperrig_head.c"]
    common = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-Ifirmware/include"]
    run(["gcc", *common, "-O2", "-fPIC", "-shared", "-fsanitize=undefined",
         "-fno-sanitize-recover=all", *sources, "-o", "build/native/libhyperrig_dsp.so"])
    compiler = "tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang"
    # POSIX symlinks in the vendor archive are resolved by WSL, not Windows.
    if not (ROOT / compiler).parent.is_dir():
        raise SystemExit("Run python tools/bootstrap.py --toolchain first")
    objects = []
    for source in sources:
        target = f"build/native/{Path(source).stem}.pi32v2.o"
        run([compiler, "-target", "pi32v2", "-mcpu=r3", *common, "-Os", "-ffreestanding",
             "-fno-builtin", "-c", source, "-o", target])
        objects.append(target)
    linker = str(Path(compiler).with_name("ld")).replace("\\", "/")
    run([linker, "-r", *objects, "-o", "build/native/hyperrig_dsp.pi32v2.o"])
    run(["python3", "tools/verify_native.py"])
    print("Compiled and checked DSP component; no bootable Mini firmware was produced.")


if __name__ == "__main__":
    main()
