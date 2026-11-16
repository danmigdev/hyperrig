"""Offline byte audit of original G CDC UBOOT; never opens a device."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_mini_boot_contract import instructions
from hyperrig.jieli import unpack_app

APP = ROOT / 'analysis/firmware/m571_g_app/app.bin'
APP_SHA = '4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e'
CANDIDATE = ROOT / 'build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin'
CANDIDATE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
BASE, RAM, RAM_SOURCE = 0x02000120, 0x01C00000, 0x02056780
DISPATCH = ((0x0200B834, 0x0200BFB0), (0x0200D60C, 0x0200DCD6),
            (0x0200E07A, 0x0200E146), (0x020112F8, 0x02014104))


def require(test, message):
    if not test:
        raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def fragment(raw, start, end):
    offset = start - BASE if start >= BASE else RAM_SOURCE - BASE + start - RAM
    return raw[offset:offset+end-start]


def walk(raw, start, end, stop=None):
    """Follow UBOOT only, modeling strcmp, rejecting every target RAM read.

    Saves/restores and stack stores are omitted because this is a control-flow
    audit, not an ABI emulator. Registers are separately initialized per helper.
    Any data-dependent safe gate would need a RAM read and is rejected here.
    """
    code = {r['address']: r for r in instructions(fragment(raw, start, end), start, start, end)}
    regs = {f'r{i}': 0 for i in range(16)}
    regs.update(r0=0x40000000, r1=0x40000005)
    pc, path, compared = start, [], []
    for _ in range(1500):
        if pc == stop:
            return {'result': 'UBOOT handler', 'path': path, 'comparisons': compared,
                    'target_RAM_reads': 0}
        require(pc in code, f'path escaped audited region at {pc:#x}')
        row = code[pc]; text = row['text'].removesuffix('  #'); after = pc + row['size']
        path.append(pc)
        if text.startswith('{pc,') or text == 'pc = [sp++]' or text == 'rts':
            return {'result': regs['r0'], 'path': path, 'comparisons': compared, 'target_RAM_reads': 0}
        if text.startswith('[--sp]') or text.startswith('sp +=') or text.startswith('[sp+'):
            pass
        elif match := re.fullmatch(r'(r\d+)_(r\d+) = (r\d+)_(r\d+)', text):
            high, low, source_high, source_low = match.groups()
            regs[high], regs[low] = regs[source_high], regs[source_low]
        elif match := re.fullmatch(r'(r\d+) = (r\d+|\d+)(?: \+ (-?\d+))?', text):
            dest, value, amount = match.groups()
            regs[dest] = (regs[value] if value.startswith('r') else int(value)) + int(amount or 0)
        elif match := re.fullmatch(r'call (-?\d+)', text):
            require(row['target'] == 0x02028308 and regs['r0'] == 0x40000000,
                    f'unexpected call at {pc:#x}: {text}')
            offset = regs['r1']-BASE
            require(0 <= offset < len(raw), 'strcmp string outside flash')
            value = raw[offset:raw.index(0, offset)]
            compared.append({'call': pc, 'string_address': regs['r1'], 'value': value.decode('ascii')})
            regs['r0'] = 0 if value == b'UBOOT' else 1
        elif match := re.fullmatch(r'if \((r\d+) (==|!=) 0\) goto (-?\d+)', text):
            reg, op, displacement = match.groups()
            taken = regs[reg] == 0
            if op == '!=': taken = not taken
            if taken: after += int(displacement)
        elif match := re.fullmatch(r'goto (-?\d+)', text):
            after += int(match[1])
        else:
            raise ValueError(f'unmodeled/target-state instruction at {pc:#x}: {text}')
        pc = after
    raise ValueError('dispatch instruction bound exceeded')


def inspect():
    raw = APP.read_bytes(); require(sha(raw) == APP_SHA, 'original G app changed')
    candidate = CANDIDATE.read_bytes()
    require(sha(candidate) == CANDIDATE_SHA, 'installed v2 candidate changed')
    current = unpack_app(candidate)[2]['app.bin']
    sections = {
        'line_dispatch': (0x02014104, 0x02014186),
        'capture_predispatch': DISPATCH[0], 'fx_predispatch': DISPATCH[1],
        'save_predispatch': DISPATCH[2], 'main_dispatch': (0x020112F8, 0x020116F2),
        'uboot_handler': (0x020140C8, 0x02014104),
        'lock_and_reset_wrapper': (0x01C00FB6, 0x01C00FDC),
        'mailbox_and_P33_reset': (0x02000B80, 0x02000BA2),
        'P33_bitfield': (0x01C00F4A, 0x01C00F72),
        'P33_read_write': (0x01C00EC8, 0x01C00F4A),
        'strcmp': (0x02028308, 0x020283AE),
    }
    evidence = {}
    for name, (start, end) in sections.items():
        data = fragment(raw, start, end)
        require(data == fragment(current, start, end), name + ' differs in installed candidate')
        evidence[name] = {'start': start, 'end_exclusive': end, 'sha256': sha(data),
                          'installed_candidate_identical': True,
                          'instructions': instructions(data, start, start, end)}
    strings = {0x02035AA3: b'UBOOT\0', 0x02035D77: b'OK UBOOT\n\0',
               0x0203A135: b'usb_update_mode\0'}
    for address, value in strings.items():
        require(fragment(raw, address, address+len(value)) == value, 'original command string differs')
        require(fragment(current, address, address+len(value)) == value, 'candidate command string differs')
    paths = [walk(raw, start, end, 0x020140C8 if index == 3 else None)
             for index, (start, end) in enumerate(DISPATCH)]
    require([p['result'] for p in paths] == [0, 0, 0, 'UBOOT handler'], 'command was filtered')
    bytecode = ROOT / 'recovered/installer/tankg_install.dis.txt'
    text = bytecode.read_text('utf-8')
    require("LOAD_CONST              37 ('UBOOT')" in text and
            "'OK UBOOT (port closed by the pedal)'" in text, 'installer bytecode evidence changed')
    return {'schema': 1, 'hardware_io': False, 'command_hex': b'UBOOT\n'.hex(),
            'actual_ACK_hex': b'OK UBOOT\n'.hex(),
            'original_app_sha256': sha(raw), 'installed_candidate_sha256': sha(candidate),
            'installer_bytecode': {'path': bytecode.relative_to(ROOT).as_posix(), 'sha256': sha(bytecode.read_bytes()),
                                  'original_lines': [3163, 3173, 3180, 3184, 3185, 5185],
                                  'port_error_must_not_be_synthetic_ACK': True},
            'safe_flag_not_read_on_audited_UBOOT_dispatch_path': True,
            'safe_mode_physical_recovery_tested': False, 'dispatch_paths': paths,
            'fragments': evidence,
            'sequence': ['reply OK UBOOT LF through 0x02006E24',
                         'delay 5 scheduler ticks through 0x0203FEB8',
                         'clear word 0x01C7FDFC', 'cli, core lock, csync at 0x01C00FB6',
                         'copy usb_update_mode NUL (16 bytes) to 0x01C7FD80',
                         'P33 address 0xA0 bit4 <-1 through bitfield helper', 'spin after reset request'],
            'NOR_operations_in_command_handler': [],
            'limits': ['ACK receipt is not proof of fresh ROM enumeration',
                       'original send may reset before host receives ACK',
                       'safe dispatch independence is static, not physical recovery proof',
                       'five ticks are not converted into unmeasured milliseconds',
                       'an unresponsive parser cannot receive this command']}


if __name__ == '__main__':
    result = inspect()
    destination = ROOT / 'research/mini-cdc-recovery.json'
    destination.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'report': str(destination), 'paths': [x['result'] for x in result['dispatch_paths']],
                      'hardware_io': False}))
