"""Pinned original-byte evidence for PC5, P33 latch release and NACK policy."""
import hashlib
from tools.audit_mini_boot_contract import instructions, stock_boot
from tools.audit_mini_ultrarig_port import BACKUP_PATH, BACKUP_SHA
from firmware.mini.audio_port.verify import ROOT, require

sha=lambda data:hashlib.sha256(data).hexdigest()
BASE=0x02000000
RAM_SOURCE=0x02056780


def fragment(data,base,start,end):
    raw=data[start-base:end-base]
    require(len(raw)==end-start,'evidence range')
    return {'start':start,'end_exclusive':end,'sha256':sha(raw),'preimage_hex':raw.hex(),
            'instructions':instructions(data,base,start,end)}


def writes_to_p33(rows,writer):
    """Straight-line startup stores; source-specific helper retains r1 in SPL.

    Every app caller reloads r1=0 before each call. This models call arguments,
    not the electrical behavior of the serial bridge or the latch domain.
    """
    regs={};writes=[]
    for row in rows:
        text=row['text']
        if text.startswith('r0 = ') and text[5:].isdigit():regs[0]=int(text[5:])
        elif text.startswith('r1 = ') and text[5:].isdigit():regs[1]=int(text[5:])
        elif text.startswith('call '):
            require(row['target']==writer and 0 in regs and regs.get(1)==0,'unexpected P33 call')
            writes.append([regs.pop(0),regs[1]])
        else:raise ValueError('unexpected startup latch instruction '+text)
    return writes


def audit(g,mini):
    pc5=fragment(mini,BASE,0x02005bce,0x02005c62)
    require(pc5['sha256']=='216b7f3a3e475bafaecd0e2eccddad0655f4aa8275cd841b38ae991e42c4b733',
            'MINI PC5 preparation changed')
    hd0=fragment(g,BASE,0x0201b1b6,0x0201b23a)
    texts=[r['text'] for r in hd0['instructions']]
    targets=[r.get('target') for r in hd0['instructions']]
    require('[r3+24] &= ~(1 << r0)' in texts and 'testset b[r4]' in texts and
            0x01c00e2e in targets and 0x01c00e46 in targets,'G HD0 helper/lock differs')
    require(int.from_bytes(g[0x3a2ac:0x3a2b0],'little')==0x50080,'G pin37 bank is not PORTC')
    # Use the real initialized RAM image rather than the ELF label map.
    critical=fragment(g[RAM_SOURCE-BASE:],0x01c00000,0x01c00e2e,0x01c00e62)
    require(critical['instructions'][0]['text']=='cli' and
            any(r['text']=='sti' for r in critical['instructions']),'G critical entry/exit differs')
    boot_raw=(ROOT/BACKUP_PATH).read_bytes();require(sha(boot_raw)==BACKUP_SHA,'physical backup changed')
    boot,_=stock_boot(boot_raw)
    spec=(ROOT/'upstream/m-bootloader/docs/SPEC.md').read_bytes()
    specs=(('G_application',g,BASE,0x02000ee2,0x02000fa0,0x01c00f0c),
           ('MINI_application',mini,BASE,0x02002fdc,0x0200309a,0x01c0104e),
           ('MINI_SPL',boot,0x01c02000,0x01c040ce,0x01c04142,0x01c02408))
    latch={}
    expected=set(range(0xd0,0xe0))|{0xad,0xae,0xaf}
    for name,data,base,start,end,writer in specs:
        item=fragment(data,base,start,end);writes=writes_to_p33(item['instructions'],writer)
        require(len(writes)==19 and {a for a,v in writes}==expected and all(v==0 for a,v in writes),
                'latch-release list differs')
        latch[name]={**item,'P33_write_function':writer,'writes':writes}
    caller=fragment(g,BASE,0x020011c2,0x020011d2)
    require(caller['instructions'][-1].get('target')==0x02000ee0,'G normal startup lost latch release call')
    p33=fragment(g[RAM_SOURCE-BASE:],0x01c00000,0x01c00f0c,0x01c00f4a)
    nack=fragment(mini,BASE,0x02006d1e,0x02006d3a)
    record=fragment(mini,BASE,0x02006dce,0x02006dec)
    table=fragment(mini,BASE,0x02006dec,0x02006e08)
    caller_mini=fragment(mini,BASE,0x0200717c,0x0200719e)
    require(any(r['address']==0x02006ddc and r.get('target')==0x02006dea for r in record['instructions']),
            'MINI address-NACK branch changed')
    require(any(r['address']==0x02006d34 and r.get('target')==0x02006d28 for r in nack['instructions']),
            'MINI data-ACK loop changed')
    require([r['text'] for r in table['instructions']][-3:]==
            ['r4 += 4','if (r4 <= 87) goto -10','{pc, r5, r4} = [sp++]'],
            'MINI unconditional table continuation changed')
    require(any(r['address']==0x02007188 and r.get('target')==0x02006dec for r in caller_mini['instructions']),
            'MINI table caller changed')
    candidate_path=ROOT/'build/hyperrig-mini-integrated/hyperrig-mini.app-area.bin'
    candidate=None
    if candidate_path.exists():
        from hyperrig.jieli import unpack_app
        raw=candidate_path.read_bytes();plain,_,_=unpack_app(raw)
        checked=[]
        for start,end in ((0x02000ee0,0x02000fb6),(0x020011c2,0x020011d2),
                          (RAM_SOURCE+0xf0c,RAM_SOURCE+0xf4a)):
            require(plain[start-BASE:end-BASE]==g[start-BASE:end-BASE],'integrated candidate changes G latch release')
            checked.append([start,end])
        candidate={'path':candidate_path.relative_to(ROOT).as_posix(),'sha256':sha(raw),
                   'G_latch_code_caller_and_RAM_writer_byte_identical':True,'ranges':checked}
    return {'PC5':{'pin':37,'bank':0x50080,'bit':5,'lock_byte':0x01c25ce2,
                   'MINI_original_preparation':pc5,
                   'sequence':['DIE|=bit5','OUT|=bit5,DIR&=~bit5','HD&=~bit5','HD0&=~bit5'],
                   'HD0_original_helper':hd0,'HD_original_helper_identified':False,
                   'HD_new_helper_uses_original_G_lock':True,'critical_API':critical,
                   'physical_function_proven':False},
            'latches':{'sequences':latch,'G_normal_startup_caller':caller,'G_RAM_P33_writer':p33,
                       'retained_MINI_SPL_releases_before_app_call':0x01c0528c,
                       'current_candidate_check':candidate,'spec_sha256':sha(spec),
                       'spec_path':'upstream/m-bootloader/docs/SPEC.md','spec_section':'3.1',
                       'ROM_latch_state_observed':False,'NACK_cause_proven':False},
            'NACK_policy':{'MINI_data_writer':nack,'MINI_single_record_writer':record,
                           'MINI_table_loop':table,'MINI_audio_caller':caller_mini,
                           'stock_stops_current_record_on_NACK':True,
                           'stock_continues_next_record_after_NACK':True,
                           'stock_table_caller_checks_ACK_count':False,
                           'v2_NACK_continuation_requires_successful_STOP':True,
                           'extra_STOP_on_NACK':True,'bit_exact_failed_transaction_equivalence':False,
                           'next_START_and_record_bytes_equal':True,
                           'electrical_or_target_state_equivalence_proven':False}}
