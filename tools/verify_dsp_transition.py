"""Compare real parameter generation through staged and active sample state."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import struct

from dsp_transition_machine import (DspTransitionProgram,REGIONS,AUDIO_REGIONS,MAPPED,ROOT,
    DYNAMICS_REGIONS,INITIALIZATION_REGIONS,MATH_REGIONS,PRIOR_REGIONS,BiquadProgram,
    TABLE,PRIOR_TABLE,RESET_CONFIGURATION,STATIC,AUDIO_STATIC,region_bytes,
    CONFIGURATION,CONTROL,CALLBACKS)
from verify_dsp_audio_path import (SOURCES as AUDIO_SOURCES,Runtime,CState as AudioState,
    configure as configure_audio,baseline,U32,I32,PINNED_IMAGE,MINI_IMAGE)

SOURCES=tuple(dict.fromkeys((*AUDIO_SOURCES,
    "firmware/include/hyperrig/hyperrig_dsp_transition.h","firmware/src/hyperrig_dsp_transition.c",
    "tools/dsp_transition_machine.py","tools/verify_dsp_transition.py","tools/build_dsp_transition.py",
    "tests/test_dsp_transition_machine.py","tests/dsp_transition_sanitize.c")))
I16=ctypes.c_int16
NOTIFY=ctypes.CFUNCTYPE(None,ctypes.c_void_p,U32,I32)


class IO(ctypes.Structure):
    _fields_=[("notify",NOTIFY),("opaque",ctypes.c_void_p)]


class CState(AudioState):
    def mutate(self,address,value,size):
        for (base,length),region in zip(MAPPED,self.regions):
            if base<=address and address+size<=base+length:
                raw=(value & ((1<<(8*size))-1)).to_bytes(size,"little")
                ctypes.memmove(ctypes.addressof(region)+address-base,raw,size)
                return
        raise ValueError("C notification mutation escaped runtime")


def configure(library):
    functions=configure_audio(library)
    for name,arguments in {"clamp":[U32,U32],
        "request":[ctypes.POINTER(Runtime),ctypes.POINTER(I16),U32,ctypes.POINTER(IO)]}.items():
        function=getattr(library,"hyperrig_dsp_transition_"+name)
        function.argtypes,function.restype=arguments,ctypes.c_int
        functions[name]=function
    return functions


def initial(seed=1,parameters=(0,0,0,0,0)):
    state=baseline(seed,parameters)
    struct.pack_into("<h",state[4],228,0)
    struct.pack_into("<I",state[6],732,0)
    state[9][:]=bytes(176);state[10][:]=bytes(176)
    return state


class Notification:
    def __init__(self,mutations):self.mutations=mutations
    def __call__(self,token,value,view):
        for address,word,size in self.mutations:view.mutate(address,word,size)


def verify(library_path,output,mini_image=None):
    if not __debug__:raise RuntimeError("verification requires assertions")
    program=DspTransitionProgram();functions=configure(ctypes.CDLL(str(library_path.resolve())))
    counts={name:0 for name in ("clamp","request","startup","process")}
    coverage=set();digest=hashlib.sha256();rng=random.Random(0x2028A34)
    producer_calls=kernel_calls=callback_calls=carried_calls=mutating_cases=samples_checked=maximum_steps=0
    complete_transitions=0;native_results={"changed":0,"unchanged":0}

    def compare(memory,operation,samples=(),*arguments,parameters=None,mutations=(),carried=False,use_io=True):
        nonlocal producer_calls,kernel_calls,callback_calls,carried_calls,mutating_cases,samples_checked,maximum_steps
        expected=program.execute(memory,operation,samples,*arguments,parameters=parameters,boundary=Notification(mutations))
        state=CState(memory,samples);calls=[];errors=[]
        def notify(_opaque,token,value):
            try:
                before=state.snapshot();Notification(mutations)(token,value,state)
                calls.append((token,value,before,state.snapshot()))
            except Exception as error:errors.append(error)
        callback=NOTIFY(notify);io=IO(callback,None)
        inputs=(I16*8)(12345,*(parameters or (0,)*6),-12345)
        pointer=ctypes.cast(ctypes.byref(inputs,2),ctypes.POINTER(I16))
        if operation=="clamp":result=functions[operation](*arguments)
        elif operation=="request":
            result=functions[operation](ctypes.byref(state.runtime),pointer,*arguments,ctypes.byref(io) if use_io else None)
        elif operation=="startup":result=functions[operation](ctypes.byref(state.runtime))
        else:result=functions[operation](ctypes.byref(state.runtime),state.samples,len(samples))
        if errors:raise errors[0]
        if operation in ("clamp","request"):assert result&0xFFFFFFFF==expected["value"],(operation,arguments,result,expected["value"])
        else:assert result==0
        differences=[(region,[(i,a,b) for i,(a,b) in enumerate(zip(left,right)) if a!=b][:10])
            for region,(left,right) in enumerate(zip(state.snapshot(),expected["memory"])) if left!=right]
        assert not differences and state.sample_values()==expected["samples"] and state.guards_ok(),(
            operation,arguments,parameters,differences,[(i,a,b) for i,(a,b) in enumerate(zip(state.sample_values(),expected["samples"])) if a!=b][:8])
        assert calls==expected.get("notification_calls",[]) and not expected["boundary_calls"]
        assert tuple(inputs)==(12345,*(parameters or (0,)*6),-12345)
        if operation=="request":
            assert expected["parameters"]==tuple(parameters)
            native_results["changed" if result else "unchanged"]+=1
        counts[operation]+=1;coverage.update(expected["visited"])
        producer_calls+=len(expected["production_calls"]);kernel_calls+=len(expected["kernel_calls"])
        callback_calls+=len(calls);carried_calls+=carried;mutating_cases+=bool(mutations)
        samples_checked+=len(samples);maximum_steps=max(maximum_steps,expected["steps"])
        digest.update(operation.encode()+b"\0")
        digest.update(struct.pack("<I",result&0xFFFFFFFF))
        for region in expected["memory"]:digest.update(region)
        digest.update(struct.pack(f"<{len(samples)}i",*expected["samples"]))
        return expected

    for index,values in ((0,range(-245,126)),(1,range(-125,126)),(5,range(-125,126))):
        for value in values:compare(initial(),"clamp",(),index,value&0xFFFFFFFF)
    for index in (0,1,2,3,4,5,6,255,0x80000000,0xFFFFFFFF):
        for value in (0x80000000,0x7FFFFFFF,0xFFFFFFFF,0,1,119,120,121,0xFFFFFF88):
            compare(initial(),"clamp",(),index,value)
    print("Complete effective clamp intervals, quantization and signed32 extremes compared.",flush=True)

    # Raw incoming signed16 data cannot escape the native clamps. Durations
    # enumerate every clamped value plus signed extremes and adjacent values.
    for duration in (*range(1,256),0,256,257,32767,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
        compare(initial(),"request",(),duration,parameters=(-17,23,-31,47,-59,0),use_io=False)
    for index in range(6):
        for value in (-32768,-241,-240,-239,-121,-120,-119,-3,-2,-1,0,1,2,3,119,120,121,32767):
            parameters=[0]*6;parameters[index]=value
            compare(initial(index),"request",(),rng.randrange(1,257),parameters=parameters)
    for enable in (0,1,2,255):
        for parameters in ((0,0,0,0,0,0),(-240,120,-120,0,1,-120),(120,-120,120,-1,0,120)):
            state=initial(parameters=parameters[:5]);state[4][28]=enable
            struct.pack_into("<h",state[4],228,parameters[5])
            result=compare(state,"request",(),0,parameters=parameters,use_io=False)
            assert result["value"]==0
            if not enable:assert result["memory"][4][28]==1
    for divisor in (0,1,2,3,48000,48077,0xFFFFFF,0x1000001,0x7FFFFFFF,0x80000000,0xFFFFFFFF):
        state=initial();struct.pack_into("<I",state[0],36,divisor)
        compare(state,"request",(),2,parameters=(-240,-120,120,-120,120,0))
    for seed in range(48):
        state=initial(seed)
        for i in range(4):struct.pack_into("<5I",state[5],44*i,*(rng.getrandbits(32) for _ in range(5)))
        struct.pack_into("<I",state[0],0,rng.getrandbits(32))
        struct.pack_into("<I",state[6],728,rng.choice((0,0xFFFFFFFF,rng.getrandbits(32))))
        compare(state,"request",(),rng.getrandbits(32),parameters=tuple(rng.randrange(-32768,32768) for _ in range(6)))
    print("All duration values, actual generated coefficients, reset/no-change and wrapped deltas compared.",flush=True)

    for token in (0,1,0x0201A9EA,0xFFFFFFFF):
        for old,new in ((0,1),(0,2),(0,3),(-5,-3),(5,3),(120,32767),(-120,-32768),(0,32767)):
            state=initial();struct.pack_into("<I",state[6],732,token);struct.pack_into("<h",state[4],228,old)
            compare(state,"request",(),2,parameters=(0,0,0,0,0,new))
    for mutations in (
        ((CONFIGURATION+36,0,4),(CONFIGURATION,0xFFFFFFFF,4)),
        ((CONTROL+218,32767,2),(CONTROL+228,32768,2),(CONTROL+28,2,1)),
        ((CALLBACKS+728,0xFFFFFFFE,4),(CALLBACKS+732,0,4)),
        ((0x01C33030,0x80000000,4),(0x01C33030+44+16,0x7FFFFFFF,4)),
    ):
        state=initial();struct.pack_into("<I",state[6],732,0x0201A9EA)
        compare(state,"request",(),7,parameters=(-20,40,-60,80,-100,25),mutations=mutations)
    print("Sixth-parameter notifications, quantized no-change and boundary mutation ordering compared.",flush=True)

    # Every integration record below is produced by the request body. No
    # coefficient, gain, step, enable or counter field is fabricated in staged
    # or active transition storage after initialization.
    for duration in (1,2,3,31,255):
        state=compare(initial(),"startup")["memory"]
        state=compare(state,"request",(),duration,parameters=(-21,37,-55,71,-89,0),carried=True,use_io=False)["memory"]
        remaining=1 if duration==1 else duration*4
        for index in range((remaining+3)//4+1):
            state=compare(state,"process",[signed32(rng.getrandbits(32)) for _ in range(128)],carried=True)["memory"]
        assert struct.unpack_from("<I",state[4],32)[0]==0
        for i in range(4):
            assert state[5][44*i:44*i+20]==state[9][20*i:20*i+20]
            assert state[5][44*i+40]==state[9][168+i]
        assert state[0][:4]==state[9][160:164]
        complete_transitions+=1
    # Replacing a pending request, interrupting an active transition, and
    # repeatedly changing the sixth value all retain real generated records.
    state=compare(initial(),"startup")["memory"]
    for index in range(24):
        parameters=tuple(rng.randrange(-32768,32768) for _ in range(6))
        state=compare(state,"request",(),(1,2,17,255)[index%4],parameters=parameters,carried=True)["memory"]
        if index%3:
            state=compare(state,"process",[signed32(rng.getrandbits(32)) for _ in range((1,31,32,33,65,128)[index%6])],carried=True)["memory"]
        unchanged=compare(state,"request",(),255,parameters=parameters,carried=True,use_io=False)
        assert unchanged["value"]==0 and unchanged["memory"]==state
        state=unchanged["memory"]
    print("Actual startup/request/update/kernel pipeline, longest transition and interrupted changes compared.",flush=True)

    invalid=invalid_checks(functions)
    new=set(program.code)-program.pre_transition_code
    missing=sorted(new-coverage);assert not missing,[hex(pc) for pc in missing]
    groups={**{f"transition_{k}":v for k,v in REGIONS.items()},**{f"audio_{k}":v for k,v in AUDIO_REGIONS.items()},
        **{f"biquad_{k}":v for k,v in BiquadProgram.REGIONS.items()},**{f"dynamics_{k}":v for k,v in DYNAMICS_REGIONS.items()},
        **{f"initialization_{k}":v for k,v in INITIALIZATION_REGIONS.items()},**{f"math_{k}":v for k,v in MATH_REGIONS.items()},
        **{f"coefficients_{k}":v for k,v in PRIOR_REGIONS.items()}}
    app=(ROOT/"analysis/firmware/m571_g_app/app.bin").read_bytes();mini_binding=None
    if mini_image:
        from hyperrig.jieli import unpack_app
        raw=mini_image.read_bytes();assert hashlib.sha256(raw).hexdigest()==MINI_IMAGE
        mini=unpack_app(raw)[2]["app.bin"]
        for start,end in (*groups.values(),*STATIC.values(),*AUDIO_STATIC.values(),TABLE,(PRIOR_TABLE,PRIOR_TABLE+10),RESET_CONFIGURATION):
            assert region_bytes(mini,start,end)==region_bytes(app,start,end)
        mini_binding={"image_sha256":MINI_IMAGE,"all_loaded_regions_identical":sorted(groups),
            "tables_reset_configuration_and_static_callback_caller_windows_identical":True}
    report={"schema":1,"project":"HyperRig","result":"pass","scope":"complete parameter request producer and real generated four-section sample pipeline",
        "original_image_sha256":PINNED_IMAGE,
        "regions":{name:{"start":start,"end_exclusive":end,"sha256":hashlib.sha256(program.transition_regions[name]).hexdigest(),
            "decoded":sum(start<=pc<end for pc in program.code),"visited":sum(start<=pc<end for pc in coverage)} for name,(start,end) in REGIONS.items()},
        "static_installed_callback":{"start":STATIC["installed_callback"][0],"end_exclusive":STATIC["installed_callback"][1],
            "sha256":hashlib.sha256(program.transition_static["installed_callback"]).hexdigest(),"executed":False},
        "comparisons":counts,"total_comparisons":sum(counts.values()),"request_results":native_results,
        "complete_coefficient_producer_calls":producer_calls,"actual_numerical_kernel_calls":kernel_calls,"sample_inputs_checked":samples_checked,
        "notification_calls":callback_calls,"mutating_notification_cases":mutating_cases,"carried_calls":carried_calls,
        "completed_transitions":complete_transitions,"maximum_transition_steps":1020,"maximum_instruction_packets":maximum_steps,
        "invalid_api_checks":invalid,"instruction_coverage":{"new_visited":len(new&coverage),"new_decoded":len(new),
            "all_visited":len(coverage),"all_decoded":len(program.code),"unvisited_new":missing},
        "compared":["all eleven runtime regions","request/clamp native returns","all sample words and immutable input halfwords",
            "notification token/value and before/after runtime","real generated staging through complete and interrupted sample transitions"],
        "outputs_and_state_sha256":digest.hexdigest(),"mini_v4_binding":mini_binding,
        "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
        "library_sha256":hashlib.sha256(library_path.read_bytes()).hexdigest(),
        "hardware_test":False,"audio_test":False,"firmware_changed":False,
        "limitations":["six signed16 inputs; original signed32 duration and clamp arguments",
            "disabled-bank reset retains prior stored-five-parameter bounds +/-1280",
            "optional sixth-parameter callback body remains an explicit external boundary; no IO/input mutation or re-entry",
            "processing remains bounded to128 samples per call and is sequenced by the verifier, not a recovered scheduler",
            "ISA/binary32 semantics retain prior assumptions; no new hardware/audio/timing measurement"]}
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("result","comparisons","total_comparisons","instruction_coverage")}))
    return report


def signed32(value):return value-(1<<32) if value>>31 else value


def invalid_checks(functions):
    state=CState(initial(),());parameters=(I16*6)(0,0,0,0,0,0);calls=[]
    callback=NOTIFY(lambda *_:calls.append(1));io=IO(callback,None)
    invalid=[(None,parameters,1,None),(ctypes.byref(state.runtime),None,1,None)]
    for args in invalid:
        before=state.snapshot();assert functions["request"](*args)==-1 and state.snapshot()==before and not calls
    count=len(invalid)
    for gate in (0,1):
        memory=initial();memory[4][28]=gate;struct.pack_into("<I",memory[6],732,0x0201A9EA)
        current=CState(memory,());changed=(I16*6)(0,0,0,0,0,3)
        for badio in (None,ctypes.byref(IO())):
            assert functions["request"](ctypes.byref(current.runtime),changed,1,badio)==-1
            assert current.snapshot()==tuple(map(bytes,memory));count+=1
    for index in range(5):
        for value in (-32768,-1281,1281,32767):
            memory=initial();memory[4][28]=0;struct.pack_into("<h",memory[4],218+2*index,value)
            current=CState(memory,())
            assert functions["request"](ctypes.byref(current.runtime),parameters,1,ctypes.byref(io))==-1
            assert current.snapshot()==tuple(map(bytes,memory)) and not calls;count+=1
    return count


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--mini-image",type=Path);args=parser.parse_args()
    if args.output.exists():parser.error("preserve completed reports; choose a fresh output path")
    verify(args.library,args.output,args.mini_image)
