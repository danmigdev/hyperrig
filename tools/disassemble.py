"""Linear pi32v2 listings with flash and copied-RAM addresses.

Includes embedded data; it is not a recovered control-flow graph. Uses the
pinned, independently validated decoder in upstream/pi32v2-isa.
"""

from pathlib import Path
import json
import re
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "upstream/pi32v2-isa"))
from pi32v2isa import codec, table


def relative_target(address, size, text):
    """pi32v2 displacements are relative to the END of each 2/4/6-byte instruction."""
    match = re.search(r"\b(?:goto|call) (-?\d+)$", text)
    return (address + size + int(match[1])) & 0xFFFFFFFF if match else None


def main():
    t = table.load()
    candidates = {}
    # Precompute the first-word masks; properties in the table otherwise walk
    # the bit patterns for every word in every binary.
    first_words = [(i, i.mask >> (i.nbits - 16), i.value >> (i.nbits - 16)) for i in t.insns]

    def decode(data, offset):
        word = int.from_bytes(data[offset:offset + 2], "little")
        if word not in candidates:
            candidates[word] = SimpleNamespace(insns=[i for i, mask, value in first_words
                if word & mask == value])
        return codec.decode(candidates[word], data, offset)

    paths = sorted((ROOT / "analysis/firmware").glob("*/app.bin"))
    paths += [ROOT / "analysis/tank-mini/app.bin"]
    for path in paths:
        data = path.read_bytes()
        prefix, offset = [], 0
        while offset < 512:
            got = decode(data, offset)
            if got:
                insn, values, size = got
                prefix.append((offset, codec.format(insn, values)))
            else:
                size = 2
            offset += size
        ram_source = ram_size = None
        for i, (_, text) in enumerate(prefix):
            if text == "r4 = 29360128" and i + 2 < len(prefix):
                a = re.fullmatch(r"r1 = (\d+)", prefix[i + 1][1])
                b = re.fullmatch(r"r2 = (\d+)", prefix[i + 2][1])
                if a and b:
                    ram_source, ram_size = int(a[1]), int(b[1])
                    break
        if ram_source is None or not 0x2000120 <= ram_source < 0x2000120 + len(data):
            raise ValueError(f"cannot establish RAM relocation from reset code: {path}")
        ram_offset = ram_source - 0x2000120
        if ram_offset + ram_size > len(data):
            raise ValueError("RAM initialization exceeds binary bounds")
        maps = {"flash_base": 0x2000120, "ram_source": ram_source,
                "ram_destination": 0x1c00000, "ram_size": ram_size,
                "evidence": "r4 destination, r1 source, r2 length in reset copy loop"}
        (path.parent / "memory-layout.json").write_text(json.dumps(maps, indent=2), encoding="utf-8")
        regions = [("flash", data[:ram_offset], 0x2000120),
                   ("ram", data[ram_offset:ram_offset + ram_size], 0x1c00000)]
        for name, raw, base in regions:
            offset = known = unknown = 0
            with (path.parent / f"{name}.asm").open("w", encoding="utf-8") as out:
                out.write("; Linear scan: includes embedded data. Not all decoded words are instructions.\n")
                while offset < len(raw):
                    got = decode(raw, offset)
                    comment = ""
                    if got:
                        insn, values, size = got
                        text = codec.format(insn, values)
                        known += 1
                        target = relative_target(base + offset, size, text)
                        if target is not None:
                            comment = f" ; target 0x{target:08x}"
                        elif re.fullmatch(r"(?:r\d+|sp|ssp|reti|rets|usp) = \d+", text):
                            value = int(text.rsplit(" ", 1)[1])
                            if value >= 65536:
                                comment = f" ; 0x{value:08x}"
                    else:
                        size = min(2, len(raw) - offset)
                        text = ".byte " + raw[offset:offset + size].hex(" ")
                        unknown += 1
                    out.write(f"{base + offset:08x}  {raw[offset:offset + size].hex(' '):<18} {text}{comment}\n")
                    offset += size
            print(f"{path.parent.name}/{name}: {known} decoded candidates, {unknown} unknown words", flush=True)


if __name__ == "__main__":
    main()
