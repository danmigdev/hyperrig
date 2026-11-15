"""Audit and compose a complete UltraRig-G-derived MINI application OFFLINE.

The candidate is a binary port work product, never an installation instruction.
It contains the entire G application, with individually asserted patches, and
MINI partition headers. It contains no bootloader or device-specific data.
No device, uploader, subprocess or network API is used here.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "upstream/pi32v2-isa"))
from hyperrig.jieli import crc16, enc, jlfs_entry, sfc, unpack_app, unpack_fwsc
from pi32v2isa import codec, table

G_PATH = "artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin"
G_SHA = "2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059"
MINI_PATH = "artifacts/tank-mini/TANK-MINI.fwsc"
MINI_SHA = "13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209"
BACKUP_PATH = "artifacts/my-mini-flash/20261115-paced-resume/flash-a.bin"
BACKUP_SHA = "72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180"
BOOT_SHA = "fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d"
FLASH_BASE, ENTRY, APP_OFFSET = 0x02000000, 0x02000120, 0x120
MINI_START, MINI_END = 0x4000, 0x82000
MINI_SIZE = MINI_END - MINI_START
G_PARTITIONS = {"VM": (0x7B000, 0xBD000), "PRCT": (0, 0x7B000),
                "BTIF": (0xBD000, 0xBE000), "OTP": (0xBE000, 0xBF000),
                "USR": (0xBF000, 0xFF000)}
MINI_PARTITIONS = {"VM": (0x82000, 0xBE000), "PRCT": (0, 0x82000),
                   "BTIF": (0xBE000, 0xBF000), "USR": (0xBF000, 0xFF000)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class BinaryPatch:
    """Equal-length, non-overlapping patch in the original G app CPU mapping."""
    name: str
    address: int
    before: bytes
    after: bytes
    rationale: str

    def record(self):
        return {"name": self.name, "cpu_address": self.address,
                "area_offset": self.address - FLASH_BASE,
                "physical_address": self.address - FLASH_BASE + MINI_START,
                "bytes": len(self.before), "before_hex": self.before.hex(),
                "after_hex": self.after.hex(), "rationale": self.rationale}


IDENTITY_PATCHES = (
    BinaryPatch("authentication_brand", 0x0203614A, b"UltraRig auth\0", b"HyperRig auth\0",
                "Same-sized user-visible brand; authentication algorithm is retained."),
    BinaryPatch("ble_name_format", 0x0203A123, b"UltraRig %02X%02X\0", b"HyperRig %02X%02X\0",
                "Same-sized advertising-name format; unique suffix is retained."),
    BinaryPatch("runtime_version", 0x0203678E, b"tankg_fw M5.71 rel ble\0", b"tankm_fw M5.71 rel ble\0",
                "MINI app handshake is ^PONG tankm_fw\\b; version fields are retained."),
    BinaryPatch("runtime_build_identity", 0x020370E8,
                b"tankg_fw M5.71 rel ble Nov 12 2026 16:04:11\0",
                b"tankm_fw M5.71 rel ble Nov 12 2026 16:04:11\0",
                "Same-sized board prefix; original build/version metadata is retained."),
    BinaryPatch("usb_product_utf16", 0x0203A264,
                b"\x20\x03" + "Tank-G UltraRig".encode("utf-16le"),
                b"\x20\x03" + "Tank-M HyperRig".encode("utf-16le"),
                "Length-32 USB string descriptor, including its original type/length."),
)
VM_PATCH = BinaryPatch(
    "mini_vm_geometry", 0x0202067E, bytes.fromhex("20e9800b60e0800b"),
    bytes.fromhex("20e9800c60e0800c"),
    "Change G's VM-size clamp from 64 KiB to MINI's 16 KiB: two 8 KiB banks, no VM migration.")


def decode_fragment(plain, start, end):
    isa, cursor, out = table.load(), start, []
    while cursor < end:
        result = codec.decode(isa, plain, cursor - FLASH_BASE)
        require(result is not None, f"undecodable instruction at {cursor:#x}")
        instruction, values, size = result
        require(cursor + size <= end, "instruction crosses fragment boundary")
        out.append({"address": cursor, "bytes": plain[cursor-FLASH_BASE:cursor-FLASH_BASE+size].hex(),
                    "assembly": codec.format(instruction, values)})
        cursor += size
    return out


def verify_vm_patch():
    """Change only the immediate field, retaining predicate/block/register bits."""
    isa = table.load()
    out = bytearray()
    records = []
    for offset in (0, 4):
        ins, fields, size = codec.decode(isa, VM_PATCH.before, offset)
        require(size == 4 and fields["r"] == 0 and codec.modimm(fields["n"]) == 65536,
                "VM clamp preimage instruction differs")
        require(ins.fields["n"].kind == "modimm", "VM immediate is not modified-immediate encoding")
        changed = dict(fields)
        changed["n"] = next(n for n in range(4096) if codec.modimm(n) == 16384)
        encoded = codec.encode(ins, changed)
        out += encoded
        ins2, fields2, size2 = codec.decode(isa, encoded)
        require(ins.id == ins2.id and size2 == size and fields2 == changed, "VM instruction roundtrip")
        records.append({"address": VM_PATCH.address + offset,
                        "before": codec.format(ins, fields), "after": codec.format(ins2, fields2)})
    require(bytes(out) == VM_PATCH.after, "VM patch disagrees with ISA field encoding")
    # Boundary arithmetic only: no claim to emulate the complete SDK VM driver.
    inputs = (0, 511, 512, 8191, 8192, 16383, 16384, 16385, 65535, 65536, 0x3C000, 0xFFFFFFFF)
    for value in inputs:
        result = 16384 if value >= 16384 else value
        require(result == min(value, 16384), "VM clamp boundary mismatch")
    return {"instructions": records, "arithmetic_boundary_cases": len(inputs),
            "full_vm_execution_emulated": False}


def validate_map(entries, expected):
    by_name = {entry.name: entry for entry in entries}
    require(len(by_name) == len(entries), "duplicate directory names")
    require(set(by_name) == {"app_area_head", "app.bin", "cfg_tool.bin"} | set(expected),
            "unexpected directory names")
    require(by_name["app_area_head"].offset == ENTRY and by_name["app.bin"].offset == APP_OFFSET,
            "entrypoint/application offset changed")
    for name, (start, end) in expected.items():
        e = by_name[name]
        require((e.offset, e.size) == (start, end-start), f"{name} partition geometry changed")
    return by_name


def pinned_inputs(g_raw, mini_fwsc):
    require(sha(g_raw) == G_SHA and len(g_raw) == 0x77000, "unexpected original G v2 image")
    require(sha(mini_fwsc) == MINI_SHA, "unexpected MINI stock reference")
    _, packed = unpack_fwsc(mini_fwsc)
    flash = packed["flash.bin"]
    require(len(flash) == MINI_END, "stock flash.bin extent changed")
    gp, ge, gf = unpack_app(g_raw)
    mp, me, mf = unpack_app(flash[MINI_START:MINI_END])
    validate_map(ge, G_PARTITIONS)
    validate_map(me, MINI_PARTITIONS)
    require(gf["cfg_tool.bin"] == mf["cfg_tool.bin"] and len(gf["cfg_tool.bin"]) == 383,
            "cfg_tool.bin is no longer identical")
    return gp, ge, gf, mp, me, mf, flash


def repack_header(template, *, offset=None, size=None, data_crc=None):
    require(len(template) == 32, "header template length")
    h = bytearray(template)
    if offset is not None:
        struct.pack_into("<I", h, 4, offset)
    if size is not None:
        struct.pack_into("<I", h, 8, size)
    if data_crc is not None:
        struct.pack_into("<H", h, 2, data_crc)
    struct.pack_into("<H", h, 0, crc16(h[2:]))
    return bytes(h)


def compose_candidate(g_raw: bytes, mini_fwsc: bytes, *,
                      additional_patches=(), append_code: bytes = b"") -> tuple[bytes, dict]:
    """Return a whole MINI-sized *application-area* candidate and audit record.

    Baseline patches are identity/branding and the proven VM-size constant.
    Optional board patches must assert exact original bytes and cannot overlap.
    Optional appended code retains every original address; cfg_tool.bin moves
    after it. This formatter proves bounds/CRCs/byte preservation, not code
    semantics, hardware compatibility or permission to upload.
    """
    gp, ge, gf, mp, me, _, _ = pinned_inputs(g_raw, mini_fwsc)
    patches = tuple(IDENTITY_PATCHES) + (VM_PATCH,) + tuple(additional_patches)
    app = bytearray(gf["app.bin"])
    covered = set()
    for p in patches:
        require(isinstance(p, BinaryPatch), "additional patch must be BinaryPatch")
        require(p.name and p.rationale and p.before and len(p.before) == len(p.after), "invalid patch contract")
        start, end = p.address-ENTRY, p.address-ENTRY+len(p.before)
        require(0 <= start < end <= len(app), "patch leaves the original application")
        require(not any(i in covered for i in range(start, end)), "overlapping patches")
        require(bytes(app[start:end]) == p.before, f"{p.name}: preimage mismatch at {p.address:#x}")
        app[start:end] = p.after
        covered.update(range(start, end))
    original_patched_size = len(app)
    append_at = APP_OFFSET + len(app)
    require(append_at % 4 == 0, "original append location is not word aligned")
    require(isinstance(append_code, bytes), "appended code must be bytes")
    app += append_code
    cfg = gf["cfg_tool.bin"]
    cfg_at = APP_OFFSET + len(app)
    head_end = cfg_at + len(cfg)
    require(head_end <= MINI_SIZE, "candidate exceeds MINI application partition")
    plain = bytearray(b"\xff" * MINI_SIZE)
    plain[APP_OFFSET:cfg_at] = app
    plain[cfg_at:head_end] = cfg
    plain[0x20:0x40] = repack_header(gp[0x20:0x40], size=len(app), data_crc=crc16(app))
    plain[0x40:0x60] = repack_header(gp[0x40:0x60], offset=cfg_at, data_crc=crc16(cfg))
    # Copy only MINI partition directory records, never its app or partition data.
    for e in me[3:]:
        plain[e.header_offset:e.header_offset+32] = mp[e.header_offset:e.header_offset+32]
    plain[:32] = repack_header(gp[:32], size=head_end, data_crc=crc16(plain[32:head_end]))
    cipher_end = (head_end + 31) & ~31
    require(cipher_end <= MINI_SIZE, "encoded application boundary outside partition")
    raw = sfc(bytes(plain[:cipher_end])) + bytes(plain[cipher_end:])
    decoded, entries, files = unpack_app(raw)
    validate_map(entries, MINI_PARTITIONS)
    require(decoded == plain and files["app.bin"] == app and files["cfg_tool.bin"] == cfg,
            "candidate encode/decode CRC roundtrip failed")
    restored = bytearray(files["app.bin"][:original_patched_size])
    for p in patches:
        start = p.address - ENTRY
        restored[start:start+len(p.after)] = p.before
    require(restored == gf["app.bin"], "unlisted original application modification")
    for brand in (b"UltraRig", "UltraRig".encode("utf-16le")):
        require(brand not in files["app.bin"], "unrebranded runtime UltraRig string remains")
    require(b"PONG %s %s %s%s\n\0" in files["app.bin"], "PONG format unexpectedly changed")
    return raw, {
        "sha256": sha(raw), "bytes": len(raw), "physical_range": [MINI_START, MINI_END],
        "cpu_entry": ENTRY, "app_bytes": len(app), "app_sha256": sha(app),
        "cfg_tool_bytes": len(cfg), "cfg_tool_area_offset": cfg_at, "head_end": head_end,
        "encoding_end": cipher_end, "directory": [e.to_dict() for e in entries],
        "patches": [p.record() for p in patches],
        "appended_code": {"cpu_address": FLASH_BASE+append_at, "bytes": len(append_code),
                          "sha256": sha(append_code)},
        "original_application_recovered_exactly_by_reversing_patches": True,
        "original_application_bytes_retained": original_patched_size,
        "stock_mini_application_bytes_used": 0,
        "stock_mini_partition_headers_used": True,
        "bootloader_included": False, "user_partition_data_included": False,
        "removed_partition": "OTP", "otp_absence_runtime_compatibility_proven": False,
        "crc_and_layout_valid": True, "board_port_complete": False,
        "boot_verified_on_mini": False, "flashable": False,
    }


def inspect_vm_geometry(raw: bytes, base: int, size: int) -> dict:
    """Read-only reconstruction of installer vm_state/vm_entries.

    Records are bounded and CRC checked. Only metadata is returned, never the
    unit-specific values. This says what the reconstructed bank rules request;
    it does not execute the firmware or prove the meaning of radio record IDs.
    """
    require(len(raw) == 0x100000 and base % 4096 == 0 and size % 8192 == 0 and
            0 < size <= len(raw)-base, "invalid VM fixture geometry")
    bank = size // 2
    ma, mb = (int.from_bytes(raw[a:a+4], "little") for a in (base, base+bank))
    good, moving, emptied = 0x55AAAA55, 0xDDEEAA55, 0xDDEEBB77
    writes = []
    if ma in (0xFFFFFFFF, 0, emptied):
        active = "B" if mb == good else None
    elif ma == moving:
        active = "A"
        writes.append("moving")
    elif ma == good:
        active = "A"
        if mb == moving:
            active = "B"
            writes.append("moving")
    else:
        active = None
    result = {"base": base, "size": size, "bank_bytes": bank,
              "magic_a": ma, "magic_b": mb, "active_bank": active,
              "predicted_maintenance_requests": writes,
              "record_schema_compatibility_proven": False}
    if active is None:
        writes.append("format")
        return result
    start = base + (bank if active == "B" else 0)
    other = base + (0 if active == "B" else bank)
    if raw[other:other+bank] != b"\xff" * bank:
        writes.append("other_bank")
    cursor, records = start+4, []
    while cursor+4 <= start+bank:
        header = raw[cursor:cursor+4]
        length = int.from_bytes(header[2:], "little") >> 4
        end = cursor+4+length
        if end > start+bank or (crc16(raw[cursor+4:end]) & 255) != header[0]:
            break
        records.append({"offset": cursor, "id": (header[2] & 15)*256+header[1], "bytes": length})
        cursor = end
    if raw[cursor:start+bank] != b"\xff" * (start+bank-cursor):
        writes.append("tail")
    if cursor > start + bank*60//100:
        writes.append("full")
    result.update(bank_start=start, write_pointer=cursor, used_bytes=cursor-start,
                  used_percent=100*(cursor-start)/bank, records=len(records),
                  record_metadata_sha256=sha(json.dumps(records, sort_keys=True).encode()),
                  all_parsed_record_crcs_valid=True,
                  distinct_record_ids=sorted({e["id"] for e in records}),
                  no_maintenance_predicted=not writes)
    return result


def audit_installer():
    constants_path = ROOT / "recovered/installer/tankg_install.constants.json"
    dis_path = ROOT / "recovered/installer/tankg_install.dis.txt"
    constants = constants_path.read_bytes()
    dis = dis_path.read_bytes()
    require(sha(constants) == "64830ea5e0abc40b05327220564c0bc98d69af3e888155660d2b324621a27e55", "installer constants changed")
    require(sha(dis) == "1a2a94103d3d0ee80deefd6820c2d602d41b9e20a6e101855b94a6100bbc170c", "installer disassembly changed")
    functions = {f["name"]: f for f in json.loads(constants)}
    names = functions["build_target"]["names"]
    require(all(n in names for n in ("APP_AREA", "VM_AREA", "USR_AREA", "TANKB_VM_SPAN", "TANKG_VM_SPAN")),
            "installer target builder branches changed")
    require(b"((15425556,))" in dis and b"(ALT_FLASH_IDS)" in dis,
            "installer alternative JEDEC declaration changed")
    return {"constants_sha256": sha(constants), "bytecode_listing_sha256": sha(dis),
            "build_target_source_line": 1623,
            "normal_g_application_payload_range": [0x4000, 0x7B000],
            "persistent_factory_bootloader_replaced": False,
            "normal_usr_policy": "keep",
            "declared_alternative_jedec_ids": [0xEB6014],
            "conditional_vm_paths_exist": ["factory-97 bank migration", "Tank-B migration", "repair from the same unit backup", "restore"],
            "evidence": "build_target bytecode 42..62 copies current, 250..286 replaces APP_AREA; VM and USR writes are explicit separate branches; plan_sectors rejects changes outside allowed ranges.",
            "mini_supported_by_original_installer": False}


def audit_nor(gp, mp):
    """Compare decoded driver fragments without erasing opcode differences.

    Only explicitly mapped callees/globals and branch destinations are
    normalized. MMIO addresses, masks, opcodes, registers and instruction
    ordering remain in the comparison. A call name is a boundary, not proof
    that the entire OS/clock/cache implementation below it is equivalent.
    """
    base = 0x01C00000
    gram = gp[0x56780:0x56780+0x2030C]
    # Derive MINI copy source from its previously decoded, pinned reset bytes.
    isa = table.load()
    # Source pointer is an immediate in MINI reset. Find that exact verified
    # instruction in the small reset prologue, never guess from file padding.
    cursor, sources = APP_OFFSET, []
    while cursor < 0x220:
        result = codec.decode(isa, mp, cursor)
        if result is None:
            cursor += 2
            continue
        ins, vals, size = result
        text = codec.format(ins, vals)
        hit = re.fullmatch(r"r1 = (\d+)", text)
        if hit and FLASH_BASE < int(hit[1]) < FLASH_BASE+MINI_SIZE:
            sources.append(int(hit[1]))
        cursor += size
    require(sources, "MINI reset RAM source not found")
    source = sources[0]
    mram = mp[source-FLASH_BASE:source-FLASH_BASE+0xE018]
    pairs = [
        ("cs_delay", (0x72, 0x88), (0x74, 0x8A), ()),
        ("chip_select_pd0", (0x88, 0xA8), (0x8A, 0xAA), ()),
        ("spi_completion", (0xA8, 0xD8), (0xAA, 0xDA), ()),
        ("spi_transmit", (0xD8, 0xF0), (0xDA, 0xF2), ()),
        ("spi_receive", (0x12E, 0x14C), (0x1DC, 0x1FC), ()),
        ("address_bytes", (0x14C, 0x170), (0x124, 0x148), ()),
        ("read_modes", (0x290, 0x3D4), (0x288, 0x3CC), ((0x2BC, 0x2B4, 8, 8),)),
        ("jedec_and_uid", (0x44C, 0x4D0), (0x500, 0x584), ()),
        ("status_read_05_35", (0x4D0, 0x50A), (0x678, 0x6B2), ()),
        ("write_enable_06", (0x5D0, 0x5E6), (0x584, 0x59A), ()),
        ("busy_wait_05", (0x600, 0x640), (0x5A4, 0x5E4), ()),
        ("erase_dispatch", (0x640, 0x6D2), (0x5E4, 0x678), ((0x65A, 0x5FE, 6, 5),)),
        ("status_write_01_31", (0x6D2, 0x79E), (0x6B2, 0x77E), ()),
        ("status_update_policy", (0x79E, 0x822), (0x77E, 0x802), ()),
        ("page_program_02", (0x840, 0x8B4), (0x820, 0x894), ()),
        ("sfc_enter_mmio", (0x36, 0x70), (0x38, 0x72), ()),
    ]
    call_pairs = {
        "nor_lock_enter": (0, 0), "nor_lock_leave": (0x3E8, 0x402),
        "exit_continuous_read": (0xF0, 0x4A4), "resume_continuous_read": (0x3D4, 0x4EC),
        "enter_four_byte_address": (0x536, 0xF2), "leave_four_byte_address": (0x56E, 0x3CC),
        "physical_to_cpu": (0x5E6, 0x494), "cache_invalidate_boundary": (0x5F6, 0x59A),
        "mode_read_bytes": (0x184, 0x15C), "mode_write_bytes": (0x214, 0x20C),
    }
    call_pairs.update({name: (g[0], m[0]) for name, g, m, _ in pairs})
    globals_ = {"nor_state": (0x01C3743C, 0x01C1E3A8),
                "nor_four_byte_flag": (0x01C3748C, 0x01C1E3F4)}

    def normalized(raw, span, special, side):
        a, b = span
        tables = {(v[side]): (v[2], v[3]) for v in special}
        cursor, insns = a, []
        while cursor < b:
            if cursor in tables:
                n, count = tables[cursor]
                insns.append((cursor, n, "table", tuple(cursor+2*v for v in raw[cursor:cursor+count])))
                cursor += n
                continue
            decoded = codec.decode(isa, raw, cursor)
            require(decoded is not None, f"NOR unknown instruction {base+cursor:#x}")
            ins, fields, n = decoded
            require(cursor+n <= b, "NOR fragment instruction boundary")
            insns.append((cursor, n, codec.format(ins, fields), None))
            cursor += n
        positions = {at: i for i, (at, _, _, _) in enumerate(insns)}
        calls = {values[side]+base: name for name, values in call_pairs.items()}
        globs = {str(values[side]): name for name, values in globals_.items()}
        out = []
        for at, size, text, tbl in insns:
            if tbl is not None:
                require(all(target in positions for target in tbl), "NOR jump-table destination outside fragment")
                out.append("tbb_targets " + repr([positions[target] for target in tbl]))
                continue
            target = re.search(r"\b(call|goto) (-?\d+)$", text)
            if target:
                dest = at+size+int(target[2])
                if target[1] == "call":
                    require(dest+base in calls, f"unmapped NOR callee {dest+base:#x}")
                    label = calls[dest+base]
                else:
                    require(dest in positions, f"NOR branch escapes {dest+base:#x}")
                    label = f"insn_{positions[dest]}"
                text = text[:target.start(2)] + label
            load = re.fullmatch(r"(r\d+) = (\d+)", text)
            if load and load[2] in globs:
                text = load[1] + " = " + globs[load[2]]
            out.append(text)
        return out

    comparisons = []
    for name, g, m, special in pairs:
        left = normalized(gram, g, special, 0)
        right = normalized(mram, m, special, 1)
        require(left == right, f"NOR normalized fragment differs: {name}")
        comparisons.append({"name": name, "g_range": [base+v for v in g],
                            "mini_range": [base+v for v in m], "instructions_or_tables": len(left),
                            "normalized_sha256": sha("\n".join(left).encode()), "equal": True})
    # The ID routine shifts the three returned JEDEC bytes into [nor_state+28].
    # Capacity uses low byte, subtracts 16, calculates 2**n, then shifts by 16.
    jedec = 0xEB6014
    capacity = (1 << ((jedec & 255)-16)) << 16
    require(capacity == 0x100000, "JEDEC capacity derivation")
    return {"mini_ram_source": source, "fragment_comparisons": comparisons,
            "normalization": "Explicit callee symbols, two declared global addresses, local branch/table instruction indices only; MMIO/masks/opcodes/register order retained.",
            "observed_jedec": jedec, "capacity_derived_by_g_bytes": capacity,
            "capacity_g_sites": [0x02002740, 0x02002746, 0x0200274A, 0x0200274C, 0x0200274E],
            "read_opcodes_in_shared_dispatch": [3, 11, 59, 107, 187, 235],
            "shared_program_opcode": 2, "shared_sector_erase_opcode": 32,
            "shared_status_read_opcodes": [5, 53], "shared_status_write_opcodes": [1, 49],
            "jedec_manufacturer_specific_gate_in_compared_fragments": False,
            "full_driver_equivalence_proven": False, "runtime_program_or_erase_tested_on_mini": False,
            "qe_bit_effect_on_chip_proven": False,
            "limitations": ["Lock/dual-core coordination and cache invalidation callees are boundaries, not proven by this normalization.",
                            "Flash/SFC timing at G CPU-clock policy is not measured.",
                            "Status-update request source and all call paths, including hardware security-register operations, are not exhaustively audited.",
                            "Shared SPI instruction sequences and physical JEDEC read do not prove erase/program success or safe recovery."]}


def negative_checks(g, m, candidate):
    tests = []
    def reject(label, fn):
        try:
            fn()
        except ValueError:
            tests.append(label)
        else:
            raise ValueError(f"negative test accepted: {label}")
    bad = bytearray(g)
    bad[0x300] ^= 1
    reject("unrecognized original image", lambda: compose_candidate(bytes(bad), m))
    reject("bad board patch preimage", lambda: compose_candidate(g, m, additional_patches=(
        BinaryPatch("bad", ENTRY, b"\x00\x00", b"\x01\x00", "negative fixture"),)))
    reject("overlapping board patch", lambda: compose_candidate(g, m, additional_patches=(IDENTITY_PATCHES[0],)))
    reject("patch outside application", lambda: compose_candidate(g, m, additional_patches=(
        BinaryPatch("bad", FLASH_BASE, b"\x00", b"\x01", "negative fixture"),)))
    reject("append beyond application partition", lambda: compose_candidate(g, m, append_code=b"\x00"*30000))
    bad = bytearray(candidate)
    bad[0x400] ^= 1
    reject("candidate payload corruption", lambda: unpack_app(bytes(bad)))
    return tests


def positive_append_check(g, m):
    """Exercise code append/cfg relocation as a byte-layout test only."""
    payload = bytes.fromhex("80008000")
    candidate, record = compose_candidate(g, m, append_code=payload)
    _, _, files = unpack_app(candidate)
    require(record["cfg_tool_area_offset"] == 0x76AAC+len(payload) and
            files["app.bin"][-len(payload):] == payload,
            "appended payload/cfg relocation failed")
    return {"appended_bytes": len(payload), "cfg_tool_relocated_by": len(payload),
            "crc_and_inverse_patch_roundtrip_passed": True, "fixture_written_to_file": False}


def make_report(g, m, candidate, candidate_record, backup=None):
    gp, ge, gf, mp, me, mf, flash = pinned_inputs(g, m)
    # Decode the stock MINI BANKCB independently of generated build artifacts.
    records = {e.name: e for e in (jlfs_entry(enc(flash[o:o+32]), 0) for o in range(32, 160, 32))}
    entry = records["uboot.boot"]
    bankcb = enc(flash[entry.offset:entry.offset+16]) + enc(flash[entry.offset+16:entry.offset+entry.size])
    banks, length, load, offset, dcrc, hcrc = struct.unpack_from("<HHIIHH", bankcb)
    require((banks, length, load, offset) == (1, 0x3820, 0x01C02000, 16), "MINI boot BANKCB geometry")
    require(crc16(bankcb[:14]) == hcrc and crc16(bankcb[16:]) == dcrc and crc16(bankcb) == entry.data_crc,
            "MINI boot BANKCB CRC")
    require(sha(bankcb[16:]) == BOOT_SHA, "MINI boot payload changed")
    fragments = {
        "reset_and_ram_copy": (0x0200018A, 0x02000224),
        "boot_descriptor_extension": (0x0200045C, 0x02000478),
        "heap_bounds": (0x0203C0CA, 0x0203C0E8),
        "vm_directory_name_scan": (0x02022208, 0x0202225E),
        "vm_bank_size": (0x02020674, 0x0202069A),
        "btif_name_lookup": (0x0201FAB8, 0x0201FB1E),
        "usr_address_function": (0x020026BA, 0x020026D6),
    }
    proofs = {name: decode_fragment(gp, a, b) for name, (a, b) in fragments.items()}
    mini_vm = decode_fragment(mp, 0x0201FD72, 0x0201FD9C)
    identity_changes = sum(a != b for a, b in zip(gf["app.bin"], unpack_app(candidate)[2]["app.bin"]))
    report = {
        "format_version": 1,
        "objective": "Port the complete UltraRig G v2 application to MINI; stock MINI is hardware/recovery evidence only.",
        "hardware_io_performed": False, "nvm_writes_performed": False,
        "sources": {"g": {"path": G_PATH, "sha256": sha(g), "area_bytes": len(g), "app_bytes": len(gf["app.bin"])},
                    "mini": {"path": MINI_PATH, "sha256": sha(m), "app_bytes": len(mf["app.bin"]), "boot_payload_sha256": BOOT_SHA}},
        "format_fit": {"same_entry": ENTRY, "same_chip_key": 0x980F,
                       "g_area_bytes": len(g), "mini_area_bytes": MINI_SIZE,
                       "partition_size_difference": MINI_SIZE-len(g),
                       "maximum_append_bytes_before_alignment": MINI_SIZE-APP_OFFSET-len(gf["app.bin"])-383,
                       "cfg_tool_identical": True, "cfg_tool_sha256": sha(gf["cfg_tool.bin"]),
                       "same_entry_and_format_proves_hardware_compatibility": False},
        "partition_mapping": {"g": {n: list(r) for n, r in G_PARTITIONS.items()},
                              "mini": {n: list(r) for n, r in MINI_PARTITIONS.items()},
                              "g_directory": [e.to_dict() for e in ge], "mini_directory": [e.to_dict() for e in me]},
        "memory": {"ram_copy_vma": [0x01C00000, 0x01C2030C], "ram_copy_lma": 0x02056780,
                   "bss": [0x01C2030C, 0x01C38050], "initial_sp": 0x01C350B8, "initial_ssp": 0x01C360B8,
                   "cpu1_usp": 0x01C363B8, "cpu1_sp": 0x01C373B8,
                   "heap": [0x01C38060, 0x01C7FBA0], "heap_bytes": 0x47B40,
                   "external_reset_copy_bytes": 0, "external_reset_clear_bytes": 0,
                   "whole_application_absence_of_external_ram_use_proven": False,
                   "g_saved_boot_context": 0x01C7FD4C,
                   "mini_boot_argument": 0x01C7FE08,
                   "extra_boot_argument_reads": [[0x01C7FE58, 8], [0x01C7FE60, 4]],
                   "extension_values_for_no_sdram_boot_proven": False,
                   "rom_plugin_slots_available_after_full_application_boot": False},
        "storage_access": {
            "vm_base_source": "Name comparison of vm with JLFS directory, then ioctl205/206 metadata; not fixed 0x7B000.",
            "vm_name_address": 0x02035851, "vm_scan_address": 0x02022208,
            "btif_base_source": "mnt/sdfile/app/btif open at 0x0201FB00, metadata read, base+512 calibration access.",
            "btif_name_address": 0x0203660C, "cfg_path_address": 0x02036AC2,
            "usr_base_hardcoded": 0xBF000, "usr_special_slots": [0xDD000, 0xDE000],
            "otp_string_count_in_app": gf["app.bin"].count(b"OTP"),
            "otp_removal_runtime_safe_proven": False,
            "negative_literal_search_is_not_control_flow_proof": True,
            "mini_record_schema_and_radio_calibration_compatible": False,
        },
        "instruction_evidence": proofs, "mini_vm_instruction_evidence": mini_vm,
        "vm_patch_validation": verify_vm_patch(), "installer": audit_installer(),
        "nor_driver_comparison": audit_nor(gp, mp),
        "candidate": dict(candidate_record, actual_original_app_bytes_changed=identity_changes),
        "validation": {"negative_cases_passed": negative_checks(g, m, candidate),
                       "append_and_cfg_relocation": positive_append_check(g, m),
                       "candidate_crc_roundtrip": True, "original_application_inverse_patch_equality": True},
        "remaining_product_gates": [
            "Board-specific codec and GPIO sequence, buttons/LED mapping and analog mute must be ported; see the separate board audit.",
            "Confirm SFC/CPU clock policy and boot descriptor extension handling under the MINI factory bootloader.",
            "Prove all OTP/BTIF consumers and radio calibration record meanings; the directory adaptation alone is insufficient.",
            "Recheck current VM bank maintenance before any future write; the frozen backup is not a permanent state assertion.",
            "Prove recovery when the application is corrupt; successful reset of intact stock is insufficient.",
            "Boot the complete port, validate USB/BLE PONG, audio and preset roundtrips, then stable restart and sustained operation.",
        ],
    }
    if backup is not None:
        require(sha(backup) == BACKUP_SHA and len(backup) == 0x100000, "unexpected frozen MINI backup")
        require(backup[:MINI_END] == flash, "backup application/boot prefix differs from stock009")
        g_vm = inspect_vm_geometry(backup, 0x82000, 0x10000)
        mini_vm_state = inspect_vm_geometry(backup, 0x82000, 0x4000)
        require(g_vm["predicted_maintenance_requests"] == ["format"], "unmodified-G VM fixture changed")
        require(mini_vm_state["no_maintenance_predicted"] and mini_vm_state["records"] == 134 and
                mini_vm_state["write_pointer"] == 0x8531E, "MINI VM fixture changed")
        corrupt_vm = bytearray(backup)
        corrupt_vm[0x84008] ^= 1
        require("tail" in inspect_vm_geometry(bytes(corrupt_vm), 0x82000, 0x4000)["predicted_maintenance_requests"],
                "VM corrupted record fixture was accepted")
        image = backup[:MINI_START] + candidate + backup[MINI_END:]
        require(image[:MINI_START] == backup[:MINI_START] and image[MINI_END:] == backup[MINI_END:],
                "offline application replacement touches protected device data")
        report["frozen_backup_check"] = {"path": BACKUP_PATH, "sha256": sha(backup),
            "stock_boot_and_app_prefix_match": True, "unmodified_g_geometry": g_vm,
            "mini_geometry": mini_vm_state, "hypothetical_in_memory_replacement_preserves_outside_application": True,
            "corrupted_vm_record_rejected_by_no_maintenance_gate": True,
            "full_flash_candidate_written_to_file": False, "recovery_from_corrupt_application_proven": False}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/mini-ultrarig/hyperrig-mini-g-derived.app.bin")
    parser.add_argument("--report", type=Path, default=ROOT / "research/mini-ultrarig-port.json")
    args = parser.parse_args()
    for path in (args.output, args.report):
        resolved = path.resolve()
        require(resolved.is_relative_to(ROOT), "outputs must stay inside this workspace")
        require(resolved != (ROOT/G_PATH).resolve() and resolved != (ROOT/MINI_PATH).resolve(), "output aliases a pinned input")
        require(not resolved.is_relative_to(ROOT/"artifacts"), "outputs cannot overwrite preserved artifacts")
    g, m = (ROOT/G_PATH).read_bytes(), (ROOT/MINI_PATH).read_bytes()
    candidate, record = compose_candidate(g, m)
    backup_path = ROOT/BACKUP_PATH
    backup = backup_path.read_bytes() if backup_path.exists() else None
    report = make_report(g, m, candidate, record, backup)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(candidate)
    report["candidate"]["path"] = args.output.relative_to(ROOT).as_posix() if args.output.is_absolute() else args.output.as_posix()
    report["builder_sha256"] = sha(Path(__file__).read_bytes())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "OFFLINE_CANDIDATE_VALID", "bytes": len(candidate),
                      "sha256": sha(candidate), "original_application_bytes": 485772,
                      "negative_cases": len(report["validation"]["negative_cases_passed"]),
                      "board_port_complete": False, "flashable": False}))


if __name__ == "__main__":
    main()
