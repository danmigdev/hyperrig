"""Staged development upgrade: backup, explicit install request, explicit boot.

Default/check-only validates local release bytes without opening any device.
The elevated worker waits for plan-bound local requests between stages. No
timeout, failure, or process exit automatically boots or restores the pedal.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Existing pyserial/rtmidi packages, without processing user .pth files, also
# remain available when the administrative broker runs Python in isolated mode.
import site
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())

from hyperrig.installer import core, upgrade
from tools.mini_host_journal import atomic_write_json, read_shared_json

DEFAULT_BUNDLE = ROOT / "build/hyperrig-mini-installer-one-switch-preview-02"
require = core._require


def prepare(bundle):
    from tools.build_mini_installer_bundle import check_bundle
    checked = check_bundle(bundle, isolated=False)
    release = core.load_release(bundle)
    require(release.manifest["firmware"]["sha256"] == core.ONE_SWITCH_FIRMWARE_SHA256,
            "Exact one-switch v4 package required")
    return release, {"kind": "mini-one-switch-upgrade-preflight", "device_io": False,
                     "bundle": str(release.root), "package": checked,
                     "from_sha256": core.FIRMWARE_SHA256,
                     "to_sha256": core.ONE_SWITCH_FIRMWARE_SHA256,
                     "sector_order": list(upgrade.SECTOR_ORDER),
                     "automatic_install": False, "automatic_boot": False}


def session_path(value):
    path = Path(value).resolve()
    require(path.is_relative_to(ROOT / "build") and path != ROOT / "build",
            "A dedicated build session directory is required")
    return path


def wait_request(workflow, name, expected, *, timeout=1200):
    request = workflow.store.root / name
    workflow.store.event("waiting_for_stage", request=name, expected=expected)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if request.exists():
            require(request.is_file() and request.stat().st_size <= 1024, "Invalid stage request")
            require(read_shared_json(request) == expected, "Stage request binding differs")
            workflow.store.event("stage_requested", request=name, binding=expected)
            return
        if (workflow.store.root / "stop.request").exists():
            raise ValueError("Stopped between stages; the pedal remains in ROM")
        time.sleep(0.25)
    raise TimeoutError("Stage request deadline expired; the pedal remains in ROM")


def run(bundle, output, port):
    release, prepared = prepare(bundle)
    output = session_path(output)
    from hyperrig.installer.upgrade_windows import UpgradeWindowsBackend
    from hyperrig.installer.windows import is_admin
    require(is_admin(), "Launch the reviewed worker with Windows UAC")
    workflow = upgrade.UpgradeWorkflow(release, UpgradeWindowsBackend(), output)

    def notify(event):
        atomic_write_json(output / "status.json", event)

    workflow.notify = notify
    try:
        workflow.store.save_json("preflight.json", prepared)
        plan = workflow.backup(port)
        wait_request(workflow, "install.request", {"plan_sha256": plan["plan_sha256"]})
        result = workflow.install()
        wait_request(workflow, "boot.request", {"full_after_sha256": result["full_after_sha256"]})
        boot = workflow.boot()
        workflow.store.save_json("completed.json", {"verification": result, "boot": boot})
        return {"verification": result, "boot": boot}
    except Exception as error:
        workflow.store.event("worker_failed", error_type=type(error).__name__, error=str(error),
                             automatic_reset=False, automatic_retry=False)
        notify({"phase": "failed", "message": str(error)})
        raise
    finally:
        workflow.close()


def request_stage(output, action):
    """Recompute the complete on-disk plan/readback before requesting a stage."""
    output = session_path(output)
    preflight = read_shared_json(output / "preflight.json")
    release, prepared = prepare(Path(preflight["bundle"]))
    require(prepared == preflight, "Release changed since session creation")
    first = (output / "v3-flash-a.bin").read_bytes()
    second = (output / "v3-flash-b.bin").read_bytes()
    plan = upgrade.plan_upgrade(release, first, second, jedec_hex=core.JEDEC_HEX)
    require(read_shared_json(output / "installation-plan.json") == plan.record, "Stored upgrade plan differs")
    status = read_shared_json(output / "status.json")
    if action == "install":
        require(status["phase"] == "backed_up", "Worker is not waiting after matching backups")
        name, binding = "install.request", {"plan_sha256": plan.installation.plan_sha256}
    else:
        require(action == "boot" and status["phase"] == "verified", "Worker is not waiting after verification")
        require((output / "full-before.bin").read_bytes() == first, "Pre-install read differs from backups")
        result = upgrade.validate_completed(plan, (output / "full-after.bin").read_bytes())
        require(read_shared_json(output / "verification.json") == result, "Stored verification differs")
        name, binding = "boot.request", {"full_after_sha256": result["full_after_sha256"]}
    require(not (output / name).exists(), "Stage was already requested")
    atomic_write_json(output / name, binding)
    return {"requested": action, "binding": binding, "device_io_in_requester": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check-only", action="store_true")
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--install", action="store_true")
    modes.add_argument("--boot", action="store_true")
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--port", default="COM3")
    args = parser.parse_args(argv)
    if args.execute or args.install or args.boot:
        require(args.output is not None, "Explicit session output required")
    if args.execute:
        result = run(args.bundle, args.output, args.port)
    elif args.install or args.boot:
        result = request_stage(args.output, "install" if args.install else "boot")
    else:
        _, result = prepare(args.bundle)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
