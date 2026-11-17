"""Compare the real sixth-parameter notification and borrowed request state."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

from dsp_transition_notification_machine import (DspTransitionNotificationProgram,REGIONS,GAIN_REGIONS,
    TRANSITION_REGIONS,MAPPED,PRIOR_MAPPED,STATE,GAIN_TABLE,GAIN_BYTES,INPUT,NOTIFICATION,ROOT,region_bytes)
from dsp_transition_machine import (AUDIO_REGIONS,DYNAMICS_REGIONS,INITIALIZATION_REGIONS,MATH_REGIONS,
    PRIOR_REGIONS,BiquadProgram,TABLE,PRIOR_TABLE,RESET_CONFIGURATION,AUDIO_STATIC,CONFIGURATION,CONTROL,CALLBACKS)
from verify_dsp_transition import SOURCES as TRANSITION_SOURCES,initial as transition_initial
from verify_dsp_audio_path import CState as AudioState,configure as configure_audio,U32,PINNED_IMAGE,MINI_IMAGE
from dot_machine import signed

CAPTURE_COMPONENTS=("controls","control_actions","selection","preset_storage","preset_assets","capture_loader")
SOURCES=tuple(dict.fromkeys((*TRANSITION_SOURCES,
    "hyperrig/jieli.py",
    *(f"firmware/src/hyperrig_{name}.c" for name in CAPTURE_COMPONENTS),
    *(f"firmware/include/hyperrig/hyperrig_{name}.h" for name in (*CAPTURE_COMPONENTS,"preset_preflight")),
    "firmware/include/hyperrig/hyperrig_dsp_transition_notification.h","firmware/src/hyperrig_dsp_transition_notification.c",
    "tools/dsp_transition_notification_machine.py","tools/verify_dsp_transition_notification.py",
    "tools/build_dsp_transition_notification.py","tests/test_dsp_transition_notification_machine.py",
    "tests/dsp_transition_notification_sanitize.c")))
MAP=ctypes.CFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,U32,U32,ctypes.c_int)
CALL=ctypes.CFUNCTYPE(U32,ctypes.c_void_p,U32,ctypes.POINTER(U32),U32)


class IO(ctypes.Structure):
    _fields_=[("map",MAP),("call",CALL),("opaque",ctypes.c_void_p)]


class CState(AudioState):
    def __init__(self,memory,samples):
        super().__init__(memory[:len(PRIOR_MAPPED)],samples)
        self.extra=[(ctypes.c_uint8*len(raw)).from_buffer_copy(raw) for raw in memory[len(PRIOR_MAPPED):]]
        self.regions.extend(self.extra)

    def pointer(self,address,length):
        for (base,size),region in zip(MAPPED,self.regions):
            if base<=address and address+length<=base+size:return ctypes.addressof(region)+address-base
        return None

    def mutate(self,address,value,size):
        pointer=self.pointer(address,size)
        if pointer is None:raise ValueError("C callback mutation outside mapped state")
        ctypes.memmove(pointer,(value&((1<<(8*size))-1)).to_bytes(size,"little"),size)


def initial(seed=1,parameters=(0,0,0,0,0,0),token=NOTIFICATION):
    memory=(*transition_initial(seed),bytearray((i*31+seed)&255 for i in range(280)),bytearray(struct.pack("<6h",*parameters)))
    struct.pack_into("<4I",memory[-2],264,0,0,0xA5A5A5A5,0xFFFFFFFF)
    struct.pack_into("<I",memory[6],732,token)
    return memory


def configure(library):
    functions=configure_audio(library)
    for name,arguments in {"notify":[U32],"mix":[U32],"set_gain":[U32,U32],
        "request":[U32,U32,ctypes.POINTER(U32)]}.items():
        function=getattr(library,"hyperrig_dsp_transition_notification_"+name)
        function.argtypes,function.restype=[*arguments,ctypes.POINTER(IO)],ctypes.c_int
        functions[name]=function
    return functions


def interface(state,mutations=(),missing=None,service=True,misalign=False):
    calls=[];errors=[]
    def mapping(_opaque,address,size,writable):
        if missing==address:return None
        pointer=state.pointer(address,size)
        if misalign and address==0x01C33030:return pointer+1
        return pointer
    def callback(_opaque,token,args,count):
        try:
            assert count==1 and tuple(args[1:5])==(0,0,0,0)
            before=state.snapshot()
            for address,value,size in mutations:state.mutate(address,value,size)
            calls.append((token,signed(args[0]),before,state.snapshot()))
        except Exception as error:errors.append(error)
        return 0xDEADBEEF
    mapper,caller=MAP(mapping),CALL(callback) if service else CALL()
    return IO(mapper,caller,None),calls,errors


def verify(library_path,output,mini_image=None):
    if not __debug__:raise RuntimeError("assertions required for verification")
    sys.path.insert(0,str(ROOT))
    from hyperrig.jieli import unpack_app
    raw=(ROOT/"artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin").read_bytes()
    app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PINNED_IMAGE and unpack_app(raw)[2]["app.bin"]==app
    program=DspTransitionNotificationProgram();functions=configure(ctypes.CDLL(str(library_path.resolve())))
    counts={name:0 for name in ("notify","mix","set_gain","request","startup","process")}
    coverage=set();digest=hashlib.sha256();rng=random.Random(0x1A9EA)
    real_calls=external_calls=gain_calls=producers=kernels=carried_calls=mutations_checked=samples_checked=maximum_steps=0

    def compare(memory,operation,samples=(),*arguments,mutations=(),carried=False):
        nonlocal real_calls,external_calls,gain_calls,producers,kernels,carried_calls,mutations_checked,samples_checked,maximum_steps
        def boundary(token,value,view):
            for address,word,size in mutations:view.mutate(address,word,size)
        expected=program.execute(memory,operation,samples,*arguments,boundary=boundary)
        state=CState(memory,samples);io,calls,errors=interface(state,mutations);result=U32(0xA5A55A5A)
        if operation=="request":status=functions[operation](*arguments,ctypes.byref(result),ctypes.byref(io))
        elif operation=="startup":status=functions[operation](ctypes.byref(state.runtime))
        elif operation=="process":status=functions[operation](ctypes.byref(state.runtime),state.samples,len(samples))
        else:status=functions[operation](*arguments,ctypes.byref(io))
        if errors:raise errors[0]
        assert status==0,(operation,status)
        if operation=="request":assert result.value==expected["value"],(result.value,expected["value"])
        differences=[(region,[(i,a,b) for i,(a,b) in enumerate(zip(left,right)) if a!=b][:8])
            for region,(left,right) in enumerate(zip(state.snapshot(),expected["memory"])) if left!=right]
        assert not differences and state.sample_values()==expected["samples"] and state.guards_ok(),(operation,arguments,differences)
        assert calls==expected["notification_calls"] and not expected["boundary_calls"]
        counts[operation]+=1;coverage.update(expected["visited"]);real_calls+=len(expected["real_notifications"])
        external_calls+=len(calls);gain_calls+=len(expected["gain_calls"]);producers+=len(expected["production_calls"])
        kernels+=len(expected["kernel_calls"]);carried_calls+=carried;mutations_checked+=bool(mutations)
        samples_checked+=len(samples);maximum_steps=max(maximum_steps,expected["steps"])
        digest.update(operation.encode()+struct.pack("<I",result.value))
        for region in expected["memory"]:digest.update(region)
        digest.update(struct.pack(f"<{len(samples)}i",*expected["samples"]))
        return expected

    edges=(0,1,4,5,6,119,120,121,124,125,126,0x7FFFFFFF,0x80000000,0xFFFFFFFF,0xFFFFFFFB)
    for value in (*range(-130,131),*(signed(rng.getrandbits(32)) for _ in range(64)),*(signed(x) for x in edges)):
        memory=initial();struct.pack_into("<I",memory[-2],264,rng.choice((*edges,0xFFFFFFE8,24)))
        compare(memory,"notify",(),value&MASK)
    for first in (-2147483648,-25,-24,-1,0,1,24,25,2147483647):
        for second in (-2147483648,-24,-1,0,1,24,2147483647):
            memory=initial();struct.pack_into("<2I",memory[-2],264,first&MASK,second&MASK)
            compare(memory,"mix",(),rng.choice((0,1,MASK)))
            compare(memory,"set_gain",(),first&MASK,rng.choice((0,1,MASK)))
    print("Raw signed notification, both gain sources and counter wrap compared.",flush=True)

    for value in range(-123,124):
        memory=initial(parameters=(-17,23,-31,47,-59,value));memory[4][28]=1 if value&1 else 0
        struct.pack_into("<I",memory[-2],264,(value//7)&MASK)
        compare(memory,"request",(),INPUT,rng.choice((0,1,2,7,255,256,0x7FFFFFFF,0x80000000,MASK)))
    for token in (0,1,NOTIFICATION,MASK):
        for old,new in ((0,0),(0,2),(0,3),(-5,-3),(5,3),(120,32767),(-120,-32768)):
            memory=initial(parameters=(0,0,0,0,0,new),token=token);struct.pack_into("<h",memory[4],228,old)
            compare(memory,"request",(),INPUT,2)
    for divisor in (0,1,3,48000,48077,0x1000001,0x7FFFFFFF,0x80000000,MASK):
        memory=initial(parameters=(-32768,32767,-32768,32767,-32768,32767));struct.pack_into("<I",memory[0],36,divisor)
        compare(memory,"request",(),INPUT,2)
    for address in (INPUT,CONFIGURATION,CONTROL+28,CONTROL+218,STATE+260,STATE+1):
        for gate in (0,1):
            memory=initial(parameters=(-20,40,-60,80,-100,25));memory[4][28]=gate
            if address==CONFIGURATION:struct.pack_into("<I",memory[0],0,0x7FFFFFFF)
            if address not in (INPUT,CONFIGURATION,CONTROL+28,CONTROL+218):
                offset=address-STATE;memory[-2][offset:offset+12]=struct.pack("<6h",-20,40,-60,80,-100,25)
            compare(memory,"request",(),address,3)
    for mutations in (
        ((CONFIGURATION+36,0,4),(CONFIGURATION,MASK,4)),
        ((CONTROL+218,32767,2),(CONTROL+228,32768,2),(CONTROL+28,2,1)),
        ((CALLBACKS+728,0xFFFFFFFE,4),(CALLBACKS+732,NOTIFICATION,4)),
        ((0x01C33030,0x80000000,4),(0x01C33030+60,0x7FFFFFFF,4)),
        ((INPUT,0x8000,2),(INPUT+10,0x7FFF,2),(STATE+264,24,4),(STATE+268,MASK,4)),
    ):
        compare(initial(parameters=(-20,40,-60,80,-100,25),token=1),"request",(),INPUT,7,mutations=mutations)
    print("Real/alternate callbacks, reset timing, input aliases and shared-state mutation compared.",flush=True)

    for duration in (1,2,17,255):
        state=compare(initial(),"startup")["memory"]
        state=compare(state,"set_gain",(),24,1,carried=True)["memory"]
        for index in range(10):
            state=tuple(bytearray(x) for x in state)
            values=(-21+index,37,-55,71,-89,(-120,0,120,25)[index%4]);state[-1][:]=struct.pack("<6h",*values)
            state=compare(state,"request",(),INPUT,duration,carried=True)["memory"]
            assert state[-2][16]==0
            state=compare(state,"process",[signed(rng.getrandbits(32)) for _ in range((1,31,32,33,65,128)[index%6])],carried=True)["memory"]
            unchanged=compare(state,"request",(),INPUT,255,carried=True)
            assert unchanged["value"]==0 and unchanged["memory"]==state
            state=unchanged["memory"]
        if duration<255:
            for _ in range((duration*4+3)//4+1):state=compare(state,"process",[0]*128,carried=True)["memory"]
            assert struct.unpack_from("<I",state[4],32)[0]==0
    print("Startup, actual notifications, generated transitions and carried sample histories compared.",flush=True)
    invalid=invalid_checks(functions)
    groups={**REGIONS,**{f"gain_{k}":v for k,v in GAIN_REGIONS.items()},
        **{f"transition_{k}":v for k,v in TRANSITION_REGIONS.items()},**{f"audio_{k}":v for k,v in AUDIO_REGIONS.items()},
        **{f"biquad_{k}":v for k,v in BiquadProgram.REGIONS.items()},**{f"dynamics_{k}":v for k,v in DYNAMICS_REGIONS.items()},
        **{f"initialization_{k}":v for k,v in INITIALIZATION_REGIONS.items()},**{f"math_{k}":v for k,v in MATH_REGIONS.items()},
        **{f"coefficients_{k}":v for k,v in PRIOR_REGIONS.items()}}
    declared={pc for pc in program.code if any(a<=pc<b for a,b in groups.values())};assert declared==set(program.code)
    new={pc for pc in program.code if any(a<=pc<b for a,b in REGIONS.values())};assert new<=coverage
    mini_binding=None
    if mini_image:
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI_IMAGE
        mini=unpack_app(raw)[2]["app.bin"]
        for a,b in (*groups.values(),*AUDIO_STATIC.values(),TABLE,(PRIOR_TABLE,PRIOR_TABLE+10),RESET_CONFIGURATION,(GAIN_TABLE,GAIN_TABLE+GAIN_BYTES)):
            assert region_bytes(mini,a,b)==region_bytes(app,a,b)
        mini_binding={"image_sha256":MINI_IMAGE,"all_loaded_regions_identical":sorted(groups),
            "all_used_tables_reset_data_and_caller_windows_identical":True}
    report={"schema":1,"project":"HyperRig","result":"pass","original_image_sha256":PINNED_IMAGE,
        "scope":"installed transition notification and borrowed request/gain integration",
        "functions":{name:{"start":a,"end_exclusive":b,"sha256":hashlib.sha256(region_bytes(app,a,b)).hexdigest(),
            "decoded":sum(a<=pc<b for pc in program.code),"visited":sum(a<=pc<b for pc in coverage)} for name,(a,b) in groups.items()},
        "gain_table":{"start":GAIN_TABLE,"end_exclusive":GAIN_TABLE+GAIN_BYTES,"sha256":hashlib.sha256(program.gain_table).hexdigest()},
        "comparisons":counts,"total_comparisons":sum(counts.values()),"actual_installed_callbacks":real_calls,
        "alternate_callback_calls":external_calls,"gain_helper_calls":gain_calls,"coefficient_producer_calls":producers,
        "actual_numerical_kernel_calls":kernels,"sample_words_checked":samples_checked,"carried_calls":carried_calls,
        "mutating_callback_cases":mutations_checked,"maximum_instruction_packets":maximum_steps,"invalid_checks":invalid,
        "instruction_coverage":{"new_decoded":len(new),"new_visited":len(new&coverage),"unvisited_new":sorted(new-coverage),
            "joined_decoded":len(declared),"joined_visited":len(declared&coverage),"unvisited_joined":sorted(declared-coverage),
            "all_decoded":len(program.code),"all_visited":len(coverage)},
        "outputs_and_state_sha256":digest.hexdigest(),"mini_v4_binding":mini_binding,
        "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "library_sha256":hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test":False,"audio_test":False,"firmware_changed":False,
        "limitations":["only the installed notification body is newly reconstructed; other original functions are reused",
            "borrowed request retains the disabled-bank stored-parameter bound +/-1280 and original raw signed16/duration domains",
            "alternate callback targets remain explicit synchronous services; installed callback arithmetic is never scripted",
            "gain words and update flags are compared; the surrounding capture-gain sample consumer remains outside this module",
            "sample processing uses the previously bounded 0..128-sample API; no scheduler or hardware timing claim"]}
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("result","comparisons","total_comparisons","actual_installed_callbacks","instruction_coverage")}))
    return report


MASK=0xFFFFFFFF
def invalid_checks(functions):
    count=0
    for operation,args in (("notify",(0,)),("mix",(0,)),("set_gain",(0,0))):
        for io in (None,ctypes.byref(IO())):
            assert functions[operation](*args,io)==-200;count+=1
    result=U32(0xA5A5A5A5)
    for missing in (CONFIGURATION,CONTROL,CALLBACKS,0x01C33030,0x01C330E0,INPUT):
        state=CState(initial(parameters=(0,0,0,0,0,25)),());io,_,_=interface(state,missing=missing)
        before=state.snapshot();assert functions["request"](INPUT,1,ctypes.byref(result),ctypes.byref(io))==-201
        assert state.snapshot()==before and result.value==0xA5A5A5A5;count+=1
    for argument in (0xFFFFFFF8,0x12345678):
        state=CState(initial(),());io,_,_=interface(state)
        assert functions["request"](argument,1,ctypes.byref(result),ctypes.byref(io))==-201;count+=1
    for gate in (0,1):
        memory=initial(parameters=(0,0,0,0,0,25));memory[4][28]=gate
        state=CState(memory,());io,_,_=interface(state,missing=STATE)
        assert functions["request"](INPUT,1,ctypes.byref(result),ctypes.byref(io))==-201
        assert state.regions[4][1]==0 and struct.unpack_from("<I",state.regions[6],728)[0]==(struct.unpack_from("<I",memory[6],728)[0]+1)&MASK
        assert result.value==0xA5A5A5A5;count+=1
    for value in (-32768,-1281,1281,32767):
        memory=initial();memory[4][28]=0;struct.pack_into("<h",memory[4],218,value)
        state=CState(memory,());io,_,_=interface(state);before=state.snapshot()
        assert functions["request"](INPUT,1,ctypes.byref(result),ctypes.byref(io))==-202 and state.snapshot()==before;count+=1
    state=CState(initial(parameters=(0,0,0,0,0,25),token=1),());io,_,_=interface(state,service=False)
    assert functions["request"](INPUT,1,ctypes.byref(result),ctypes.byref(io))==-202 and state.regions[4][1]==0;count+=1
    state=CState(initial(),());io,_,_=interface(state,misalign=True);before=state.snapshot()
    assert functions["request"](INPUT,1,ctypes.byref(result),ctypes.byref(io))==-202 and state.snapshot()==before;count+=1
    for io,result_pointer in ((None,ctypes.byref(result)),(ctypes.byref(IO()),ctypes.byref(result)),(ctypes.byref(io),None)):
        assert functions["request"](INPUT,1,result_pointer,io)==-200;count+=1
    return count


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--library",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True);parser.add_argument("--mini-image",type=Path);args=parser.parse_args()
    if args.output.exists():parser.error("choose a fresh verification path")
    verify(args.library,args.output,args.mini_image)
