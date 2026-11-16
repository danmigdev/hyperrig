"""One UBOOT on a fresh application session, observing detach before close.

This keeps the earlier entry implementation and its failed evidence intact.
No reset, control-line toggle, reconnect, or repeated UBOOT is performed here.
"""
import time

from . import core, windows
from .upgrade_windows import PONG, VERSION
from tools import probe_mini_app_cdc_handshake as handshake


def observe_detach(transport, port, store, *, timeout=20):
    deadline = time.monotonic() + timeout
    count = 0
    while time.monotonic() < deadline:
        try:
            raw = transport.read(512)
        except OSError as error:
            store.event("cdc_read_ended_after_UBOOT", error=str(error), ROM_verified=False)
            return
        if raw:
            count += len(raw)
            core._require(count <= 4096, "Post-UBOOT response exceeds its bound")
            store.event("cdc_after_UBOOT", hex=raw.hex(), bytes=len(raw), ROM_verified=False)
        if not any(item["device"] == port for item in windows.hyperrig_ports()):
            store.event("cdc_absent_after_UBOOT", ROM_verified=False)
            return
        time.sleep(0.1)
    store.event("cdc_detach_not_observed_before_deadline", ROM_verified=False)


class ObservedRomEntryBackend(windows.WindowsBackend):
    def __init__(self):
        super().__init__()
        self.entry_attempted = False

    def enter_hyperrig_rom(self, selection, release, store):
        core._require(windows.is_admin(), "Administrator access is required for ROM USB")
        core._require(not self.entry_attempted and self.attestation is None, "ROM entry already attempted")
        core._require(release.manifest["firmware"]["sha256"] == core.ONE_SWITCH_FIRMWARE_SHA256,
                      "Pinned v4 transport package required")
        self.entry_attempted = True
        self.store = store
        self._claim_host_session()
        core._require(not windows.discover_windows_rom_disks() and not windows.stock_devices(),
                      "Fresh application USB entry required")
        ports = windows.hyperrig_ports()
        core._require(len(ports) == 1 and ports[0]["device"] == selection, "Select the sole HyperRig port")
        transport = None
        try:
            store.event("cdc_open_intent", port=selection, dtr=True, rts=False)
            transport = handshake.host.HostOpenTransport.open(selection)
            time.sleep(1)
            _, identity, attempts = handshake.identify(transport, VERSION, log=store.event)
            core._require(identity["lines"] == [PONG], "Exact normal HyperRig PONG required")
            core._require(windows.hyperrig_ports() == ports and not windows.discover_windows_rom_disks()
                          and not windows.stock_devices(), "USB selection changed before UBOOT")
            submitted = time.time()
            store.event("hyperrig_to_rom_intent", command="UBOOT", hex="55424f4f540a",
                        submitted_unix=submitted, automatic_retry=False, close_after_observation=True)
            try:
                count = transport.write(b"UBOOT\n")
            except OSError as error:
                store.event("uboot_write_error", error=str(error), outcome_unknown=True)
            else:
                core._require(count == 6, "Incomplete UBOOT write; no retry")
                store.event("uboot_write_complete", bytes=count)
            observe_detach(transport, selection, store)
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
        core._require(len(candidates) == 1, "One fresh ROM disk was not observed; no repeated UBOOT")
        core._require(not windows.hyperrig_ports() and not windows.stock_devices(),
                      "Application USB remains present; ROM is ambiguous")
        self.attestation = windows.RomDiskAttestation.from_discovery(candidates[0])
        with self._open(windows.B, "nor-reader") as transport:
            arrival = transport.attestation.last_arrival_filetime
            core._require(arrival is not None and arrival / 10_000_000 - 11644473600 >= submitted - 1,
                          "ROM arrival predates this request")
            self.mcn = windows.MiniMediaChangePause(transport, log=self._event)
        store.event("fresh_rom_verified", attestation=self.attestation.summary())
