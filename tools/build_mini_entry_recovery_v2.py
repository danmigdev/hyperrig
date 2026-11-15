"""Build/verify an application-only footswitch guard at an explicit XIP address.

No device access and no integrated-candidate mutation. Frozen v1 check/reset
sources and emitted bytes are pinned. The caller must bind the returned code
to its actual preceding append bytes; a link address alone is not allocation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from firmware.mini.entry_recovery import verify as v1
from tools.audit_mini_ultrarig_port import BinaryPatch, G_PATH, G_SHA
from tools.audit_mini_panel_port import encode
from hyperrig.jieli import unpack_app

G_PLAIN_SHA='2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334'
APPEND_ORIGIN=0x02076aac
CODE_LIMIT=0x0207de81
PINNED={
    'firmware/mini/entry_recovery/check.S':'81759eccb5502189248617a6e90a87b699e6537302b71562194423e17adfcb5f',
    'firmware/mini/entry_recovery/reset.S':'bec61640edc8ab6bcf92422091e9b6a9489ad94dfa4ad2eb6a4c95c4ae09af2c',
    'firmware/mini/entry_recovery/verify.py':'62fa4b21503b3df839af18a7a42aa047cc058dd2e99cb67f5cd3c11366393180',
}
CHECK_CODE_SHA='0872924dc1d476913a441a6d58b83025962a00ca6b9ceb0e8b66e07d8afc045d'
RESET_CODE_SHA='a84be9b34190a67265f001ed328372eaba2c48fcea3111b2ead481a6bb7ee48f'
require=v1.require
sha=lambda data:hashlib.sha256(data).hexdigest()


def checked_address(address):
    require(type(address) is int and APPEND_ORIGIN<=address<CODE_LIMIT and address%4==0,
            'explicit word-aligned address inside G-to-MINI append window required')
    return address


def patches(g_plain:bytes,address:int)->tuple[BinaryPatch,...]:
    """Exact-original-G hook; does not reserve/append or install any bytes."""
    checked_address(address)
    require(sha(g_plain)==G_PLAIN_SHA,'entry guard source must be original decoded pinned G')
    before=v1.EXPECTED_PREIMAGE
    require(g_plain[v1.HOOK-0x02000000:v1.RESUME-0x02000000]==before,'G stack setup preimage differs')
    displacement=address-(v1.HOOK+4)
    require(displacement%2==0 and -(1<<22)<=displacement//2<(1<<22),'entry branch range')
    after=encode('goto.l',n=(displacement//2)&((1<<23)-1))+encode('nop')*4
    rows=v1.instructions(after,v1.HOOK,v1.HOOK,v1.HOOK+len(after))
    require(len(after)==len(before) and rows[0]['target']==address and
            all(row['text']=='nop' for row in rows[1:]),'entry hook branch roundtrip')
    return (BinaryPatch('mini_entry_footswitch_recovery_v2',v1.HOOK,before,after,
                'Branch before G startup to an application guard: preserve context, force PA10/PA0/PA3 input, '
                'check the chord, then reset with stock ROM marker or resume the original G entry.'),)


def inspect_elf(raw,address):
    checked_address(address)
    def read(fmt,offset):
        require(0<=offset<=len(raw)-struct.calcsize(fmt),'truncated v2 ELF')
        return struct.unpack_from(fmt,raw,offset)
    require(raw[:7]==b'\x7fELF\x01\x01\x01','ELF32LE required')
    h=read('<HHIIIIIHHHHHH',16)
    require(h[:4]==(2,0xf1,1,address) and h[7:11]==(52,32,1,40),'v2 ELF identity/header')
    p=read('<8I',h[4])
    require(p[0]==1 and p[2]==p[3]==address and 0<p[4]==p[5]<1024 and p[6]==5,
            'one initialized RX segment without BSS required')
    require(p[1]<=len(raw)-p[4] and address+p[4]<=CODE_LIMIT and p[7]>0 and
            p[7]&(p[7]-1)==0 and p[1]%p[7]==address%p[7],'v2 mapping/range/alignment')
    sections=[read('<10I',h[5]+40*i) for i in range(h[11])]
    symbols={};regions=[]
    for section in sections:
        _,kind,flags,start,offset,size,link,_,align,stride=section
        require(kind==8 or 0<=offset<=len(raw)-size,'section beyond file')
        if flags&2 and size:
            require(kind==1 and flags==6 and address<=start and start+size<=address+p[4] and
                    offset==p[1]+start-address,'uninitialized/writable/out-of-payload section')
            require(not align or start%align==0,'section alignment')
            regions.append((start,start+size))
        if kind!=2:continue
        require(stride==16 and size%16==0 and link<len(sections),'symbol table geometry')
        names_section=sections[link]
        require(names_section[1]==3,'symbol names section')
        names=raw[names_section[4]:names_section[4]+names_section[5]]
        for off in range(offset,offset+size,16):
            name,value,length,info,_,ndx=read('<IIIBBH',off)
            if not name:continue
            require(name<len(names) and b'\0' in names[name:],'symbol name bounds')
            label=names[name:names.index(0,name)].decode('ascii')
            require(ndx!=0,'undefined symbol '+label)
            require(label not in symbols,'duplicate symbol '+label)
            symbols[label]={'address':value,'bytes':length,'type':info&15}
    regions.sort()
    require(regions and regions[0][0]==address and regions[-1][1]==address+p[4] and
            all(a[1]==b[0] for a,b in zip(regions,regions[1:])),'allocated payload coverage')
    names=('hyperrig_mini_entry_guard_v2','hyperrig_mini_entry_recovery_check',
           'hyperrig_mini_entry_recovery_to_rom','hyperrig_mini_g_startup_resume')
    require(all(n in symbols for n in names),'missing v2 symbols')
    require(symbols[names[0]]['address']==address and symbols[names[3]]['address']==v1.RESUME,
            'guard entry or G continuation differs')
    payload=raw[p[1]:p[1]+p[4]]
    for name,size,digest in ((names[1],190,CHECK_CODE_SHA),(names[2],54,RESET_CODE_SHA)):
        symbol=symbols[name];off=symbol['address']-address
        require(symbol['bytes']==size and 0<=off<=len(payload)-size and
                sha(payload[off:off+size])==digest,'frozen v1 callable bytes changed: '+name)
    require(payload[:12]==v1.EXPECTED_PREIMAGE,'original G stack setup is not reproduced')
    return payload,symbols


class PolicyMachine(v1.Machine):
    """v1 instruction model plus the new input-direction policy and entry hook.

    PSR is deliberately disturbed after the policy store to make restoration
    observable. This is an adversarial preservation check, not a PSR simulator.
    """
    def __init__(self,code,symbols,address,seed,levels,direction,*,alias=False,fault=None):
        super().__init__(code,symbols,seed,levels,prefix=True,change_unrelated=True,
                         sp_alias_ssp=alias,fault=fault)
        self.address=address;self.pc=v1.HOOK;self.policy_stores=0
        self.mmio[v1.PORT+8]=(self.mmio[v1.PORT+8]&~v1.MASK)|direction
        self.original_mmio=dict(self.mmio)
        if seed%2==0:self.regs['r0']=self.original_regs['r0']=0x01c7fd50

    def set(self,name,value):
        super().set(name,value)
        if self.prefix and ((self.pc==self.address and name=='sp') or
                            (self.pc==self.address+6 and name=='ssp' and self.sp_alias_ssp)):
            self.min_sp=value&0xffffffff

    def write(self,address,value):
        if address==v1.PORT+8 and self.policy_stores==0:
            require(value==(self.original_mmio[address]|v1.MASK),'policy changed foreign GPIO bits')
            self.policy_stores+=1
            self.regs['psr']^=0xa55aa55a
        super().write(address,value)

    def check_gpio_restore(self):
        for address,value in self.original_mmio.items():
            expected=value^(0x20000000 if self.changed else 0)
            if address==v1.PORT+8:expected|=v1.MASK
            require(self.mmio[address]==expected,'v2 GPIO final state differs')
        require(self.policy_stores==1,'missing application input policy')


def verify_flow(payload,symbols,address,hook):
    rows=v1.instructions(payload,address,address,address+len(payload))
    entry_rows=v1.instructions(hook.after,v1.HOOK,v1.HOOK,v1.RESUME)
    code={row['address']:row for row in rows+entry_rows}
    simple={name:s['address'] for name,s in symbols.items()}
    prefix=[row for row in rows if row['address']<simple['hyperrig_mini_entry_recovery_check']]
    expected=['sp = 29577400','ssp = 29581496','[--sp] = {psr, rets, reti}',
              '[--sp] = {r15-r0}','r0 = 0x50000','r1 = [r0+8]','r2 = 1033',
              'r1 |= r2','[r0+8] = r1','csync']
    require([r['text'] for r in prefix[:10]]==expected,'v2 prefix policy instruction contract')
    require(prefix[10]['text'].startswith('call ') and prefix[10]['target']==simple['hyperrig_mini_entry_recovery_check'],
            'callable target differs')
    cases=0;maximum_stack=0
    def verify(machine,held):
        nonlocal cases,maximum_stack
        require(machine.run()==('reset_wait' if held else 'startup_resume'),'wrong v2 recovery/continuation')
        machine.check_gpio_restore()
        require(machine.stack_top-machine.min_sp==100,'unexpected v2 maximum stack')
        maximum_stack=max(maximum_stack,machine.stack_top-machine.min_sp)
        # 19 incoming registers are stored before the sole policy write.
        require(machine.writes[19][0]==v1.PORT+8 and machine.syncs[0]==20,'policy store/barrier order')
        if held:
            marker=b''.join(struct.pack('<I',machine.memory[v1.MAILBOX+i]) for i in range(0,16,4))
            require(marker==b'usb_update_mode\0' and machine.writes[-1]==(v1.RESET,machine.reset_word|16),
                    'v2 marker/reset order')
            require(machine.syncs[-2:]==[len(machine.writes)-1,len(machine.writes)],'reset barriers')
            require(machine.samples==32 and machine.delay_iterations==3300000,'held chord sample counts')
        else:
            for name in [*(f'r{i}' for i in range(16)),'psr','rets','reti']:
                require(machine.regs[name]==machine.original_regs[name],'incoming register lost: '+name)
            require((machine.regs['sp'],machine.regs['ssp'])==
                    (v1.SSP if machine.sp_alias_ssp else v1.SP,v1.SSP),'G stacks not restored')
            require(not any(v1.MAILBOX<=a<v1.MAILBOX+16 or a==v1.RESET for a,_ in machine.writes),
                    'recovery effect on ordinary continuation')
        cases+=1
    pinmask=lambda bits:sum(((bits>>i)&1)<<pin for i,pin in enumerate((0,3,10)))
    for alias in (False,True):
        for direction in range(8):
            for levels in range(8):
                for seed in range(8):
                    machine=PolicyMachine(code,simple,address,seed,[pinmask(levels)|0xa5000000],
                                          pinmask(direction),alias=alias)
                    verify(machine,levels==0)
                    if levels:require(machine.samples==1 and machine.delay_iterations==100000,'no-key fast return')
            for fault in v1.CONFIG:
                machine=PolicyMachine(code,simple,address,11,[0],pinmask(direction),alias=alias,fault=fault)
                verify(machine,False)
                require(machine.samples==0,'configuration fault sampled physical keys')
    for alias in (False,True):
        for position in range(32):
            for pin in (0,3,10):
                machine=PolicyMachine(code,simple,address,position,[0]*position+[1<<pin]+[0]*32,
                                      0,alias=alias)
                verify(machine,False)
                require(machine.samples==position+1,'released sample was ignored')
    return {'cases':cases,'maximum_stack_bytes':maximum_stack,
            'initial_DIR_combinations':8,'key_level_combinations':8,'SP_alias_models':2,
            'incoming_r0_context_and_all_GPRs_preserved_on_resume':True,
            'PSR_RETS_RETI_preserved_on_resume':True,'foreign_GPIO_bits_preserved':True,
            'key_direction_final':'input even when initially output',
            'PSR_test':'adversarial clobber, not CPU status-flag simulation',
            'push_pop_model':'matched frames; physical stack order not independently executed',
            'hardware_timing_or_electrical_simulation':False},rows,entry_rows


def bind_append(g_plain:bytes,preceding_append:bytes,payload:bytes,manifest:dict)->bytes:
    """Join append pieces only when address, hashes and G hook match.

    The caller owns preceding bytes and their board semantics. This helper
    prevents an address gap/overlap; it cannot prove a candidate is installable.
    """
    require(isinstance(preceding_append,bytes) and isinstance(payload,bytes),'append parts must be immutable bytes')
    address=manifest['component']['address']
    patches(g_plain,address)
    require(manifest.get('schema')==2 and manifest.get('kind')=='mini-entry-recovery-v2',
            'wrong append manifest kind')
    require(address==APPEND_ORIGIN+len(preceding_append),'guard address differs from actual preceding append end')
    require(sha(payload)==manifest['component']['payload_sha256'] and
            len(payload)==manifest['component']['payload_bytes'],'guard payload differs from verified manifest')
    require(manifest['component']['end_exclusive']==address+len(payload)<=CODE_LIMIT,'guard append bounds')
    require(manifest['patches']==[p.record() for p in patches(g_plain,address)],'manifest hook differs from allocation')
    return preceding_append+payload


def build(address:int)->dict:
    checked_address(address)
    out=ROOT/f'build/mini-entry-recovery-v2/{address:08x}'
    out.mkdir(parents=True,exist_ok=True)
    source_files=[*PINNED,'firmware/mini/entry_recovery_v2/prefix.S',
                  'firmware/mini/entry_recovery_v2/append.ld','tools/build_mini_entry_recovery_v2.py',
                  'tools/audit_mini_ultrarig_port.py','tools/audit_mini_panel_port.py',
                  'tools/audit_mini_boot_contract.py']
    hashes={p:sha((ROOT/p).read_bytes()) for p in source_files}
    require(all(hashes[p]==digest for p,digest in PINNED.items()),'frozen v1 dependency changed')
    g_raw=(ROOT/G_PATH).read_bytes()
    require(sha(g_raw)==G_SHA,'original G container changed')
    g,_,files=unpack_app(g_raw)
    require(0x02000120+len(files['app.bin'])==APPEND_ORIGIN and len(files['cfg_tool.bin'])==383,'append geometry changed')
    hook=patches(g,address)[0]
    prefix=['wsl.exe','--distribution','Ubuntu','--exec'] if os.name=='nt' else []
    vendor='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    def local(p):return p.relative_to(ROOT).as_posix()
    def run(args):
        result=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True,timeout=60)
        require(result.returncode==0,result.stdout+result.stderr)
        return result.stdout
    objects=[]
    for source in ['firmware/mini/entry_recovery_v2/prefix.S',*list(PINNED)[:2]]:
        target=out/(Path(source).stem+'.o')
        run([vendor+'clang','-target','pi32v2','-mcpu=r3','-c',source,'-o',local(target)])
        objects.append(local(target))
    elf_path=out/'entry-recovery-v2.elf'
    run([vendor+'ld','-z','max-page-size=0x20','-z','common-page-size=0x20',
         '--defsym',f'HYPERRIG_ENTRY_GUARD_ADDRESS={address}',
         '-T','firmware/mini/entry_recovery_v2/append.ld',*objects,'-o',local(elf_path)])
    raw=elf_path.read_bytes();payload,symbols=inspect_elf(raw,address)
    tests,rows,hook_rows=verify_flow(payload,symbols,address,hook)
    (out/'entry-recovery-v2.bin').write_bytes(payload)
    (out/'entry-recovery-v2.asm').write_text(run([vendor+'objdump','-d',local(elf_path)]),encoding='utf-8')
    # Vendor disassembly independently checks the actual fixed-size entry hook.
    (out/'hook.bin').write_bytes(hook.after)
    (out/'hook.S').write_text('.section .text,"ax",@progbits\n.global hook\nhook:\n.incbin "'+
                              local(out/'hook.bin')+'"\n',encoding='utf-8')
    (out/'hook.ld').write_text('ENTRY(hook)\nSECTIONS { .text 0x0200018a : { *(.text) } }\n',encoding='utf-8')
    run([vendor+'clang','-target','pi32v2','-mcpu=r3','-c',local(out/'hook.S'),'-o',local(out/'hook.o')])
    run([vendor+'ld','-T',local(out/'hook.ld'),local(out/'hook.o'),'-o',local(out/'hook.elf')])
    hook_asm=run([vendor+'objdump','-d',local(out/'hook.elf')])
    (out/'hook.vendor.asm').write_text(hook_asm,encoding='utf-8')
    vendor_rows={}
    for line in hook_asm.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(.*)',line)
        if m:vendor_rows[int(m[1],16)]=(bytes.fromhex(m[2]),m[3].split(' <',1)[0].strip())
    for row in hook_rows:
        require(vendor_rows.get(row['address'])==(bytes.fromhex(row['bytes']),row['text']),'vendor entry hook decode differs')
    negative=[]
    def reject(label,fn):
        try:fn()
        except (ValueError,KeyError,struct.error,UnicodeError):negative.append(label)
        else:raise ValueError('invalid input accepted: '+label)
    reject('changed_G',lambda:patches(g[:-1]+bytes((g[-1]^1,)),address))
    for bad in (True,APPEND_ORIGIN-4,address+1,CODE_LIMIT):
        reject('address_'+str(bad),lambda bad=bad:patches(g,bad))
    h=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
    for label,off,value in (('ELF_entry',24,address+4),('ELF_LMA',h[4]+12,address+4),
                            ('ELF_BSS',h[4]+20,len(payload)+4),('ELF_permissions',h[4]+24,7)):
        bad=bytearray(raw);struct.pack_into('<I',bad,off,value)
        reject(label,lambda bad=bad:inspect_elf(bytes(bad),address))
    check=symbols['hyperrig_mini_entry_recovery_check']['address']-address
    segment=struct.unpack_from('<8I',raw,h[4]);bad=bytearray(raw);bad[segment[1]+check]^=1
    reject('mutated_frozen_callable',lambda:inspect_elf(bytes(bad),address))
    report={'schema':2,'kind':'mini-entry-recovery-v2','source_sha256':hashes,
            'G_container_sha256':G_SHA,'G_decoded_sha256':sha(g),
            'component':{'address':address,'end_exclusive':address+len(payload),'payload_bytes':len(payload),
                         'payload_sha256':sha(payload),'file':local(out/'entry-recovery-v2.bin'),
                         'elf':local(elf_path),'elf_sha256':sha(raw),'symbols':symbols,
                         'BSS_bytes':0,'initialized_RAM_bytes':0,'stack_bytes':100},
            'patches':[hook.record()],'hook_instructions':hook_rows,'instructions':rows,'tests':tests,
            'frozen_callables':{'check':{'bytes':190,'sha256':CHECK_CODE_SHA},
                                'reset':{'bytes':54,'sha256':RESET_CODE_SHA}},
            'policy':{'PORTA_DIR_address':0x50008,'permanent_input_mask':v1.MASK,
                      'requires_initial_DIR_inputs':False,'other_GPIO_configuration_restored':True,
                      'G_context_restored_on_normal_resume':True,'resume_address':v1.RESUME,
                      'ROM_plugin_callable':False,'SFC_PLL_IRQ_writes':False},
            'allocation':{'original_append_origin':APPEND_ORIGIN,'code_limit_with_cfg_reserved':CODE_LIMIT,
                          'preceding_append_bytes_required':address-APPEND_ORIGIN,
                          'actual_preceding_payload_validated':False,
                          'binding_API':'bind_append(g_plain, preceding_append, payload, manifest)'},
            'candidate_modified':False,'hardware_executed':False,'recovery_hardware_qualified':False,
            'device_access':False,'NVM_access':False,'flashable':False,
            'limits':['The ordinary application path preserves the incoming context; the deliberate reset path does not return.',
                      'The prefix owns only key direction permanently; check/reset remain byte-identical to v1.',
                      'ROM key/reset qualification does not execute this XIP prefix or prove cold boot behavior.',
                      'A valid application that hangs after the guard is a different case from damaged header/entry/guard.',
                      'Instruction counts are not measured delay time, GPIO voltages, mux validity or continuous debounce.']}
    previous=bytes(address-APPEND_ORIGIN)
    require(bind_append(g,previous,payload,report)==previous+payload,'append binding selfcheck')
    reject('append_length',lambda:bind_append(g,previous+b'\0',payload,report))
    reject('append_payload_hash',lambda:bind_append(g,previous,payload[:-1]+bytes((payload[-1]^1,)),report))
    report['negative_cases_rejected']=negative
    require(all(sha((ROOT/p).read_bytes())==digest for p,digest in hashes.items()),'source changed while building')
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address',required=True,type=lambda value:int(value,0),help='explicit allocator-selected XIP entry')
    args=parser.parse_args();report=build(args.address)
    (ROOT/'research/mini-entry-recovery-v2.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'PASS','component':report['component'],'tests':report['tests'],
                      'device_access':False,'candidate_modified':False},indent=2))


if __name__=='__main__':main()
