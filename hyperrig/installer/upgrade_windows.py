"""One native CDC ROM-entry request, followed by the existing ROM backend."""
from __future__ import annotations

import time

from . import core, windows
from tools import probe_mini_app_cdc_handshake as handshake

VERSION = "tankm_fw M5.71 rel ble"
PONG = "PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11"
require = core._require


class UpgradeWindowsBackend(windows.WindowsBackend):
    def __init__(self):
        super().__init__()
        self.entry_attempted = False

    def enter_hyperrig_rom(self, selection, release, store):
        require(windows.is_admin(), "Administrator access is required for ROM USB")
        require(not self.entry_attempted and self.attestation is None, "ROM entry already attempted")
        require(release.manifest["firmware"]["sha256"] == core.ONE_SWITCH_FIRMWARE_SHA256,
                "The upgrade target must be the exact v4 release")
        self.entry_attempted = True
        self.store = store
        self._claim_host_session()
        require(not windows.discover_windows_rom_disks() and not windows.stock_devices(),
                "Fresh HyperRig application entry is required")
        ports = windows.hyperrig_ports()
        require(len(ports) == 1 and ports[0]["device"] == selection,
                "Select the sole connected HyperRig USB port")
        transport = None
        try:
            store.event("cdc_open_intent", port=selection, dtr=True, rts=False)
            transport = handshake.host.HostOpenTransport.open(selection)
            time.sleep(1)
            _, result, attempts = handshake.identify(transport, VERSION, log=store.event)
            require(result["lines"] == [PONG], "Exact normal HyperRig PONG required before UBOOT")
            store.event("hyperrig_identity_verified", pong=PONG, attempts=len(attempts),
                        binary_hash_attested_by_device=False)
            require(windows.hyperrig_ports() == ports and not windows.discover_windows_rom_disks()
                    and not windows.stock_devices(), "USB selection changed before UBOOT")
            submitted = time.time()
            store.event("hyperrig_to_rom_intent", command="UBOOT", hex="55424f4f540a",
                        port=selection, submitted_unix=submitted, automatic_retry=False)
            try:
                written = transport.write(b"UBOOT\n")
            except OSError as error:
                # Reset may detach USB before write completion. Only fresh ROM
                # arrival can resolve this outcome; the command is never resent.
                store.event("uboot_write_error", error=str(error), outcome_unknown=True)
            else:
                store.event("uboot_write_complete", bytes=written)
                require(written == 6, "Incomplete UBOOT write; no retry")
            time.sleep(0.2)
        finally:
            if transport is not None:
                transport.close()
                store.event("cdc_closed")
        deadline = time.monotonic() + 45
        candidates = []
        while time.monotonic() < deadline:
            candidates = windows.discover_windows_rom_disks()
            if candidates:
                break
            time.sleep(1)
        require(len(candidates) == 1, "One fresh ROM disk was not observed; UBOOT will not be repeated")
        require(not windows.hyperrig_ports() and not windows.stock_devices(),
                "Application USB is still present; ROM selection is ambiguous")
        self.attestation = windows.RomDiskAttestation.from_discovery(candidates[0])
        with self._open(windows.B, "nor-reader") as transport:
            arrival = transport.attestation.last_arrival_filetime
            require(arrival is not None and arrival / 10_000_000 - 11644473600 >= submitted - 1,
                    "ROM arrival predates this upgrade session")
            self.mcn = windows.MiniMediaChangePause(transport, log=self._event)
        store.event("fresh_rom_verified", attestation=self.attestation.summary())
