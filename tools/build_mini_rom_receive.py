"""Build the HYRX RAM-only receive observer; no transport or device I/O."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "firmware/mini/rom_receive"
OUT = ROOT / "build/mini-rom-receive"
BASES, SPAN, RECORD_BYTES, MAX_BYTES = (0x1C20000, 0x1C28000), 32768, 512, 260


def sha(data): return hashlib.sha256(data).hexdigest()
def require(condition, message):
    if not condition: raise ValueError(message)


def inspect_elf(raw, base):
    def read(fmt, offset):
        require(0 <= offset <= len(raw)-struct.calcsize(fmt), "truncated ELF structure")
        return struct.unpack_from(fmt, raw, offset)
    require(base in BASES and raw[:7] == b"\x7fELF\x01\x01\x01", "wrong ELF/slot")
    h = read("<HHIIIIIHHHHHH", 16)
    require(h[:4] == (2, 0xF1, 1, base) and h[7] == 52 and h[8] == 32 and h[10] == 40,
            "wrong pi32v2 header/entry")
    segments = [read("<8I", h[4]+i*h[8]) for i in range(h[9])]
    segments = [p for p in segments if p[0] == 1]
    require(len(segments) == 1, "one owned RAM segment required")
    p = segments[0]
    require(p[2] == p[3] == base and 0 < p[4] <= p[5] <= SPAN and p[6] == 7,
            "load segment outside owned slot")
    require(p[1] <= len(raw)-p[4] and p[7] > 0 and not p[7] & (p[7]-1)
            and p[1] % p[7] == base % p[7], "invalid segment mapping")
    sections = [read("<10I", h[5]+i*h[10]) for i in range(h[11])]
    symbols, ranges = {}, []
    for s in sections:
        _, kind, flags, address, offset, size, link, _, align, stride = s
        require(kind == 8 or 0 <= offset <= len(raw)-size, "truncated section")
        if flags & 2:
            require(kind in (1, 8) and base <= address <= base+p[5]
                    and size <= base+p[5]-address and (not align or address % align == 0), "section outside RAM")
            if kind == 8:
                require(address >= base+p[4], "BSS overlaps image")
            elif size:
                require(address <= base+p[4]-size and offset == p[1]+address-base, "section bytes not mapped")
            if size: ranges.append((address,address+size))
        if kind != 2: continue
        require(stride == 16 and size % 16 == 0 and link < len(sections), "invalid symbols")
        st = sections[link]
        require(st[1] == 3 and st[4] <= len(raw)-st[5], "invalid string table")
        names = raw[st[4]:st[4]+st[5]]
        for off in range(offset,offset+size,16):
            name,value,count,info,_,index = read("<IIIBBH",off)
            if not name: continue
            require(name < len(names) and b"\0" in names[name:], "invalid symbol name")
            text = names[name:names.index(0,name)].decode("ascii")
            require(index or info >> 4 not in (1,2), "undefined symbol: "+text)
            if index: symbols[text] = {"address":value,"bytes":count,"type":info & 15}
    ranges.sort()
    require(all(a[1] <= b[0] for a,b in zip(ranges,ranges[1:])), "overlapping sections")
    required = ("hyperrig_receive_entry","hyperrig_receive_initialize","hyperrig_receive_dispatch",
                "hyperrig_receive_record","state","__slot_start","__slot_end","__image_file_end",
                "__bss_start","__bss_end")
    require(all(n in symbols for n in required), "missing receive probe symbol")
    at = lambda n:symbols[n]["address"]
    require(at("hyperrig_receive_entry") == at("__slot_start") == base and at("__slot_end") == base+SPAN
            and at("__image_file_end") == at("__bss_start") == base+p[4] and at("__bss_end") == base+p[5],
            "linker bounds differ")
    spans=[]
    for name in ("state","hyperrig_receive_record"):
        item=symbols[name]
        require(base+p[4] <= item["address"] <= base+p[5]-item["bytes"] and item["bytes"] > 0,
                "private state outside own BSS")
        spans.append((item["address"],item["address"]+item["bytes"]))
    spans.sort()
    require(spans[0][1] <= spans[1][0] and symbols["hyperrig_receive_record"]["bytes"] == RECORD_BYTES,
            "private state/record overlap or extent differs")
    forbidden=("spi", "flash", "codec", "gpio", "mmio", "hal_reset", "wren")
    require(not any(any(part in n.lower() for part in forbidden) for n in symbols), "peripheral symbol linked")
    payload=raw[p[1]:p[1]+p[4]]
    return payload,symbols,{"base":base,"entry":base,"span":SPAN,"payload_bytes":len(payload),
            "memory_bytes":p[5],"state_bytes":symbols["state"]["bytes"],"record_address":at("hyperrig_receive_record"),
            "record_bytes":RECORD_BYTES,"elf_sha256":sha(raw),"payload_sha256":sha(payload)}


def poison(length, seed):
    return bytes((seed ^ (i*73+0xA5)) & 255 for i in range(length))


def inspect_generated_stack(listing):
    """Record compiler save frames; ROM callback stack use remains unknown."""
    frames={};current=None
    for line in listing.splitlines():
        label=re.fullmatch(r"([A-Za-z_][A-Za-z_0-9]*):",line.strip())
        if label: current=label[1];frames[current]=0;continue
        if "sp" not in line or ":" not in line: continue
        push=re.search(r"\[--sp\] = \{([^}]+)\}",line)
        if push:
            require(current is not None and frames[current]==0,"unexpected second stack save")
            count=0
            for register in push[1].split(","):
                register=register.strip();pair=re.fullmatch(r"r(\d+)-r(\d+)",register)
                count+=abs(int(pair[1])-int(pair[2]))+1 if pair else 1
            frames[current]=count*4
        elif "[sp++]" not in line:
            # Ignore source/symbol names containing 'dispatch'; actual stack
            # expressions outside the supported saves/restores need review.
            require(not re.search(r"\bsp\b",line),"unreviewed generated stack operation")
    require(frames.get("hyperrig_receive_dispatch")==44 and frames.get("guard_mask")==24,
            "generated frame changed; review the callback stack before freezing")
    return {"function_save_bytes":frames,"dispatch_plus_largest_helper_bytes":68,
            "internal_ROM_callback_stack_included":False,"inherited_stack_capacity_qualified":False}


def validate_record(raw, *, base, build_tag, sequence, nonce, payload, seed):
    require(len(raw) == RECORD_BYTES and raw[:4] == b"HYRX" and raw[508:] == b"DONE", "HYRX record framing differs")
    require(zlib.crc32(raw[:504]) == int.from_bytes(raw[504:508],"little"), "HYRX record checksum differs")
    w=struct.unpack_from("<24I",raw)
    require(w[1] == 1 and w[2] == base and w[3] == build_tag and w[4] == sequence and w[5] == nonce
            and w[6] == len(payload) and w[9] == seed and w[10] == zlib.crc32(payload), "HYRX identity/request differs")
    require(1 <= len(payload) <= MAX_BYTES and w[7] <= 4 and w[8] <= 5 and w[14] <= 1 and w[15] <= 1
            and w[16] <= 3 and w[17] <= 3 and w[18] <= 1 and w[21] <= 1 and w[22] <= 1 and w[23] >= 1,
            "HYRX invalid observation fields")
    require(raw[108:128] == bytes(20) and raw[420:504] == bytes(84), "HYRX reserved bytes differ")
    observed=raw[128:128+len(payload)]; tail=raw[128+len(payload):388]
    all_poison=poison(MAX_BYTES,seed)
    expected_prefix=bytes((0x69 ^ i*11) & 255 for i in range(16))
    expected_suffix=bytes((0xD3 ^ i*11) & 255 for i in range(16))
    guards=int(raw[388:404] == expected_prefix) | (int(raw[404:420] == expected_suffix)<<1)
    changed=sum(a != b for a,b in zip(observed,all_poison))
    require(w[12] == zlib.crc32(observed) and w[17] == guards and w[18] == int(tail == all_poison[len(payload):])
            and w[20] == changed and w[19] <= len(payload), "HYRX sample counters/CRC differ")
    raw_return=struct.unpack_from("<i",raw,52)[0]
    if w[15] and w[21]:
        require(w[11] == w[12] and w[19] == w[20], "HYRX stable sample disagrees with immediate sample")
    complete=(w[7] == 3 and w[8] == 0 and w[14] == w[15] == w[22] == 1 and w[16] == w[17] == 3
              and w[18] == w[21] == 1 and observed == payload and w[11] == w[10])
    return {"record_valid":True,"state":w[7],"error":w[8],"sequence":sequence,"nonce":nonce,
            "length":len(payload),"raw_return":raw_return,"callback_entered":bool(w[14]),
            "callback_returned":bool(w[15]),"data_matches_expected":observed == payload,
            "observed_complete_and_stable":complete,"canary_mask":guards,"sample_count":w[23],
            "changed_bytes":changed,"return_semantics_qualified":False,"synchronous_completion_proven":False,
            "rom_pointer_observations":dict(zip(("send","receive","handler_slot"),struct.unpack_from("<3I",raw,96))),
            "pointer_address_map_validated":False,
            "record_sha256":sha(raw),"record_hex":raw.hex()}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=sorted(p for p in SOURCES.iterdir() if p.is_file())
    tag=int(sha(b"".join(p.read_bytes() for p in sources))[:8],16)
    (OUT/"build_tag.h").write_text(f"#define HYPERRIG_RECEIVE_BUILD_TAG UINT32_C(0x{tag:08x})\n",encoding="utf-8",newline="\n")
    prefix=["wsl.exe","--distribution","Ubuntu","--exec"] if os.name == "nt" else []
    def run(args):
        r=subprocess.run(prefix+args,cwd=ROOT,text=True,capture_output=True)
        if r.returncode: raise RuntimeError(" ".join(args)+"\n"+r.stdout+r.stderr)
        return r.stdout
    common=["-std=c99","-Wall","-Wextra","-Werror","-Ifirmware/mini/rom_receive","-Ibuild/mini-rom-receive"]
    core="firmware/mini/rom_receive/rom_receive.c"
    run(["gcc",*common,"-O1","-g","-fsanitize=address,undefined","-fno-sanitize-recover=all",
         core,"firmware/mini/rom_receive/host_test.c","-o","build/mini-rom-receive/host-sanitize"])
    host=json.loads(run(["build/mini-rom-receive/host-sanitize"]))
    vendor="tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/"
    objects=[]
    for source in ["firmware/mini/rom_receive/entry.c",core]:
        obj="build/mini-rom-receive/"+Path(source).stem+".o"
        run([vendor+"clang","-target","pi32v2","-mcpu=r3",*common,"-Os","-ffreestanding","-fno-builtin",
             "-DHYPERRIG_RECEIVE_TARGET","-c",source,"-o",obj])
        objects.append(obj)
    artifacts=[]
    for base in BASES:
        name=f"build/mini-rom-receive/hyperrig-receive-{base:08x}"
        run([vendor+"ld","-z","max-page-size=0x20","-z","common-page-size=0x20","--defsym",f"PROBE_ADDRESS={base}",
             "-T","firmware/mini/rom_receive/receive.ld",*objects,"-Map",name+".map","-o",name+".elf"])
        flat,symbols,item=inspect_elf((ROOT/(name+".elf")).read_bytes(),base)
        (ROOT/(name+".bin")).write_bytes(flat)
        listing=run([vendor+"objdump","-d",name+".elf"])
        (ROOT/(name+".asm")).write_text(listing,encoding="utf-8",newline="\n")
        item["generated_stack"]=inspect_generated_stack(listing)
        item.update(file=name+".bin",elf=name+".elf",symbols=symbols)
        artifacts.append(item)
    payload=bytes((0x55 ^ (i*73+0xA5) ^ 0xFF) & 255 for i in range(260))
    checks={}
    for kind in ("complete","partial","late"):
        record=(OUT/f"host-{kind}.bin").read_bytes()
        item=validate_record(record,base=BASES[0],build_tag=tag,sequence=1,nonce=0x1234ABCD,payload=payload,seed=0x55)
        item.pop("record_hex");checks[kind]=item
    require(checks["complete"]["observed_complete_and_stable"] and not checks["partial"]["data_matches_expected"]
            and checks["late"]["error"] == 5, "host record negative controls differ")
    tracked=sources+[Path(__file__),ROOT/"tools/probe_mini_receive.py",ROOT/"tests/test_mini_receive_protocol.py",
                     ROOT/"tools/probe_mini_recovery.py"]
    report={"project":"HyperRig","kind":"HYRX RAM-only receive observer","build_tag":tag,
            "source_sha256":{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in tracked},
            "host":{**host,"asan":True,"ubsan":True,"saved_record_checks":checks},"artifacts":artifacts,
            "hardware_executed":False,"hardware_mmio_available":False,"NVM_commands_available":False,
            "callback_receive_return_semantics_qualified":False,"callback_synchronous_completion_proven":False,
            "pointer_observations":{"record_offsets":[96,100,104],"host_64_bit_values_truncated_to_low32":True,
                                    "only_target_observations_are_ROM_pointers":True,"extra_memory_read":False},
            "flashable":False,"firmware_installation_package":False,
            "stack":{"private_stack":False,"reason":"small bounded RAM operations; callbacks remain on incoming ROM stack",
                     "inherited_stack_capacity_qualified":False},
            "protocol":{"identity":"FC82 IN16","arm":"FC83 seqBE16,lengthBE16,nonceBE32,CRC32BE,seed8,FF IN16",
                        "receive":"FB84 seqBE16,nonceBE32,lengthBE16,FF6 OUT exact length1..260",
                        "record":"FD85 FF14 IN512","automatic_retry":False,"nonce_is_authentication":False},
            "limits":["A blocked receive callback cannot be preempted by this observer; host timeout is ambiguous.",
                      "Stable record samples do not prove a synchronous callback or general error semantics.",
                      "Malformed OUT commands are refused without calling receive and may leave a stalled USB phase.",
                      "Private legacy flash commands are consumed/refused; only FB06/FD07/FB08 defer to ROM.",
                      "Send return <0 is retained as a refusal; its general semantics are also not inferred."]}
    (ROOT/"research/mini-rom-receive.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"host":host,"build_tag":tag,"artifacts":[{k:v for k,v in a.items() if k!="symbols"} for a in artifacts]}))


if __name__ == "__main__": main()
