"""Attach only to a fresh, user-confirmed cold-start ROM observation."""
from datetime import datetime
import time

from . import core, windows


class ColdRomBackend(windows.WindowsBackend):
    def __init__(self, evidence):
        super().__init__()
        core._require(isinstance(evidence, dict) and evidence.get("user_acknowledged_sequence") is True,
                      "Explicit user acknowledgement of the cold-start sequence is required")
        core._require(len(evidence.get("rom_disks", [])) == 1
                      and evidence.get("hyperrig_ports") == [] and evidence.get("stock_devices") == [],
                      "A single observed ROM without application USB is required")
        stamp = datetime.fromisoformat(evidence["requested_utc"])
        core._require(stamp.utcoffset() is not None, "Timezone-aware cold-start request required")
        self.requested = stamp.timestamp()
        self.observed = evidence["rom_disks"][0].copy()
        self.attempted = False

    def enter_hyperrig_rom(self, selection, release, store):
        core._require(selection == "user-confirmed-cold-rom", "Explicit cold-ROM selection required")
        core._require(windows.is_admin(), "Administrator access is required for ROM USB")
        core._require(not self.attempted and self.attestation is None, "Cold ROM was already attached")
        core._require(0 <= time.time() - self.requested <= 1800, "Cold-start observation is too old")
        self.attempted = True
        self.store = store
        self._claim_host_session()
        core._require(not windows.hyperrig_ports() and not windows.stock_devices(),
                      "Application USB is present; cold ROM is not uniquely established")
        current = windows.discover_windows_rom_disks()
        core._require(current == [self.observed], "The observed cold-ROM device changed")
        self.attestation = windows.RomDiskAttestation.from_discovery(current[0])
        with self._open(windows.B, "nor-reader") as transport:
            arrival = transport.attestation.last_arrival_filetime
            core._require(arrival is not None and arrival / 10_000_000 - 11644473600 >= self.requested,
                          "ROM arrival predates the requested cold start")
            self.mcn = windows.MiniMediaChangePause(transport, log=self._event)
        store.event("user_cold_rom_verified", attestation=self.attestation.summary(),
                    software_UBOOT_sent=False, physical_sequence_independently_observed=False)
