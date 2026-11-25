"""Run the installer's tests (app/installer) in node, with the loader's own engine compiled natively. Offline; no device is opened.

The whole course is simulated: a TANK-MINI with the original firmware 011 becomes one with HyperRig and back, with
messages lost, doubled and damaged, the cable pulled, the power gone at flash operations, the program closed and opened again,
a full disk, another computer, and everything that has to be refused.

Usage, from the repository root:
    python -B tools/check_installer.py BUILD [--distro Ubuntu]
BUILD is an output directory of tools/build_mini_stage.py.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('firmware/mini_stage/engine.c', 'firmware/mini_stage/host_server.c')


def engine(folder, distro='Ubuntu'):
    """The engine behind a pipe; its path from the repository root."""
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    binary = f'{folder.relative_to(ROOT).as_posix()}/host_server'
    prefix = ['wsl.exe', '--distribution', distro, '--exec'] if os.name == 'nt' else []
    done = subprocess.run(prefix + ['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-Ifirmware/mini_stage', *SOURCES, '-o', binary],
                          cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        raise SystemExit(done.stderr)
    return binary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('build', type=Path)
    parser.add_argument('--distro', default='Ubuntu')
    args = parser.parse_args(argv)
    binary = engine(ROOT / args.build / 'host', args.distro)
    return subprocess.run(['node', 'app/installer/test_installer.js', binary, str(args.build)], cwd=ROOT).returncode


if __name__ == '__main__':
    raise SystemExit(main())
