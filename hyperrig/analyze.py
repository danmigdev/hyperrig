"""Reproduce the offline findings from locally downloaded release artifacts."""

import itertools
import json
from pathlib import Path
import re
import shutil
import struct
import zipfile

from .jieli import sha256, unpack_app, unpack_fwsc
from .recover import recover_installer
from .a2l import inspect as inspect_a2l


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def analyze_image(raw: bytes, output: Path, metadata: dict) -> dict:
    plain, entries, files = unpack_app(raw)
    output.mkdir(parents=True, exist_ok=True)
    (output / "app_area.dec.bin").write_bytes(plain)
    for name, data in files.items():
        (output / name).write_bytes(data)
    write_json(output / "jlfs.json", [e.to_dict() for e in entries])
    rows = [(m.start(), m[0].decode()) for m in re.finditer(rb"[\x20-\x7e]{4,}", plain[:entries[0].size])]
    (output / "strings.tsv").write_text("container_offset\tphysical_flash_offset\tcpu_flash_address\ttext\n" +
        "\n".join(f"0x{o:06x}\t0x{o + 0x4000:06x}\t0x{o + 0x2000000:08x}\t{s}" for o, s in rows), encoding="utf-8")
    version = next((m.group().decode() for m in [re.search(
        rb"tankg_fw [A-Za-z0-9.+]+(?: [a-z0-9]+)*|TANK MINI_\d+", plain)] if m), None)
    commands = next((s.split() for o, s in rows if s.startswith("PING EVT LVL LVLSUB STAT MEM MODEL AUDIO")), [])
    result = {**metadata, "sha256": sha256(raw), "size": len(raw), "version_in_binary": version,
              "entry_address": entries[0].offset, "application_bytes": len(files["app.bin"]),
              "all_jlfs_crc_valid": True, "commands_in_firmware": commands,
              "directory": [e.to_dict() for e in entries]}
    captures = []
    for match in re.finditer(b"A2L1", plain[:entries[0].size]):
        try:
            capture = inspect_a2l(plain[match.start():], allow_trailing=True)
        except ValueError:
            continue  # The instruction stream also contains an immediate 'A2L1'.
        capture["container_offset"] = match.start()
        name = f"embedded-{len(captures)}.a2l"
        (output / name).write_bytes(plain[match.start():match.start() + capture["bytes"]])
        write_json(output / (name + ".json"), capture)
        captures.append({k: v for k, v in capture.items() if k not in (
            "layer_parameters", "rechannel_weights", "head_weights", "head_bias")})
    result["embedded_captures"] = captures
    write_json(output / "summary.json", result)
    return result


def analyze(root: Path) -> dict:
    locked = json.loads((root / "research/input-manifest.json").read_text(encoding="utf-8"))
    release = json.loads((root / "artifacts/alpha11/release.json").read_text(encoding="utf-8"))
    actual = {a["name"]: a for a in release["assets"]}
    if release["tag_name"] != locked["release"]["tag"]:
        raise ValueError("release tag differs from pinned reference")
    checks = []
    for asset in locked["release"]["assets"]:
        path = root / "artifacts/alpha11" / asset["name"]
        digest = sha256(path.read_bytes())
        if digest != asset["sha256"] or path.stat().st_size != asset["size"]:
            raise ValueError(f"pinned asset SHA/size mismatch: {path.name}")
        if "sha256:" + digest != actual[path.name]["digest"]:
            raise ValueError(f"release asset SHA mismatch: {path.name}")
        checks.append({"name": path.name, "sha256": digest, "matches_release": True})
    summaries, images = [], {}
    for reference in locked["firmware_images"]:
        path = root / reference["path"]
        meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        raw = path.read_bytes()
        if (len(raw) != reference["size"] or sha256(raw) != reference["sha256"]
                or meta != {k: v for k, v in reference.items() if k != "path"}):
            raise ValueError(f"firmware metadata mismatch: {path.name}")
        summary = analyze_image(raw, root / "analysis/firmware" / path.stem, meta)
        summaries.append(summary)
        images[path.stem] = (root / "analysis/firmware" / path.stem / "app.bin").read_bytes()
    if len(summaries) != 4:
        raise ValueError("expected exactly four UltraRig application images")
    comparisons = []
    for (an, a), (bn, b) in itertools.combinations(images.items(), 2):
        different = sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))
        comparisons.append({"a": an, "b": bn, "different_bytes_at_same_offset": different,
                            "compared_span": max(len(a), len(b)),
                            "note": "positional comparison; linking shifts invalidate semantic percentages"})
    write_json(root / "analysis/comparisons.json", comparisons)

    mini_path = root / "artifacts/tank-mini/TANK-MINI.fwsc"
    mini_raw = mini_path.read_bytes()
    if sha256(mini_raw) != locked["tank_mini"]["sha256"] or len(mini_raw) != locked["tank_mini"]["size"]:
        raise ValueError("TANK MINI package differs from pinned reference")
    fwsc, files = unpack_fwsc(mini_raw)
    out = root / "analysis/tank-mini"
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "fwsc.json", fwsc)
    for name, data in files.items():
        (out / name).write_bytes(data)
    mini = analyze_image(files["flash.bin"][0x4000:], out,
                         {"model": "tank-mini", "factory_package_chip": fwsc["chip"]})

    v2 = root / "artifacts/alpha11/v2/UltraRig-alpha11-v2-win"
    recover_installer(v2 / "UltraRig-Installer.exe", root / "recovered/installer")
    recovered = root / "recovered/ultrarig-original"
    recovered.mkdir(parents=True, exist_ok=True)
    shutil.copytree(v2 / "web", recovered / "web", dirs_exist_ok=True)
    for name in ("LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md"):
        shutil.copyfile(v2 / name, recovered / name)
    js = (v2 / "web/tankg.html").read_text(encoding="utf-8")
    calls = []
    for m in re.finditer(r'Pedal\.cmd\(\s*(["`])(.+?)\1', js):
        calls.append({"line": js.count("\n", 0, m.start()) + 1, "template": m[2]})
    write_json(root / "analysis/protocol-call-sites.json", calls)
    with zipfile.ZipFile(root / "artifacts/alpha11/UltraRig-alpha11-android.apk") as z:
        for name in ("assets/capacitor.config.json", "assets/capacitor.plugins.json", "assets/public/index.html", "assets/public/nam2chip.js"):
            p = root / "recovered/android" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(name))
    result = {"release": release["tag_name"], "assets": checks, "ultrarig": summaries,
              "tank_mini": mini, "hardware_tested": False}
    write_json(root / "analysis/summary.json", result)
    return result
