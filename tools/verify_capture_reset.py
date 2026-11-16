"""Compare capture reset C with original instructions, including caller integration."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from capture_reset_machine import CaptureResetProgram, REGIONS, ROOT, EXTRA, ARENA, ARENA_BYTES, WRAP, WRAP_BYTES
from capture_dispatch_machine import CONTEXT, DSP, RESET, PARSER, LAYERS, image_offset
from capture_container_machine import SOURCE, CACHED, EMBEDDED, HEAP, ALLOCATE, FREE, LOADER
from control_machine import GLOBAL, STATE
from preset_storage_machine import READ
from verify_capture_dispatch import (CState as DispatchState, CMemory as DispatchMemory, Runtime, IO, ContainerIO,
    SERVICE, READ_CALLBACK, MAPPING, METADATA_CALLBACK, PARSER_CALLBACK, U32, BYTE_POINTER,
    Reads, Script, ParserScript, heap_first, baseline as dispatch_baseline, slot_reads, request, record_reads)

LENGTH_TABLE, POINTER_TABLE = ARENA + 0x100, ARENA + 0x200
RINGS, MAIN_RING, AUX_RINGS, FINAL_RING = ARENA + 0x1000, ARENA + 0x4000, ARENA + 0x8000, ARENA + 0xC000


def put(data, offset, value, size=4):
    data[offset:offset + size] = (value & ((1 << (8 * size)) - 1)).to_bytes(size, "little")


def baseline(layers=2, channels=3, layer_length=0, span=0, auxiliary=False, auxiliary_length=0, final_length=0):
    memory = dispatch_baseline() + (bytearray([0xA7] * ARENA_BYTES), bytearray([0xB9] * WRAP_BYTES))
    context, records, arena = memory[22], memory[26], memory[27]
    context[78] = channels
    put(context, 84, layers, 2)
    for offset, value in ((80, MAIN_RING), (84, span), (88, 0xDEADBEEF), (92, LAYERS),
            (140, POINTER_TABLE if auxiliary else 0), (144, LENGTH_TABLE), (148, FINAL_RING), (152, final_length)):
        put(context, 76 + offset, value)
    for i in range(8):
        put(records, 80 * i + 68, RINGS + 1024 * i)
        put(records, 80 * i + 76, layer_length)
        put(arena, 0x100 + i * 4, auxiliary_length)
        put(arena, 0x200 + i * 4, AUX_RINGS + 1024 * i)
    return memory


class ResetIO(ctypes.Structure):
    _fields_ = [("map", MAPPING), ("opaque", ctypes.c_void_p)]


class CState(DispatchState):
    def __init__(self, memory):
        super().__init__(memory[:27])
        self.arena = (ctypes.c_uint8 * ARENA_BYTES).from_buffer_copy(memory[27])
        self.wrap = (ctypes.c_uint8 * WRAP_BYTES).from_buffer_copy(memory[28])

    def snapshot(self):
        return super().snapshot() + (bytes(self.arena), bytes(self.wrap))

    def mapping(self, address, count, writable):
        for (base, size), array in zip(EXTRA, (self.arena, self.wrap)):
            offset = (address - base) & 0xFFFFFFFF
            if offset + count <= size and address + count <= 0x100000000:
                return ctypes.addressof(array) + offset
        return super().mapping(address, count, writable)


class CMemory(DispatchMemory):
    def __init__(self, state):
        super().__init__(state)
        for (base, _), array in zip(EXTRA, (state.arena, state.wrap)):
            self.extra.update({(base + i) & 0xFFFFFFFF: (array, i) for i in range(len(array))})


def configure(library):
    runtime, io = ctypes.POINTER(Runtime), ctypes.POINTER(IO)
    signatures = {"reset": [BYTE_POINTER, ctypes.POINTER(ResetIO)],
        "load_context": [runtime, U32, U32, U32, U32, io], "load": [runtime, U32, U32, U32, U32, io],
        "cleanup": [runtime, io], "install": [runtime, U32, U32, U32, BYTE_POINTER, io], "slot": [runtime, U32, io]}
    result = {}
    for name, signature in signatures.items():
        fn = getattr(library, "hyperrig_capture_reset" + ("" if name == "reset" else "_" + name))
        fn.argtypes, fn.restype = signature, ctypes.c_int
        result[name] = fn
    return result


def c_run(functions, memory, operation, arguments=(), reads=(), plan=None, parses=None, blocked=None):
    state, calls, clears, errors, flash = CState(memory), [], [], [], Reads(reads)
    script, parser = Script(plan, heap_first=heap_first(operation, arguments)), ParserScript(parses)
    def service(_opaque, svc, a, b, c, d):
        try:
            if svc == RESET:
                raise AssertionError("reset escaped to a synthetic service")
            args = a, b, c, d
            calls.append((svc, args, state.snapshot()))
            result = script(svc, args, CMemory(state))
            if svc == ALLOCATE and result == HEAP:
                state.allocation_size = a
            return result
        except Exception as error:
            errors.append(error)
            return 1
    def read(_opaque, address, destination, size):
        try:
            label, offset = state.target(destination, size)
            calls.append((READ, (address, label, offset, size), state.snapshot()))
            result, data = flash.read(address, size, CMemory(state))
            if data:
                ctypes.memmove(destination, data, len(data))
            return result
        except Exception as error:
            errors.append(error)
            return 1
    def metadata(_opaque, slot, header, identity):
        try:
            from capture_container_machine import METADATA
            args = slot, ctypes.string_at(header, 40), identity, 0
            calls.append((METADATA, args, state.snapshot()))
            return script(METADATA, args, CMemory(state))
        except Exception as error:
            errors.append(error)
            return 1
    def parse(_opaque, context, ledger, source, length):
        try:
            label = CONTEXT if ctypes.cast(context, ctypes.c_void_p).value == ctypes.addressof(state.dispatch.dsp) + 76 else "query"
            args = label, tuple(ledger[i] for i in range(3)), source, length
            calls.append((PARSER, args, state.snapshot()))
            return parser(args, ledger, CMemory(state))
        except Exception as error:
            errors.append(error)
            return 1
    def mapping(_opaque, address, count, writable):
        try:
            if blocked is not None and blocked(address, count, writable):
                return None
            pointer = state.mapping(address, count, writable)
            if pointer and writable and count == 4 and not HEAP <= address < HEAP + 8192:
                clears.append((address, int.from_bytes(ctypes.string_at(pointer, 4), "little")))
            return pointer
        except Exception as error:
            errors.append(error)
            return None
    callbacks = SERVICE(service), READ_CALLBACK(read), MAPPING(mapping), METADATA_CALLBACK(metadata)
    io = IO(ContainerIO(*callbacks, None), PARSER_CALLBACK(parse))
    if operation == "reset":
        direct = ResetIO(callbacks[2], None)
        context = ctypes.cast(ctypes.byref(state.dispatch.dsp, 76), BYTE_POINTER)
        result = functions[operation](context, ctypes.byref(direct))
    else:
        args = [ctypes.byref(state.dispatch), *arguments]
        if operation == "install":
            args.append(state.request)
        result = functions[operation](*args, ctypes.byref(io))
    if errors:
        raise errors[0]
    return {"result": result & 0xFFFFFFFF, "memory": state.snapshot(), "calls": calls,
            "clears": clears, "reads": flash.requests}


def verify(library_path, output, mini_image=None):
    if not __debug__:
        raise RuntimeError("run verification without Python optimization")
    program, functions = CaptureResetProgram(), configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, words, reset_entries, alias_cases = dict.fromkeys(functions, 0), set(), 0, 0, 0
    def compare(memory, operation="reset", *arguments, reads=(), plan=None, parses=None):
        nonlocal words, reset_entries
        flash = Reads(reads)
        original = program.execute(memory, operation, *arguments, reader=flash.read,
            boundary=Script(plan, heap_first=heap_first(operation, arguments)), parser=ParserScript(parses))
        actual = c_run(functions, memory, operation, arguments, reads, plan, parses)
        for key in ("result", "memory", "calls", "clears"):
            if original[key] != actual[key]:
                if key == "memory":
                    detail = [(i, next((j for j,(a,b) in enumerate(zip(x,y)) if a!=b), None))
                              for i,(x,y) in enumerate(zip(actual[key],original[key])) if i!=2 and x!=y]
                else:
                    detail = (actual[key], original[key]) if key=="result" else (len(actual[key]),len(original[key]))
                raise AssertionError((operation,arguments,key,detail))
        assert flash.requests == actual["reads"] and len(flash.requests) == len(reads)
        counts[operation] += 1
        coverage.update(original["visited"])
        words += len(original["clears"])
        reset_entries += original["reset_entries"]
        return original

    for layers in (0, 1, 2, 4):
        for channels in (0, 1, 2, 3, 4):
            for length in (0, 1, 0xFFFFFFC0, 0xFFFFFFC1, 0xFFFFFFFF):
                compare(baseline(layers, channels, length))
    for span in (0, 1, 62, 63, 64, 65, 127, 0xFFFFFFBF, 0xFFFFFFFE, 0xFFFFFFFF):
        for channels in (0, 1, 3, 255):
            memory = baseline(0, channels, span=span)
            count = ((((span + 1) & 0xFFFFFFFF) + min((span + 1) & 0xFFFFFFFF,64)) * channels) & 0xFFFFFFFF
            if count <= 4096:
                compare(memory)
    for layers in (0, 1, 3):
        for auxiliary in (False, True):
            for length in (0, 1, 0xFFFFFFC0, 0xFFFFFFC1, 0xFFFFFFFF, 0x55555516):
                compare(baseline(layers, 3, 0xFFFFFFC0, 0xFFFFFFFF, auxiliary, length, length))
    # A layer count is retained even with zero channels; descriptor size words are read.
    compare(baseline(8, 0, 0xFFFFFFFF, 0xFFFFFFFF, True))
    # Nonzero factors can wrap their product to zero or a small mapped span.
    for channels, length in ((4,0x3FFFFFC0),(4,0x3FFFFFC1),(2,0x7FFFFFC1),(255,0xFEFEFEBF)):
        compare(baseline(1,channels,length,0xFFFFFFFF))
    # Wrapped word-address increments: 0xfffffffc is followed by 0, then 4.
    memory = baseline(1, 1, 0xFFFFFFC2, 0xFFFFFFFF)
    put(memory[26], 68, WRAP)
    compare(memory)
    memory = baseline(0, 1, span=1)
    put(memory[22], 76 + 80, WRAP)
    compare(memory)
    # A ring overwrites its own size word. Original code rereads it after the store.
    memory = baseline(1, 1, 0xFFFFFFFF, 0xFFFFFFFF)
    put(memory[26], 68, LAYERS + 76)
    compare(memory)
    alias_cases += 1
    memory = baseline(1, 3, 0xFFFFFFC0, 0xFFFFFFFF, True, 0xFFFFFFFF, 0xFFFFFFC0)
    put(memory[27], 0x200, LENGTH_TABLE)
    compare(memory)
    alias_cases += 1
    # Main-ring clearing changes auxiliary lengths before those loops start.
    memory = baseline(1, 3, 0xFFFFFFC0, 0, True, 0xFFFFFFFF, 0xFFFFFFC0)
    put(memory[22], 76 + 80, LENGTH_TABLE)
    compare(memory)
    alias_cases += 1
    rng = random.Random(0x128782026)
    for _ in range(32):
        memory = baseline(rng.randrange(5), rng.randrange(5), rng.randrange(10), rng.randrange(70), bool(rng.randrange(2)))
        compare(memory)
    print("Reset spans, preserved bytes, unsigned wrapping and aliased size rereads passed.", flush=True)

    for operation in ("load_context", "load"):
        for channels in (0, 1, 3):
            for layers in (0, 1, 3):
                compare(baseline(layers, channels, auxiliary=True), operation, ARENA + 3, 512, SOURCE, 128)
        for error in (-17, 1, 0x80000000):
            compare(baseline(), operation, ARENA, 512, SOURCE, 128, parses={0:(error,(None,64,None),())})
        compare(baseline(), operation, 0, 512, SOURCE, 128)
        compare(baseline(), operation, ARENA, 8, SOURCE, 128)
    for source in (SOURCE, CACHED, EMBEDDED):
        for auxiliary in (False, True):
            compare(baseline(auxiliary=auxiliary), "install", source, 8, 0)
    for slot in (0,2,14):
        compare(baseline(auxiliary=True), "slot", slot, reads=slot_reads())
    compare(baseline(), "cleanup")
    compare(baseline(), "install", SOURCE, 8, 0, parses={1:(-19,(None,64,None),())})
    # A later synthetic parser changes ring data; cleanup must reset that new data too.
    compare(baseline(), "install", SOURCE, 8, 0, parses={1:(-19,(None,64,None),()),
        3:(0,(None,64,None),((RINGS,0x12345678,4),))})
    memory=baseline(); memory[22][78]=1
    compare(memory, "install", SOURCE,8,0)
    print("Real reset loops in load/context/cleanup/container/slot callers passed.", flush=True)

    invalid, guards = 0, 0
    context=(ctypes.c_uint8*228)(); seen=[]
    mapping=MAPPING(lambda *args:seen.append(args) or None)
    direct=ResetIO(mapping,None)
    for args in ((None,ctypes.byref(direct)),(context,None),(context,ctypes.byref(ResetIO()))):
        assert functions["reset"](*args)==-200 and not seen
        invalid+=1
    state=CState(baseline())
    io=IO(ContainerIO(SERVICE(),READ_CALLBACK(),MAPPING(),METADATA_CALLBACK(),None),PARSER_CALLBACK())
    for op,args in (("load_context",(ARENA,512,SOURCE,8)),("load",(ARENA,512,SOURCE,8)),("cleanup",()),
                    ("install",(SOURCE,8,0,state.request)),("slot",(2,))):
        for rt,iop in ((None,ctypes.byref(io)),(ctypes.byref(state.dispatch),None),(ctypes.byref(state.dispatch),ctypes.byref(io))):
            before=state.snapshot()
            assert functions[op](rt,*args,iop)==-200 and state.snapshot()==before
            invalid+=1
    for address in (LAYERS+76,LAYERS+68,RINGS,RINGS+4,MAIN_RING,POINTER_TABLE,LENGTH_TABLE,AUX_RINGS,FINAL_RING):
        memory=baseline(auxiliary=True)
        result=c_run(functions,memory,"reset",blocked=lambda a,n,w:a==address)
        assert result["result"]==(-201)&0xFFFFFFFF
        assert result["memory"][22][164:168]==memory[22][164:168]
        guards+=1
    for op,args,reads in (("load_context",(ARENA,512,SOURCE,8),()),("load",(ARENA,512,SOURCE,8),()),("cleanup",(),()),
                         ("install",(SOURCE,8,0),()),("slot",(2,),slot_reads())):
        memory=baseline()
        result=c_run(functions,memory,op,args,reads,blocked=lambda a,n,w:a==RINGS+4)
        assert result["result"]==(-201)&0xFFFFFFFF
        assert result["memory"][27][0x1000:0x1004]==bytes(4)
        assert result["memory"][27][0x1004:0x1008]==memory[27][0x1004:0x1008]
        if op in ("install","slot"):
            assert result["memory"][0][60:68]==memory[0][60:68]
            assert result["memory"][1][676:680]==memory[1][676:680]
            assert any(svc==FREE and args[0]==HEAP for svc,args,_ in result["calls"])
        if op in ("install","slot","cleanup"):
            assert result["memory"][1][500]==0
        if op=="slot":assert result["memory"][0][9]==memory[0][9]
        guards+=1
    for op,args,reads in (("install",(SOURCE,8,0),()),("slot",(2,),slot_reads())):
        memory=baseline()
        result=c_run(functions,memory,op,args,reads,blocked=lambda a,n,w:a==LAYERS and n==1)
        assert result["result"]==(-201)&0xFFFFFFFF
        assert result["memory"][0][60:68]==memory[0][60:68]
        assert result["memory"][1][676:680]==memory[1][676:680]
        assert result["memory"][1][500]==1  # The previous capture reset succeeded.
        if op=="slot":assert result["memory"][0][9]==memory[0][9]
        guards+=1
    new_code=set(program.code)-program.pre_reset_code
    assert not new_code-coverage,[hex(pc) for pc in sorted(new_code-coverage)]
    mini_binding=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!="d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2":
            raise ValueError("MINI image is not the reviewed v4 application")
        app=unpack_app(raw)[2]["app.bin"]
        for name,(start,end) in REGIONS.items():assert app[image_offset(start):image_offset(end)]==program.reset_regions[name]
        mini_binding={"image_sha256":digest,"all_reset_regions_byte_identical":True}
    inherited=json.loads((ROOT/"build/reverse-capture-dispatch-03/verification.json").read_text())
    sources=set(inherited["source_sha256"])
    sources.update(("firmware/src/hyperrig_capture_reset.c","firmware/include/hyperrig/hyperrig_capture_reset.h",
        "tools/capture_reset_machine.py","tools/verify_capture_reset.py","tools/build_capture_reset.py",
        "tests/test_capture_reset_machine.py","tests/capture_reset_sanitize.c"))
    report={"schema":1,"project":"HyperRig","result":"pass",
        "original_image_sha256":inherited["original_image_sha256"],
        "functions":{name:{"start":start,"end_exclusive":end,"bytes_sha256":hashlib.sha256(program.reset_regions[name]).hexdigest()}
                     for name,(start,end) in REGIONS.items()},
        "comparisons":counts,"total_comparisons":sum(counts.values()),"reset_entries":reset_entries,
        "compared_zero_word_writes":words,"alias_cases":alias_cases,"invalid_api_checks":invalid,"mapping_guard_checks":guards,
        "instruction_coverage":{"new_decoded":len(new_code),"new_visited":len(new_code&coverage),
            "all_decoded":len(program.code),"all_visited":len(coverage),"unvisited_new":[]},
        "compared":["semantic results","all 29 mapped regions including preserved neighboring bytes",
            "ordered reset word addresses and pre-write values","ordered service/parser arguments and state snapshots"],
        "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(sources)},
        "library_sha256":hashlib.sha256(library_path.read_bytes()).hexdigest(),"mini_v4_binding":mini_binding,
        "limitations":["whole raw parser remains synthetic; no native capture sample processing",
            "mapping is pure/consistent and disjoint from context/IO; mapped arrays may alias",
            "verifier uses up to 8 layers, 65536 arena bytes and 4096 wrapped-address bytes",
            "unmapped accesses are new partial-write guards, not original behavior",
            "allocator, metadata lookup, storage, scheduling, mode and priority remain external"],
        "hardware_test":False,"audio_test":False,"firmware_changed":False}
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("result","total_comparisons","reset_entries","compared_zero_word_writes","instruction_coverage")}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mini-image",type=Path)
    args=parser.parse_args()
    if args.output.exists():parser.error("preserve existing reports; choose a new path")
    verify(args.library,args.output,args.mini_image)
