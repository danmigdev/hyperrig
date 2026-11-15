"""Replay the stock clock decoder on saved HYC2 data; no target/device access."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tools'))
from tools.build_mini_rom_codec_board import validate_record
from tools.verify_mini_platform import Snapshot, StockClockMachine, decode

OBSERVED = (0,0x1c1,0x10000,0x80,0x0940022b,0x3f5030ee,0,0,0,0,0x01580034,1)
RECORD_SHA = 'd5494ce5fe320b951f1470d0e896ccce214a6dce1fd48c2f138635c4bd225083'
PINS = {
    'research/mini-rom-codec-board.json': '4e22b804e6cb7fb9e02c7a86755d8d2f87b011c2073e2fc12904bccd8f902ade',
    'analysis/tank-mini/app.bin': 'bc46bc604d42067449cdf5b8200f8ebbafd668b722243e3db1b033289e49bdea',
    'upstream/ac79-sdk-reference/cpu/wl82/liba/cpu.a': '00cea21d3c8d99487821f2c2b203f2c5a04b2cc8421bc05e9b875a0d70e42c62',
    'upstream/ac79-sdk-reference/include_lib/driver/cpu/wl82/clock_hw.h': 'ae1ea1b672b3855f6b0e2378d9ee1583e1b87614ed617db3d41f001681f855ae',
    'upstream/m-bootloader/docs/SPEC.md': 'd86ae060b1db368a8aba421e21903b3b9c7517943bcf2667ee170a5a96a2863c',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, why):
    if not ok:
        raise ValueError(why)


def archive_member(raw, wanted):
    require(raw[:8] == b'!<arch>\n', 'not an ar archive')
    pos = 8
    while pos < len(raw):
        header = raw[pos:pos+60]
        require(len(header)==60 and header[58:]==b'`\n', 'truncated ar header')
        size = int(header[48:58]); start = pos+60
        require(start+size <= len(raw), 'truncated ar member')
        if header[:16].decode('ascii').strip().rstrip('/') == wanted:
            return raw[start:start+size]
        pos = start+size+(size&1)
    raise ValueError('missing ar member: '+wanted)


def main():
    for path, expected in PINS.items():
        require(sha((ROOT/path).read_bytes())==expected, 'evidence changed: '+path)
    report_path = ROOT/'research/mini-rom-clock.json'
    record_path = ROOT/'analysis/hardware/mini-codec-board-initial-snapshot.bin'
    if record_path.exists():
        record = record_path.read_bytes()
    else:
        # The tracked audit carries the exact non-identifying diagnostic bytes,
        # so a new clone does not require a private hardware-session directory.
        record = bytes.fromhex(json.loads(report_path.read_text())['evidence']['record_hex'])
    require(sha(record)==RECORD_SHA, 'saved HYC2 record mismatch')
    validation = validate_record(record, base=0x1c20000, build_tag=1906373303,
                                 sequence=1, phase=0, reg=0xffff)
    require(validation['gate']==4 and validation['setup_flags']==0, 'HYC2 gate was not preserved')
    words = struct.unpack_from('<17I', record,112)
    require(words[:12]==OBSERVED and record[112:180]==record[180:248], 'snapshot differs')
    app = (ROOT/'analysis/tank-mini/app.bin').read_bytes()
    program = decode(app,0x02002d76,0x02002ec8)
    machine = StockClockMachine(program,app,Snapshot(*words))
    nominal = machine.run()
    require({k:nominal[k] for k in ('sys_hz','hsb_hz','lsb_hz','sdram_hz')} ==
            {'sys_hz':48000000,'hsb_hz':48000000,'lsb_hz':48000000,'sdram_hz':0}, 'stock clock replay')
    bitcode = archive_member((ROOT/'upstream/ac79-sdk-reference/cpu/wl82/liba/cpu.a').read_bytes(), 'clock.c.o')
    require(sha(bitcode)=='8a5f9b26dec4ddada3673567745dbf70b003d8a2706905efe4c2a0bed44dadb4', 'SDK clock bitcode')
    out = ROOT/'build/mini-rom-clock'
    out.mkdir(parents=True,exist_ok=True)
    (out/'sdk-clock.bc').write_bytes(bitcode)
    prefix = ['wsl.exe','--distribution','Ubuntu','--exec'] if os.name=='nt' else []
    compiler = 'tools/vendor/jieli-linux-toolchains-20260730.1/pi32v2/bin/clang'
    subprocess.run(prefix+[compiler,'-target','pi32v2','-mcpu=r3','-x','ir','-S','-emit-llvm',
                   'build/mini-rom-clock/sdk-clock.bc','-o','build/mini-rom-clock/sdk-clock.ll'],
                   cwd=ROOT,check=True,capture_output=True)
    llvm = (out/'sdk-clock.ll').read_text()
    start = llvm.index('define i32 @clk_early_init()')
    function = llvm[start:llvm.index('\n}',start)+2]
    for fragment in ('[ 192000000, %if.then ]', '%div28 = udiv i32 %.sink, %conv27',
                     '%div30 = udiv i32 %div28, %conv29'):
        require(fragment in function, 'SDK nominal source/division differs')
    require('@sys_clock_update.clk_div0 = private unnamed_addr constant [4 x i8] c"\\01\\03\\05\\07"' in llvm,
            'SDK odd divider table differs')
    require('@sys_clock_update.clk_div1 = private unnamed_addr constant [4 x i8] c"\\01\\02\\04\\08"' in llvm,
            'SDK power-of-two divider table differs')
    spec = (ROOT/'upstream/m-bootloader/docs/SPEC.md').read_text(encoding='utf-8')
    require('ROM PLL 192 MHz /4 gives 48 MHz' in spec, 'SPEC ROM nominal statement missing')
    report = {
        'schema':1,'project':'HyperRig','type':'offline audit of saved MINI ROM clocks',
        'evidence':{'record_sha256':RECORD_SHA,'record_hex':record.hex(),
                    'record_validation':validation,'snapshot_words':list(words),
                    'pins':PINS,'SDK_clock_member_sha256':sha(bitcode),
                    'SDK_clk_early_init_IR_sha256':sha(function.encode())},
        'stock_replay':{'start':'0x02002d76','end_exclusive':'0x02002ec8',
                        'sha256':sha(program.raw),'interpreted_instructions':machine.steps,
                        'nominal':nominal,'unused_pll2_result_is_not_physical':True},
        'active_clock':{'main_selector':7,'test_selector':0,'osc_selector':0,
                        'source_nibble':0,'source_nominal_hz':192000000,
                        'odd_divisor':1,'power_of_two_divisor':4,
                        'sys_nominal_hz':48000000,'HSB_nominal_hz':48000000,'LSB_nominal_hz':48000000,
                        'SFCbit0':0,'stock_delay_iterations_per_unit':12,'physical_frequency_measured':False},
        'PLL_observation':{'primary_control0':'0x0940022b','primary_control1':'0x3f5030ee',
                           'divider_field_plus_two':12,'feedback_field_plus_two':240,
                           'candidate_24MHz_div12_times240_hz':480000000,
                           'candidate_formula_is_not_the_clock_gate_basis':True,
                           'secondary_control0':0,'secondary_control1':0},
        'HYC3_gate_proposal':{'exact_first_12_words':list(OBSERVED),'nominal_hz':48000000,
                              'iterations_per_unit':12,'clock_USB_writes':False,
                              'unknown_tuple_action':'snapshot-only; no GPIO setup or bus read'},
        'limitations':['The SDK 24/40MHz oscillator heuristic must not be used to infer a physical oscillator from this ROM profile.',
                       'The disabled secondary PLL arithmetic result is not an enabled clock.',
                       'The observed exact tuple and independent stock/SDK/SPEC nominal decode do not measure edge timing or analog PLL lock.',
                       'No hardware execution is performed by this audit; HYC2 remains unchanged.'],
        'source_sha256':sha(Path(__file__).read_bytes()),'device_access':False,'network_access':False,
    }
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'nominal_hz':48000000,'iterations_per_unit':12,'stock_instructions':machine.steps,
                      'report_sha256':sha(report_path.read_bytes()),'device_access':False}))


if __name__ == '__main__':
    main()
