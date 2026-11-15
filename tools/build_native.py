"""Compile recovered DSP C on the host and for pi32v2; no firmware flashing."""
import argparse
import hashlib
import json
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
    sources = ["firmware/src/hyperrig_dot.c", "firmware/src/hyperrig_head.c",
               "firmware/src/hyperrig_a2l.c", "firmware/src/hyperrig_rechannel.c",
               "firmware/src/hyperrig_layer.c", "firmware/src/hyperrig_engine.c"]
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
    harness = "tests/native_a2l_sanitize.c"
    run(["gcc", *common, "-O1", "-g", "-fsanitize=address,undefined",
         "-fno-sanitize-recover=all", *sources, harness, "-o", "build/native/a2l_sanitize"])
    checked = subprocess.run(prefix + ["build/native/a2l_sanitize",
                             "analysis/firmware/m571_g_app/embedded-0.a2l"],
                             cwd=ROOT, capture_output=True, text=True)
    if checked.returncode:
        sys.stderr.write(checked.stdout + checked.stderr)
        checked.check_returncode()
    sanitizer_report = json.loads(checked.stdout)
    sanitizer_report["harness_sha256"] = hashlib.sha256((ROOT / harness).read_bytes()).hexdigest()
    evidence = ROOT / "analysis/native"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "a2l-sanitizers.json").write_text(json.dumps(sanitizer_report, indent=2) + "\n", encoding="utf-8")
    print(f"A2L: {sanitizer_report['cases']} exact-buffer cases passed ASan/UBSan", flush=True)
    run(["python3", "tools/verify_native.py"])
    print("Compiled and checked DSP component; no bootable Mini firmware was produced.")


if __name__ == "__main__":
    main()
