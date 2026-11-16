"""Plan an approved MINI_009 application replacement without device I/O.

Only caller-supplied backups are used. No historical unit dump, unit plan,
research manifest, transport, reset, or firmware build is opened here. Matching
bytes establish a readback result, not boot, audio, or recovery qualification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.install_mini_app import Installation

CAPACITY = 0x100000
APP_START, APP_END = 0x4000, 0x82000
SECTOR_BYTES, PAGE_BYTES = 4096, 256
WRITER_SLOT, READER_SLOT, RESET_SLOT = 0x01C20000, 0x01C28000, 0x01C20000
STOCK_IDENTITY = "TANK MINI_009"
JEDEC_HEX = "eb6014"
FIRMWARE_SHA256 = "9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c"
ONE_SWITCH_FIRMWARE_SHA256 = "d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2"
WRITER_SHA256 = "09e0772b1c4f2087f6864fd16f09fa48ac5b0d2d46ab3e408e3d839447d51749"
WRITER_ELF_SHA256 = "39880f9272d2714d73bd165258288e5a63c9de305364cf8b723e59ee639835cd"
WRITER_BUILD_TAG = 3953063795
READER_SHA256 = "7a492bf17d98f0f5ca5d2fb0d0da7d369937169075507676bfb51b88c9bb2b83"
READER_ELF_SHA256 = "c59cff25df5c3e3bfe0d85392d9aa861e1fe287dc1f7d8afcf40e5f7575acf72"
RESET_SHA256 = "cf3526d914eef007649f88f1f22e085a908359b9ad0e9f4743427b4757c0540f"
RESET_ELF_SHA256 = "3a9aa6ba1c5043b548df3e521ffc82b2c2b58a4378d51d6eb3807feb51f0a081"

# Derived from flash.bin in the official FWSC, not from a private unit dump.
STOCK_FWSC_SHA256 = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
STOCK_SPL_SHA256 = "d9f43191777656de01c7bed4f9e9ba2e34e94832c5d2ed02c3fc7ab7a6d9bd67"
STOCK_APP_SHA256 = "11ade0ace13c48d1b633669ee8beae71d98a269690f1ffb93eb2c6ce14922eda"
QUALIFICATION_FLAGS = (
    "direct_stock_to_v3", "cold_boot_recovery", "interrupted_write_recovery",
)
FIRMWARE_VARIANTS = {
    FIRMWARE_SHA256: ("v3", QUALIFICATION_FLAGS),
    ONE_SWITCH_FIRMWARE_SHA256: ("v4", ("direct_stock_to_v4", "cold_boot_recovery", "interrupted_write_recovery")),
}
PRESERVED_REGIONS = (
    ("factory_SPL_and_boot_configuration", 0, APP_START),
    ("VM_including_factory_staged_updater", APP_END, 0xBE000),
    ("BTIF", 0xBE000, 0xBF000),
    ("USR", 0xBF000, 0xFF000),
    ("key_mac", 0xFF000, CAPACITY),
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        _require(key not in result, "Duplicate release JSON key: " + key)
        result[key] = value
    return result


def _manifest(raw: bytes) -> dict:
    _require(type(raw) is bytes and 0 < len(raw) <= 65536, "Release manifest size is invalid")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=lambda text: (_ for _ in ()).throw(ValueError(text)))
    except (UnicodeError, ValueError) as error:
        raise ValueError("Invalid release JSON: " + str(error)) from error
    _require(type(value) is dict, "Release manifest must be an object")
    _require(type(value.get("schema")) is int and value["schema"] == 1,
             "Unsupported release schema")
    for key, expected in (("project", "HyperRig"), ("target", "tank-mini"),
                          ("stock_identity", STOCK_IDENTITY), ("jedec_hex", JEDEC_HEX)):
        _require(value.get(key) == expected, "Unsupported release " + key)
    for key, expected in (("stock_usb", [0x4C4A, 0xC755]),
                          ("rom_usb", [0x4C4A, 0x8057]),
                          ("application_range", [APP_START, APP_END])):
        actual = value.get(key)
        _require(type(actual) is list and all(type(n) is int for n in actual)
                 and actual == expected, "Unsupported release " + key)
    firmware = value.get("firmware")
    _require(type(firmware) is dict and type(firmware.get("sha256")) is str
             and firmware["sha256"] in FIRMWARE_VARIANTS,
             "Unapproved release firmware")
    firmware_sha256 = firmware["sha256"]
    _, qualification_flags = FIRMWARE_VARIANTS[firmware_sha256]
    qualification = value.get("qualification")
    _require(type(qualification) is dict and set(qualification) == set(qualification_flags)
             and all(qualification[key] is False for key in qualification_flags),
             "Release qualification flags must remain explicitly false")
    specs = (("firmware", firmware_sha256, APP_END - APP_START, None),
             ("writer", WRITER_SHA256, 6432, WRITER_SLOT),
             ("reader", READER_SHA256, 2308, READER_SLOT),
             ("reset", RESET_SHA256, 26, RESET_SLOT))
    for key, digest, length, slot in specs:
        item = value.get(key)
        _require(type(item) is dict and item.get("sha256") == digest
                 and type(item.get("bytes")) is int and item["bytes"] == length,
                 "Unapproved release artifact: " + key)
        if slot is not None:
            _require(type(item.get("slot")) is int and item["slot"] == slot,
                     "Unapproved RAM slot: " + key)
    writer = value["writer"]
    _require(type(writer.get("build_tag")) is int and writer["build_tag"] == WRITER_BUILD_TAG
             and writer.get("elf_sha256") == WRITER_ELF_SHA256, "Unapproved writer build/ELF")
    _require(value["reset"].get("elf_sha256") == RESET_ELF_SHA256, "Unapproved reset ELF")
    reader = value["reader"]
    if "elf_path" in reader or "elf_sha256" in reader:
        _require("elf_path" in reader and reader.get("elf_sha256") == READER_ELF_SHA256,
                 "Unapproved reader ELF")
    return value


def _contained_file(root: Path, name: str) -> Path:
    _require(type(name) is str and bool(name) and "\\" not in name and ":" not in name,
             "Artifact path must be relative POSIX syntax")
    parts = name.split("/")
    _require(not PurePosixPath(name).is_absolute()
             and all(part not in ("", ".", "..") for part in parts),
             "Artifact path traversal is forbidden")
    try:
        path = root.joinpath(*parts).resolve(strict=True)
        _require(path.is_relative_to(root) and path.is_file(), "Artifact leaves the release bundle")
        return path
    except (OSError, RuntimeError) as error:
        raise ValueError("Release artifact is unavailable: " + name) from error


def _read_file(root: Path, name: str, limit: int) -> bytes:
    path = _contained_file(root, name)
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError as error:
        raise ValueError("Cannot read release artifact: " + name) from error
    _require(0 < len(raw) <= limit, "Release artifact exceeds its size limit: " + name)
    return raw


@dataclass(frozen=True)
class Release:
    """Validated immutable payloads; manifest returns a fresh JSON copy."""

    root: Path
    _manifest_raw: bytes
    firmware: bytes
    writer: bytes
    writer_elf: bytes
    reader: bytes
    reset: bytes
    reset_elf: bytes
    reader_elf: bytes | None = None

    @property
    def manifest(self) -> dict:
        return _manifest(self._manifest_raw)

    @property
    def manifest_sha256(self) -> str:
        return _sha(self._manifest_raw)

    @property
    def reset_contract(self) -> dict:
        return {"kind": "mini-ram-reset", "slot": RESET_SLOT, "entry": RESET_SLOT,
                "no_flash_writes": True, "image_bytes": 26,
                "image_sha256": RESET_SHA256, "elf_sha256": RESET_ELF_SHA256}


def _validate_release(release: Release, *, inspect_elf: bool) -> dict:
    _require(isinstance(release, Release), "A validated Release is required")
    manifest = release.manifest
    for key in ("firmware", "writer", "reader", "reset"):
        raw, item = getattr(release, key), manifest[key]
        _require(type(raw) is bytes and len(raw) == item["bytes"] and _sha(raw) == item["sha256"],
                 "Release artifact bytes/hash differ: " + key)
    for key in ("writer", "reset", "reader"):
        item, raw = manifest[key], getattr(release, key + "_elf")
        if "elf_sha256" not in item:
            _require(raw is None, "Unexpected reader ELF bytes")
            continue
        _require(type(raw) is bytes and 0 < len(raw) <= 131072
                 and _sha(raw) == item["elf_sha256"], "Release ELF hash differs: " + key)
    if inspect_elf:
        from tools.build_mini_app_writer_operational import inspect_operational_elf
        from tools.probe_mini_recovery import validate_reset_artifact

        payload, layout = inspect_operational_elf(release.writer_elf, WRITER_SLOT)
        _require(payload == release.writer and layout["mutation_gate_value"] == 1
                 and layout["memory_bytes"] <= 32768, "Writer ELF/payload layout differs")
        validate_reset_artifact(release.reset, release.reset_elf, release.reset_contract, slot=RESET_SLOT)
    return manifest


def load_release(bundle_path: Path) -> Release:
    """Read only release-local files; accept an explicitly pinned candidate."""
    try:
        root = Path(bundle_path).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError("Release bundle directory is unavailable") from error
    _require(root.is_dir(), "Release bundle must be a directory")
    raw = _read_file(root, "release.json", 65536)
    manifest = _manifest(raw)
    payloads = {key: _read_file(root, manifest[key].get("path"), manifest[key]["bytes"])
                for key in ("firmware", "writer", "reader", "reset")}
    for key in ("writer", "reset", "reader"):
        payloads[key + "_elf"] = (_read_file(root, manifest[key].get("elf_path"), 131072)
                                  if "elf_sha256" in manifest[key] else None)
    release = Release(root=root, _manifest_raw=raw, **payloads)
    _validate_release(release, inspect_elf=True)
    return release


@dataclass(frozen=True)
class PreparedInstall:
    """A unit-specific plan in memory, containing no device access capability."""

    release: Release
    installation: Installation
    backup: bytes
    expected_full: bytes
    _record_raw: bytes

    @property
    def record(self) -> dict:
        return json.loads(self._record_raw)


def _preserved(backup: bytes) -> list[dict]:
    return [{"name": name, "range": [start, end], "bytes": end - start,
             "sha256": _sha(backup[start:end])} for name, start, end in PRESERVED_REGIONS]


def _stock_backup(raw: bytes) -> None:
    _require(type(raw) is bytes and len(raw) == CAPACITY, "Each backup must be immutable full 1 MiB bytes")
    _require(_sha(raw[:APP_START]) == STOCK_SPL_SHA256, "Unknown stock SPL/boot configuration")
    _require(_sha(raw[APP_START:APP_END]) == STOCK_APP_SHA256, "Unknown stock MINI_009 application")


def plan_install(release: Release, backup_a: bytes, backup_b: bytes, *,
                 identity: str, jedec_hex: str) -> PreparedInstall:
    """Compare two supplied backups and plan only changed application sectors."""
    manifest = _validate_release(release, inspect_elf=True)
    _require(identity == STOCK_IDENTITY, "Expected exact stock identity TANK MINI_009")
    _require(type(jedec_hex) is str and jedec_hex.lower() == JEDEC_HEX, "Unsupported NOR JEDEC identity")
    _stock_backup(backup_a)
    _stock_backup(backup_b)
    _require(backup_a == backup_b, "The two full backups differ")
    from tools.install_mini_app import Installation
    from tools.build_mini_app_writer_operational import page_order

    preimage = backup_a[APP_START:APP_END]
    expected_full = backup_a[:APP_START] + release.firmware + backup_a[APP_END:]
    sectors = []
    for address in range(APP_START, APP_END, SECTOR_BYTES):
        offset = address - APP_START
        old, new = preimage[offset:offset + SECTOR_BYTES], release.firmware[offset:offset + SECTOR_BYTES]
        if old != new:
            sectors.append({"address": address, "bytes": SECTOR_BYTES,
                            "preimage_sha256": _sha(old), "candidate_sha256": _sha(new),
                            "page_order": page_order(address)})
    sectors.sort(key=lambda item: (item["address"] == APP_START, item["address"]))
    order = tuple(item["address"] for item in sectors)
    plan = {"schema": 1, "project": "HyperRig", "target": "tank-mini",
            "kind": "portable-stock-to-" + FIRMWARE_VARIANTS[manifest["firmware"]["sha256"]][0] + "-plan",
            "stock_identity": identity, "jedec_hex": JEDEC_HEX,
            "release_sha256": release.manifest_sha256,
            "candidate_sha256": manifest["firmware"]["sha256"], "application_range": [APP_START, APP_END],
            "backup_bytes": CAPACITY, "backup_a_sha256": _sha(backup_a), "backup_b_sha256": _sha(backup_b),
            "two_supplied_backups_identical": True, "physical_backup_acquisition_verified": False,
            "stock_reference": {"fwsc_sha256": STOCK_FWSC_SHA256, "SPL_sha256": STOCK_SPL_SHA256,
                                "application_sha256": STOCK_APP_SHA256},
            "expected_full_sha256": _sha(expected_full), "changed_sectors": len(order),
            "sector_order": list(order), "sectors": sectors,
            "header_sector_last": True, "header_page_last": True,
            "initial_header_invalidation": False, "power_loss_atomicity_proven": False,
            "preserved_regions": _preserved(backup_a),
            "factory_OTA_sha256": _sha(backup_a[0xB7000:0xBD000]),
            "qualification": manifest["qualification"], "device_access_performed": False,
            "automatic_reset": False, "automatic_rollback": False}
    plan_sha256 = _sha(_canonical(plan))
    installation = Installation(
        slot=WRITER_SLOT, build_tag=WRITER_BUILD_TAG, image=release.writer,
        image_sha256=WRITER_SHA256, elf_sha256=WRITER_ELF_SHA256,
        manifest_sha256=release.manifest_sha256, plan_sha256=plan_sha256,
        candidate=release.firmware, preimage=preimage, backup_sha256=_sha(backup_a), sector_order=order)
    record = {**plan, "plan_sha256": plan_sha256, "installation": installation.summary()}
    return PreparedInstall(release, installation, backup_a, expected_full, _canonical(record))


def validate_completed(prepared: PreparedInstall, full_after: bytes) -> dict:
    """Validate supplied final bytes; never infer boot, sound, or safe recovery."""
    _require(isinstance(prepared, PreparedInstall), "Prepared installation is required")
    _validate_release(prepared.release, inspect_elf=False)
    _stock_backup(prepared.backup)
    expected = prepared.backup[:APP_START] + prepared.release.firmware + prepared.backup[APP_END:]
    _require(prepared.expected_full == expected
             and prepared.installation.candidate == prepared.release.firmware
             and prepared.installation.preimage == prepared.backup[APP_START:APP_END]
             and prepared.installation.backup_sha256 == _sha(prepared.backup), "Prepared installation was changed")
    record = prepared.record
    plan = {key: value for key, value in record.items() if key not in ("plan_sha256", "installation")}
    _require(record.get("plan_sha256") == prepared.installation.plan_sha256 == _sha(_canonical(plan))
             and record.get("installation") == prepared.installation.summary()
             and record.get("expected_full_sha256") == _sha(expected), "Prepared record binding differs")
    _require(type(full_after) is bytes and len(full_after) == CAPACITY, "Final full 1 MiB read required")
    for name, start, end in PRESERVED_REGIONS:
        _require(full_after[start:end] == prepared.backup[start:end], "Final read changed preserved region: " + name)
    _require(full_after[APP_START:APP_END] == prepared.release.firmware, "Final application differs from approved firmware")
    _require(full_after == expected, "Final complete read differs from the planned image")
    return {"schema": 1, "project": "HyperRig", "target": "tank-mini",
            "kind": "portable-mini-completed-byte-validation", "verified": True,
            "validation_scope": "supplied-full-read-bytes-only", "plan_sha256": prepared.installation.plan_sha256,
            "release_sha256": prepared.release.manifest_sha256, "full_after_sha256": _sha(full_after),
            "bytes": CAPACITY, "application_exact": True, "external_regions_unchanged": True,
            "preserved_regions": _preserved(full_after), "qualification": prepared.release.manifest["qualification"],
            "device_access_performed": False, "boot_verified": False, "audio_verified": False}
