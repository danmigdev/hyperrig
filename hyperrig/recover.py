"""Static extraction of a PyInstaller archive, without importing its programs."""

import dis
import importlib.util
import json
import marshal
from pathlib import Path
import struct
import sys
import types
import zlib


def safe_path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("archive path outside extraction root")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def describe_code(code: types.CodeType) -> list[dict]:
    rows = [{"name": code.co_qualname, "source": code.co_filename,
             "line": code.co_firstlineno, "names": list(code.co_names),
             "constants": [repr(x) for x in code.co_consts if not isinstance(x, types.CodeType)]}]
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            rows.extend(describe_code(c))
    return rows


def recover_installer(path: Path, output: Path) -> dict:
    exe = path.read_bytes()
    cookie = exe.rfind(b"MEI\x0c\x0b\x0a\x0b\x0e")
    if cookie < 0 or cookie + 88 > len(exe):
        raise ValueError("PyInstaller cookie missing/truncated")
    magic, size, toc_offset, toc_size, version, lib = struct.unpack_from("!8sIIII64s", exe, cookie)
    if version != sys.version_info.major * 100 + sys.version_info.minor:
        raise ValueError(f"installer needs Python {version}; marshal/dis versions must match")
    base = cookie + 88 - size
    if base < 0 or base + toc_offset + toc_size > cookie:
        raise ValueError("invalid archive bounds")
    output.mkdir(parents=True, exist_ok=True)
    table = exe[base + toc_offset:base + toc_offset + toc_size]
    pos, manifest = 0, []

    def save_code(name, data):
        code = marshal.loads(data)  # Parse code objects as DATA. Never exec/import them.
        if not isinstance(code, types.CodeType):
            raise ValueError("archive item is not a code object")
        safe_path(output, name + ".marshal").write_bytes(data)
        with safe_path(output, name + ".dis.txt").open("w", encoding="utf-8") as f:
            dis.dis(code, file=f)
        safe_path(output, name + ".constants.json").write_text(
            json.dumps(describe_code(code), indent=2, ensure_ascii=False), encoding="utf-8")

    while pos < len(table):
        if pos + 18 > len(table):
            raise ValueError("truncated PyInstaller TOC")
        n, offset, compressed, expanded, flag, kind = struct.unpack_from("!iIIIBc", table, pos)
        if n < 18 or pos + n > len(table) or offset + compressed > toc_offset:
            raise ValueError("invalid PyInstaller entry bounds")
        name = table[pos + 18:pos + n].split(b"\0", 1)[0].decode()
        pos += n
        data = exe[base + offset:base + offset + compressed]
        if flag:
            data = zlib.decompress(data)
        if len(data) != expanded:
            raise ValueError("PyInstaller decompressed length mismatch")
        manifest.append({"name": name, "type": kind.decode(), "size": len(data)})
        if kind == b"s":
            save_code(name, data)
        elif kind == b"z":
            if data[:4] != b"PYZ\0" or data[4:8] != importlib.util.MAGIC_NUMBER:
                raise ValueError("incompatible PYZ bytecode")
            offset = struct.unpack_from("!i", data, 8)[0]
            if not 12 <= offset < len(data):
                raise ValueError("invalid PYZ table offset")
            contents = marshal.loads(data[offset:])
            for module, entry in (contents.items() if isinstance(contents, dict) else contents):
                kind, offset, length = entry
                if module.startswith(("tankg", "ultrarig", "jltech", "scsiio")):
                    if offset < 12 or offset + length > len(data):
                        raise ValueError("invalid PYZ module bounds")
                    save_code(module, zlib.decompress(data[offset:offset + length]))
    result = {"python": version, "archive": str(path), "entries": manifest,
              "execution": "none; marshal parsing and disassembly only"}
    (output / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
