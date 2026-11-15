"""Two fixed-size G hooks; original G DSP/open/rate/IRQ code remains in place."""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.audit_mini_ultrarig_port import BinaryPatch
from tools.disassemble import codec, relative_target, table

ISA = table.load()
INS = {i.id: i for i in ISA.insns}
BASE = 0x02000000
PRE = 0x020053a4
POST_CALL = 0x0200541e
RESUME = 0x020053c6
FAIL = 0x02005436
POST_STUB = 0x020053ae
G_SHA = '2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def enc(name, **fields):
    data = codec.encode(INS[name], fields)
    ins, got, size = codec.decode(ISA, data)
    require(ins.id == name and got == fields and size == len(data), 'encoder roundtrip')
    return data


def branch(name, address, target, **fields):
    ins = INS[name]
    size = len(ins.words) * 2
    disp = target - (address + size)
    bits = len(ins.field_bits('n'))
    require(not disp % 2 and -(1 << (bits-1)) <= disp//2 < (1 << (bits-1)),
            'branch out of range')
    raw = enc(name, n=(disp//2) & ((1 << bits)-1), **fields)
    decoded = codec.decode(ISA, raw)
    require(relative_target(address, size, codec.format(decoded[0], decoded[1])) == target,
            'branch target roundtrip')
    return raw


def audio_patches(g, symbols):
    require(hashlib.sha256(g).hexdigest() == G_SHA, 'audio source is not pinned G')
    pre = int(symbols['hyperrig_mini_g_audio_pre_current_clock'])
    post = int(symbols['hyperrig_mini_g_audio_post'])
    require(pre >= 0x02076aac and post >= 0x02076aac, 'hook entry is outside append code')
    require(pre < 0x0207de81 and post < 0x0207de81, 'hook entry exceeds append window')
    code = enc('li.u8', r=6, n=1)
    code += branch('call.l', PRE+len(code), pre)
    code += branch('bnez', PRE+len(code), FAIL, r=0)
    code += branch('goto.s', PRE+len(code), RESUME)
    require(PRE+len(code) == POST_STUB, 'local post stub moved')
    code += enc('push.rets_rl', l=4)
    code += branch('call.l', PRE+len(code), post)
    code += enc('pop.rets_rl', l=4)
    code += branch('bnez', PRE+len(code), FAIL, r=0)
    code += enc('rts')
    code += enc('nop') * ((RESUME-PRE-len(code))//2)
    require(len(code) == 34, 'preamble patch size')
    before = bytes.fromhex('482041214621bfeaf5fa48214121bfeaf1fa48254121bfeaedfa40294120bfeae9fa')
    require(g[PRE-BASE:RESUME-BASE] == before, 'preamble preimage changed')
    call_before = bytes.fromhex('bfeab9fe')
    require(g[POST_CALL-BASE:POST_CALL-BASE+4] == call_before, 'post call changed')
    return (
        BinaryPatch('mini_codec_pre_and_post_trampoline', PRE, before, code,
            'Retain r6=1; codec-pre failure skips IRQ/ALNK setup. Local post trampoline restores RETS/r4 and skips success flags on failure.'),
        BinaryPatch('mini_codec_post_call', POST_CALL, call_before,
            branch('call.l', POST_CALL, POST_STUB),
            'Call the local post trampoline, which invokes original G channel-start through the C binding then MINI PA9 sequence.'),
    )


def decoded_patches(patches):
    out = []
    for patch in patches:
        cursor = 0
        while cursor < len(patch.after):
            ins, fields, size = codec.decode(ISA, patch.after, cursor)
            text = codec.format(ins, fields)
            address = patch.address+cursor
            row = {'address': address, 'bytes': patch.after[cursor:cursor+size].hex(),
                   'instruction': ins.id, 'fields': fields, 'assembly': text}
            target = relative_target(address, size, text)
            if target is not None:
                row['direct_target'] = target
            out.append(row)
            cursor += size
    return out


def verify_control_flow(patches, symbols):
    """Bounded model over DECODED patch opcodes and normal C ABI callbacks.

    This checks hook wiring, stack/RETS and failure destinations, not G RTOS,
    interrupts or the behavior of an actual C callback/peripheral.
    """
    program = {row['address']: row for row in decoded_patches(patches)}
    pre = int(symbols['hyperrig_mini_g_audio_pre_current_clock'])
    post = int(symbols['hyperrig_mini_g_audio_post'])
    cases = 0
    for which in ('pre', 'post'):
        for status in (0, -1, -2, -3, -4, -37, 1):
            for seed in (0, 0x1000, 0xdead0000):
                regs = [seed+i for i in range(16)]
                initial = list(regs)
                sp, saved, rets = 0x1c36000, {}, 0x02001234
                address = PRE if which == 'pre' else POST_CALL
                callbacks, steps = [], 0
                while address in program:
                    row = program[address]
                    ins, f = row['instruction'], row['fields']
                    next_pc = address + len(bytes.fromhex(row['bytes']))
                    steps += 1
                    require(steps < 32, 'unbounded hook control flow')
                    if ins == 'li.u8': regs[f['r']] = f['n']
                    elif ins == 'call.l':
                        rets = next_pc
                        target = row['direct_target']
                        if target in (pre, post):
                            callbacks.append(target)
                            regs[0:4] = [status & 0xffffffff, 0xbad1, 0xbad2, 0xbad3]
                            next_pc = rets
                        else: next_pc = target
                    elif ins == 'bnez':
                        if regs[f['r']] != 0: next_pc = row['direct_target']
                    elif ins == 'goto.s': next_pc = row['direct_target']
                    elif ins == 'push.rets_rl':
                        require(f['l'] == 4, 'unexpected save registers')
                        sp -= 8
                        saved[sp] = (rets, regs[4])
                    elif ins == 'pop.rets_rl':
                        require(f['l'] == 4 and sp in saved, 'invalid restore')
                        rets, regs[4] = saved.pop(sp)
                        sp += 8
                    elif ins == 'rts': next_pc = rets
                    elif ins != 'nop': raise ValueError('unsupported hook instruction '+ins)
                    address = next_pc
                expected = FAIL if status else RESUME if which == 'pre' else POST_CALL+4
                require(address == expected and sp == 0x1c36000 and not saved, 'hook destination/stack')
                require(callbacks == [pre if which == 'pre' else post], 'wrong callback count')
                for index in range(4, 16):
                    require(regs[index] == (1 if which == 'pre' and index == 6 else initial[index]),
                            'callee-saved register changed')
                if which == 'post': require(rets == POST_CALL+4, 'incoming RETS not restored')
                cases += 1
    return cases
