"""Durable, per-device installation workflow with an injected hardware backend."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time
import re

from .core import plan_install, validate_completed, STOCK_IDENTITY, _sha, _require


def interrupted_stock_entry(directory, *, timestamp=None):
    """Accept only a recent stock entry that stopped before any ROM command."""
    root = Path(directory).resolve(strict=True)
    journal = (root / "journal.jsonl").read_bytes()
    _require(len(journal) <= 128 * 1024, "Previous entry journal exceeds its bound")
    events = [json.loads(line) for line in journal.splitlines()]
    allowed = {"session_created", "phase", "stock_midi_input_closed_before_transition",
               "stock_to_rom_intent", "session_failed"}
    _require(events and all(isinstance(event, dict) and event.get("event") in allowed for event in events),
             "Only a stopped entry with no ROM access can continue")
    starts = [event for event in events if event["event"] == "session_created"]
    intents = [event for event in events if event["event"] == "stock_to_rom_intent"]
    failures = [event for event in events if event["event"] == "session_failed"]
    phases = [event["phase"] for event in events if event["event"] == "phase"]
    _require(len(starts) == len(intents) == len(failures) == 1 and phases == ["identifying"]
             and events[0] == starts[0] and events[-1] == failures[0] and failures[0]["failed_phase"] == "identifying",
             "Previous session did not stop during stock entry")
    intent = intents[0]
    _require(intent["identity"] == STOCK_IDENTITY and intent["stock_device"]["status"] == "OK",
             "Previous stock identity is unsupported")
    instance = intent["stock_device"]["instance_id"]
    _require(isinstance(instance, str) and re.fullmatch(r"USB\\VID_4C4A&PID_C755\\[A-Za-z0-9&_.-]+", instance, re.I),
             "Invalid previous stock USB identity")
    submitted = intent["submitted_unix"]
    _require(type(submitted) in (int, float) and 0 <= (time.time() if timestamp is None else timestamp) - submitted <= 1800,
             "Previous USB entry is older than 30 minutes; a fresh stock entry is required")
    presets = (root / "stock-presets" / "presets.bin").read_bytes()
    info = json.loads((root / "stock-presets" / "presets.json").read_bytes())
    _require(len(presets) == 1942 and info["identity"] == STOCK_IDENTITY and info["equal_reads"] == 2
             and info["bytes"] == len(presets) and info["sha256"] == _sha(presets),
             "Previous preset backup is incomplete or changed")
    from hyperrig.mini import decode_table
    decode_table(presets)
    return {"source_directory": str(root), "source_journal_sha256": _sha(journal),
            "source_release_sha256": starts[0]["release_sha256"], "identity": STOCK_IDENTITY,
            "stock_instance_id": instance, "submitted_unix": submitted,
            "preset_sha256": _sha(presets)}


def now():
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    """Exclusive local session; backups and journals never leave this directory."""

    def __init__(self, destination):
        self.root = Path(destination).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        self._stream = (self.root / "journal.jsonl").open("x", encoding="utf-8", newline="\n")
        self._lock = threading.Lock()

    def event(self, event, **fields):
        record = {"utc": now(), "event": event, **fields}
        with self._lock:
            self._stream.write(json.dumps(record, sort_keys=True) + "\n")
            self._stream.flush()
            os.fsync(self._stream.fileno())
        return record

    def save_bytes(self, name, data):
        if Path(name).name != name:
            raise ValueError("Session output must be a plain filename")
        with (self.root / name).open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    def save_json(self, name, value):
        self.save_bytes(name, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8"))

    def close(self):
        self._stream.close()


class InstallWorkflow:
    """Backup, review, install, verify, and boot are separate explicit actions.

    Any failed action ends this session. No automatic reset, rollback, or new
    installation is attempted. Transport reconciliation remains in the reviewed
    backend and cannot turn an unknown mutation into a blind retry.
    """

    def __init__(self, release, backend, destination, *, notify=None):
        self.release, self.backend = release, backend
        self.store = SessionStore(destination)
        self.notify = notify or (lambda event: None)
        self.phase = "created"
        self.prepared = None
        self._busy = threading.Lock()
        self._closed = False
        self.store.event("session_created", release_sha256=release.manifest_sha256,
                         hardware_tests_claimed=False, automatic_rollback=False)

    def _phase(self, phase, message):
        self.store.event("phase", phase=phase)
        self.phase = phase
        self.notify({"phase": phase, "message": message})

    def progress(self, stage, done, total):
        self.notify({"phase": self.phase, "stage": stage, "done": done, "total": total})

    def _action(self, expected, operation):
        if not self._busy.acquire(blocking=False):
            raise ValueError("An installation action is already running")
        try:
            if self._closed:
                raise ValueError("The installation session is closed")
            if self.phase not in expected:
                raise ValueError(f"Action unavailable in state {self.phase}")
            try:
                return operation()
            except Exception as error:
                failed_phase = self.phase
                self.phase = "failed"
                try:
                    self.store.event("session_failed", failed_phase=failed_phase,
                                     error_type=type(error).__name__, message=str(error),
                                     automatic_reset=False, automatic_retry=False)
                finally:
                    self.backend.close()
                self.notify({"phase": "failed", "message": str(error)})
                raise
        finally:
            self._busy.release()

    def backup(self, selection):
        def run():
            self._phase("identifying", "Checking the selected stock MINI")
            identity = self.backend.enter_stock_rom(selection, self.release, self.store)
            return self._save_full_backups(identity)
        return self._action({"created"}, run)

    def continue_backup(self, source):
        def run():
            entry = interrupted_stock_entry(source)
            _require(Path(entry["source_directory"]) != self.store.root, "Use a new session for continuation")
            self.store.save_json("continued-stock-entry.json", entry)
            origin = Path(entry["source_directory"])
            self.store.save_bytes("source-entry-journal.jsonl", (origin / "journal.jsonl").read_bytes())
            destination = self.store.root / "stock-presets"
            destination.mkdir()
            for name in ("presets.bin", "presets.json"):
                with (destination / name).open("xb") as stream:
                    stream.write((origin / "stock-presets" / name).read_bytes())
                    stream.flush()
                    os.fsync(stream.fileno())
            _require(interrupted_stock_entry(origin) == entry, "Previous entry changed during continuation")
            _require(_sha((self.store.root / "source-entry-journal.jsonl").read_bytes()) == entry["source_journal_sha256"]
                     and _sha((destination / "presets.bin").read_bytes()) == entry["preset_sha256"],
                     "Retained entry evidence changed")
            self._phase("identifying", "Checking the recovered USB connection")
            identity = self.backend.continue_stock_rom(entry, self.release, self.store)
            return self._save_full_backups(identity)
        return self._action({"created"}, run)

    def _save_full_backups(self, identity):
        self._phase("backing_up", "Reading two complete copies of this pedal's flash")
        first = self.backend.read_full(self.release, self.store, self.progress, "backup-a")
        self.store.save_bytes("stock-flash-a.bin", first)
        second = self.backend.read_full(self.release, self.store, self.progress, "backup-b")
        self.store.save_bytes("stock-flash-b.bin", second)
        self.prepared = plan_install(self.release, first, second, identity=identity,
                                     jedec_hex=self.backend.jedec_hex)
        self.store.save_json("installation-plan.json", self.prepared.record)
        self._phase("backed_up", "Two matching backups verified. Review before installing.")
        return self.prepared.record

    def install(self):
        def run():
            self._phase("checking_preimage", "Checking the pedal against its verified backup")
            fresh = self.backend.read_full(self.release, self.store, self.progress, "pre-install")
            if fresh != self.prepared.backup:
                raise ValueError("Flash changed after backup; no erase is allowed")
            self.store.save_bytes("full-before.bin", fresh)
            self._phase("installing", "Installing HyperRig; keep power and USB connected")
            self.backend.write_application(self.prepared.installation, self.store, self.progress)
            self._phase("verifying", "Reading the entire flash back and checking preserved data")
            after = self.backend.read_full(self.release, self.store, self.progress, "full-after")
            self.store.save_bytes("full-after.bin", after)
            result = validate_completed(self.prepared, after)
            self.store.save_json("verification.json", result)
            self._phase("verified", "Firmware and preserved data verified. Ready to boot HyperRig.")
            return result
        return self._action({"backed_up"}, run)

    def boot(self):
        def run():
            self._phase("booting", "Starting HyperRig; leave all footswitches released")
            result = self.backend.boot(self.release, self.store, expected="hyperrig")
            self.store.save_json("boot-observation.json", result)
            self._phase("usb_detected", "HyperRig USB detected. Open the editor to check audio and presets.")
            return result
        return self._action({"verified"}, run)

    def cancel_to_stock(self):
        def run():
            self._phase("checking_stock", "Checking that stock firmware is unchanged")
            fresh = self.backend.read_full(self.release, self.store, self.progress, "cancel-check")
            if fresh != self.prepared.backup:
                raise ValueError("Flash differs from the backup; automatic boot is blocked")
            result = self.backend.boot(self.release, self.store, expected="stock")
            self.store.save_json("stock-return-observation.json", result)
            self._phase("stock_usb_detected", "Stock USB detected. No firmware was written.")
            return result
        return self._action({"backed_up"}, run)

    def close(self):
        if not self._busy.acquire(blocking=False):
            raise ValueError("Wait for the current operation before closing")
        try:
            if self._closed:
                return
            self._closed = True
            try:
                self.backend.close()
            finally:
                self.store.close()
        finally:
            self._busy.release()
