"""Staged restoration of this development MINI; default is file-only preflight."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import upgrade_mini_one_switch as stages
from hyperrig.installer import core, restoration
from tools.mini_host_journal import atomic_write_json, read_shared_json


def prepare(bundle):
    release, package = stages.prepare(bundle)
    stock = (ROOT / restoration.frozen.BACKUP_PATH).read_bytes()
    core._require(core._sha(stock) == restoration.frozen.BACKUP_SHA, "Original unit backup changed")
    return release, stock, {"kind": "mini-stock-restoration-preflight", "transport_package": package,
                            "stock_backup_sha256": core._sha(stock), "target_app_sha256": core.STOCK_APP_SHA256,
                            "device_io": False, "automatic_boot": False}


def run(bundle, output, port):
    release, stock, prepared = prepare(bundle)
    output = stages.session_path(output)
    from hyperrig.installer.upgrade_windows import UpgradeWindowsBackend
    from hyperrig.installer.windows import is_admin
    core._require(is_admin(), "Launch the reviewed restoration worker with Windows UAC")
    workflow = restoration.RestorationWorkflow(release, UpgradeWindowsBackend(), output, stock)
    workflow.notify = lambda event: atomic_write_json(output / "status.json", event)
    try:
        workflow.store.save_json("preflight.json", prepared)
        workflow.backup(port)
        stages.wait_request(workflow, "restore.request", {"plan_sha256": workflow.prepared.installation.plan_sha256})
        verified = workflow.install()
        stages.wait_request(workflow, "boot.request", {"full_after_sha256": verified["full_readback_sha256"]})
        boot = workflow.boot()
        result = {"verification": verified, "boot": boot}
        workflow.store.save_json("completed.json", result)
        return result
    except Exception as error:
        workflow.store.event("worker_failed", error=str(error), automatic_reset=False, automatic_retry=False)
        workflow.notify({"phase": "failed", "message": str(error)})
        raise
    finally:
        workflow.close()


def request(output, action):
    output = stages.session_path(output)
    original = read_shared_json(output / "preflight.json")
    release, stock, preflight = prepare(Path(original["transport_package"]["bundle"]))
    core._require(preflight == original, "Restoration package changed")
    first = (output / "hyperrig-flash-a.bin").read_bytes()
    second = (output / "hyperrig-flash-b.bin").read_bytes()
    prepared = restoration.prepare_restoration(release, first, second, stock, jedec_hex=core.JEDEC_HEX)
    core._require((output / "restoration-plan.json").read_bytes() == prepared.plan_bytes, "Restoration plan changed")
    state = read_shared_json(output / "status.json")["phase"]
    if action == "restore":
        core._require(state == "backed_up", "Worker must be waiting after matching backups")
        name, binding = "restore.request", {"plan_sha256": prepared.installation.plan_sha256}
    else:
        core._require(action == "boot" and state == "verified", "Worker must be waiting after full verification")
        core._require((output / "full-before.bin").read_bytes() == first, "Third read differs from the backups")
        result = restoration.frozen.validate_restored_full(prepared, (output / "full-after.bin").read_bytes())
        core._require(result == read_shared_json(output / "verification.json"), "Final verification changed")
        name, binding = "boot.request", {"full_after_sha256": result["full_readback_sha256"]}
    core._require(not (output / name).exists(), "This stage has already been requested")
    atomic_write_json(output / name, binding)
    return {"requested": action, "binding": binding, "device_io_in_requester": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--execute", action="store_true")
    group.add_argument("--restore", action="store_true")
    group.add_argument("--boot", action="store_true")
    parser.add_argument("--bundle", type=Path, default=stages.DEFAULT_BUNDLE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--port", default="COM3")
    args = parser.parse_args(argv)
    if args.execute or args.restore or args.boot:
        core._require(args.output is not None, "A new dedicated session directory is required")
    if args.execute:
        value = run(args.bundle, args.output, args.port)
    elif args.restore or args.boot:
        value = request(args.output, "restore" if args.restore else "boot")
    else:
        _, _, value = prepare(args.bundle)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
