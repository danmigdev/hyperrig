"""Offline v3-to-v4 builder for any-one-footswitch entry recovery.

The shared implementation verifies the existing v3 before assembling only the
small guard. It emits a separate application, manifests and reverse proof; it
does not access hardware or update the installer's approved firmware.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_mini_entry_recovery_one import main


if __name__ == "__main__":
    main()
