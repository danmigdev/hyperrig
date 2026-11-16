"""Restore after a user-assisted cold ROM entry; never resend failed UBOOT."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import restore_mini_stock_live as base
from hyperrig.installer.cold_rom import ColdRomBackend
from hyperrig.installer.restoration import RestorationWorkflow


def run(observation, output):
    release, stock, prepared = base.prepare(base.stages.DEFAULT_BUNDLE)
    output = base.stages.session_path(output)
    evidence = base.read_shared_json(observation)
    workflow = RestorationWorkflow(release, ColdRomBackend(evidence), output, stock)
    workflow.notify = lambda value: base.atomic_write_json(output / "status.json", value)
    try:
        workflow.store.save_json("preflight.json", prepared)
        workflow.store.save_json("cold-entry-evidence.json", evidence)
        workflow.backup("user-confirmed-cold-rom")
        base.stages.wait_request(workflow, "restore.request", {"plan_sha256": workflow.prepared.installation.plan_sha256})
        verified = workflow.install()
        base.stages.wait_request(workflow, "boot.request", {"full_after_sha256": verified["full_readback_sha256"]})
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"device_io": False, "software_UBOOT_sent": False}))
        return
    base.core._require(args.observation is not None and args.output is not None,
                       "Explicit cold-start observation and new output directory required")
    print(json.dumps(run(args.observation, args.output), indent=2))


if __name__ == "__main__":
    main()
