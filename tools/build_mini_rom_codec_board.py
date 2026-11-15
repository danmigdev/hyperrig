"""Build HYC2 offline: clock snapshot and a separately requested board/I2C read.

No device, installation image, clock writer or codec-data writer is used here.
HYC1 inputs are only read; its source/build files are never regenerated.
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
import types
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_rom_codec as original

OUT = ROOT/'build/mini-rom-codec-board'
BASES = original.BASES
SPAN, STACK, RECORD_BYTES = 32768, 4096, 512
ALLOWED_REGISTERS = original.ALLOWED_REGISTERS
sha, require = original.sha, original.require
# Reuse the reviewed structural ELF validator with an isolated constant set.
# No global or source file in the frozen HYC1 module is modified.
inspect_elf = types.FunctionType(original.inspect_elf.__code__,
    {**original.inspect_elf.__globals__, 'RECORD_BYTES': RECORD_BYTES}, 'inspect_elf')
negative_elf_checks = types.FunctionType(original.negative_elf_checks.__code__,
    {**original.negative_elf_checks.__globals__, 'inspect_elf': inspect_elf}, 'negative_elf_checks')


def clock_gate(s):
    """Pure counterpart of the deliberately narrow, nominal target gate."""
    require(len(s) == 17, 'clock snapshot size')
    _, clk0, _, clk2, pll0, pll1, pll20, pll21, _, _, sfc, baud, *_ = s
    main, source = (clk0 >> 6) & 7, clk2 & 15
    if clk0 & 12:
        return 1, 0, 0
    if main not in (4, 7):
        return 2, 0, 0
    if clk0 & 48:
        return 4, 0, 0
    if main == 4:
        hz = 24_000_000
    else:
        if source > 7:
            return 3, 0, 0
        if pll0 & 0xcc00007f != 0x44000003 or pll1 & 4095 != 38:
            return 4, 0, 0
        if source < 5:
            if not pll1 & (1 << (26, 27, 25, 24, 28)[source]):
                return 4, 0, 0
        elif pll20 & 0x0fc007ff != 0x0940022b or pll21 & 0x07000000 != 0x07000000:
            return 4, 0, 0
        elif (pll21 & 4095)+2 > 120*(9-source):
            return 5, 0, 0
        if baud == 0xffffffff:
            return 5, 0, 0
        if source < 5:
            hz = (192000000, 137000000, 320000000, 480000000, 107000000)[source]
            hz //= 2*((clk2 >> 4) & 3)+1
            hz //= 1 << ((clk2 >> 6) & 3)
        else:
            pll2 = (24000000 // (((pll20 >> 2) & 31)+2)) * ((pll21 & 4095)+2)
            hz = (pll2*2) // (9-source)
    if not 8_000_000 <= hz <= 480_000_000:
        return 5, 0, 0
    return 0, hz, hz // (8_000_000 if sfc & 1 else 4_000_000)


def validate_record(record, *, base, build_tag, sequence, phase, reg=0xffff, target=True):
    """Validate a saved result, including NACK/unsupported-clock records."""
    require(len(record) == 512 and record[:4] == b'HYC2' and record[508:] == b'DONE', 'record framing')
    u = lambda o: struct.unpack_from('<I', record, o)[0]
    si = lambda o: struct.unpack_from('<i', record, o)[0]
    require(base in BASES and 1 <= sequence <= 65535 and phase in (0, 1), 'expected identity')
    require(reg == 0xffff if phase == 0 else reg in ALLOWED_REGISTERS, 'expected register')
    require((u(4),u(8),u(12),u(16),u(20),u(24)) == (2,base,build_tag,sequence,phase,reg), 'record identity')
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
    native=['firmware/mini/rom_codec_board/rom_codec.c','firmware/mini/codec/hyperrig_mini_codec.c',
            'firmware/mini/codec_probe/read16.c','firmware/mini/platform/hyperrig_mini_platform.c']
    sources=['firmware/mini/rom_codec_board/entry.c',*native,'firmware/mini/boot/runtime.c',
             'firmware/mini/rom_stack/rom_stack_pi32v2.S','firmware/mini/codec/spin_pi32v2.S']
    tracked=[*sources,'firmware/mini/rom_codec_board/rom_codec.h','firmware/mini/rom_codec_board/host_test.c',
             'firmware/mini/rom_codec_board/codec.ld','firmware/mini/platform/hyperrig_mini_platform.h',
             'firmware/mini/codec/hyperrig_mini_codec.h','firmware/mini/codec_probe/read16.h',
             'firmware/mini/rom_stack/rom_stack.h','tools/verify_mini_rom_stack.py',
             'tools/build_mini_rom_codec.py','tools/build_mini_rom_codec_board.py']
    hashes={p:sha((ROOT/p).read_bytes()) for p in tracked}
    tag=int(sha(json.dumps(hashes,sort_keys=True).encode())[:8],16)
    (OUT/'build_tag.h').write_text(f'#define HYPERRIG_CODEC_BUILD_TAG UINT32_C(0x{tag:08x})\n',encoding='utf-8',newline='\n')
    prefix=['wsl.exe','--distribution','Ubuntu','--exec'] if os.name=='nt' else []
    def run(args):
        r=subprocess.run(prefix+args,cwd=ROOT,capture_output=True,text=True)
        if r.returncode:
            sys.stderr.write(r.stdout+r.stderr); r.check_returncode()
        return r.stdout
    common=['-std=c99','-Wall','-Wextra','-Werror','-Ifirmware/mini/rom_codec_board','-Ibuild/mini-rom-codec-board']
    run(['gcc',*common,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',
         *native,'firmware/mini/rom_codec_board/host_test.c','-o','build/mini-rom-codec-board/host-sanitize'])
    host=json.loads(run(['build/mini-rom-codec-board/host-sanitize']))
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
    vendor='tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/'
    objects=[]
    for source in sources:
        obj='build/mini-rom-codec-board/'+Path(source).stem+'.o'
        run([vendor+'clang','-target','pi32v2','-mcpu=r3',*common,'-Os','-ffreestanding','-fno-builtin',
             '-ffunction-sections','-fdata-sections','-DHYPERRIG_ROM_CODEC_TARGET','-c',source,'-o',obj])
        objects.append(obj)
    artifacts=[]; negative_elf=0
    for base in BASES:
        name=f'build/mini-rom-codec-board/hyperrig-rom-codec-board-{base:08x}'
        run([vendor+'ld','-z','max-page-size=0x20','-z','common-page-size=0x20','--gc-sections',
             '--defsym',f'PROBE_ADDRESS={base}','-T','firmware/mini/rom_codec_board/codec.ld',*objects,'-o',name+'.elf'])
        raw=(ROOT/(name+'.elf')).read_bytes(); payload,symbols,item=inspect_elf(raw,base)
        negative_elf+=negative_elf_checks(raw,base)
        require(not any(n.startswith(('hyperrig_mini_watchdog','hyperrig_mini_cache','p33_')) for n in symbols),
                'unexpected platform writer linked')
        (ROOT/(name+'.bin')).write_bytes(payload)
        asm=run([vendor+'objdump','-d',name+'.elf'])
        (ROOT/(name+'.asm')).write_text(asm,encoding='utf-8',newline='\n')
        item.update(file=name+'.bin',elf=name+'.elf',assembly=name+'.asm',stack=stack_audit(asm,symbols))
        artifacts.append(item)
    report={'project':'HyperRig','type':'HYC2 staged board/codec ROM diagnostic','build_tag':tag,
        'source_sha256':hashes,'host':{**host,'asan':True,'ubsan':True,'real_MMIO':False},'artifacts':artifacts,
        'negative_ELF_cases':negative_elf,
        'protocol':{'snapshot':'FC68','read_register':'FC69','read_record':'FD6A','magic':'HYC2','version':2,
                    'record_bytes':512,'schema':'firmware/mini/rom_codec_board/rom_codec.h',
                    'read_arguments':'registerBE16 then snapshotSequenceBE16','padding':'unused CDB bytes FF',
                    'one_read_per_snapshot':True,'register_allowlist':list(ALLOWED_REGISTERS)},
        'effects':{'entry_MMIO':False,'FC68_writes':False,'FC69_GPIO':['PA1','PA2','PA9','PC5'],
                   'codec_data_writes':False,'codec_reset':False,'clock_writes':False,'NOR_access':False,
                   'PC5_role_known':False,'settle_spin_iterations':100000,'settle_microseconds':None},
        'clock_gate':{'main_selectors':[4,7],'test_selector':0,'osc_selector':0,
            'external_crystal_nominal_hz':24000000,'PLL_sources':list(range(8)),
            'primary_control0_mask':'0xcc00007f','primary_control0_value':'0x44000003','primary_N':38,
            'secondary_control0_mask':'0x0fc007ff','secondary_control0_value':'0x0940022b',
            'secondary_output_enable_mask':'0x07000000','minimum_hz':8000000,'maximum_hz':480000000,
            'secondary_N_bound_before_uint32_decoder':'N+2 <= 120*(9-source)',
            'formula':'units * floor(active_nominal_hz / (SFCbit0 ? 8000000 : 4000000))',
            'source_header_url':'https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h',
            'source_header_sha256':'ae1ea1b672b3855f6b0e2378d9ee1583e1b87614ed617db3d41f001681f855ae'},
        'hardware_execution_verified':False,'codec_identity_verified':False,'calibrated_timing':False,
        'firmware_installation_package':False,
        'limits':['Main RC, RTC, test sources and unrecognized PLL references remain snapshot-only.',
                  'Clock snapshots are reads, not a hardware-atomic measurement or proof of analog PLL lock.',
                  'The complete first twelve snapshot words must be stable around the operation; each delay additionally checks CLK_CON0 and SFCbit0.',
                  'PC5 stock setup is observed; it is not proven to control codec power. It is also periodically toggled by stock UI.',
                  'The stock RTOS delay(10) before codec replay is not reconstructed as elapsed time; only the 100000-iteration counted settle is reproduced.',
                  'Raw bus spin counts follow stock arithmetic but RAM execution/callback overhead/IRQ activity differ from stock; physical edge timing remains unmeasured.',
                  'This manifest attests only offline builds and mocks, never board boot, audio, flash or hardware readiness.']}
    (ROOT/'research/mini-rom-codec-board.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'host':host,'artifacts':artifacts,'hardware_execution_verified':False},indent=2))


if __name__=='__main__':
    main()
