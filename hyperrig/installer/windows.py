"""Explicit Windows stock-MINI USB backend using the reviewed ROM transports."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import subprocess
import time

from hyperrig.device import ReadOnlyMini, ports
from tools.install_mini_app import MiniAppInstallerSession
from tools.mini_nor_read_recovery import NorReadRecoveryTransport
from tools.mini_windows_mcn import MiniMediaChangePause
from tools.mini_windows_quiet import QuietBufferedRomTransport, RomDiskAttestation
from tools.probe_mini_recovery import (
    MiniNorSession, MiniRamSession, SOFT_KEY_SYSEX, discover_windows_rom_disks,
)
from tools.recover_mini_read_v6 import BoundedCommandRecoveryTransport

A, B = 0x01C20000, 0x01C28000
CAPACITY = 0x100000


def require(value, message):
    if not value:
        raise ValueError(message)


def is_admin():
    return os.name == "nt" and bool(ctypes.windll.shell32.IsUserAnAdmin())


def stock_devices():
    """Read metadata for whole stock USB devices, excluding composite children."""
    require(os.name == "nt", "This installer preview supports Windows only")
    script = r"""$ErrorActionPreference = 'Stop'
$devices = @(Get-PnpDevice -PresentOnly | Where-Object {
    $_.InstanceId -match '^USB\\VID_4C4A&PID_C755\\'
} | ForEach-Object {
    [pscustomobject]@{instance_id=$_.InstanceId; status=$_.Status}
})
ConvertTo-Json -InputObject $devices -Compress
"""
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                            capture_output=True, text=True, check=True, timeout=45,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    return json.loads(result.stdout)


def hyperrig_ports():
    from serial.tools.list_ports import comports
    return [{"device": item.device, "vid": item.vid, "pid": item.pid}
            for item in comports() if (item.vid, item.pid) == (0x3654, 0x5155)]


def scan():
    return {**ports(), "stock_devices": stock_devices(), "hyperrig_ports": hyperrig_ports()}


class WindowsBackend:
    def __init__(self):
        self.attestation = None
        self.live_slot = None
        self.jump_unknown = False
        self.jedec_hex = None
        self.reader = self.reader_wrapper = self.reader_transport = None
        self.mcn = None
        self.store = None
        self.command_number = 0
        self._mutex = self._mutex_api = None

    def _claim_host_session(self):
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        api.CreateMutexW.restype = ctypes.c_void_p
        api.CloseHandle.argtypes, api.CloseHandle.restype = [ctypes.c_void_p], ctypes.c_int
        handle = api.CreateMutexW(None, False, "Local\\HyperRigMiniInstallerSession")
        error = ctypes.get_last_error()
        if not handle:
            raise OSError(error, "Cannot reserve the HyperRig installation session")
        if error == 183:
            api.CloseHandle(handle)
            raise ValueError("Another HyperRig installation session is already open")
        self._mutex, self._mutex_api = handle, api

    def _event(self, item):
        item = dict(item)
        name = item.pop("event", "transport_observation")
        self.store.event(name, **item)

    def _open(self, slot, profile):
        transport = QuietBufferedRomTransport(self.attestation, slot=slot, profile=profile)
        self.attestation = transport.attestation
        original = transport.exchange

        def exchange(cdb, data_out=None, read_length=0):
            time.sleep(0.005)
            opcode = int.from_bytes(cdb[:2], "big")
            self.command_number += 1
            number = self.command_number
            if opcode == 0xFB08:
                require(self.live_slot != slot and not self.jump_unknown,
                        "A RAM jump needs a known inactive slot")
                self.jump_unknown = True
                self.live_slot = None
            self.store.event("usb_command_intent", command_number=number, profile=profile,
                             opcode=f"{opcode:04x}", cdb_hex=cdb.hex(),
                             slot=slot, out_bytes=len(data_out) if data_out else 0, in_bytes=read_length,
                             data_out_sha256=hashlib.sha256(data_out).hexdigest() if data_out is not None else None)
            try:
                raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                self.store.event("usb_command_error", command_number=number,
                                 opcode=f"{opcode:04x}", error=str(error))
                raise
            if opcode == 0xFC73:
                transport.last_reader_status_raw = raw
            # Page contents and complete dumps stay in private local files.
            self.store.event("usb_command_reply", command_number=number, opcode=f"{opcode:04x}",
                             bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                             response_hex=raw.hex() if len(raw) <= 128 else None)
            return raw

        transport.exchange = exchange
        return transport

    def enter_stock_rom(self, selection, release, store):
        self.store = store
        require(is_admin(), "Administrator access is required for ROM USB; reopen with Windows UAC")
        require(self.attestation is None, "Start a new workflow for a new pedal")
        self._claim_host_session()
        require(not discover_windows_rom_disks(), "A device is already in ROM; fresh stock entry is required")
        require(not hyperrig_ports(), "This workflow starts from stock. A HyperRig pedal is already connected")
        devices = stock_devices()
        require(len(devices) == 1 and devices[0]["status"] == "OK",
                "Connect exactly one healthy stock MINI before continuing")
        current_ports = ports()
        for direction, index_key, name_key in (("inputs", "input_index", "input_name"),
                                                ("outputs", "output_index", "output_name")):
            index = selection[index_key]
            require(type(index) is int and 0 <= index < len(current_ports[direction])
                    and current_ports[direction][index] == selection[name_key],
                    "The MIDI port list changed; scan and select it again")
        with ReadOnlyMini(selection["input_index"], selection["output_index"]) as device:
            require(device.identity == release.manifest["stock_identity"], "Unsupported stock identity")
            device.backup(store.root / "stock-presets")
            # Send the soft key on the same open output that answered identity.
            require(stock_devices() == devices and not discover_windows_rom_disks(),
                    "USB device selection changed during identification")
            identity = device.identity
            submitted = time.time()
            store.event("stock_to_rom_intent", identity=identity, stock_device=devices[0],
                        submitted_unix=submitted, automatic_retry=False)
            device.midi_out.send_message(list(SOFT_KEY_SYSEX))
            time.sleep(0.1)
        deadline = time.monotonic() + 45
        candidates = []
        while time.monotonic() < deadline:
            candidates = discover_windows_rom_disks()
            if candidates:
                break
            time.sleep(1)
        require(len(candidates) == 1, "The MINI did not appear as one ROM disk; no command was repeated")
        require(not stock_devices(), "Stock USB is still present; ROM entry is not uniquely established")
        self.attestation = RomDiskAttestation.from_discovery(candidates[0])
        with self._open(B, "nor-reader") as transport:
            arrival = transport.attestation.last_arrival_filetime
            require(arrival is not None and arrival / 10_000_000 - 11644473600 >= submitted - 1,
                    "ROM arrival predates this installation session")
            self.mcn = MiniMediaChangePause(transport, log=self._event)
        store.event("fresh_rom_verified", attestation=self.attestation.summary())
        return identity

    def _reopen_reader(self):
        require(self.live_slot == B and not self.jump_unknown, "Reader lifecycle changed")
        return self._open(B, "nor-reader")

    def _close_reader(self):
        if self.reader_wrapper is not None:
            self.reader_wrapper.close()
        elif self.reader_transport is not None:
            self.reader_transport.close()
        self.reader = self.reader_wrapper = self.reader_transport = None

    def _start_reader(self, release):
        require(self.live_slot in (None, A) and not self.jump_unknown, "Reader B is not known inactive")
        self.reader_transport = transport = self._open(B, "nor-reader")
        self.reader = reader = MiniNorSession(transport, slot=B, known_free_slot=True)
        reader.upload_and_start(release.reader, expected_sha256=release.manifest["reader"]["sha256"])
        self.live_slot, self.jump_unknown = B, False
        self.jedec_hex = reader.initialize_spi()["jedec_hex"]
        require(self.jedec_hex == release.manifest["jedec_hex"], "Unsupported MINI flash chip")
        self.reader_wrapper = NorReadRecoveryTransport(transport, log=self._event,
                                                      reopen_factory=self._reopen_reader, max_recoveries=8)
        self.reader_wrapper.bind_session(reader, status_raw=transport.last_reader_status_raw)

    def read_full(self, release, store, progress, label):
        require(store is self.store, "The installation journal changed")
        if self.reader is None:
            self._start_reader(release)
        require(self.live_slot == B and not self.jump_unknown, "Full read requires a known live reader")
        reader = self.reader
        reader._handshake()
        reader._status(reader.successful_bytes)
        before = reader.successful_bytes
        lost_before = self.reader_wrapper.lost_read_bytes

        def update(done, total):
            if done % 8192 == 0 or done == total:
                progress(label, done, total)

        data = reader.read_flash(0, CAPACITY, progress=update)
        missed = self.reader_wrapper.lost_read_bytes - lost_before
        require(reader.successful_bytes == before + CAPACITY + missed,
                "Physical reader counter does not match the complete flash read")
        store.event("complete_flash_read", label=label, bytes=len(data),
                    physical_counter=reader.successful_bytes, reconciled_lost_bytes=missed)
        return data

    def write_application(self, installation, store, progress):
        require(self.live_slot == B and not self.jump_unknown and self.reader is not None,
                "Verified reader B must precede the writer")
        self.reader._handshake()
        self.reader._status(self.reader.successful_bytes)
        self._close_reader()
        transport = self._open(A, "app-writer-operational")

        def reopen():
            require(self.live_slot == A and not self.jump_unknown, "Writer lifecycle changed")
            return self._open(A, "app-writer-operational")

        wrapper = writer = None
        count = 0

        def journal(item):
            nonlocal count
            self._event(item)
            if item["event"] == "sector_verified":
                count += 1
                progress("writing", count, len(installation.sector_order))

        try:
            wrapper = BoundedCommandRecoveryTransport(transport, log=self._event,
                                                      reopen_factory=reopen, max_recoveries=32)
            writer = MiniAppInstallerSession(wrapper, installation, journal=journal, known_free_slot=True)
            wrapper.bind_session(writer)
            writer.upload_and_start(installation.image, expected_sha256=installation.image_sha256)
            self.live_slot, self.jump_unknown = A, False
            writer.initialize_spi()
            writer.verify_complete_preimage()
            result = writer.install_application()
            require(writer.image_verified and not writer.failed, "Application verification did not complete")
            store.event("writer_complete", result=result)
        finally:
            try:
                if writer is not None:
                    store.event("writer_terminal_state", phase=writer.phase, failed=writer.failed,
                                image_verified=writer.image_verified, preimage_verified=writer.preimage_verified,
                                verified_sectors=writer.verified_sectors, last_audit=writer.last_audit,
                                last_status=writer.last_status, mutation_command_submitted=writer.mutation_command_submitted,
                                mutation_completion_unknown=writer.mutation_completion_unknown,
                                ambiguous_operation=writer.ambiguous_operation,
                                live_slot=self.live_slot, jump_unknown=self.jump_unknown)
            finally:
                (wrapper if wrapper is not None else transport).close()

    def boot(self, release, store, *, expected):
        require(expected in ("stock", "hyperrig"), "Unknown boot target")
        require(self.live_slot == B and not self.jump_unknown and self.reader is not None,
                "Boot requires the retained final verification reader")
        self.reader._handshake()
        self.reader._status(self.reader.successful_bytes)
        require(not hyperrig_ports() and not stock_devices(), "Unexpected application USB before reset")
        self._close_reader()
        if self.mcn is not None:
            self.mcn.close()
            self.mcn = None
        with self._open(A, "ram-probe") as transport:
            session = MiniRamSession(transport, slot=A, known_free_slot=True)
            session.upload_only(release.reset, expected_sha256=release.manifest["reset"]["sha256"])
            result = session.start_reset_once(release.reset, elf=release.reset_elf,
                                              manifest=release.reset_contract)
            store.event("reset_submitted_once", result=result)
        deadline = time.monotonic() + 60
        devices = []
        while time.monotonic() < deadline:
            devices = hyperrig_ports() if expected == "hyperrig" else stock_devices()
            if devices:
                break
            time.sleep(1)
        require(len(devices) == 1, "Application USB was not uniquely observed; reset will not be repeated")
        self.live_slot, self.jump_unknown = None, False
        return {"expected_application": expected, "USB_observed": True, "devices": devices,
                "firmware_handshake_verified": False, "audio_verified": False,
                "cold_boot_recovery_tested": False, "reset_attempts": 1}

    def close(self):
        try:
            self._close_reader()
        finally:
            try:
                if self.mcn is not None:
                    pause, self.mcn = self.mcn, None
                    pause.close()
            finally:
                if self._mutex is not None:
                    handle, self._mutex = self._mutex, None
                    self._mutex_api.CloseHandle(handle)
