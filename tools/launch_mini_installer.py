"""Launch the portable HyperRig MINI installer; --check-only never opens a device."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-only", action="store_true")
    mode.add_argument("--editor", action="store_true")
    mode.add_argument("--gui-smoke-output", type=Path)
    parser.add_argument("--admin", action="store_true")
    parser.add_argument("--backup-directory", type=Path)
    args = parser.parse_args()
    default = Path(sys.executable).parent if getattr(sys, "frozen", False) else ROOT
    if not (default / "release.json").exists() and not args.bundle:
        default = ROOT / "build" / "hyperrig-mini-installer-preview"
    bundle = (args.bundle or default).resolve()
    from tools.build_mini_installer_bundle import check_bundle
    package = check_bundle(bundle, isolated=False)
    from hyperrig.installer.core import load_release
    release = load_release(bundle)
    if args.check_only:
        print(json.dumps({"name": "HyperRig MINI installer preview", "target": "tank-mini",
                          "firmware_sha256": release.manifest["firmware"]["sha256"],
                          "device_io": False, "package": package,
                          "qualification": release.manifest["qualification"]}, indent=2))
        return
    from hyperrig.installer.gui import InstallerWindow
    if args.admin:
        from hyperrig.installer.windows import is_admin
        if not is_admin():
            raise RuntimeError("Windows administrator access was not granted")
    window = InstallerWindow(bundle, backup_directory=args.backup_directory,
                             smoke=args.gui_smoke_output is not None)
    if args.gui_smoke_output:
        window.root.after(150, lambda: window.smoke_report(args.gui_smoke_output))
    elif args.editor:
        window.root.after(150, window.open_editor)
    window.root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if getattr(sys, "frozen", False) and sys.stdout is None:
            import tkinter.messagebox
            tkinter.messagebox.showerror("HyperRig", str(error))
        else:
            print(f"HyperRig: {error}", file=sys.stderr)
        raise SystemExit(1)
