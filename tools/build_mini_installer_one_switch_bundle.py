"""Build the separate, read-only-editor v4 one-switch installer preview.

This entry performs local packaging/verification only. It never changes a
sealed v3 bundle or treats v3 hardware observations as v4 qualification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_mini_installer_bundle import build, check_bundle, DEFAULT_EDITOR

DEFAULT_OUTPUT = ROOT / "build/hyperrig-mini-installer-one-switch-preview"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build", type=Path, nargs="?", const=DEFAULT_OUTPUT)
    action.add_argument("--check-only", type=Path)
    parser.add_argument("--editor", type=Path, default=DEFAULT_EDITOR)
    parser.add_argument("--executable", action="store_true")
    args = parser.parse_args(argv)
    if args.executable and not args.build:
        parser.error("--executable is a build option")
    result = (build(args.build, editor=args.editor, executable=args.executable, variant="v4")
              if args.build else check_bundle(args.check_only))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
