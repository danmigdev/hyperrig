"""Independent offline checks of a completed MINI installation and full dump.

Default/import never opens a device or a hardware log. --inspect first reads a
shared snapshot and refuses unfinished runs before reading their trace/journal.
This verifies retained evidence, not successful execution of the installed app.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_mini_app_writer import validate_audit_record
from tools.mini_host_journal import read_shared_json

APP_START, APP_END, CAPACITY = 0x4000, 0x82000, 0x100000
STOCK_SHA = '72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180'
CANDIDATE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
EXPECTED_FULL_SHA = 'a35868ab3a4beb42454070ce46d67efaf695615a670de177343860e88d107c47'
REGIONS = ((0, 0x4000, 'SPL and boot configuration'),
           (0x82000, 0xBE000, 'VM and staged updater'),
           (0xBE000, 0xBF000, 'BTIF'), (0xBF000, 0xFF000, 'USR'),
           (0xFF000, 0x100000, 'key_mac'))
STATEFUL = {0xFC7A, 0xFB7C, 0xFD87, 0xFC7B, 0xFC7D, 0xFC80}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()
def crc(data): return zlib.crc32(data) & 0xFFFFFFFF


def page_order(sector):
    require(type(sector) is int and APP_START <= sector < APP_END and sector % 4096 == 0,
            'sector outside MINI application')
    pages = list(range(sector, sector + 4096, 256))
    return pages[1:] + pages[:1] if sector == APP_START else pages


def compare_nor(stock, preimage, candidate, observed):
    require(all(isinstance(x, bytes) for x in (stock, preimage, candidate, observed)),
            'immutable input bytes required')
    require(len(stock) == len(preimage) == len(observed) == CAPACITY
            and len(candidate) == APP_END - APP_START, 'complete NOR/application extents required')
    require(observed[APP_START:APP_END] == candidate, 'installed application differs from candidate')
    regions = []
    for start, end, name in REGIONS:
        require(preimage[start:end] == stock[start:end], 'preimage differs outside app: ' + name)
        require(observed[start:end] == stock[start:end], 'post-install bytes differ outside app: ' + name)
        regions.append({'name': name, 'range': [start, end], 'bytes': end - start,
                        'sha256': sha(observed[start:end]), 'byte_for_byte_unchanged': True})
    changed, retained = [], []
    for address in range(APP_START, APP_END, 4096):
        page = candidate[address - APP_START:address - APP_START + 4096]
        (retained if preimage[address:address + 4096] == page else changed).append(address)
    order = [a for a in changed if a != APP_START] + ([APP_START] if APP_START in changed else [])
    return {'full_NOR_sha256': sha(observed), 'candidate_sha256': sha(candidate),
            'preserved_regions': regions, 'sector_order': order,
            'already_matching_sectors': retained, 'application_exact': True}


def expected_stateful_commands(preimage, candidate, order):
    """Reconstruct wire bytes independently of the installer CDB builders."""
    result = []
    for token, sector in enumerate(order, 1):
        require(sector in range(APP_START, APP_END, 4096), 'invalid sector')
        old = preimage[sector:sector + 4096]
        new = candidate[sector - APP_START:sector - APP_START + 4096]
        result.append((b'\xfc\x7a' + struct.pack('>III', sector, crc(old), crc(new)) + b'\xff\xff', None, None))
        sequence = 1
        for index, address in enumerate(page_order(sector)):
            page = candidate[address - APP_START:address - APP_START + 256]
            sequence += 1
            result.append((b'\xfb\x7c' + struct.pack('>IIIH', token, sequence, address, 256),
                           sha(page + struct.pack('>I', crc(page))), sha(b'')))
            result.append((b'\xfd\x87' + struct.pack('>III', token, sequence, address) + b'\xff\xff',
                           None, sha(page)))
            if index == 0:
                sequence += 1
                result.append((b'\xfc\x7b' + struct.pack('>III', token, sequence, sector) + b'\xff\xff', None, None))
            sequence += 1
            result.append((b'\xfc\x7d' + struct.pack('>III', token, sequence, address) + b'\xff\xff', None, None))
        sequence += 1
        require(sequence == 35, 'sector sequence reconstruction differs')
        result.append((b'\xfc\x80' + struct.pack('>III', token, sequence, sector) + b'\xff\xff', None, None))
    return result


def inspect_history(journal, trace, preimage, candidate, order):
    require(len(order) == len(set(order)) and order == sorted(a for a in order if a != APP_START)
            + ([APP_START] if APP_START in order else []), 'sector order differs or repeats')
    pairs, pending = [], None
    for entry in journal:
        event = entry['event']
        require(event != 'terminal_error', 'installer journal contains a terminal error')
        if event == 'command_intent':
            require(pending is None, 'command intent has no preceding reply')
            pending = entry
        elif event == 'command_reply':
            require(pending is not None and pending['opcode'] == entry['opcode'], 'unmatched journal reply')
            pairs.append((pending, entry)); pending = None
    require(pending is None, 'journal ends with an ambiguous command')
    actual = [(a, b) for a, b in pairs if int(a['opcode'], 16) in STATEFUL]
    expected = expected_stateful_commands(preimage, candidate, order)
    require(len(actual) == len(expected), 'stateful command count differs')
    for (intent, reply), (cdb, out_hash, reply_hash) in zip(actual, expected):
        require(intent['cdb_hex'] == cdb.hex() and intent['data_out_sha256'] == out_hash,
                'stage/echo/erase/program/finish bytes or ordering differ')
        require(reply_hash is None or reply['sha256'] == reply_hash, 'stage or echo reply differs from candidate page')
    pages = [address for sector in order for address in page_order(sector)]
    for event, addresses, width in (('page_echo_verified', pages, 256),
                                    ('page_program_verified', pages, 256),
                                    ('sector_verified', order, 4096)):
        entries = [x for x in journal if x['event'] == event]
        require([x['address'] for x in entries] == addresses, event + ': address order differs')
        for item in entries:
            address = item['address']; expected_bytes = candidate[address - APP_START:address - APP_START + width]
            require(item['sha256'] == sha(expected_bytes), event + ': bytes hash differs')
            if width == 4096:
                require(item['program_page_order'] == page_order(address), 'recorded header page order differs')
    require(len(trace) % 2 == 0, 'trace has unmatched command intent')
    observed, errors = [], []
    for before, after in zip(trace[::2], trace[1::2]):
        require(before['state'] == 'before' and after['state'] in ('after', 'error')
                and before['cdb'] == after['cdb'] and before['stage'] == after['stage'], 'trace command pairing differs')
        op = int(before['cdb'][:4], 16)
        if after['state'] == 'error':
            require(op in (0xFD7F, 0xFC7E, 0xFD88)
                    and after['native_transfer']['win32_error'] == 31,
                    'trace contains a mutation/OUT/jump failure or unreviewed error')
            errors.append(after)
        else:
            if 'response_hex' in after:
                raw = bytes.fromhex(after['response_hex'])
                require(len(raw) == after['response_bytes'] and sha(raw) == after['response_sha256'], 'trace response hash differs')
            if op in STATEFUL:
                observed.append(after)
    require(len(observed) == len(actual), 'stateful command was omitted/repeated in transport trace')
    for row, (intent, reply) in zip(observed, actual):
        require(row['cdb'] == intent['cdb_hex'] and row['response_sha256'] == reply['sha256'],
                'transport and installer command evidence disagree')
    require(APP_START not in order or pages[-1] == APP_START, 'header page was not programmed last')
    return {'erase_commands': len(order), 'program_commands': len(pages),
            'expected_WREN_count': len(order) + len(pages), 'program_order': pages,
            'header_sector_last': APP_START not in order or order[-1] == APP_START,
            'header_page_last': APP_START not in order or pages[-1] == APP_START,
            'read_query_errors': len(errors), 'stateful_transport_commands': len(observed),
            'automatic_mutation_retries_observed': False}


def inspect_bundle(run_path):
    run_path = Path(run_path).resolve()
    run = read_shared_json(run_path)
    require(run.get('finished_utc') and not run.get('error')
            and run['phase'] == 'installed_verified_waiting_for_footswitch', 'completed successful run required')
    require(run['installed_image_verified'] and run['full_NOR_verified']
            and run['known_live_slot'] == 0x1C28000 and not run['jump_outcome_unknown']
            and not run['mutation_completion_unknown'] and not run['writer_final']['failed'], 'run ended with unresolved hardware state')
    require(run['MCN_pause_closed'] and run['MCN_explicitly_reenabled'], 'MCN cleanup incomplete')
    for name, digest in run['source_pins'].items():
        require(sha((ROOT / name).read_bytes()) == digest, 'recorded source changed: ' + name)
    plan_path = ROOT / run['new_preimage_plan']; plan_raw = plan_path.read_bytes(); plan = json.loads(plan_raw)
    require(sha(plan_raw) == run['installation']['plan_sha256'], 'installation plan binding differs')
    stock_path = ROOT / plan['stock_backup']['path']; before_path = ROOT / run['full_before']['path']
    after_path = ROOT / run['full_after']['path']
    candidate_path = ROOT / 'build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin'
    stock, before, candidate, after = [p.read_bytes() for p in (stock_path, before_path, candidate_path, after_path)]
    require(sha(stock) == STOCK_SHA and sha(candidate) == CANDIDATE_SHA and sha(after) == EXPECTED_FULL_SHA,
            'pinned unit backup, candidate or final NOR differs')
    images = compare_nor(stock, before, candidate, after); order = images['sector_order']
    require(order == plan['sector_order'] == run['installation']['sector_order'], 'changed sectors differ from plan')
    require(sha(before) == run['full_before']['sha256'] == plan['fresh_full_read']['sha256'], 'fresh preimage binding differs')
    prefix = str(run_path)[:-len('-run.json')]
    journal_path, trace_path = Path(prefix + '-journal.jsonl'), Path(prefix + '-trace.jsonl')
    journal = [json.loads(x) for x in journal_path.read_text().splitlines()]
    trace = [json.loads(x) for x in trace_path.read_text().splitlines()]
    history = inspect_history(journal, trace, before, candidate, order)
    audit_rows = [x for x in journal if x['event'] == 'audit_raw']
    require(audit_rows, 'raw target audits missing')
    counters = (0, 0, 0); last = None
    for row in audit_rows:
        raw = bytes.fromhex(row['record_hex']); require(sha(raw) == row['sha256'], 'audit hash differs')
        item = validate_audit_record(raw, base=run['installation']['slot'],
            build_tag=run['installation']['build_tag'], expected_mutations_enabled=True)
        require(item['error'] == 0 and item['rx_guards_ok'] == item['stack_guards_ok'] == 1,
                'target audit error or guard damage')
        current = item['wren_attempts'], item['erase_attempts'], item['program_attempts']
        require(current[0] == current[1] + current[2] and all(a <= b for a, b in zip(counters, current)),
                'target mutation counter regression or mismatch')
        require(not item['sr1'] & 0x7F and not item['sr2'] & 0x40, 'busy/write-enabled/protected target audit')
        counters, last = current, item
    expected_counts = (len(order) * 17, len(order), len(order) * 16)
    require(counters == expected_counts and last == run['writer_final']['last_audit'], 'final target counters/audit differ')
    require(last['read_bytes'] == 2 * len(candidate) + 40960 * len(order), 'final target read counter differs')
    require(last['phase'] == 5 and last['token'] == 0 and last['sequence'] == 35
            and last['sector'] == last['page'] == APP_START and last['page_bitmap'] == 65535
            and last['raw_receive_return'] == 260 and last['staged'] == last['echoed'] == 0,
            'final committed header-sector state differs')
    require(run['writer_final']['verified_sectors'] == order, 'final verified sector list differs')
    events = [x for x in journal if x['event'] == 'application_verified']
    require(len(events) == 1 and events[0]['application_sha256'] == sha(candidate)
            and events[0]['application_verified'] is True, 'final application evidence missing')
    full_preimage = [x for x in journal if x['event'] == 'whole_preimage_verified']
    require(len(full_preimage) == 1 and full_preimage[0]['sha256'] == sha(before[APP_START:APP_END]),
            'complete preimage verification evidence differs')
    inputs = (run_path, plan_path, stock_path, before_path, candidate_path, after_path, journal_path, trace_path)
    return {'schema': 1, 'kind': 'independent-offline-installed-MINI-verification',
            'verified': True, 'inputs': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p.read_bytes()) for p in inputs},
            'images': images, 'history': history, 'target_audits_checked': len(audit_rows),
            'final_target_audit': last, 'source_pins_match': True,
            'finished_utc': run['finished_utc'], 'application_execution_proven': False,
            'power_loss_atomicity_proven': False, 'device_io_performed_by_verifier': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--run', type=Path, default=ROOT / 'analysis/hardware/mini-mcn-install-run.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = inspect_bundle(args.run) if args.inspect else {'device_io': False, 'logs_read': False}
    if args.output:
        require(args.inspect, '--output requires --inspect')
        with args.output.open('x', encoding='utf8', newline='\n') as stream:
            stream.write(json.dumps(result, indent=2) + '\n')
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
