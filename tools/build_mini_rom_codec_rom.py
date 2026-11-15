"""Build HYC3 offline: clock snapshot and a separately requested board/I2C read.

No device, installation image, clock writer or codec-data writer is used here.
HYC1/HYC2 inputs are only read; their source/build files are never regenerated.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_rom_codec as original

OUT = ROOT/'build/mini-rom-codec-rom'
BASES = original.BASES
SPAN, STACK, RECORD_BYTES = 32768, 4096, 512
ALLOWED_REGISTERS = original.ALLOWED_REGISTERS
sha, require = original.sha, original.require
# Copied structural validator from frozen HYC1, with only the public symbol
# prefix changed. HYC3 uses the same single-slot/BSS/stack ABI contract.
from tools.verify_mini_rom_stack import decode as decode_stack_bridge, validate_stack_layout

def inspect_elf(raw, base):
    """Validate load/section/symbol coverage and extract the single RAM image."""
    def read(fmt, off):
        size = struct.calcsize(fmt)
        require(0 <= off <= len(raw)-size, 'truncated ELF structure')
        return struct.unpack_from(fmt, raw, off)

    require(base in BASES, 'unsupported ROM slot')
    require(raw[:7] == b'\x7fELF\x01\x01\x01', 'expected ELF32 little endian')
    h = read('<HHIIIIIHHHHHH', 16)
    require(h[:4] == (2, 0xF1, 1, base) and h[7] == 52 and h[8] == 32 and h[10] == 40,
            'wrong target, entry or ELF header')
    segments = []
    for i in range(h[9]):
        p = read('<8I', h[4]+i*h[8])
        if p[0] != 1:
            continue
        _, offset, va, pa, filesz, memsz, flags, align = p
        require(va == pa == base and 0 < filesz <= memsz <= SPAN,
                'load segment leaves the owned slot')
        require(offset <= len(raw)-filesz and flags == 7 and align > 0 and
                not align & (align-1) and offset % align == va % align,
                'invalid segment file range/flags/alignment')
        segments.append(p)
    require(len(segments) == 1, 'expected one ROM slot load segment')
    p = segments[0]
    sections = [read('<10I', h[5]+i*h[10]) for i in range(h[11])]
    symbols, allocated = {}, []
    for section in sections:
        _, kind, flags, address, offset, size, link, _, align, stride = section
        require(kind == 8 or 0 <= offset <= len(raw)-size, 'section outside ELF')
        if flags & 2:
            require(kind in (1, 8) and base <= address <= base+p[5] and
                    size <= base+p[5]-address, 'allocated section outside segment')
            require(not align or address % align == 0, 'unaligned allocated section')
            if kind == 8:
                require(address >= base+p[4], 'BSS overlaps uploaded bytes')
            elif size:
                require(address <= base+p[4]-size and offset == p[1]+address-base,
                        'section bytes missing or incorrectly mapped')
            if size:
                allocated.append((address, address+size))
        if kind != 2:
            continue
        require(stride == 16 and size % stride == 0 and link < len(sections), 'invalid symbol table')
        strings = sections[link]
        require(strings[1] == 3 and strings[4] <= len(raw)-strings[5], 'invalid symbol names')
        names = raw[strings[4]:strings[4]+strings[5]]
        for off in range(offset, offset+size, stride):
            name, value, count, info, _, index = read('<IIIBBH', off)
            if not name:
                continue
            require(name < len(names) and b'\0' in names[name:], 'invalid symbol name')
            text = names[name:names.index(0, name)].decode('ascii')
            require(index or info >> 4 not in (1, 2), 'undefined symbol: '+text)
            if index:
                if text in symbols and symbols[text]['address'] != value:
                    text += '@'+hex(value)
                symbols[text] = {'address': value, 'bytes': count, 'type': info & 15}
    allocated.sort()
    require(all(a[1] <= b[0] for a, b in zip(allocated, allocated[1:])), 'allocated sections overlap')
    required = ('hyperrig_rom_codec_rom_entry', 'hyperrig_rom_codec_rom_record',
                'hyperrig_rom_codec_rom_initialize', 'hyperrig_rom_codec_rom_dispatch',
                '__slot_start', '__slot_end', '__image_file_end', '__bss_start', '__bss_end',
                'private_stack', 'state', 'hyperrig_mini_rom_run_on_stack',
                'hyperrig_mini_codec_bus_init', 'hyperrig_mini_codec_read16',
                'hyperrig_mini_codec_probe_register_allowed', 'hyperrig_mini_codec_spin_pi32v2')
    require(all(n in symbols for n in required), 'required codec diagnostic symbol missing')
    addr = lambda n: symbols[n]['address']
    require(addr('__slot_start') == addr('hyperrig_rom_codec_rom_entry') == base and
            addr('__slot_end') == base+SPAN and addr('__image_file_end') == base+p[4] and
            addr('__bss_start') == base+p[4] and addr('__bss_end') == base+p[5], 'linker bounds disagree')
    spans = []
    for name in ('private_stack', 'state', 'hyperrig_rom_codec_rom_record'):
        item = symbols[name]
        require(base+p[4] <= item['address'] <= base+p[5]-item['bytes'], 'private state not inside BSS: '+name)
        spans.append((item['address'], item['address']+item['bytes']))
    spans.sort()
    require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'private state overlaps')
    require(symbols['hyperrig_rom_codec_rom_record']['bytes'] == RECORD_BYTES and
            symbols['private_stack']['bytes'] == STACK+64, 'record/private stack size mismatch')
    bottom = addr('private_stack')+32
    require(bottom % 8 == 0, 'private stack alignment')
    validate_stack_layout(base, base+p[4], addr('private_stack'), bottom, bottom+STACK)
    allowed_codec = {'hyperrig_mini_codec_bus_init', 'hyperrig_mini_codec_read16',
                     'hyperrig_mini_codec_probe_register_allowed', 'hyperrig_mini_codec_spin_pi32v2'}
    linked_codec = {n for n in symbols if n.startswith('hyperrig_mini_codec_')}
    require(linked_codec == allowed_codec, 'unexpected linked codec functionality: '+repr(sorted(linked_codec-allowed_codec)))
    forbidden = ('stock_records', 'hyperrig_mini_codec_write', 'hyperrig_mini_codec_write_adapter',
                 'hyperrig_mini_codec_apply_stock', 'hyperrig_mini_codec_soft_mute',
                 'hyperrig_mini_codec_control_apply_stock', 'hyperrig_mini_codec_bind_mmio')
    require(not any(n in symbols for n in forbidden), 'write/reset/MMIO-binding codec routine linked')
    payload = raw[p[1]:p[1]+p[4]]
    bridge = symbols['hyperrig_mini_rom_run_on_stack']
    bridge_bytes = payload[bridge['address']-base:bridge['address']-base+bridge['bytes']]
    bridge_instructions = decode_stack_bridge(bridge_bytes)
    return payload, symbols, {
        'base': base, 'span': SPAN, 'entry': base, 'payload_bytes': len(payload),
        'bss_bytes': p[5]-p[4], 'memory_bytes': p[5], 'slot_free_bytes': SPAN-p[5],
        'record_address': addr('hyperrig_rom_codec_rom_record'), 'record_bytes': RECORD_BYTES,
        'private_stack_bottom': bottom, 'private_stack_top': bottom+STACK, 'private_stack_bytes': STACK,
        'state_bytes': symbols['state']['bytes'], 'elf_sha256': sha(raw), 'payload_sha256': sha(payload),
        'linked_codec_functions': sorted(linked_codec), 'forbidden_codec_symbols_absent': True,
        'stack_bridge': {'bytes': len(bridge_bytes), 'sha256': sha(bridge_bytes),
                         'instructions': bridge_instructions, 'incoming_stack_bytes': 8,
                         'inherited_interrupt_stack_qualified': False},
    }


def negative_elf_checks(raw, base):
    tests = [raw[:20], raw[:-16]]
    bad = bytearray(raw)
    struct.pack_into('<I', bad, 24, base+2)
    tests.append(bytes(bad))
    h = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    for field, value in ((12, base+SPAN), (20, SPAN+1), (16, len(raw)+1)):
        bad = bytearray(raw)
        struct.pack_into('<I', bad, h[4]+field, value)
        tests.append(bytes(bad))
    rejected = 0
    for bad in tests:
        try:
            inspect_elf(bad, base)
        except (ValueError, UnicodeError, struct.error):
            rejected += 1
    require(rejected == len(tests), 'invalid ELF accepted by slot validator')
    return rejected



OBSERVED_ROM_WORDS = (0,0x1c1,0x10000,0x80,0x0940022b,0x3f5030ee,0,0,0,0,0x01580034,1)


def clock_gate(s):
    """Only the recorded ROM profile; other states remain snapshot-only."""
    require(len(s)==17, 'clock snapshot size')
    return (0,48000000,12) if tuple(s[:12])==OBSERVED_ROM_WORDS else (4,0,0)


def validate_record(record, *, base, build_tag, sequence, phase, reg=0xffff, target=True):
    """Validate a saved result, including NACK/unsupported-clock records."""
    require(len(record) == 512 and record[:4] == b'HYC3' and record[508:] == b'DONE', 'record framing')
    u = lambda o: struct.unpack_from('<I', record, o)[0]
    si = lambda o: struct.unpack_from('<i', record, o)[0]
    require(base in BASES and 1 <= sequence <= 65535 and phase in (0, 1), 'expected identity')
    require(reg == 0xffff if phase == 0 else reg in ALLOWED_REGISTERS, 'expected register')
    require((u(4),u(8),u(12),u(16),u(20),u(24)) == (3,base,build_tag,sequence,phase,reg), 'record identity')
    require(u(504) == zlib.crc32(record[:504]) and not any(record[400:504]), 'CRC/reserved bytes')
    first = struct.unpack_from('<17I',record,112)
    last = struct.unpack_from('<17I',record,180)
    calculated, hz, scale = clock_gate(first)
    equal = first[:12] == last[:12]
    gate, setup, restored = u(32),u(60),u(92)
    require(gate <= 7 and setup in (0, 7) and restored <= 3 and u(104) in (0, 1), 'unknown flags')
    require((u(36),u(40),u(44),u(48),u(52),u(96)) ==
            (hz,(first[1]>>6)&7,first[3]&15,scale,first[10]&1,int(equal)), 'clock arithmetic/flags')
    require((0 < u(100) <= STACK) if target else u(100) == 0, 'stack observation')
    require(si(64) in (-4, -3, -2, 0) and u(68) <= 65535, 'read result')
    if not setup:
        require(not any(record[248:392]) and not u(392) and not restored, 'unattempted GPIO changed')
        require(si(64) == -4 and u(68) == 65535 and
                all(u(o) == 0 for o in (56,72,76,80,84,88,108)), 'unattempted bus result')
        if phase == 0:
            require(gate == (calculated if equal else 6) and u(396) == 0, 'snapshot gate')
            expected = 0 if not gate else -8 if gate == 6 else -3
        else:
            require(gate in (calculated,6,7) and gate != 0 and u(396) == sequence-1, 'rejected read gate')
            expected = -8 if gate == 6 else -3
    else:
        require(phase == 1 and not calculated and gate in (0,6) and
                u(396) == sequence-1 and u(392) == 100000, 'setup preconditions')
        require(gate == (0 if equal else 6), 'clock-change gate')
        ap, aq = struct.unpack_from('<9I',record,248),struct.unpack_from('<9I',record,284)
        cp, cq = struct.unpack_from('<9I',record,320),struct.unpack_from('<9I',record,356)
        am = (0x206,0,0x206,6,6,6,0,0,0)
        cm = (32,0,32,32,0,0,32,32,0)
        actual = int(all(not ((x^y)&m) for x,y,m in zip(ap,aq,am)))
        actual |= int(all(not ((x^y)&m) for x,y,m in zip(cp,cq,cm))) << 1
        require(restored == actual and 0 < u(56) <= 193 and u(84) == 1 and
                100000 <= u(108) <= 100000+690*scale, 'restore/delay/STOP result')
        if si(64) == 0:
            require((u(72),u(76),u(80),u(56),u(88),u(108)) ==
                    (4,2,20,193,0,100000+690*scale), 'complete read counters')
        elif si(64) == -2:
            ack = u(72)
            require(ack < 4 and u(68) == 65535 and u(76) == 0 and u(80) == ack+1 and not u(88), 'NACK data')
            require(u(56) == (123 if ack == 3 else 35+28*ack) and
                    u(108) == 100000+(135+108*ack+(15 if ack==3 else 0))*scale, 'NACK timing counts')
        else:
            require(si(64) == -3 and u(68) == 65535 and u(72) <= 4 and u(76) <= 2 and
                    u(80) <= 20 and si(88) in (0,-3), 'clock abort counters')
        expected = -6 if restored != 3 else -8 if not equal else si(64)
    require(si(28) == (expected if u(104) else -7), 'combined status')
    return {'record_valid':True,'phase':phase,'sequence':sequence,'register':reg,
            'status':si(28),'gate':gate,'nominal_active_hz':hz,'iterations_per_unit':scale,
            'read_successful':phase==1 and si(28)==0,'value':u(68) if phase==1 and si(28)==0 else None,
            'setup_flags':setup,'restoration_flags':restored,'stack_observed_bytes':u(100),
            'record_sha256':sha(record),'calibrated_timing':False}


def stack_audit(assembly, symbols):
    """Frame bound with explicit callback edges; excludes interrupt/ROM stacks."""
    functions = {v['address']:(k,v['bytes']) for k,v in symbols.items() if v['type']==2 and v['bytes']}
    callbacks = {
        'core':('read_word','write_word','spin'), 'bits':('read_word','write_word'),
        'gpio':('read_word','write_word'), 'restore':('read_word','write_word'),
        'read_port':('read_word',), 'snapshot_read':('read_word',), 'sample_bus':('read_word',),
        'delay_bus':('read_word','spin'), 'hyperrig_mini_clock_read_snapshot':('snapshot_read',),
        'hyperrig_mini_codec_bus_init':('gpio',),
        'hyperrig_mini_codec_read16':('gpio','delay_bus','sample_bus'),
        'start':('gpio','delay_bus'), 'sample':('sample_bus',)
    }
    ins=[]
    for line in assembly.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\s*(.*)',line)
        if m: ins.append((int(m[1],16),m[2]))
    active=set(); rows={}; memo={}
    def visit(addr):
        if addr in memo: return memo[addr]
        require(addr not in active and addr in functions, 'recursive/unknown core call')
        active.add(addr); name,size=functions[addr]; frame=0; calls=set()
        for pc,code in ins:
            if not addr<=pc<addr+size: continue
            if m:=re.search(r'\[--sp\] = (\{[^}]+\}|rets|r\d+)',code):
                for r in m[1].strip('{}').split(','):
                    span=re.fullmatch(r'r(\d+)-r(\d+)',r.strip())
                    frame+=4*(abs(int(span[1])-int(span[2]))+1 if span else 1)
            if m:=re.search(r'\bsp \+= -(\d+)',code): frame+=int(m[1])
            require(not re.search(r'\bsp\s*=(?!=)',code),'dynamic private stack')
            is_call=re.search(r'\bcall\b',code)
            if is_call or code.startswith('goto '):
                m=re.search(r'<[^:]+:\s*([0-9a-f]+)\s*>',code)
                if not m:
                    require((is_call or re.fullmatch(r'goto r\d+',code)) and name in callbacks,
                            'unknown indirect call: '+name+': '+code)
                    for target in callbacks[name]:
                        require(target in symbols,'callback symbol missing: '+target)
                        calls.add(symbols[target]['address'])
                else:
                    target=int(m[1],16)
                    if is_call or not addr<=target<addr+size: calls.add(target)
        child=max((visit(c) for c in calls),default=0)
        active.remove(addr); memo[addr]=frame+child
        rows[name]={'frame_bytes':frame,'bound_bytes':memo[addr],
                    'calls':sorted(functions[c][0] for c in calls)}
        return memo[addr]
    bound=visit(symbols['core']['address'])
    require(bound+256<=STACK,'private stack margin insufficient')
    return {'core_bound_bytes':bound,'private_stack_bytes':STACK,'margin_bytes':STACK-bound,
            'callback_edges_are_explicit':True,'interrupt_stack_included':False,'functions':rows}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    native=['firmware/mini/rom_codec_rom/rom_codec.c','firmware/mini/codec/hyperrig_mini_codec.c',
            'firmware/mini/codec_probe/read16.c','firmware/mini/platform/hyperrig_mini_platform.c']
    sources=['firmware/mini/rom_codec_rom/entry.c',*native,'firmware/mini/boot/runtime.c',
             'firmware/mini/rom_stack/rom_stack_pi32v2.S','firmware/mini/codec/spin_pi32v2.S']
    tracked=[*sources,'firmware/mini/rom_codec_rom/rom_codec.h','firmware/mini/rom_codec_rom/host_test.c',
             'firmware/mini/rom_codec_rom/codec.ld','firmware/mini/platform/hyperrig_mini_platform.h',
             'firmware/mini/codec/hyperrig_mini_codec.h','firmware/mini/codec_probe/read16.h',
             'firmware/mini/rom_stack/rom_stack.h','tools/verify_mini_rom_stack.py',
             'tools/build_mini_rom_codec.py','tools/build_mini_rom_codec_rom.py',
             'tools/build_mini_rom_codec_board.py','research/mini-rom-codec-board.json',
             'tools/audit_mini_rom_clock.py','research/mini-rom-clock.json']
    hashes={p:sha((ROOT/p).read_bytes()) for p in tracked}
    tag=int(sha(json.dumps(hashes,sort_keys=True).encode())[:8],16)
    (OUT/'build_tag.h').write_text(f'#define HYPERRIG_CODEC_BUILD_TAG UINT32_C(0x{tag:08x})\n',encoding='utf-8',newline='\n')
    prefix=['wsl.exe','--distribution','Ubuntu','--exec'] if os.name=='nt' else []
    def run(args):
        r=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True)
        if r.returncode:
            sys.stderr.write(r.stdout+r.stderr); r.check_returncode()
        return r.stdout
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/mini/rom_codec_rom','-Ibuild/mini-rom-codec-rom']
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',
         *native,'firmware/mini/rom_codec_rom/host_test.c','-o','build/mini-rom-codec-rom/host-sanitize'])
    host=json.loads(run(['build/mini-rom-codec-rom/host-sanitize']))
    samples=[]
    for saved in host.pop('sample_records'):
        blob=bytes.fromhex(saved)
        u=lambda off:struct.unpack_from('<I',blob,off)[0]
        samples.append(validate_record(blob,base=u(8),build_tag=tag,sequence=u(16),
                                       phase=u(20),reg=u(24),target=False))
    host['saved_record_cases']=samples
    record=bytes.fromhex(host.pop('record_hex'))
    expected=dict(base=BASES[1],build_tag=tag,sequence=2,phase=1,reg=0x59,target=False)
    host['record_validation']=validate_record(record,**expected)
    negative=0
    for off in (4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68,72,76,80,84,88,92,96,100,104,108,392,396,400):
        bad=bytearray(record); bad[off]^=1
        struct.pack_into('<I',bad,504,zlib.crc32(bad[:504]))
        try: validate_record(bad,**expected)
        except ValueError: negative+=1
    # Value itself is unconstrained: a successful codec may return any uint16.
    require(negative==29,'malformed record accepted beyond variable data')
    host['negative_record_cases']=negative
    legacy=bytearray(record)
    legacy[:4]=b'HYC2'; struct.pack_into('<I',legacy,4,2)
    struct.pack_into('<I',legacy,504,zlib.crc32(legacy[:504]))
    try:
        validate_record(legacy,**expected)
    except ValueError:
        host['legacy_HYC2_record_rejected']=True
    else:
        raise ValueError('HYC2 record accepted by HYC3 validator')
    vendor='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    objects=[]
    for source in sources:
        obj='build/mini-rom-codec-rom/'+Path(source).stem+'.o'
        run([vendor+'clang','-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin',
             '-ffunction-sections','-fdata-sections','-DHYPERRIG_ROM_CODEC_TARGET','-c',source,'-o',obj])
        objects.append(obj)
    artifacts=[]; negative_elf=0
    for base in BASES:
        name=f'build/mini-rom-codec-rom/hyperrig-rom-codec-rom-{base:08x}'
        run([vendor+'ld','-z','max-page-size=0x20','-z','common-page-size=0x20','--gc-sections',
             '--defsym',f'PROBE_ADDRESS={base}','-T','firmware/mini/rom_codec_rom/codec.ld',*objects,'-o',name+'.elf'])
        raw=(ROOT/(name+'.elf')).read_bytes(); payload,symbols,item=inspect_elf(raw,base)
        negative_elf+=negative_elf_checks(raw,base)
        require(not any(n.startswith(('hyperrig_mini_watchdog','hyperrig_mini_cache','p33_')) for n in symbols),
                'unexpected platform writer linked')
        (ROOT/(name+'.bin')).write_bytes(payload)
        asm=run([vendor+'objdump','-d',name+'.elf'])
        (ROOT/(name+'.asm')).write_text(asm,encoding='utf-8',newline='\n')
        item.update(file=name+'.bin',elf=name+'.elf',assembly=name+'.asm',stack=stack_audit(asm,symbols))
        artifacts.append(item)
    report={'project':'HyperRig','type':'HYC3 staged board/codec ROM diagnostic','build_tag':tag,
        'source_sha256':hashes,'host':{**host,'asan':True,'ubsan':True,'real_MMIO':False},'artifacts':artifacts,
        'negative_ELF_cases':negative_elf,
        'protocol':{'snapshot':'FC6B','read_register':'FC6C','read_record':'FD6D','magic':'HYC3','version':3,
                    'record_bytes':512,'schema':'firmware/mini/rom_codec_rom/rom_codec.h',
                    'read_arguments':'registerBE16 then snapshotSequenceBE16','padding':'unused CDB bytes FF',
                    'one_read_per_snapshot':True,'register_allowlist':list(ALLOWED_REGISTERS)},
        'effects':{'entry_MMIO':False,'FC6B_writes':False,'FC6C_GPIO':['PA1','PA2','PA9','PC5'],
                   'codec_data_writes':False,'codec_reset':False,'clock_writes':False,'NOR_access':False,
                   'PC5_role_known':False,'settle_spin_iterations':100000,'settle_microseconds':None},
        'clock_gate':{'exact_first_12_words':list(OBSERVED_ROM_WORDS),
            'nominal_active_hz':48000000,'iterations_per_unit':12,
            'nominal_is_not_physical_measurement':True,
            'evidence':'research/mini-rom-clock.json',
            'evidence_sha256':sha((ROOT/'research/mini-rom-clock.json').read_bytes())},
        'hardware_execution_verified':False,'codec_identity_verified':False,'calibrated_timing':False,
        'firmware_installation_package':False,
        'limits':['Only the exact twelve-word observed ROM profile is accepted; every other clock profile remains snapshot-only.',
                  'Clock snapshots are reads, not a hardware-atomic measurement or proof of analog PLL lock.',
                  'The complete first twelve snapshot words must be stable around the operation; each delay additionally checks CLK_CON0 and SFCbit0.',
                  'PC5 stock setup is observed; it is not proven to control codec power. It is also periodically toggled by stock UI.',
                  'The stock RTOS delay(10) before codec replay is not reconstructed as elapsed time; only the 100000-iteration counted settle is reproduced.',
                  'Raw bus spin counts follow stock arithmetic but RAM execution/callback overhead/IRQ activity differ from stock; physical edge timing remains unmeasured.',
                  'This manifest attests only offline builds and mocks, never board boot, audio, flash or hardware readiness.']}
    (ROOT/'research/mini-rom-codec-rom.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'host':host,'artifacts':artifacts,'hardware_execution_verified':False},indent=2))


if __name__=='__main__':
    main()
