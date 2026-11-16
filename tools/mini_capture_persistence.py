"""Pure plan/parsers for persisting the original embedded A2 capture.

No device, browser, file or process access occurs here. A caller retains the raw
responses and controls its own connection/identity/firmware provenance gates.
Only a free-slot CSAVE of the already active, pristine A2 is planned. There is
no upload, retry, delete, CLOAD, AUDIO, preset or reset operation in this module.
"""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import re
import struct
import zlib

A2_BYTES = 4892
A2_SHA256 = '86f5ea91f8069180e30612bcaad5820b14a94dd6c2552290ca09253082238c47'
A2_CRC32 = 0x2144DF1C
A2_CONTENT_ID = 0x77AC505B
A2_ADDRESS = 0x02033C8C
A2_NAME = 'A2'
SLOTS, CHUNK_BYTES = 15, 96
ORIGINAL_PLAIN_SHA256 = '2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334'
MODEL_LINE = "MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=0.0"


class CapturePersistenceError(ValueError):
    pass


def require(test, message):
    if not test:
        raise CapturePersistenceError(message)


def _lines(value):
    if isinstance(value, str):
        value = value.splitlines()
    require(isinstance(value, (list, tuple)) and 0 < len(value) <= 64,
            'a bounded, nonempty command response is required')
    require(all(isinstance(line, str) and 0 < len(line) <= 4096
                and all(32 <= ord(c) <= 126 for c in line) for line in value),
            'response contains control/non-ASCII characters or an oversized line')
    return list(value)


def _one(value):
    lines = _lines(value)
    require(len(lines) == 1, 'exactly one response line is required')
    return lines[0]


def _slot(value):
    require(type(value) is int and 0 <= value < SLOTS, 'capture slot must be 0..14')
    return value


def validate_blob(blob):
    """Identify the exact original default; this is not a generic upload codec."""
    require(isinstance(blob, bytes) and len(blob) == A2_BYTES,
            'the pristine embedded A2 must contain 4892 bytes')
    require(hashlib.sha256(blob).hexdigest() == A2_SHA256, 'embedded A2 SHA256 differs')
    require(blob[:4] == b'A2L1' and zlib.crc32(blob) == A2_CRC32
            and struct.unpack_from('<I', blob, len(blob)-4)[0] == A2_CONTENT_ID
            and zlib.crc32(blob[:-4]) == A2_CONTENT_ID,
            'embedded A2 format/CRC/content id differs')
    return {'bytes': len(blob), 'sha256': A2_SHA256, 'crc': A2_CRC32,
            'id': A2_CONTENT_ID, 'format': 'A2L1', 'name': A2_NAME}


def parse_clist(value):
    """Strict full CLIST; a missing/endless/garbled listing never implies free."""
    lines = _lines(value)
    end = re.fullmatch(r'CLIST end current=(-?\d+) slots=(\d+)', lines[-1])
    require(end is not None and int(end[2]) == SLOTS, 'complete 15-slot CLIST required')
    current = int(end[1])
    require(-1 <= current < SLOTS, 'CLIST current is outside the capture library')
    entries, last = [], -1
    pattern = re.compile(r"CAP (\d+) (\d+) '([^']{0,23})' trim=(-?\d+(?:\.\d+)?)"
                         r"(?: in=(-?\d+(?:\.\d+)?))?( amx)?")
    for line in lines[:-1]:
        match = pattern.fullmatch(line)
        require(match is not None, 'malformed or extra CLIST response')
        slot, length = int(match[1]), int(match[2])
        require(last < slot < SLOTS and 0 < length <= 8152,
                'CLIST slots must be unique, ascending and within bounds')
        last = slot
        entries.append({'slot': slot, 'bytes': length, 'name': match[3],
                        'trim': float(match[4]),
                        'in_dbu': None if match[5] is None else float(match[5]),
                        'amx': match[6] is not None})
    require(current == -1 or any(e['slot'] == current for e in entries),
            'current capture is absent from the complete CLIST')
    return {'current': current, 'slots': SLOTS, 'entries': entries, 'raw': lines}


def parse_cread_header(value, *, slot):
    slot = _slot(slot)
    line = _one(value)
    match = re.fullmatch(r"CREAD (\d+) len=(\d+) crc=([0-9a-f]{8}) id=([0-9a-f]{8})"
                         r" aux=(-?\d+) fs=(\d+) name='([^']{0,23})'", line)
    require(match is not None and int(match[1]) == slot, 'CREAD header slot/format differs')
    length, aux = int(match[2]), int(match[5])
    require(0 < length <= 8152 and -(1 << 31) <= aux < (1 << 31), 'CREAD header out of bounds')
    return {'slot': slot, 'len': length, 'crc': int(match[3], 16),
            'id': int(match[4], 16), 'aux': aux, 'fs': int(match[6]),
            'name': match[7], 'raw': line}


def parse_cread_chunk(value, *, slot, offset, total=A2_BYTES):
    slot = _slot(slot)
    require(type(total) is int and 0 < total <= 8152 and type(offset) is int
            and 0 <= offset < total and offset % CHUNK_BYTES == 0,
            'CREAD chunk offset/total is outside the bounded sequence')
    line = _one(value)
    match = re.fullmatch(r'CREAD (\d+) (\d+) (\d+) ([0-9a-f]{8}) ([A-Za-z0-9+/]+={0,2})', line)
    require(match is not None and int(match[1]) == slot and int(match[2]) == offset,
            'CREAD chunk slot/offset/format differs')
    expected = min(CHUNK_BYTES, total-offset)
    require(int(match[3]) == expected, 'CREAD chunk length differs from firmware 96-byte framing')
    try:
        data = base64.b64decode(match[5], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise CapturePersistenceError('invalid CREAD base64') from exc
    require(len(data) == expected and base64.b64encode(data).decode('ascii') == match[5],
            'CREAD base64 is noncanonical or has a different length')
    require(zlib.crc32(data) == int(match[4], 16), 'CREAD chunk CRC differs')
    return {'slot': slot, 'offset': offset, 'len': len(data),
            'crc': int(match[4], 16), 'data': data, 'raw': line}


def _a2_entry(slot):
    return {'slot': slot, 'bytes': A2_BYTES, 'name': A2_NAME,
            'trim': 0.0, 'in_dbu': None, 'amx': False}


def plan_capture(answers, blob):
    """Plan at most one CSAVE; existing active A2 is read/verified without write.

    answers maps literal command strings to their response-line lists. Firmware
    image, fresh PONG, connection ownership, audio and preset gates belong to the
    caller. MODEL/CLIST are observations, not proof of the live model's RAM bytes.
    """
    validate_blob(blob)
    require(isinstance(answers, dict) and 'MODEL' in answers and 'CLIST' in answers,
            'MODEL and complete CLIST observations are required')
    require(_one(answers['MODEL']) == MODEL_LINE, 'only the unchanged default A2/trim0 is supported')
    before = parse_clist(answers['CLIST'])
    slot = before['current']
    save = slot == -1
    if save:
        occupied = {entry['slot'] for entry in before['entries']}
        slot = next((s for s in range(SLOTS) if s not in occupied), None)
        require(slot is not None, 'no free capture slot; existing captures will not be overwritten')
    else:
        entry = next(e for e in before['entries'] if e['slot'] == slot)
        require(entry == _a2_entry(slot), 'current capture metadata is not pristine A2')
    return {'schema': 1, 'kind': 'mini-default-a2-capture-persistence-plan',
            'slot': slot, 'name': A2_NAME, 'request': f'CSAVE {slot} A2' if save else None,
            'before': before, 'model_before': _one(answers['MODEL']),
            'header_request': f'CREAD {slot}',
            'chunk_requests': [f'CREAD {slot} {off}' for off in range(0, A2_BYTES, CHUNK_BYTES)],
            'expected': {**validate_blob(blob), 'aux': 0, 'fs': 0},
            'retries': 0, 'capture_intentionally_retained': True,
            'cold_reload_proven': False, 'audio_quality_proven': False}


def verify_capture(plan, answers, blob):
    """Verify ACK, full readback and inventory from a retained command transcript.

    This result verifies supplied bytes only. The browser wrapper must attach
    actual transport/identity/image/close provenance; this function cannot claim
    that hardware executed the transcript or that a power-cycle retained it.
    """
    require(isinstance(plan, dict) and isinstance(answers, dict), 'plan and response mapping required')
    require('before' in plan and 'model_before' in plan, 'capture plan is incomplete')
    canonical = plan_capture({'MODEL': [plan['model_before']], 'CLIST': plan['before'].get('raw')}, blob)
    require(plan == canonical, 'capture plan differs from its observed immutable preconditions')
    slot, request = plan['slot'], plan['request']
    needed = {'MODEL', 'CLIST', plan['header_request'], *plan['chunk_requests']}
    if request:
        needed.add(request)
    require(set(answers) == needed, 'capture transcript has missing, extra or unrelated commands')
    if request:
        require(_one(answers[request]) == f"CSAVE ok {slot} 'A2' {A2_BYTES} B",
                'CSAVE ACK differs or did not confirm the complete capture')
    require(_one(answers['MODEL']) == plan['model_before'], 'MODEL changed during capture persistence')
    after = parse_clist(answers['CLIST'])
    expected_entries = copy.deepcopy(plan['before']['entries'])
    if request:
        expected_entries.append(_a2_entry(slot)); expected_entries.sort(key=lambda e: e['slot'])
    require(after['current'] == slot and after['entries'] == expected_entries,
            'current capture or existing library metadata changed unexpectedly')
    header = parse_cread_header(answers[plan['header_request']], slot=slot)
    expected_head = {'slot': slot, 'len': A2_BYTES, 'crc': A2_CRC32, 'id': A2_CONTENT_ID,
                     'aux': 0, 'fs': 0, 'name': A2_NAME}
    require({k: v for k, v in header.items() if k != 'raw'} == expected_head,
            'stored A2 metadata differs from the planned header')
    chunks = [parse_cread_chunk(answers[command], slot=slot, offset=off)
              for off, command in zip(range(0, A2_BYTES, CHUNK_BYTES), plan['chunk_requests'])]
    received = b''.join(chunk['data'] for chunk in chunks)
    require(received == blob, 'CREAD bytes differ from the original embedded A2')
    validate_blob(received)
    return {'schema': 1, 'kind': 'mini-default-a2-capture-transcript-verification',
            'verified': True, 'slot': slot, 'name': A2_NAME,
            'capture_sha256': A2_SHA256, 'capture_bytes': A2_BYTES,
            'capture_crc32': A2_CRC32, 'capture_content_id': A2_CONTENT_ID,
            'csave_request': request, 'csave_ack': _one(answers[request]) if request else None,
            'current_capture': after['current'], 'clist': after, 'header': header,
            'model': _one(answers['MODEL']), 'chunk_count': len(chunks),
            'chunk_offsets': [c['offset'] for c in chunks],
            'readback_byte_exact': True, 'preexisting_inventory_metadata_unchanged': True,
            'capture_intentionally_retained': True, 'command_responses': copy.deepcopy(answers),
            'hardware_execution_attested': False, 'cold_reload_proven': False,
            'power_cycle_retention_proven': False, 'audio_quality_proven': False}


def audit_default(original_plain, candidate_plain, editor_source, blob):
    """Offline byte provenance for direct CSAVE and the original CREAD framing.

    Both images are decoded application-area bytes whose CPU base is02000000.
    The caller supplies all inputs; no file access or candidate mutation occurs.
    """
    validate_blob(blob)
    require(isinstance(original_plain, bytes) and isinstance(candidate_plain, bytes)
            and hashlib.sha256(original_plain).hexdigest() == ORIGINAL_PLAIN_SHA256,
            'original decoded G application differs')
    require(isinstance(editor_source, str), 'original editor text required')
    anchors = ('Pedal.cmd(`CSAVE ${slot} ${name.slice(0, 23)}`, "CSAVE", 8000)',
               'await send(`${c} ${slot}`, pre, 3000)',
               'await send(`${c} ${slot} ${off}`, pre, 3000)',
               'const PIO_SLOT_MAX = 8152',
               'S.capSlot = c ? +c[1] : -1;',
               'trim=-3.0 [in=16.3] de MODEL / CLIST / CTRIM')
    require(all(a in editor_source for a in anchors), 'original editor CSAVE/CREAD anchors changed')
    pieces = {
        'csave_validate_copy': (0x0200C28C, 0x0200C2CA),
        'csave_header_and_store': (0x0200C2CA, 0x0200C36E),
        'csave_success': (0x0200C532, 0x0200C56E),
        'capture_store_write_readback': (0x0200A622, 0x0200A730),
        'cread_handler': (0x020070A4, 0x020072EA),
        'capture_load': (0x020087CC, 0x0200892C),
        'capture_aux_pack': (0x0200A5E2, 0x0200A622),
        'model_trim_and_optional_input_level': (0x020127B4, 0x02012830),
        'initialized_current_slot': (0x02075909, 0x0207590A),
        'initialized_pointer_and_length': (0x0207593C, 0x02075944),
    }
    evidence = {}
    for label, (start, end) in pieces.items():
        offset, size = start-0x02000000, end-start
        data = original_plain[offset:offset+size]
        require(len(data) == size and candidate_plain[offset:offset+size] == data,
                label+' differs from original firmware')
        evidence[label] = {'start': start, 'end_exclusive': end,
                           'sha256': hashlib.sha256(data).hexdigest(), 'candidate_identical': True}
    require(original_plain[0x75909] == 0xff
            and struct.unpack_from('<II', original_plain, 0x7593C) == (A2_ADDRESS, A2_BYTES),
            'default capSlot/pointer/length initialization differs')
    offset = A2_ADDRESS-0x02000000
    require(original_plain[offset:offset+A2_BYTES] == blob
            and candidate_plain[offset:offset+A2_BYTES] == blob
            and original_plain.count(blob) == 1 and candidate_plain.count(blob) == 1,
            'embedded A2 is not unique at the pinned address')
    return {'schema': 1, 'kind': 'mini-default-a2-csave-offline-audit',
            'original_plain_sha256': ORIGINAL_PLAIN_SHA256,
            'candidate_plain_sha256': hashlib.sha256(candidate_plain).hexdigest(),
            'editor_text_sha256': hashlib.sha256(editor_source.encode('utf-8')).hexdigest(),
            'capture': {**validate_blob(blob), 'address': A2_ADDRESS}, 'fragments': evidence,
            'csave_accepts_current_minus_one': True,
            'csave_uses_active_pointer_and_length': True,
            'csave_requires_upload': False, 'csave_success_assigns_current_slot': True,
            'same_slot_cload_can_reuse_live_model': True,
            'cread_header_request': 'CREAD <slot>',
            'cread_chunk_request': 'CREAD <slot> <offset>', 'chunk_max_bytes': CHUNK_BYTES,
            'metadata': {
                'shared_live_metadata': 0x01C26B48,
                'trim_half_db_offset': 0, 'input_decidbu_offset': 4,
                'input_level_present_offset': 8,
                'MODEL_uses_same_metadata_as_CSAVE': True,
                'exact_MODEL_requires_trim_zero_and_no_optional_in_field': True,
                'aux_zero': 'A5F6 returns clamped trim lowbyte when input-level-present is zero.',
                'capture_fs_zero': 'CREAD capture-only branch sets r1=0 at020072CC; IR branch sets24/48.',
                'fs_is_not_the_A2L_sample_rate': True,
                'header_aux_and_CLIST_in_absence_must_still_match_after_save': True},
            'slot_zero_flash_range': [0xDF000, 0xE1000], 'slot_header_bytes': 40,
            'hardware_executed': False, 'power_cycle_retention_proven': False,
            'limits': ['MODEL/CLIST do not prove the live RAM capture contents before CSAVE.',
                       'Exact CREAD byte comparison is required after any CSAVE.',
                       'The observed library metadata, not every other capture payload, is compared.',
                       'This audit does not grant a UI write capability or prove audio quality.']}
