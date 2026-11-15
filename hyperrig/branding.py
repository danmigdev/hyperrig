"""Build local HyperRig derivatives while preserving the original evidence.

Parses archives and bytecode as data; never executes the recovered installer.
Original licenses/attribution are copied verbatim by the packaging tool.
"""
import importlib.util
import marshal
import re
import struct
import sys
import types
import zlib

from .jieli import crc16, sfc, unpack_app

BRAND = re.compile(r"ultrarig", re.IGNORECASE)
BYTE_BRAND = re.compile(b"ultrarig", re.IGNORECASE)
TELEMETRY = "https://ovftdiikshwnvhwfynkz.supabase.co/rest/v1/rpc/submit_report"


def spelling(word):
    if word.isupper():
        return "HYPERRIG"
    if word.islower():
        return "hyperrig"
    if word == "Ultrarig":
        return "Hyperrig"
    if word[0].islower():
        return "hyperRig"
    return "HyperRig"


def rename_text(text, network=True):
    if network:
        # Do not point a derivative at the original author's telemetry,
        # updates or donations, nor at an unowned hyperrig.app domain.
        text = text.replace(TELEMETRY, "https://hyperrig.invalid/report")
        for old, new in (
                ("https://ultrarig.app", "https://hyperrig.invalid"),
                ("github.com/manuaguirre9/ultrarig", "hyperrig.invalid/source"),
                ("https://ko-fi.com/ultrarig", "https://hyperrig.invalid/support"),
                ("https://link.mercadopago.com.ar/ultrarig", "https://hyperrig.invalid/support"),
                ("https://mpago.la/2wmakNP", "https://hyperrig.invalid/support"),
                ("https://mpago.la/1wFqmxg", "https://hyperrig.invalid/support"),
                ("https://www.facebook.com/groups/1483259953756787", "https://hyperrig.invalid/community")):
            text = text.replace(old, new)
    text = BRAND.sub(lambda m: spelling(m[0]), text)
    text = text.replace("Ultra<i>Rig", "Hyper<i>Rig")
    # The existing vector favicon is a U; keep its dimensions/colors and draw H.
    text = text.replace("M20 13v21a12 12 0 0 0 24 0V13", "M20 13v38M44 13v38M20 32h24")
    return text


def rename_fixed(data):
    """Equal-length ASCII/UTF-16 substitutions for binary string pools."""
    out = BYTE_BRAND.sub(lambda m: spelling(m[0].decode("ascii")).encode("ascii"), data)
    for encoding in ("utf-16le", "utf-16be"):
        for old in ("UltraRig", "ultrarig", "ULTRARIG", "Ultrarig", "ultraRig"):
            out = out.replace(old.encode(encoding), spelling(old).encode(encoding))
    if len(out) != len(data):
        raise ValueError("binary branding must preserve all offsets")
    return out


def rebrand_firmware(raw):
    plain, entries, files = unpack_app(raw)
    patched = bytearray(plain)
    changes = {}
    for entry in entries[1:]:
        if entry.flags != 0x82:
            continue
        before = files[entry.name]
        after = rename_fixed(before)
        if after != before:
            changes[entry.name] = len(BYTE_BRAND.findall(before))
            patched[entry.offset:entry.offset + entry.size] = after
            struct.pack_into("<H", patched, entry.header_offset + 2, crc16(after))
            struct.pack_into("<H", patched, entry.header_offset,
                             crc16(patched[entry.header_offset + 2:entry.header_offset + 32]))
    head = entries[0]
    struct.pack_into("<H", patched, 2, crc16(patched[32:head.size]))
    struct.pack_into("<H", patched, 0, crc16(patched[2:32]))
    cipher_end = min((head.size + 31) & ~31, len(raw))
    result = sfc(bytes(patched[:cipher_end])) + bytes(patched[cipher_end:])
    checked, new_entries, new_files = unpack_app(result)
    if checked != patched or len(result) != len(raw):
        raise ValueError("rebranded SFC image failed its round trip")
    if [(e.name, e.offset, e.size, e.flags) for e in new_entries] != [
            (e.name, e.offset, e.size, e.flags) for e in entries]:
        raise ValueError("firmware layout changed")
    if any(BYTE_BRAND.search(value) for value in new_files.values()):
        raise ValueError("unreplaced firmware brand")
    return result, changes


def rename_code(value):
    if isinstance(value, types.CodeType):
        return value.replace(co_consts=tuple(rename_code(x) for x in value.co_consts),
                             co_names=tuple(rename_text(x) for x in value.co_names),
                             co_varnames=tuple(rename_text(x) for x in value.co_varnames),
                             co_freevars=tuple(rename_text(x) for x in value.co_freevars),
                             co_cellvars=tuple(rename_text(x) for x in value.co_cellvars),
                             co_filename=rename_text(value.co_filename),
                             co_name=rename_text(value.co_name),
                             co_qualname=rename_text(value.co_qualname))
    if isinstance(value, str):
        return rename_text(value)
    if isinstance(value, bytes):
        return rename_fixed(value)
    if isinstance(value, tuple):
        return tuple(rename_code(x) for x in value)
    if isinstance(value, frozenset):
        return frozenset(rename_code(x) for x in value)
    return value


def rewrite_pyz(raw):
    if raw[:4] != b"PYZ\0" or raw[4:8] != importlib.util.MAGIC_NUMBER:
        raise ValueError("PYZ requires matching Python bytecode version")
    toc_offset = struct.unpack_from("!I", raw, 8)[0]
    if not 12 <= toc_offset < len(raw):
        raise ValueError("invalid PYZ table")
    original = marshal.loads(raw[toc_offset:])
    toc = original.items() if isinstance(original, dict) else original
    output, rows, count = bytearray(raw[:12]), [], 0
    for name, (kind, offset, length) in toc:
        if offset < 12 or offset + length > toc_offset:
            raise ValueError("PYZ module outside payload")
        compressed = raw[offset:offset + length]
        payload = zlib.decompress(compressed)
        if kind in (0, 1):
            code = marshal.loads(payload)
            if not isinstance(code, types.CodeType):
                raise ValueError("expected PYZ code object")
            new_payload = marshal.dumps(rename_code(code))
            if new_payload != payload:
                compressed = zlib.compress(new_payload, 9)
                count += 1
        new_name = rename_text(name)
        rows.append((new_name, (kind, len(output), len(compressed))))
        output.extend(compressed)
    struct.pack_into("!I", output, 8, len(output))
    output.extend(marshal.dumps(dict(rows) if isinstance(original, dict) else rows))
    return bytes(output), count


def archive_entries(exe):
    cookie = exe.rfind(b"MEI\x0c\x0b\x0a\x0b\x0e")
    if cookie < 0 or cookie + 88 != len(exe):
        raise ValueError("expected an unsigned PyInstaller executable with terminal cookie")
    magic, size, offset, length, version, lib = struct.unpack_from("!8sIIII64s", exe, cookie)
    if version != sys.version_info.major * 100 + sys.version_info.minor:
        raise ValueError("use Python 3.12 to rebuild this installer's marshal data")
    base = cookie + 88 - size
    if base < 0 or base + offset + length != cookie:
        raise ValueError("invalid PyInstaller archive bounds")
    table = exe[base + offset:cookie]
    rows, pos = [], 0
    while pos < len(table):
        n, at, packed, expanded, flag, kind = struct.unpack_from("!iIIIBc", table, pos)
        if n < 18 or pos + n > len(table) or at + packed > offset or flag not in (0, 1):
            raise ValueError("invalid PyInstaller TOC entry")
        name = table[pos + 18:pos + n].split(b"\0", 1)[0].decode("utf-8")
        payload = exe[base + at:base + at + packed]
        if flag:
            payload = zlib.decompress(payload)
        if len(payload) != expanded:
            raise ValueError("PyInstaller entry length mismatch")
        rows.append((name, kind, flag, payload))
        pos += n
    return exe[:base], (magic, version, lib), rows


def rebrand_installer(exe):
    prefix, (magic, version, lib), rows = archive_entries(exe)
    prefix = bytearray(rename_fixed(prefix))
    pe = struct.unpack_from("<I", prefix, 0x3C)[0]
    optional = pe + 24
    pe_kind = struct.unpack_from("<H", prefix, optional)[0]
    directory = optional + (112 if pe_kind == 0x20B else 96)
    if struct.unpack_from("<II", prefix, directory + 4 * 8) != (0, 0):
        raise ValueError("refuse to retain an invalid Authenticode signature")
    struct.pack_into("<I", prefix, optional + 64, 0)  # Optional PE checksum.
    output, table, changed = bytearray(), bytearray(), []
    for name, kind, flag, payload in rows:
        before = payload
        if kind in (b"s", b"m", b"M"):
            code = marshal.loads(payload)
            if not isinstance(code, types.CodeType):
                raise ValueError("expected marshalled code")
            payload = marshal.dumps(rename_code(code))
        elif kind == b"z":
            payload, modules = rewrite_pyz(payload)
        if before != payload:
            changed.append(name)
        packed = zlib.compress(payload, 9) if flag else payload
        renamed = rename_text(name).encode("utf-8") + b"\0"
        entry_size = (18 + len(renamed) + 15) & ~15
        table.extend(struct.pack("!iIIIBc", entry_size, len(output), len(packed), len(payload), flag, kind))
        table.extend(renamed + b"\0" * (entry_size - 18 - len(renamed)))
        output.extend(packed)
    toc_offset = len(output)
    output.extend(table)
    output.extend(struct.pack("!8sIIII64s", magic, len(output) + 88, toc_offset, len(table), version, lib))
    result = bytes(prefix) + output
    _, _, rebuilt = archive_entries(result)
    if len(rebuilt) != len(rows):
        raise ValueError("installer archive did not round trip")
    return result, {"entries_rebuilt": changed, "python_version": version,
                    "validation": "archive parsing only; installer never executed"}
