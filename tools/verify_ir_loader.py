"""Compare IR ownership/loading C with original instructions and synthetic services."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import zlib

from ir_loader_machine import (IrLoaderProgram, REGIONS, SERVICES, ROOT, GLOBAL, STATE,
    HEADER_BUFFER, HEAP, CALLBACK, CAPACITY, ALLOCATE, FREE, LOCK, UNLOCK, INSTALL,
    INSTALL_SLOT, OWNS, REFRESH, NOTIFY, PRIORITY, POLL, READ, ACTIVITY)
from preset_assets_machine import REGIONS as ASSET_REGIONS
from preset_storage_machine import REGIONS as STORAGE_REGIONS
from selection_machine import REGIONS as SELECTION_REGIONS
from verify_preset_assets import baseline as asset_baseline, CState as AssetState, CMemory as AssetMemory, Reads
from verify_preset_storage import Storage, READ_CALLBACK

SERVICE = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, *([ctypes.c_uint32] * 5))
class Runtime(ctypes.Structure):
    _fields_ = [("storage", Storage), ("callback", ctypes.c_uint8 * 4)]
class IO(ctypes.Structure):
    _fields_ = [("call", SERVICE), ("read", READ_CALLBACK), ("opaque", ctypes.c_void_p),
                ("allocation", ctypes.POINTER(ctypes.c_uint8)), ("capacity", ctypes.c_uint32)]


def baseline():
    memory = asset_baseline() + (bytearray(b"\x12\x34\x56\x78"), bytearray([0xA6] * CAPACITY))
    memory[0][10] = 255
    memory[1][152:180] = bytes(28)
    memory[1][1796:1812] = bytes(16)
    memory[4][:] = bytes((4, 2))
    memory[5][:] = bytes((0, 1, 2, 255)) + bytes(6) + bytes((0, 3)) + bytes(8)
    memory[6][:] = bytes(48)
    memory[6][:12] = bytes((7, 1, 1, 7, 0, 1, 7, 1, 0, 8, 1, 1))
    return memory


def record(payload=b"\x01\x02\x03\x04", tag=0x4A474B54, metadata=48000, crc=None):
    return struct.pack("<IIII", tag, len(payload), zlib.crc32(payload) if crc is None else crc, metadata) + bytes(24)


def load_reads(payload=b"\x01\x02\x03\x04", tag=0x4A474B54, metadata=48000):
    header = record(payload, tag, metadata)
    return [(0, header, ())] * (2 if tag == 0x49474B54 else 1) + [(0, header, ()), (0, payload, ())]


class CState(AssetState):
    def __init__(self, memory):
        super().__init__(memory[:15])
        self.ir = Runtime(self.storage, (ctypes.c_uint8 * 4).from_buffer_copy(memory[15]))
        self.storage = self.ir.storage
        self.allocation = (ctypes.c_uint8 * CAPACITY).from_buffer_copy(memory[16])
    def snapshot(self):
        return super().snapshot() + (bytes(self.ir.callback), bytes(self.allocation))
    def target(self, pointer, size):
        address = ctypes.cast(pointer, ctypes.c_void_p).value
        start = ctypes.addressof(self.allocation)
        if start <= address and address + size <= start + CAPACITY:
            return "allocation", address - start
        return super().target(pointer, size)


class CMemory(AssetMemory):
    def __init__(self, state):
        super().__init__(state)
        for base, array in ((CALLBACK, state.ir.callback), (HEAP, state.allocation)):
            self.extra.update({base + i: (array, i) for i in range(len(array))})


class Script:
    def __init__(self, plan=None):
        self.plan, self.counts = plan or {}, {}
    def __call__(self, service, args, view):
        index = self.counts.get(service, 0) + 1
        self.counts[service] = index
        result, writes = self.plan.get((service, index), self.plan.get(service, (HEAP if service == ALLOCATE else 0, ())))
        for address, value, size in writes:
            view.write(address, value, size)
        return result


def configure(library):
    u32, rt, io = ctypes.c_uint32, ctypes.POINTER(Runtime), ctypes.POINTER(IO)
    out = ctypes.POINTER(u32)
    signatures = {"pending": [rt, out], "query": [rt, out, out, out],
                  "attach": [rt, u32, u32, u32, u32, io], "refresh": [rt, io], "load": [rt, u32, u32, io]}
    result = {}
    for name, args in signatures.items():
        function = getattr(library, "hyperrig_ir_" + name)
        function.argtypes, function.restype = args, ctypes.c_int
        result[name] = function
    return result


def verify(library_path, output, mini_image=None):
    if not __debug__: raise RuntimeError("run without Python optimization")
    program, functions = IrLoaderProgram(), configure(ctypes.CDLL(str(library_path.resolve())))
    counts, coverage, visited_services = dict.fromkeys(functions, 0), set(), set()
    mutating = 0
    rng = random.Random(0x89728A62)
    def compare(memory, operation, *args, reads=(), plan=None):
        nonlocal mutating
        nr, cr, ns, cs = Reads(reads), Reads(reads), Script(plan), Script(plan)
        native = program.execute(memory, operation, *args, reader=nr.read, boundary=ns)
        state, calls, errors = CState(memory), [], []
        def service(_opaque, svc, a, b, c, d):
            try:
                calls.append((svc, (a, b, c, d), state.snapshot()))
                return cs(svc, (a, b, c, d), CMemory(state))
            except Exception as error:
                errors.append(error)
                return 0
        def read(_opaque, address, destination, size):
            try:
                label, offset = state.target(destination, size)
                calls.append((READ, (address, label, offset, size), state.snapshot()))
                status, data = cr.read(address, size, CMemory(state))
                if data: ctypes.memmove(destination, data, len(data))
                return status
            except Exception as error:
                errors.append(error)
                return 1
        call_cb, read_cb = SERVICE(service), READ_CALLBACK(read)
        io, result = IO(call_cb, read_cb, None, state.allocation, CAPACITY), ctypes.c_uint32(0xAABBCCDD)
        rt = ctypes.byref(state.ir)
        if operation == "pending":
            assert functions[operation](rt, ctypes.byref(result)) == 0
            actual = result.value
        elif operation == "query":
            first = ctypes.c_uint32.from_buffer(state.header, 0)
            second = ctypes.c_uint32.from_buffer(state.header, 4)
            assert functions[operation](rt, ctypes.byref(first), ctypes.byref(second), ctypes.byref(result)) == 0
            actual = result.value
        else:
            actual = functions[operation](rt, *args, ctypes.byref(io))
            if operation in ("attach", "refresh"):
                assert actual == 0
                actual = native["result"]  # Original void return register is incidental.
        if errors: raise errors[0]
        if ((actual & 0xFFFFFFFF) != native["result"] or state.snapshot() != native["memory"] or calls != native["calls"] or cr.requests != nr.requests):
            diffs = [(i, next((j for j,(a,b) in enumerate(zip(left,right)) if a!=b), None))
                     for i,(left,right) in enumerate(zip(state.snapshot(),native["memory"])) if i != 2 and left != right]
            mismatch = next((i for i,(a,b) in enumerate(zip(calls,native["calls"])) if a != b), None)
            raise AssertionError((operation,args,actual,native["result"],diffs,"calls",mismatch,
                calls[mismatch][:2] if mismatch is not None else len(calls),
                native["calls"][mismatch][:2] if mismatch is not None else len(native["calls"])))
        counts[operation] += 1
        coverage.update(native["visited"])
        visited_services.update(row[0] for row in calls)
        mutating += bool(plan and any(writes for _,writes in plan.values())) or any(row[2] for row in reads)
        return native

    for present in (0, 1, 2, 255):
        for handle in (0, HEAP, 0xFFFFFFFF):
            for pending in (0, 1, 256, 0xFFFFFFFF):
                memory = baseline()
                memory[1][160] = present
                struct.pack_into("<I", memory[1], 164, handle)
                struct.pack_into("<I", memory[1], 172, pending)
                struct.pack_into("<II", memory[1], 152, rng.getrandbits(32), rng.getrandbits(32))
                compare(memory, "pending")
                compare(memory, "query")
                for slot in (0, 7, 254, 255):
                    memory[0][10] = slot
                    compare(memory, "refresh")
    for old in (0, HEAP, HEAP + 100):
        for token in (0, HEAP, HEAP + 100):
            for fmt in (0, 1, 255, 0xFFFFFFFF):
                memory = baseline()
                struct.pack_into("<I", memory[1], 164, old)
                compare(memory, "attach", token, rng.getrandbits(32), rng.getrandbits(32), fmt)
    for svc in (LOCK, INSTALL, UNLOCK, FREE):
        memory = baseline()
        struct.pack_into("<I", memory[1], 164, HEAP + 100)
        compare(memory, "attach", HEAP, 1024, 48000, 1,
            plan={svc: (123, ((STATE + 164, HEAP + 200, 4), (STATE + 152, 42, 4)))})
    for svc in (LOCK, INSTALL_SLOT, UNLOCK, FREE):
        for status in (0, 1, 0xFFFFFFFF):
            memory = baseline()
            memory[0][10], memory[1][160] = 3, 1
            struct.pack_into("<I", memory[1], 164, HEAP)
            compare(memory, "refresh", plan={svc: (status, ((STATE + 164, HEAP + 40, 4), (STATE + 744, 99, 4)))})
    print("IR queries, attachment and pending-slot ownership comparisons passed.", flush=True)
    for tag in (0x4A474B54, 0x49474B54):
        for slot in (0, 1, 7, 8, 255, 256, 0xFFFFFFFF):
            for refresh in (0, 1):
                for size in (0, 1, 4, 7, 32):
                    payload = rng.randbytes(size)
                    compare(baseline(), "load", slot, refresh, reads=load_reads(payload,tag))
    for size in (255, 256, 257, 513, 1490, 8152):
        compare(baseline(), "load", 2, 0, reads=load_reads(rng.randbytes(size)))
    for same_slot in (False, True):
        for tag in (0x4A474B54, 0x49474B54):
            for size in (0, 7, 8152):
                memory = baseline()
                payload = bytes(size)
                header = record(payload, tag, 12345)
                if same_slot: memory[0][10] = 3
                else:
                    memory[1][1796:1812] = struct.pack("<BB2xIII", 1, int(tag == 0x4A474B54), zlib.crc32(payload), size, 12345)
                reads = [(0,header,())] * (1 if tag == 0x4A474B54 else 2)
                compare(memory, "load", 3, 1, reads=reads)
    for result in (0, 1, 0xFFFFFFFF):
        compare(baseline(), "load", 0, 0, reads=load_reads(), plan={INSTALL_SLOT:(result,())})
    for prefix in (0, 4, 39, 40):
        compare(baseline(), "load", 1, 0, reads=[(1,record()[:prefix],()),(1,record()[:prefix],())])
    compare(baseline(), "load", 1, 0, reads=[(0,record(),())], plan={ALLOCATE:(0,())})
    for outcome in ("header", "read", "crc", "tag"):
        reads = load_reads()
        if outcome == "header": reads = reads[:1] + [(1,b"",())]
        if outcome == "read": reads[-1] = (1,b"\x01",())
        if outcome == "crc": reads[-1] = (0,b"\0"*4,())
        if outcome == "tag": reads = reads[:1] + [(0,record(tag=0),())]
        compare(baseline(), "load", 2, 0, reads=reads)
    # Reloading a smaller accepted length stays within the initial allocation.
    compare(baseline(), "load", 1, 0, reads=[(0,record(bytes(16)),()),(0,record(b"xy"),()),(0,b"xy",())])
    for svc in (PRIORITY, ACTIVITY, ALLOCATE, NOTIFY, LOCK, UNLOCK, INSTALL, OWNS, REFRESH, INSTALL_SLOT):
        for value in (0, 1, 0xFFFFFFFF):
            mutation = ((STATE + 164, HEAP + 100, 4), (STATE + 744, 0x87654321, 4), (GLOBAL + 10, 6, 1))
            result = HEAP if svc == ALLOCATE else value
            compare(baseline(), "load", 2, 1, reads=load_reads(), plan={svc:(result,mutation)})
    print("IR reuse, full records, failures and mutating-service comparisons passed.", flush=True)

    state, seen = CState(baseline()), []
    call_cb = SERVICE(lambda *args: seen.append(args) or 0)
    read_cb = READ_CALLBACK(lambda *args: seen.append(args) or 0)
    io = IO(call_cb,read_cb,None,state.allocation,CAPACITY)
    rt, out = ctypes.byref(state.ir), ctypes.c_uint32(99)
    invalid = [("pending",(None,ctypes.byref(out))), ("pending",(rt,None)),
               ("query",(None,ctypes.byref(out),ctypes.byref(out),ctypes.byref(out))),
               ("query",(rt,None,ctypes.byref(out),ctypes.byref(out))),
               ("query",(rt,ctypes.byref(out),None,ctypes.byref(out))),
               ("query",(rt,ctypes.byref(out),ctypes.byref(out),None)),
               ("attach",(None,0,0,0,0,ctypes.byref(io))), ("attach",(rt,0,0,0,0,None)),
               ("refresh",(None,ctypes.byref(io))), ("refresh",(rt,None)),
               ("load",(None,0,0,ctypes.byref(io))), ("load",(rt,0,0,None))]
    for operation,args in invalid:
        before = state.snapshot()
        assert functions[operation](*args) == -200
        assert state.snapshot() == before and not seen and out.value == 99
    for bad in (IO(SERVICE(),read_cb,None,state.allocation,CAPACITY),
                IO(call_cb,READ_CALLBACK(),None,state.allocation,CAPACITY),
                IO(call_cb,read_cb,None,None,CAPACITY), IO(call_cb,read_cb,None,state.allocation,CAPACITY-1)):
        before=state.snapshot()
        assert functions["load"](rt,0,0,ctypes.byref(bad)) == -200
        assert state.snapshot()==before and not seen
    state.ir.storage.selection.counts[0]=11
    before=state.snapshot()
    assert functions["load"](rt,0,0,ctypes.byref(io))==-200 and state.snapshot()==before and not seen

    # A changed record length cannot exceed the allocation request in the C API.
    state=CState(baseline()); services=[]; reads=iter((record(b"12"),record(b"1234")))
    def guarded_call(_o,svc,a,b,c,d):
        services.append((svc,a,b,c,d))
        return HEAP if svc==ALLOCATE else 0
    def guarded_read(_o,addr,dest,size):
        assert size==40
        ctypes.memmove(dest,next(reads),40)
        return 0
    gc,gr=SERVICE(guarded_call),READ_CALLBACK(guarded_read)
    guarded_io=IO(gc,gr,None,state.allocation,CAPACITY)
    assert functions["load"](ctypes.byref(state.ir),0,0,ctypes.byref(guarded_io))==-201
    assert bytes(state.allocation)==bytes([0xA6]*CAPACITY)
    assert [row[0] for row in services][-4:]==[PRIORITY,FREE,NOTIFY,ACTIVITY]

    new=set(program.code)-program.pre_ir_code
    missing=sorted(new-coverage)
    assert not missing,[hex(pc) for pc in missing]
    mini_binding=None
    checked=[(REGIONS,program.ir_regions),(ASSET_REGIONS,program.assets_regions),
             (STORAGE_REGIONS,program.storage_regions),(SELECTION_REGIONS,program.selection_regions)]
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        if digest!='d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2':
            raise ValueError('MINI input is not reviewed v4')
        app=unpack_app(raw)[2]['app.bin']
        for regions,originals in checked:
            for name,(start,end) in regions.items():
                assert app[start-0x02000120:end-0x02000120]==originals[name],name
        mini_binding={'image_sha256':digest,'all_five_ir_and_twenty_five_dependency_regions_byte_identical':True}
    sources=[f'tools/{name}.py' for name in ('dot_machine','control_machine','control_action_machine','selection_machine',
        'preset_storage_machine','preset_preflight_machine','preset_assets_machine','ir_loader_machine',
        'verify_controls','verify_control_actions','verify_selection','verify_preset_storage','verify_preset_preflight',
        'verify_preset_assets','verify_ir_loader','build_ir_loader')]
    sources+=['tests/test_ir_loader_machine.py']
    for name in ('controls','control_actions','selection','preset_storage','preset_preflight','preset_assets','ir_loader'):
        sources+=[f'firmware/src/hyperrig_{name}.c',f'firmware/include/hyperrig/hyperrig_{name}.h']
    sources+=['upstream/pi32v2-isa/pi32v2isa/codec.py','upstream/pi32v2-isa/pi32v2isa/table.py',
              'upstream/pi32v2-isa/isa/pi32v2.toml','upstream/pi32v2-isa/hw/fm1-2026-10-24-v2/README.md']
    report={'schema':1,'project':'HyperRig','result':'pass','scope':'IR loading, record checks and ownership orchestration',
        'original_image_sha256':'2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059',
        'functions':{name:{'start':start,'end_exclusive':end,'bytes_sha256':hashlib.sha256(program.ir_regions[name]).hexdigest()}
                     for name,(start,end) in REGIONS.items()},
        'comparisons':counts,'total_comparisons':sum(counts.values()),'mutating_service_cases':mutating,
        'invalid_api_checks':len(invalid)+5,'allocation_growth_guard_checks':1,
        'instruction_coverage':{'new_visited':len(new&coverage),'new_decoded':len(new),'all_visited':len(coverage),
                              'all_decoded':len(program.code),'unvisited_new':missing},
        'external_services_visited':['read' if svc==READ else SERVICES[svc][0] for svc in sorted(visited_services)],
        'compared':['semantic returns','all previous mapped bytes','IR callback word','8152 allocation bytes',
                    'ordered read/service arguments and mapped state at each boundary'],
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},
        'mini_v4_binding':mini_binding,'library_sha256':hashlib.sha256(library_path.read_bytes()).hexdigest(),
        'hardware_test':False,'audio_test':False,'firmware_changed':False,
        'limitations':['allocation/free/DSP installation/locking/physical read remain scripted services',
            'allocation token is opaque, backed by caller storage; callback domain excludes allocation growth',
            'private header/stack bytes are not persistent compared state',
            'no capture loading, top-level preset application, actual IR convolution or persistence validation']}
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('result','total_comparisons','comparisons','instruction_coverage')}))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mini-image',type=Path)
    args=parser.parse_args()
    if args.output.exists(): parser.error('preserve existing reports; use a new output path')
    verify(args.library,args.output,args.mini_image)
