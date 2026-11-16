"""Durable, per-device installation workflow with an injected hardware backend."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading

from .core import plan_install, validate_completed


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
        return self._action({"created"}, run)

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
