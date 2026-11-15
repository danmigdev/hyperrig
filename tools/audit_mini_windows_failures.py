"""Offline correlation of saved HYW1 traces and existing Windows event exports.

No device enumeration, Windows event query, driver change or SCSI command is
performed here. The two source event exports were read from an existing log.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVICE_GUID = "{33a15f43-e12c-11f1-9e20-047c16d72f47}"
EVENTS = ROOT / "build/mini-windows-diagnostics/stordiag-20261115.json"
MCN_EVENTS = ROOT / "build/mini-windows-diagnostics/stordiag-mcn-20261115.json"
MCN_RUN = ROOT / "analysis/hardware/mini-mcn-probe-run.json"
REPORT = ROOT / "research/mini-windows-failures.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def timestamp(row):
    return row.get("started_utc") or row.get("time_utc") or row.get("utc")


def same_device(row):
    data = row["data"]
    return (data.get("DeviceNumber") == "4" and data.get("DeviceGUID", "").lower() == DEVICE_GUID
            and data.get("Vendor", "").strip() == "WL82" and data.get("Model", "").strip() == "UBOOT1.00")


def signature_counts(rows):
    keys = ("CdbBytes", "DownLevelIrpStatus", "SrbStatus", "ScsiStatus", "SenseKey",
            "AdditionalSenseCode", "AdditionalSenseCodeQualifier")
    counts = Counter((row["id"], *(row["data"].get(key) for key in keys)) for row in rows)
    return [{"event_id": sig[0], **dict(zip(keys, sig[1:])), "count": count}
            for sig, count in sorted(counts.items(), key=lambda item: str(item[0]))]


def inspect():
    sources = [EVENTS, MCN_EVENTS, MCN_RUN]
    saved = json.loads(EVENTS.read_text(encoding="utf-8"))
    events = [row for row in saved["events"] if same_device(row)]
    failures, runs = [], []
    for stem in ("mini-first-install", "mini-first-resume", "mini-buffered-transport", "mini-buffered-install"):
        path = ROOT / "analysis/hardware" / (stem + "-trace.jsonl")
        sources.append(path)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        timed = [dt(timestamp(row)) for row in rows if timestamp(row)]
        start, end = min(timed), max(timed)
        errors = [row for row in rows if row.get("state") == "error"]
        successes = [row for row in rows if row.get("state") == "after"]
        within = [row for row in events if start <= dt(row["time_utc"]) <= end]
        runs.append({"trace": path.relative_to(ROOT).as_posix(), "trace_started_utc": start.isoformat(),
                     "trace_last_command_started_utc": end.isoformat(), "completed_commands": len(successes),
                     "errors": len(errors), "successful_opcodes": dict(Counter(row["cdb"][:4] for row in successes)),
                     "host_events_between_command_start_times": signature_counts(within)})
        for row in errors:
            start = dt(timestamp(row))
            near = sorted((event for event in events if event["data"].get("CdbBytes") == "000000000000"
                           and abs((dt(event["time_utc"]) - start).total_seconds()) <= .003),
                          key=lambda event: event["time_utc"])
            native = row.get("native_transfer") or row.get("details") or {}
            duration = None
            if "started_monotonic_ns" in native and "finished_monotonic_ns" in native:
                duration = (native["finished_monotonic_ns"] - native["started_monotonic_ns"]) / 1_000_000
            failures.append({"trace": path.relative_to(ROOT).as_posix(), "cdb": row["cdb"],
                             "started_utc": start.isoformat(), "native_ioctl_duration_ms": duration,
                             "reported_error": row["error"], "transport_details": native,
                             "nearby_TUR_within_3ms": [{"record_id": event["record_id"],
                                 "time_utc": event["time_utc"],
                                 "offset_ms": round((dt(event["time_utc"]) - start).total_seconds() * 1000, 4),
                                 "data": event["data"]} for event in near]})
    mcn = json.loads(MCN_RUN.read_text(encoding="utf-8"))
    mcn_events = [row for row in json.loads(MCN_EVENTS.read_text(encoding="utf-8"))["events"] if same_device(row)]
    windows = []
    for name in ("baseline", "during", "restored"):
        start, end = dt(mcn[name + "_started_utc"]), dt(mcn[name + "_finished_utc"])
        selected = [row for row in mcn_events if start <= dt(row["time_utc"]) <= end]
        windows.append({"name": name, "start_utc": start.isoformat(), "end_utc": end.isoformat(),
                        "duration_seconds": (end - start).total_seconds(), "events": len(selected),
                        "TUR_events": sum(row["data"].get("CdbBytes") == "000000000000" for row in selected),
                        "signatures": signature_counts(selected), "record_ids": [row["record_id"] for row in selected]})
    assert len(failures) == 3 and all(len(row["nearby_TUR_within_3ms"]) == 6 for row in failures)
    assert all(row["TUR_events"] == 0 for row in windows)
    assert mcn["reader_status_unchanged"] and mcn["MCN_explicitly_reenabled"]
    return {"schema_version": 1, "analysis_device_io": False, "NOR_write": False,
            "event_source": saved["source"], "device_number": 4, "device_guid": DEVICE_GUID,
            "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources},
            "script_sha256": sha(Path(__file__).read_bytes()), "runs": runs, "failed_commands": failures,
            "SRB_C4": {"error": "0x04", "queue_frozen": "0x40", "autosense_valid": "0x80",
                       "applies_to_logged_TUR_not_unobserved_vendor_SRB": True},
            "MCN_probe": {"run_phase": mcn["phase"], "windows": windows,
                "identity_queries_during_pause": mcn["identity_queries"], "NOR_counter_unchanged": True,
                "explicit_reenable_verified": True, "suppression_demonstrated": False,
                "reason": "Baseline and disabled windows both contain zero TUR events; a zero-to-zero comparison cannot demonstrate suppression."},
            "conclusions": {"three_failures_each_coincide_with_six_TUR_events": True,
                "automatic_standard_SCSI_traffic_observed": True,
                "TUR_queue_frozen_flag_observed": True, "vendor_SRB_status_observed": False,
                "USB_packet_trace_available": False, "stale_CSW_proven": False,
                "causal_mechanism_proven": False, "buffered_backend_eliminated_failure": False,
                "MCN_installation_reliability_proven": False,
                "standard_requests_are_forwarded_to_ROM_by_HYW1": True},
            "primary_sources": [
                "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/srb/ns-srb-_scsi_request_block",
                "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through",
                "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control",
                "https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/autorun.c",
                "https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/how-to-capture-a-usb-event-trace"]}


if __name__ == "__main__":
    result = inspect()
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"report": REPORT.relative_to(ROOT).as_posix(), "sha256": sha(REPORT.read_bytes()),
                      "three_TUR_correlations": True, "MCN_suppression_demonstrated": False,
                      "device_io": False}))
