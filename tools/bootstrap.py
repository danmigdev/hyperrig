"""Recreate pinned research dependencies without installing anything system-wide."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download_checked(url, destination, expected):
    if destination.exists():
        if digest(destination) != expected:
            raise ValueError(f"existing file differs from the pinned reference: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "HyperRig-research"})
    print(f"Downloading {destination.name}", flush=True)
    with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
    if digest(temporary) != expected:
        raise ValueError(f"download SHA-256 mismatch: {destination.name}")
    temporary.replace(destination)


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, text=True, encoding="utf-8",
                          check=True, stdout=subprocess.PIPE).stdout.strip()


def checkout(name, reference):
    directory = ROOT / "upstream" / name
    if not directory.exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--no-checkout", reference["url"], str(directory))
        git("checkout", "--detach", reference["commit"], cwd=directory)
    if Path(git("rev-parse", "--show-toplevel", cwd=directory)).resolve() != directory.resolve():
        raise ValueError(f"not a separate upstream repository: {directory}")
    if git("rev-parse", "HEAD", cwd=directory) != reference["commit"]:
        raise ValueError(f"{name}: checkout differs from lock; existing work was left untouched")
    if git("status", "--porcelain", "--untracked-files=no", cwd=directory):
        raise ValueError(f"{name}: tracked local edits; existing work was left untouched")
    print(f"Verified {name} at {reference['commit'][:12]}")


def install_decompiler(reference):
    vendor = ROOT / "tools" / "vendor"
    archive = vendor / reference["name"]
    download_checked(reference["url"], archive, reference["sha256"])
    ghidra = vendor / f"ghidra_{reference['version']}_PUBLIC"
    if not ghidra.exists():
        with zipfile.ZipFile(archive) as zipped:
            for item in zipped.namelist():
                if not (vendor / item).resolve().is_relative_to(ghidra.resolve()):
                    raise ValueError("unexpected path in Ghidra archive")
            zipped.extractall(vendor)
    source = ROOT / "upstream" / "ghidra-jieli"
    processor = ghidra / "Ghidra" / "Processors" / "JieLi"
    shutil.copytree(source / "data", processor / "data", dirs_exist_ok=True)
    shutil.copyfile(source / "Module.manifest", processor / "Module.manifest")
    compiler = ghidra / "support" / ("sleigh.bat" if os.name == "nt" else "sleigh")
    if os.name != "nt":
        compiler.chmod(compiler.stat().st_mode | 0o111)
        launcher = ghidra / "support" / "launch.sh"
        launcher.chmod(launcher.stat().st_mode | 0o111)
    subprocess.run([str(compiler), "-a", str(processor / "data" / "languages")], check=True)
    print("Ghidra and JieLi processor ready; generated C remains incomplete pseudocode")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decompiler", action="store_true", help="also fetch Ghidra (~570 MB); needs a JDK")
    parser.add_argument("--toolchain", action="store_true", help="fetch pinned JieLi Linux compiler (usable through WSL)")
    args = parser.parse_args()
    locked = json.loads((ROOT / "research" / "sources.lock.json").read_text(encoding="utf-8"))
    for name, reference in locked["repositories"].items():
        checkout(name, reference)
    sdk = locked["sdk_reference"]
    directory = ROOT / "upstream" / "ac79-sdk-reference"
    for item in sdk["files"]:
        path = directory / item["path"]
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("invalid SDK reference path")
        download_checked(item["url"], path, item["sha256"])
    (directory / "provenance.json").write_text(json.dumps(sdk, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(sdk['files'])} SDK reference files")
    if args.decompiler:
        install_decompiler(locked["ghidra"])
    if args.toolchain:
        reference = locked["jieli_toolchain"]
        archive = ROOT / "tools/vendor" / reference["name"]
        download_checked(reference["url"], archive, reference["sha256"])
        destination = archive.parent / reference["directory"]
        if not destination.exists():
            with tarfile.open(archive) as packed:
                if any(not (archive.parent / item.name).resolve().is_relative_to(destination.resolve())
                       for item in packed.getmembers()):
                    raise ValueError("unexpected toolchain archive path")
                packed.extractall(archive.parent, filter="data")
        print("JieLi pi32v2 compiler ready (Linux/WSL); no device operations performed")


if __name__ == "__main__":
    main()
