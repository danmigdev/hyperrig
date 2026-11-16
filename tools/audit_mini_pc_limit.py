"""Offline diagnosis of the observed MINI CPU0 PC-limit exception; no device I/O."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app
from firmware.mini.pc_limit_port.patches import (
    BASE, ENTRY, ORIGINAL_END, APPEND_START, PATCH_ADDRESS, BEFORE, DEBUG_RANGE,
    consumer_inventory, pc_limit_patches, simulate_limit_setup, verify_candidate, require,
)
from tools.audit_mini_boot_contract import instructions

PROOF = ROOT/'build/mini-desktop-real-03/connected-proof.json'
PROOF_SHA = '96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2'
IMAGE = ROOT/'build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin'
IMAGE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
G = ROOT/'analysis/firmware/m571_g_app/app_area.dec.bin'
SDK = ROOT/'build/mini-cdc-analysis/sdk-debug.c'
SDK_SHA = '92d7927fb423e933f8f20ab51d6727d3944954cfd56037a044e4e4d3f48f789a'
SDK_URL = ('https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/'
           'ffbb2a8d925682ba6880d643a83a63ee0691ec09/cpu/wl82/debug.c')
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def diagnose(plain, proof, sdk_text):
    commands = proof['guard']['commands']
    def reply(name):
        found = [x['lines'] for x in commands if x.get('line') == name]
        require(len(found) == 1 and found[0], 'one retained '+name+' reply required')
        return found[0]
    require(proof['state']['demo'] is False and proof['state']['connected'] is True and
            proof['guard']['pongMatched'] is True, 'actual connected non-demo proof required')
    pong, = reply('PING')
    require(pong == 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe',
            'unexpected physical firmware identity')
    crash = reply('CRASH')
    m = re.fullmatch(r'CRASH EXC cpu=(\d+) dbg=0x([0-9a-f]+) emu=0x([0-9a-f]+) '
                     r'reti=0x([0-9a-f]+) rets=0x([0-9a-f]+) other_pc=0x([0-9a-f]+) ago=(\d+)', crash[0])
    require(m is not None, 'unsupported exception record')
    cpu, dbg, emu, reti, rets, other, ago = [int(v, 10 if i in (0,6) else 16)
                                           for i,v in enumerate(m.groups())]
    require((cpu, dbg, emu, reti, rets, ago) ==
            (0, 0x1000, 0, APPEND_START+2, 0x020053AA, 1), 'different crash witness')
    require(any(line.startswith('ETM c0 02076aac 0200538e 01c04b9a 01c04b78 c1 ')
                for line in crash), 'crash branch trace does not match shim entry')
    begin = sdk_text.index('static const char *const debug_msg[32]')
    labels = re.findall(r'"([a-z0-9_]+)"', sdk_text[begin:sdk_text.index('};',begin)])
    require(len(labels) == 32 and labels[12] == 'c0_pc_limit_err_r', 'SDK debug-bit mapping differs')
    setup = simulate_limit_setup(plain, 1)
    require(setup['PC_limits'][str(0x01EEE380)] == ORIGINAL_END, 'installed limit is already extended')
    pre = instructions(plain, BASE, APPEND_START, APPEND_START+12)
    require([row['text'] for row in pre] ==
            ['[--sp] = rets','r2 = 33560700','r0 = 37','r1 = 1'], 'shim entry differs')
    require(reti > ORIGINAL_END and rets < ORIGINAL_END, 'PC/caller do not straddle the old range')
    return {'cpu': cpu, 'DBG_MSG': dbg, 'EMU_MSG': emu, 'SDK_cause': labels[12],
            'RETI': reti, 'RETS': rets, 'other_core_PC': other, 'crash_age_boots': ago,
            'old_flash_high': ORIGINAL_END, 'shim_entry': APPEND_START,
            'entry_instructions': pre, 'original_setup': setup,
            'codec_GPIO_call_reached_in_this_trace': False,
            'conclusion': 'Observed CPU0 PC-limit exception on entry to appended code.',
            'limitation': 'Exception delivery can be delayed; RETI is a saved PC, not proof of exact last retired instruction.'}


def audit():
    raw, proof_raw, g, sdk_raw = IMAGE.read_bytes(), PROOF.read_bytes(), G.read_bytes(), SDK.read_bytes()
    require(sha(raw) == IMAGE_SHA and sha(proof_raw) == PROOF_SHA and sha(sdk_raw) == SDK_SHA,
            'pinned installed image, physical proof or primary SDK source changed')
    plain, _, files = unpack_app(raw)
    end = ENTRY+len(files['app.bin'])
    patch, = pc_limit_patches(g,end)
    lo, hi = DEBUG_RANGE
    require(plain[lo-BASE:hi-BASE] == g[lo-BASE:hi-BASE], 'installed debug setup differs from G')
    modified = bytearray(plain); modified[PATCH_ADDRESS-BASE:PATCH_ADDRESS-BASE+6] = patch.after
    original = [simulate_limit_setup(plain,cpu) for cpu in (0,1)]
    patched = [simulate_limit_setup(modified,cpu) for cpu in (0,1)]
    require(original[0] == patched[0], 'CPU0 setup changed')
    old, new = original[1]['writes'], patched[1]['writes']
    differences = [i for i,(a,b) in enumerate(zip(old,new)) if a != b]
    require(len(old) == len(new) and len(differences) == 1 and
            new[differences[0]] == {'instruction':0x02000684,'address':0x01EEE380,'value':end},
            'patch changes more than the shared flash PC high word')
    return {'schema':1, 'kind':'mini-pc-limit-port-offline',
            'inputs':{'installed_image':{'path':IMAGE.relative_to(ROOT).as_posix(),'sha256':IMAGE_SHA},
                      'physical_app_proof':{'path':PROOF.relative_to(ROOT).as_posix(),'sha256':PROOF_SHA},
                      'SDK_debug':{'path':SDK.relative_to(ROOT).as_posix(),'sha256':SDK_SHA,'url':SDK_URL}},
            'diagnosis':diagnose(plain,json.loads(proof_raw),sdk_raw.decode('utf-8')),
            'literal_consumers':consumer_inventory(g), 'patch':patch.record(),
            'future_end_rule':'ENTRY + final JLFS app.bin size, including all appended code and entry guard',
            'decoded_original_setup':original,'decoded_patched_setup':patched,
            'only_changed_register':0x01EEE380,
            'callers':{'CPU0':0x020011C6,'CPU1':0x02000AE6,'debug_init':0x02000628},
            'protection_enabled_after_entry_guard':True,
            'new_image_emitted':False,'device_io':False,'new_image_hardware_tested':False,
            'audio_verified':False,'source_sha256':{
                p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
                [Path(__file__),ROOT/'firmware/mini/pc_limit_port/patches.py',
                 ROOT/'tests/test_mini_pc_limit.py', ROOT/'tools/audit_mini_boot_contract.py',
                 ROOT/'tools/audit_mini_ultrarig_port.py',ROOT/'hyperrig/jieli.py']}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--candidate',type=Path)
    args=parser.parse_args(argv)
    report=audit()
    if args.candidate:
        raw=args.candidate.read_bytes(); _,_,files=unpack_app(raw)
        report['candidate_check']=verify_candidate(raw,executable_end=ENTRY+len(files['app.bin']),g_plain=G.read_bytes())
    if args.output:
        out=args.output.resolve(); require(out.is_relative_to(ROOT),'report must stay in workspace')
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'diagnosis':report['diagnosis']['SDK_cause'],'patch':report['patch'],
                      'candidate_checked':'candidate_check' in report,'device_io':False}))
    return 0


if __name__=='__main__':raise SystemExit(main())
