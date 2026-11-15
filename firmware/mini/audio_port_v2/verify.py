"""Offline v2 board shim build; no device access or integrated-image changes."""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from hyperrig.jieli import unpack_app,unpack_fwsc
from tools.audit_mini_ultrarig_port import G_PATH,G_SHA,MINI_PATH,MINI_SHA
from tools.audit_mini_boot_contract import instructions
from firmware.mini.audio_port.verify import inspect,evidence
from firmware.mini.audio_port.patches import audio_patches,decoded_patches,verify_control_flow,require
from firmware.mini.audio_port_v2.evidence import audit

sha=lambda data:hashlib.sha256(data).hexdigest()
OUT=ROOT/'build/mini-audio-port-v2'


def function_bytes(raw,name,payload,base):
    h=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
    sections=[struct.unpack_from('<10I',raw,h[5]+40*i) for i in range(h[11])]
    for s in sections:
        if s[1]!=2:continue
        strings=sections[s[6]];table=raw[strings[4]:strings[4]+strings[5]]
        for off in range(s[4],s[4]+s[5],16):
            label,value,size,_,_,index=struct.unpack_from('<IIIBBH',raw,off)
            if label and index and table[label:table.index(0,label)].decode()==name:
                require(size>0 and base<=value<value+size<=base+len(payload),'function bounds')
                return value,payload[value-base:value-base+size]
    raise ValueError('missing target function '+name)


def verify_hd(raw,payload,base):
    address,body=function_bytes(raw,'hyperrig_mini_g_pc5_hd_clear',payload,base)
    rows=instructions(body,address,address,address+len(body));code={r['address']:r for r in rows}
    require([r['text'] for r in rows if r['text'].startswith('testset')]==['testset b[r4]'],'HD lock opcode')
    cases=0
    for seed in range(64):
        for busy in (0,1,3):
            for nesting in (0,1,2):
                rng=random.Random(seed);regs={f'r{i}':rng.getrandbits(32) for i in range(16)}
                original=dict(regs);hd=original_hd=rng.getrandbits(32)
                pc=address;stack=[];owned=False;depth=nesting;attempts=0;condition=False
                writes=[];calls=[];syncs=[];steps=0;rets=0xdead0000
                while pc in code:
                    row=code[pc];text=row['text'];next_pc=pc+row['size'];steps+=1
                    require(steps<100,'HD lock model escaped budget')
                    if text=='[--sp] = {rets, r4}':stack.append((rets,regs['r4']))
                    elif text=='{pc, r4} = [sp++]':next_pc,regs['r4']=stack.pop()
                    elif m:=re.fullmatch(r'(r\d+) = (0x[0-9a-fA-F]+|\d+)',text):regs[m[1]]=int(m[2],0)
                    elif text=='call r0':
                        target=regs['r0'];calls.append(target);rets=next_pc
                        if target==0x01c00e2e:depth+=1
                        elif target==0x01c00e46:
                            require(not owned and depth==nesting+1,'exit with bank lock or wrong depth');depth-=1
                        else:raise ValueError('unexpected critical API')
                        for i in range(4):regs[f'r{i}']=rng.getrandbits(32)
                    elif text=='csync':syncs.append((len(calls),owned,len(writes)))
                    elif text=='testset b[r4]':
                        require(regs['r4']==0x01c25ce2 and depth==nesting+1,'wrong bank lock/critical scope')
                        attempts+=1;condition=attempts>busy;owned=condition
                    elif text.startswith('ifeq goto '):
                        if not condition:next_pc=row['target']
                    elif text=='[r0+0] &= 0xFFFFFFDF':
                        require(regs['r0']==0x5009c and owned and depth==nesting+1,'HD RMW outside G lock')
                        hd&=~32;writes.append((0x5009c,hd))
                    elif text=='b[r4+0] = r0':
                        require(regs['r4']==0x01c25ce2 and regs['r0']==0 and owned,'wrong bank release')
                        owned=False
                    else:raise ValueError('unsupported HD instruction '+text)
                    pc=next_pc
                require(pc==0xdead0000 and not stack and not owned and depth==nesting,'HD return/lock state')
                require(calls==[0x01c00e2e,0x01c00e46] and writes==[(0x5009c,original_hd&~32)],'HD effects')
                require(syncs==[(1,False,0),(1,True,0),(1,True,1)],'HD barrier ordering')
                require(all(regs[f'r{i}']==original[f'r{i}'] for i in range(4,16)),'HD callee registers')
                cases+=1
    return {'address':address,'bytes':len(body),'sha256':sha(body),'instructions':rows,
            'cases':cases,'stack_bytes':8,'only_peripheral_write':{'address':0x5009c,'clear_mask':32},
            'lock_byte':0x01c25ce2,'critical_enter':0x01c00e2e,'critical_exit':0x01c00e46,
            'critical_calls_and_atomic_lock_results_simulated':True,'physical_multicore_execution_proven':False}


def verify_pc5_wrapper(raw,payload,base,symbols):
    address,body=function_bytes(raw,'hyperrig_mini_g_audio_pre_current_clock',payload,base)
    rows=instructions(body,address,address,address+len(body))
    expected=['[--sp] = rets','r2 = 33560700','r0 = 37','r1 = 1','call r2',
              'r2 = 33573272','r0 = 37','r1 = 1','call r2',None,
              'r1 = 33665462','r0 = 37','call r1','{rets} = [sp++]',None]
    require(len(rows)==len(expected),'PC5 wrapper instruction count')
    require(all(text is None or row['text']==text for row,text in zip(rows,expected)),
            'PC5 wrapper argument, order or RETS preservation changed')
    require(rows[9]['id']=='call.l' and rows[9]['target']==symbols['hyperrig_mini_g_pc5_hd_clear'],
            'PC5 wrapper HD call changed')
    require(rows[14]['id']=='goto.l' and rows[14]['target']==symbols['hyperrig_mini_g_audio_pre_current_clock_v1'],
            'PC5 wrapper must tail-call unchanged G binding after restoring RETS')
    return {'address':address,'bytes':len(body),'sha256':sha(body),'instructions':rows,
            'arguments_and_call_order_verified':True,'caller_RETS_preserved':True,
            'GPR_callee_saved_registers_not_modified':True,'stack_bytes':4}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old_manifest=ROOT/'build/mini-audio-port/manifest.json';old_raw=old_manifest.read_bytes()
    old=json.loads(old_raw)
    require(sha(old_raw)=='67b34b8e77dfe7a40dcab8b4499eb741ab70b73de5fa2cc82007311b4f98b2b0','frozen audio v1 manifest changed')
    for path,digest in old['source_sha256'].items():require(sha((ROOT/path).read_bytes())==digest,'frozen v1 dependency changed: '+path)
    g_raw=(ROOT/G_PATH).read_bytes();mini_raw=(ROOT/MINI_PATH).read_bytes()
    require(sha(g_raw)==G_SHA and sha(mini_raw)==MINI_SHA,'pinned source firmware changed')
    g,_,files=unpack_app(g_raw);_,mf=unpack_fwsc(mini_raw);mini,_,_=unpack_app(mf['flash.bin'][0x4000:])
    records=mini[0x35e35:0x35e8d]
    require(sha(records)=='1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d','codec table changed')
    base=0x02000120+len(files['app.bin']);limit=0x0207de81
    require(base==0x02076aac,'append origin')
    proofs=audit(g,mini)
    own=[p.relative_to(ROOT).as_posix() for p in (ROOT/'firmware/mini/audio_port_v2').glob('*') if p.is_file()]
    paths=sorted(set(own+list(old['source_sha256'])+['tools/audit_mini_boot_contract.py',
        'upstream/m-bootloader/docs/SPEC.md','tools/disassemble.py','tools/verify_mini_codec.py']))
    hashes={path:sha((ROOT/path).read_bytes()) for path in paths}
    prefix=['wsl.exe','--distribution','Ubuntu','--exec'] if os.name=='nt' else []
    vendor='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    rel=lambda p:p.relative_to(ROOT).as_posix()
    def run(args):
        r=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True,timeout=90)
        require(r.returncode==0,r.stdout+r.stderr);return r.stdout
    common=['-std=c11','-Wall','-Wextra','-Werror']
    host={}
    for name,sources in [('policy',['firmware/mini/audio_port_v2/audio_port.c','firmware/mini/codec/hyperrig_mini_codec.c',
                                   'firmware/mini/audio_port_v2/test_policy.c']),
                         ('PC5',['-DHYPERRIG_AUDIO_V2_HOST','firmware/mini/audio_port_v2/pre_pc5.c',
                                 'firmware/mini/audio_port_v2/test_pc5.c'])]:
        executable=rel(OUT/('test-'+name.lower()))
        run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*sources,'-o',executable])
        host[name]=json.loads(run([executable]))
    objects=[]
    sources=['firmware/mini/audio_port_v2/pre_pc5.c','firmware/mini/audio_port_v2/audio_port.c',
             'firmware/mini/audio_port/g_bindings.c','firmware/mini/codec/hyperrig_mini_codec.c',
             'firmware/mini/codec/spin_pi32v2.S','firmware/mini/audio_port_v2/pc5_hd.S']
    for source in sources:
        obj=rel(OUT/(Path(source).stem+'.o'))
        macros=['-Dhyperrig_mini_g_audio_pre_current_clock=hyperrig_mini_g_audio_pre_current_clock_v1'] if source.endswith('g_bindings.c') else []
        run([vendor+'clang','-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin',
             *macros,'-c',source,'-o',obj]);objects.append(obj)
    name=rel(OUT/'hyperrig-mini-g-audio-v2')
    run([vendor+'ld','-z','max-page-size=0x20','-z','common-page-size=0x20',
         '--defsym',f'AUDIO_PORT_ADDRESS={base}','--defsym',f'AUDIO_PORT_LIMIT={limit}',
         '-T','firmware/mini/audio_port/audio_port.ld',*objects,'-o',name+'.elf'])
    raw=(ROOT/(name+'.elf')).read_bytes();payload,metadata=inspect(raw,base,limit)
    require(payload.count(records)==1,'stock table not present exactly once')
    hd=verify_hd(raw,payload,base)
    wrapper=verify_pc5_wrapper(raw,payload,base,metadata['symbols'])
    (ROOT/(name+'.bin')).write_bytes(payload)
    (ROOT/(name+'.asm')).write_text(run([vendor+'objdump','-d',name+'.elf']),encoding='utf-8')
    hooks=audio_patches(g,metadata['symbols']);flows=verify_control_flow(hooks,metadata['symbols'])
    for index,hook in enumerate(hooks):(OUT/f'hook{index}.bin').write_bytes(hook.after)
    (OUT/'hooks.S').write_text(''.join(f'.section .hook{i},"ax",@progbits\n.global hook{i}\nhook{i}:\n.incbin "'+
                                     rel(OUT/f'hook{i}.bin')+'"\n' for i in range(2)),encoding='utf-8')
    (OUT/'hooks.ld').write_text('ENTRY(hook0)\nSECTIONS { .hook0 0x020053a4 : { *(.hook0) } .hook1 0x0200541e : { *(.hook1) } }\n',encoding='utf-8')
    run([vendor+'clang','-target','pi32v2','-mcpu=r3','-c',rel(OUT/'hooks.S'),'-o',rel(OUT/'hooks.o')])
    run([vendor+'ld','-T',rel(OUT/'hooks.ld'),rel(OUT/'hooks.o'),'-o',rel(OUT/'hooks.validation.elf')])
    asm=run([vendor+'objdump','-d',rel(OUT/'hooks.validation.elf')]);(OUT/'hooks.vendor.asm').write_text(asm,encoding='utf-8')
    vendor_rows={}
    for line in asm.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(.*)',line)
        if m:vendor_rows[int(m[1],16)]=(bytes.fromhex(m[2]),m[3].split(' <',1)[0].strip())
    for row in decoded_patches(hooks):
        got=vendor_rows[row['address']]
        require(got[0].hex()==row['bytes'] and re.sub(r'\s+','',got[1])==re.sub(r'\s+','',row['assembly']),
                'vendor hook disassembly mismatch')
    require(flows==42,'hook flow count')
    report={'project':'HyperRig','scope':'PC5 preparation and stock-derived per-record NACK continuation, integral G shim v2',
            'source_sha256':hashes,'frozen_v1_manifest_sha256':sha(old_raw),
            'G_container_sha256':G_SHA,'G_decoded_sha256':sha(g),'codec_script':old['codec_script'],
            'host_asan_ubsan':host,'hook_control_flow_cases':flows,'hook_vendor_disassembly_match':True,
            'original_G_binding_evidence':evidence(g),'additional_evidence':proofs,'HD_target_instruction_model':hd,
            'PC5_compiled_wrapper':wrapper,
            'elf':dict(metadata,path=name+'.elf',sha256=sha(raw)),
            'payload':{'path':name+'.bin','bytes':len(payload),'sha256':sha(payload),'base':base,
                       'read_only_xip':True,'extra_application_BSS_bytes':0},
            'patches':[p.record() for p in hooks],'decoded_hook_instructions':decoded_patches(hooks),
            'success_flow':['PC5 digital=1, output=1/direction=0, HD=0, HD0=0 under original G bank lock',
                'unchanged G MHz getter and checked Hz','PA9 low','100000 spin iterations','MINI bus GPIO init',
                '22 unchanged stock codec records; clean NACK continues and is never counted as ACK',
                'unchanged original G IRQ/open/rate/start','100000 spin iterations','PA9 high'],
            'failure_flow':'Software/clock/timing/cleanup failures still skip G IRQ/ALNK success path and keep PA9 low.',
            'NACK_policy':'Continue only NACK with STOP cleanup=0, stop_attempted and initialized bus; return0 is permission to continue, not ACK evidence.',
            'extra_STOP_after_NACK':True,'physical_equivalence_to_stock_failed_transfer_proven':False,
            'unchanged':['22-record codec table','OSR','G ALNK open/rate/start','nominal48000 configuration','G DSP','G RTOS'],
            'remaining_gates':['PC5 electrical purpose and actual codec identity are unproven.',
                'Full G boot, physical clock/audio and preset mutation remain separate qualifications.',
                'No new P33 write is added; preserved SPL/G latch-release paths are audited offline.',
                'Extra STOP changes the failed-transaction boundary; the next START/address/data is checked, electrical equivalence is not.',
                'GPIO helpers and HD wrapper require the original G critical/bank-lock state; never call them from ROM.'],
            'candidate_composed':False,'hardware_accessed':False}
    require(all(sha((ROOT/p).read_bytes())==digest for p,digest in hashes.items()),'source changed during v2 build')
    require(old_manifest.read_bytes()==old_raw,'v1 manifest changed')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (ROOT/'research/mini-audio-port-v2.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('payload','host_asan_ubsan','hook_control_flow_cases','candidate_composed','hardware_accessed')},indent=2))


if __name__=='__main__':main()
