"""Use the installer of the built desktop program with a simulated pedal, and try its locks. No device is opened.

The program runs outside the screens with a profile of its own and --no-pedal, so that it never gets a real port; the page is
given the ports of a simulated TANK-MINI (app/installer/simulated_pedal.js, with the loader's own engine). From the original
firmware to HyperRig and back, with the cable pulled, the program closed and the power gone on the way; the copies that are
kept; the look at several sizes; the locks of the page; a damaged firmware refused at the start.

Usage, from the repository root:
    python -B tools/check_desktop_installer.py --program build/hyperrig-desktop-NN --loader build/mini-stage-NN --output build/CHECK-NN
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_desktop_editor as desktop  # noqa: E402
import check_installer  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--program', type=Path, required=True)
    parser.add_argument('--loader', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--distro', default='Ubuntu')
    args = parser.parse_args(argv)
    output = (ROOT / args.output).resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        parser.error('use a fresh directory under build/')
    desktop.check(ROOT / args.program)
    output.mkdir(parents=True)
    binary = check_installer.engine(output / 'host', args.distro)
    return subprocess.run(['node', '--experimental-websocket', '--no-warnings', 'app/installer/check_program.js', str((ROOT / args.program).resolve()), binary,
                           str((ROOT / args.loader).resolve()), str(output)], cwd=ROOT).returncode


if __name__ == '__main__':
    raise SystemExit(main())
