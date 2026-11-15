"""Build HYK1 entirely offline; no device, flash writer or shared dispatcher.

The GPIO check and reset ASM are the frozen entry_recovery components. The
application prefix and its application-owned stacks are deliberately absent.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.verify_mini_rom_stack import decode as decode_bridge, validate_stack_layout
from firmware.mini.entry_recovery import verify as guard

OUT=ROOT/'build/mini-rom-entry-recovery'
BASES=(0x01C20000,0x01C28000)
SPAN,STACK,RECORD_BYTES=32768,4096,256
MASK=0x409
DISPATCHER_SHA256='1d512173776f5f87424e7870731df2871cdf1f9293636765a6371c7bb44191e8'


def sha(data): return hashlib.sha256(data).hexdigest()
def require(condition,message):
    if not condition: raise ValueError(message)


def inspect_elf(raw,base):
    def read(fmt,off):
        size=struct.calcsize(fmt)
        require(0<=off<=len(raw)-size,'truncated ELF')
        return struct.unpack_from(fmt,raw,off)
    require(base in BASES and raw[:7]==b'\x7fELF\x01\x01\x01','ELF32LE/slot')
    h=read('<HHIIIIIHHHHHH',16)
    require(h[:4]==(2,0xF1,1,base) and h[7:11]==(52,32,1,40),'ELF identity/header')
    p=read('<8I',h[4])
    require(p[0]==1 and p[2]==p[3]==base and 0<p[4]<=p[5]<=SPAN,'RAM-only load bounds')
    require(p[1]<=len(raw)-p[4] and p[6]==7 and p[7]>0 and not p[7]&(p[7]-1)
            and p[1]%p[7]==base%p[7],'load file mapping/alignment')
    sections=[read('<10I',h[5]+40*i) for i in range(h[11])]
    symbols={};ranges=[]
    for s in sections:
        _,kind,flags,address,offset,size,link,_,align,stride=s
        require(kind==8 or 0<=offset<=len(raw)-size,'section outside ELF')
        if flags&2:
            require(kind in (1,8) and base<=address<=base+p[5] and size<=base+p[5]-address,
                    'allocated section outside slot')
            require(not align or address%align==0,'section alignment')
            if kind==8: require(address>=base+p[4],'BSS overlaps file bytes')
            elif size: require(address+size<=base+p[4] and offset==p[1]+address-base,'file-backed coverage')
            if size:ranges.append((address,address+size))
        if kind!=2:continue
        require(stride==16 and size%stride==0 and link<len(sections),'symbol table')
        t=sections[link];require(t[1]==3 and t[4]<=len(raw)-t[5],'string table')
        names=raw[t[4]:t[4]+t[5]]
        for off in range(offset,offset+size,16):
            name,value,count,info,_,index=read('<IIIBBH',off)
            if not name:continue
            require(name<len(names) and b'\0' in names[name:],'symbol name bounds')
            label=names[name:names.index(0,name)].decode('ascii')
            require(index or info>>4 not in (1,2),'undefined symbol '+label)
            if index:
                require(label not in symbols or symbols[label]['address']==value,'duplicate symbol')
                symbols[label]={'address':value,'bytes':count,'type':info&15}
    ranges.sort();require(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])),'section overlap')
    required=('hyperrig_rom_entry','hyperrig_rom_entry_initialize','hyperrig_rom_entry_dispatch',
              'hyperrig_rom_entry_record','private_stack','state','core','reset_core',
              'hyperrig_mini_rom_run_on_stack','hyperrig_mini_entry_recovery_check',
              'hyperrig_mini_entry_recovery_to_rom','__slot_start','__slot_end',
              '__image_file_end','__bss_start','__bss_end')
    require(all(s in symbols for s in required),'missing HYK1 symbol')
    require(not any(s in symbols for s in ('hyperrig_mini_entry_guard','hyperrig_mini_g_startup_resume')),
            'application prefix must never enter a ROM plugin')
    a=lambda s:symbols[s]['address']
    require(a('__slot_start')==a('hyperrig_rom_entry')==base and a('__slot_end')==base+SPAN and
            a('__image_file_end')==a('__bss_start')==base+p[4] and a('__bss_end')==base+p[5],
            'linker bounds mismatch')
    occupied=[]
    for name in ('private_stack','state','hyperrig_rom_entry_record'):
        s=symbols[name];require(base+p[4]<=s['address']<=base+p[5]-s['bytes'],'state outside BSS')
        occupied.append((s['address'],s['address']+s['bytes']))
    occupied.sort();require(all(a[1]<=b[0] for a,b in zip(occupied,occupied[1:])),'private state overlap')
    require(symbols['private_stack']['bytes']==STACK+64 and symbols['hyperrig_rom_entry_record']['bytes']==RECORD_BYTES,
            'private object sizes')
    bottom=a('private_stack')+32
    validate_stack_layout(base,base+p[4],a('private_stack'),bottom,bottom+STACK)
    payload=raw[p[1]:p[1]+p[4]]
    bridge=symbols['hyperrig_mini_rom_run_on_stack']
    b=payload[bridge['address']-base:bridge['address']-base+bridge['bytes']]
    decoded=decode_bridge(b)
    return payload,symbols,{'base':base,'span':SPAN,'entry':base,'payload_bytes':len(payload),
        'bss_bytes':p[5]-p[4],'memory_bytes':p[5],'slot_free_bytes':SPAN-p[5],
        'record_address':a('hyperrig_rom_entry_record'),'record_bytes':RECORD_BYTES,
        'private_stack_bottom':bottom,'private_stack_top':bottom+STACK,'private_stack_bytes':STACK,
        'state_bytes':symbols['state']['bytes'],'elf_sha256':sha(raw),'payload_sha256':sha(payload),
        'application_prefix_absent':True,'stack_bridge':{'bytes':len(b),'sha256':sha(b),'instructions':decoded,
        'incoming_stack_bytes':8,'interrupt_stack_qualified':False}}


def validate_record(record,*,base,build_tag,sequence,phase,target=True):
    require(len(record)==256 and record[:4]==b'HYK1' and record[252:]==b'DONE','HYK1 record framing')
    require(base in BASES and 1<=sequence<=65535 and phase in (0,1,2),'expected record identity')
    u=lambda off:struct.unpack_from('<I',record,off)[0]
    signed=lambda off:struct.unpack_from('<i',record,off)[0]
    require((u(4),u(8),u(12),u(16),u(20))==(1,base,build_tag,sequence,phase),'identity/build/sequence')
    require(u(248)==zlib.crc32(record[:248]) and not any(record[240:248]),'CRC/reserved fields')
    require(u(32)==MASK and u(40) in (0,1) and u(44) in (0,1) and u(232) in (0,1),'mask/boolean fields')
    before=struct.unpack_from('<9I',record,64);after=struct.unpack_from('<9I',record,100)
    clocks_a=record[136:184];clocks_b=record[184:232]
    equal_gpio=all(before[i]==after[i] for i in range(9) if i!=1)
    require(u(44)==int(equal_gpio) and u(232)==int(clocks_a==clocks_b),'equality flags')
    require((u(48),u(52))==(before[1]&MASK,after[1]&MASK),'raw input masks')
    require((0<u(36)<=STACK) if target else u(36)==0,'stack observation')
    require(u(56)==int(phase==1) and u(60) in (0,1),'operation flags')
    require(u(60)==0 if phase==1 else True,'check cannot run after reset attempt')
    require(u(60)==1 if phase==2 else True,'reset-return phase without reset')
    require(u(236)==0 if phase==0 else u(236)==sequence-1,'consumed sequence')
    if phase==1:require(u(28) in (0,1,2,0xffffffff),'unknown check result')
    else:require(u(28)==0xffffffff,'check result without check')
    status=-9 if phase==2 else -10 if phase==1 and u(28)==0xffffffff else -3 if phase==1 and u(28)==2 else 0
    if not u(232):status=-8
    if not u(44):status=-6
    if not u(40):status=-7
    require(signed(24)==status,'combined status contradicts diagnostics')
    return {'record_valid':True,'base':base,'sequence':sequence,'phase':phase,'status':status,
            'check_result':u(28) if phase==1 else None,'all_three_observed':phase==1 and status==0 and u(28)==1,
            'gpio_configuration_restored':bool(u(44)),'clock_words_unchanged':bool(u(232)),
            'stack_guards_ok':bool(u(40)),'stack_observed_bytes':u(36),'reset_attempted':bool(u(60)),
            'ROM_reset_verified':False,'cold_SPL_state_verified':False,'record_sha256':sha(record)}


def target_byte_checks(payload,symbols,base):
    """Evaluate actual relocated check bytes; audit reset stores independently."""
    rows=[]
    for name in ('hyperrig_mini_entry_recovery_check','hyperrig_mini_entry_recovery_to_rom'):
        s=symbols[name]
        rows+=guard.instructions(payload,base,s['address'],s['address']+s['bytes'])
    code={r['address']:r for r in rows}
    simple={name:s['address'] for name,s in symbols.items()}
    cases=0
    for seed in range(8):
        for bits in range(8):
            levels=sum(((bits>>i)&1)<<pin for i,pin in enumerate((0,3,10)))
            m=guard.Machine(code,simple,seed,[levels],change_unrelated=True)
            require(m.run()=='returned' and m.regs['r0']==int(bits==0),'RAM-linked check behavior')
            m.check_gpio_restore();cases+=1
    for pin in (0,3,10):
        m=guard.Machine(code,simple,pin,[0],output_pin=True)
        require(m.run()=='returned' and m.regs['r0']==2,'RAM-linked initial-output rejection');cases+=1
    for seed in range(32):
        m=guard.Machine(code,simple,seed,[0]);m.pc=simple['hyperrig_mini_entry_recovery_to_rom']
        require(m.run()=='reset_wait','RAM-linked reset tail')
        marker=b''.join(struct.pack('<I',m.memory[guard.MAILBOX+i]) for i in range(0,16,4))
        require(marker==b'usb_update_mode\0' and m.writes[-1]==(guard.RESET,m.reset_word|16),'RAM-linked reset stores')
        require(len(m.writes)==5 and m.syncs==[4,5],'RAM-linked reset ordering');cases+=1
    return {'cases':cases,'instructions':rows,'GPIO_clock_cache_IRQ_model':False,
            'check_source_sha256':sha((ROOT/'firmware/mini/entry_recovery/check.S').read_bytes()),
            'reset_source_sha256':sha((ROOT/'firmware/mini/entry_recovery/reset.S').read_bytes())}


def stack_audit(assembly,symbols):
    functions={s['address']:(name,s['bytes']) for name,s in symbols.items() if s['type']==2 and s['bytes']}
    callbacks={'core':('read_word','check_keys'),'snapshot':('read_word',),
               'reset_core':('request_rom',)}
    ins=[]
    for line in assembly.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\s*(.*)',line)
        if m:ins.append((int(m[1],16),m[2]))
    active=set();memo={};rows={}
    def visit(address):
        if address in memo:return memo[address]
        require(address in functions and address not in active,'unknown/recursive private-stack call')
        active.add(address);name,size=functions[address];frame=0;calls=set()
        for pc,text in ins:
            if not address<=pc<address+size:continue
            if m:=re.search(r'\[--sp\] = (\{[^}]+\}|rets|r\d+)',text):
                for reg in m[1].strip('{}').split(','):
                    span=re.fullmatch(r'r(\d+)-r(\d+)',reg.strip())
                    frame+=4*(int(span[1])-int(span[2])+1) if span else 4
            if m:=re.match(r'sp \+= -(\d+)',text):frame+=int(m[1])
            if m:=re.match(r'(?:call|goto) -?\d+ <[^>]+ : ([0-9a-f]+) >',text):
                target=int(m[1],16)
                if target in functions and target!=address:calls.add(target)
            if re.match(r'(?:call|goto) r\d+',text):
                require(name in callbacks,'unknown indirect private-stack call '+name)
                calls.update(symbols[n]['address'] for n in callbacks[name])
        bound=frame+max([visit(a) for a in calls] or [0]);memo[address]=bound;active.remove(address)
        rows[name]={'frame':frame,'callees':[functions[a][0] for a in sorted(calls)],'bound':bound}
        return bound
    bound=max(visit(symbols[n]['address']) for n in ('core','reset_core'))
    require(bound+256<=STACK,'private stack margin')
    return {'private_callgraph_bound':bound,'private_stack_bytes':STACK,'margin':STACK-bound,
            'interrupt_stack_included':False,'functions':rows}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    native=['firmware/mini/rom_entry_recovery/probe.c']
    sources=['firmware/mini/rom_entry_recovery/entry.c',*native,'firmware/mini/boot/runtime.c',
             'firmware/mini/rom_stack/rom_stack_pi32v2.S','firmware/mini/entry_recovery/check.S',
             'firmware/mini/entry_recovery/reset.S']
    tracked=[*sources,'firmware/mini/rom_entry_recovery/rom_entry_recovery.h',
             'firmware/mini/rom_entry_recovery/host_test.c','firmware/mini/rom_entry_recovery/probe.ld',
             'firmware/mini/entry_recovery/entry_recovery.h','firmware/mini/entry_recovery/verify.py',
             'firmware/mini/rom_stack/rom_stack.h','tools/verify_mini_rom_stack.py',
             'tools/build_mini_rom_entry_recovery.py','tools/probe_mini_entry_recovery.py',
             'firmware/mini/rom_entry_recovery/test_client.py','tools/probe_mini_recovery.py']
    hashes={p:sha((ROOT/p).read_bytes()) for p in tracked}
    require(hashes['tools/probe_mini_recovery.py']==DISPATCHER_SHA256,'shared dispatcher differs from reviewed pin')
    tag=int(sha(json.dumps(hashes,sort_keys=True).encode())[:8],16)
    (OUT/'build_tag.h').write_text(f'#define HYPERRIG_ENTRY_BUILD_TAG UINT32_C(0x{tag:08x})\n',encoding='utf-8')
    prefix=['wsl.exe','--distribution','Ubuntu','--exec'] if os.name=='nt' else []
    def run(args):
        r=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True,timeout=90)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        return r.stdout
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/mini/rom_entry_recovery','-Ibuild/mini-rom-entry-recovery']
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',*native,
         'firmware/mini/rom_entry_recovery/host_test.c','-o','build/mini-rom-entry-recovery/host-sanitize'])
    host=json.loads(run(['build/mini-rom-entry-recovery/host-sanitize']))
    saved=host.pop('sample_records');validated=[]
    for hx in saved:
        record=bytes.fromhex(hx);u=lambda off:struct.unpack_from('<I',record,off)[0]
        validated.append(validate_record(record,base=u(8),build_tag=tag,sequence=u(16),phase=u(20),target=False))
    host['validated_records']=validated
    (OUT/'host-records.json').write_text(json.dumps(saved,indent=2)+'\n',encoding='utf-8')
    client_run=subprocess.run([sys.executable,str(ROOT/'firmware/mini/rom_entry_recovery/test_client.py')],
                              cwd=ROOT,capture_output=True,text=True,timeout=30)
    require(client_run.returncode==0,'client protocol tests failed: '+client_run.stdout+client_run.stderr)
    client_tests=json.loads(client_run.stdout)
    negative=0;record=bytes.fromhex(saved[1]);expected=dict(base=BASES[0],build_tag=tag,sequence=2,phase=1,target=False)
    validate_record(record,**expected)
    for off in (4,8,12,16,20,24,32,36,40,44,48,52,56,60,232,236,240,244,248):
        bad=bytearray(record);bad[off]^=1
        if off!=248:struct.pack_into('<I',bad,248,zlib.crc32(bad[:248]))
        try:validate_record(bad,**expected)
        except ValueError:negative+=1
    require(negative==19,'unexpected strict record rejection count')
    host['malformed_record_cases_rejected']=negative
    vendor='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    objects=[]
    for source in sources:
        obj='build/mini-rom-entry-recovery/'+Path(source).stem+'.o'
        run([vendor+'clang','-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin',
             '-ffunction-sections','-fdata-sections','-DHYPERRIG_ROM_ENTRY_TARGET','-c',source,'-o',obj])
        objects.append(obj)
    artifacts=[];elf_negatives=0
    for base in BASES:
        name=f'build/mini-rom-entry-recovery/hyperrig-rom-entry-recovery-{base:08x}'
        run([vendor+'ld','-z','max-page-size=0x20','-z','common-page-size=0x20','--gc-sections',
             '--defsym',f'PROBE_ADDRESS={base}','-T','firmware/mini/rom_entry_recovery/probe.ld',*objects,'-o',name+'.elf'])
        raw=(ROOT/(name+'.elf')).read_bytes();payload,symbols,item=inspect_elf(raw,base)
        tests=[raw[:20],raw[:-16]];h=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
        for off,value in ((24,base+2),(h[4]+12,base+SPAN),(h[4]+20,SPAN+1),(h[4]+16,len(raw)+1)):
            bad=bytearray(raw);struct.pack_into('<I',bad,off,value);tests.append(bytes(bad))
        for bad in tests:
            try:inspect_elf(bad,base)
            except (ValueError,struct.error,UnicodeError):elf_negatives+=1
            else:raise ValueError('malformed RAM ELF accepted')
        (ROOT/(name+'.bin')).write_bytes(payload)
        asm=run([vendor+'objdump','-d',name+'.elf']);(ROOT/(name+'.asm')).write_text(asm,encoding='utf-8')
        item.update(file=name+'.bin',elf=name+'.elf',assembly=name+'.asm',stack=stack_audit(asm,symbols),
                    target_byte_checks=target_byte_checks(payload,symbols,base))
        artifacts.append(item)
    require(all(sha((ROOT/p).read_bytes())==digest for p,digest in hashes.items()),'source changed while building')
    report={'project':'HyperRig','type':'HYK1 entry recovery qualification ROM diagnostic',
        'build_tag':tag,'source_sha256':hashes,'host':{**host,'ASan':True,'UBSan':True,'real_MMIO':False},
        'client_tests':client_tests,
        'artifacts':artifacts,'malformed_ELF_cases_rejected':elf_negatives,
        'protocol':{'identity':'FC74','snapshot':'FC75','check':'FC76','record':'FD77','reset':'FC81',
                    'magic':'HYK1','version':1,'record_bytes':256,'schema':'firmware/mini/rom_entry_recovery/rom_entry_recovery.h',
                    'host_client':'tools/probe_mini_entry_recovery.py','Windows_transport_profile':'ram-entry-recovery',
                    'reset_token':'sequenceBE32 + recordCRCBE32 + ROM!', 'token_is_authentication':False,
                    'reset_requires_exposed_record':True,'automatic_reset_or_retry':False},
        'effects':{'entry_MMIO':False,'identity_MMIO':False,'snapshot_writes':False,
                   'check_GPIO':['PA10','PA0','PA3'],'check_resets':False,'check_rejects_initial_output':True,
                   'reset_only_on_FC81':True,'reset_mailbox':'0x01C7FD80..0x01C7FD90',
                   'reset_RMW':{'address':0x10000,'OR_mask':16},'NOR_access':False,'clock_writes':False,
                   'application_prefix_linked':False},
        'hardware_execution_verified':False,'marker_reset_to_ROM_verified':False,'cold_SPL_state_verified':False,
        'cold_handover_observation':{'verified_RAM_only_path_found':False,
                    'SPL_application_call':0x01c0528c,'ROM_state_is_cold_SPL_state':False,
                    'stock_USB_services_run_after_application_GPIO_initialization':True},
        'future_application_prefix_policy':{'implemented_in_this_probe':False,
                    'permanent_input_direction_mask':MASK,'removes_initial_DIR_precondition':True,
                    'ROM_callable_policy_unchanged':'reject initial outputs; restore GPIO configuration'},
        'firmware_installation_package':False,
        'limits':['Host protocol tests substitute ASM callbacks; target-byte tests separately execute the scalar check/reset instruction model.',
                  'Fixed delay loops are counts, not elapsed time; actual ROM clock and command duration must be qualified.',
                  'A successful check in ROM does not measure GPIO state at cold SPL-to-application handover.',
                  'FC81 has no promised USB reply and must never be automatically repeated after transport ambiguity.',
                  'A reset requires fresh ROM enumeration; a token or accepted command is not reset completion.',
                  'Private stack bounds exclude inherited ROM interrupt stack requirements.']}
    (ROOT/'research/mini-rom-entry-recovery.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'PASS','host_cases':host['host_cases'],'client_tests':client_tests['tests'],
        'build_tag':tag,'artifacts':[
        {k:a[k] for k in ('base','payload_bytes','memory_bytes','payload_sha256')} for a in artifacts],
        'device_access':False},indent=2))


if __name__=='__main__':main()
