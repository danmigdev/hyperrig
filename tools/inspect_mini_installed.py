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
MUTATIONS = {0xFC7B, 0xFC7D}
WRITER_RECOVERABLE = {0xFD7F, 0xFC7E, 0xFD88, 0xFD87, *MUTATIONS, 0xFC80}
NOR_READ_STAGES = {'full_after', 'full-read-recovery-reopen'}


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


def recovery_groups(recovery):
    """Keep mixed v2/v3/v4/v5 records in their durable, original order."""
    groups = []
    for item in recovery['events']:
        event = item['event']
        require(not event.endswith(('_terminal', '_not_permitted')),
                'successful run contains a terminal recovery event')
        if event in ('readonly_recovery_begin', 'unexecuted_mutation_recovery_begin',
                     'unexecuted_finish_recovery_begin'):
            groups.append([])
        require(groups, 'recovery event precedes its begin witness')
        groups[-1].append(item)
    require(len(groups) == recovery['summary']['recovery_attempts'],
            'recovery event/summary count differs')
    return groups


def validate_v4_policy(recovery):
    require(recovery is not None and recovery.get('v4_source_pinned') is True
            and recovery.get('v3_source_pinned') is True, 'v4 and inherited v3 source pins required')
    summary, policy = recovery['summary'], recovery['policy']
    require(summary.get('version') in (4, 5, 6) and summary.get('failed') is False
            and type(summary['max_recoveries']) is int
            and 0 <= summary['recovery_attempts'] <= summary['max_recoveries'] <= (32 if summary['version'] == 6 else 8)
            and summary.get('completed_NOR_mutations_repeated') == 0
            and summary.get('mutation_retries_allowed') is True
            and summary.get('executed_or_ambiguous_mutation_retry') is False
            and summary.get('synthetic_mutation_ACK') is False,
            'v4 summary permits executed mutations, synthetic ACK or excess retries')
    require(policy.get('enabled') is True and policy.get('only_Windows_error') == 31
            and policy.get('mutation_retries_allowed') is True
            and policy.get('mutation_request_reissue_requires_exact_prior_audit') is True
            and policy.get('one_recovery_per_command_and_expected_state') is True
            and policy.get('executed_mutation_retries_allowed') is False
            and policy.get('OUT_retries_allowed') is False
            and policy.get('jump_or_reset_retries_allowed') is False
            and policy.get('backend_fallback_allowed') is False,
            'v4 mutation recovery policy is not the reviewed nonexecution policy')
    if summary['version'] >= 5:
        require(recovery.get('v5_source_pinned') is True
                and policy.get('FINISH_reissue_requires_exact_prior_audit_and_complete_candidate_sector') is True
                and summary.get('completed_FINISH_requests_repeated') == 0
                and summary.get('executed_or_ambiguous_FINISH_retry') is False
                and summary.get('synthetic_FINISH_ACK') is False,
                'v5 FINISH source and exact nonexecution policy required')
    if summary['version'] == 6:
        require(recovery.get('v6_source_pinned') is True
                and summary.get('command_witness_policy_unchanged_from_v5') is True
                and policy.get('command_witness_policy_unchanged_from_v5') is True
                and policy.get('max_reopens') == summary['max_recoveries'],
                'v6 bounded session limit lacks its pinned unchanged command policy')
    return recovery_groups(recovery)


def inspect_echo_recoveries(journal, trace, candidate, recovery):
    """Independently reconcile v3's sole extra retry: frozen-RAM FD87 IN."""
    faults = [index for index, row in enumerate(trace)
              if row['state'] == 'error' and row['cdb'].startswith('fd87')]
    if not faults:
        require(recovery is None or recovery['summary'].get('echo_reissues', 0) == 0,
                'echo recovery summary has no corresponding transport error')
        return []
    require(recovery is not None and recovery.get('v3_source_pinned') is True,
            'FD87 errors require pinned v3 recovery evidence')
    summary, policy, events = recovery['summary'], recovery['policy'], recovery['events']
    version = summary.get('version')
    require(version in (3, 4, 5, 6) and not summary['failed']
            and summary['echo_reissues'] == len(faults)
            and 1 <= summary['recovery_attempts'] <= summary['max_recoveries'] <= (32 if version == 6 else 8),
            'v3 echo recovery version/count/budget differs')
    require(policy['enabled'] and policy['only_Windows_error'] == 31
            and policy['FD87_requires_same_staged_page_and_exact_audit_except_echoed_and_record_CRC']
            and policy['FD87_reissue_requires_exact_candidate_page_bytes']
            and policy['mutation_retries_allowed'] is (version >= 4) and not policy['OUT_retries_allowed']
            and not policy['jump_or_reset_retries_allowed'] and not policy['backend_fallback_allowed'],
            'v3 recovery policy is not the reviewed bounded RAM-echo policy')
    groups = validate_v4_policy(recovery) if version >= 4 else recovery_groups(recovery)
    echoes = [group for group in groups if group[0]['cdb'].startswith('fd87')]
    require(len(echoes) == len(faults), 'FD87 errors and recovery witnesses differ')
    names = ['begin', 'close_intent', 'reopen_intent', 'identity_intent', 'identity_reply',
             'audit_intent', 'audit_reply', 'reissue_intent', 'reissue_reply']
    results, keys = [], set()
    for fault_index, group in zip(faults, echoes):
        require([item['event'] for item in group] == ['readonly_recovery_' + name for name in names],
                'FD87 recovery event order differs')
        begin, identity, audit_event, reissue, reply = (group[i] for i in (0,4,6,7,8))
        cdb = bytes.fromhex(trace[fault_index]['cdb'])
        token, sequence, address = struct.unpack_from('>III', cdb, 2)
        require(len(cdb) == 16 and cdb[14:] == b'\xff\xff'
                and APP_START <= address <= APP_END - 256 and address % 256 == 0,
                'FD87 recovery address/CDB differs')
        page = candidate[address - APP_START:address - APP_START + 256]
        require(begin['cdb'] == reissue['cdb'] == cdb.hex() and begin['read_length'] == reissue['read_length'] == 256
                and begin['win32_error'] == 31 and begin['mutation_audit'] is False
                and begin['mutation_retries_allowed'] is False,
                'FD87 recovery witness describes another operation')
        expected = begin['expected_state']
        material = json.dumps({'cdb': cdb.hex(), 'length': 256, 'expected': expected,
                               'mutation_audit': False}, sort_keys=True, separators=(',', ':')).encode()
        require(begin['witness_sha256'] == sha(material) and begin['witness_sha256'] not in keys,
                'FD87 recovery witness hash differs or was used twice')
        keys.add(begin['witness_sha256'])
        prior_raw, fresh_raw = bytes.fromhex(begin['prior_audit_hex']), bytes.fromhex(audit_event['raw_hex'])
        old = validate_audit_record(prior_raw, base=recovery['slot'], build_tag=recovery['build_tag'], expected_mutations_enabled=True)
        fresh = validate_audit_record(fresh_raw, base=recovery['slot'], build_tag=recovery['build_tag'], expected_mutations_enabled=True)
        require(old['error'] == 0 and old['phase'] == 4 and old['staged'] == 1 and old['echoed'] == 0
                and old['raw_receive_return'] == 260 and old['jedec'] == 0xEB6014
                and old['rx_guards_ok'] == old['stack_guards_ok'] == 1 and old['stack_observed_bytes'] > 0
                and not old['sr1'] & 0x7F and not old['sr2'] & 0x40
                and (old['token'], old['sequence'], old['page']) == (token, sequence, address)
                and old['page_crc32'] == old['last_crc32'] == crc(page)
                and all(old.get(name) == value for name, value in expected.items()),
                'FD87 prior audit is not the exact staged candidate witness')
        require(fresh['echoed'] in (0,1) and prior_raw[:104] == fresh_raw[:104]
                and prior_raw[108:120] == fresh_raw[108:120] and prior_raw[124:] == fresh_raw[124:]
                and sha(fresh_raw) == audit_event['sha256'],
                'FD87 fresh audit changed beyond echoed and envelope CRC')
        identity_raw = b'\xfc\x78HYW1\1\1' + struct.pack('>II', recovery['slot'], 32768)
        require(bytes.fromhex(identity['raw_hex']) == identity_raw
                and reissue['read_only'] is True and reissue['no_NOR_access'] is True
                and reissue['prior_echoed'] == 0 and reissue['fresh_echoed'] == fresh['echoed']
                and reissue['stack_observed_bytes_unchanged'] == old['stack_observed_bytes']
                and begin['candidate_page_sha256'] == reissue['candidate_page_sha256'] == reply['sha256'] == sha(page)
                and reply['bytes'] == 256 and reply['echo_already_emitted'] == bool(fresh['echoed'])
                and reply['subsequent_installer_status_and_audit_still_required'] is True,
                'FD87 recovery identity/page/stack evidence differs')
        require(fault_index >= 2 and trace[fault_index-2]['state'] == 'after'
                and trace[fault_index-2]['cdb'] == 'fd88' + 'ff' * 14
                and bytes.fromhex(trace[fault_index-2]['response_hex']) == prior_raw,
                'failed FD87 lacks its immediately preceding validated audit')
        following = trace[fault_index+1:fault_index+7]
        require(len(following) == 6 and [row['state'] for row in following] == ['before','after'] * 3
                and [row['cdb'] for row in following[::2]] == ['fc78' + 'ff' * 14, 'fd88' + 'ff' * 14, cdb.hex()]
                and bytes.fromhex(following[1]['response_hex']) == identity_raw
                and bytes.fromhex(following[3]['response_hex']) == fresh_raw
                and following[5]['response_bytes'] == 256 and following[5]['response_sha256'] == sha(page),
                'FD87 transport recovery is not identity/audit/one exact echo reissue')
        intents = [index for index, row in enumerate(journal)
                   if row['event'] == 'command_intent' and row['cdb_hex'] == cdb.hex()]
        require(len(intents) == 1, 'FD87 recovery created multiple installer command intents')
        index = intents[0]
        require(journal[index+1]['event'] == 'command_reply' and journal[index+1]['opcode'] == 'fd87'
                and journal[index+1]['sha256'] == sha(page), 'FD87 installer reply differs')
        later = journal[index+2:]
        audit_index = next((n for n, row in enumerate(later) if row['event'] == 'audit_raw'), None)
        require(audit_index is not None and all(row.get('opcode') not in ('fc7b','fc7d','fb7c','fc80')
                for row in later[:audit_index]), 'mutation preceded reconciled echo audit')
        echoed_raw = bytearray(prior_raw)
        struct.pack_into('<I', echoed_raw, 104, 1)
        struct.pack_into('<I', echoed_raw, 120, crc(echoed_raw[:120]))
        require(bytes.fromhex(later[audit_index]['record_hex']) == bytes(echoed_raw),
                'post-reissue installer audit did not confirm echoed1 with unchanged state')
        results.append({'address': address, 'token': token, 'sequence': sequence,
                        'prior_audit_sha256': sha(prior_raw), 'fresh_audit_sha256': sha(fresh_raw),
                        'already_echoed': bool(fresh['echoed']), 'candidate_page_sha256': sha(page)})
    require(sum(item['already_echoed'] for item in results) == summary['echo_already_emitted'],
            'v3 already-emitted echo count differs')
    return results


def inspect_mutation_recoveries(journal, trace, candidate, recovery):
    """Require target nonexecution, one real ACK and one counted operation.

    This reconstructs the command and resulting audit without importing the
    recovery wrapper, installer or their CDB builders. A postexecution audit
    is never accepted as the witness for reissuing a mutation.
    """
    faults = [index for index, row in enumerate(trace) if row['state'] == 'error'
              and int(row['cdb'][:4], 16) in MUTATIONS]
    if not faults and (recovery is None or recovery['summary'].get('version') not in (4, 5, 6)):
        return []
    groups = validate_v4_policy(recovery)
    summary = recovery['summary']
    require(summary['recovery_attempts'] == sum(x['state'] == 'error'
            and int(x['cdb'][:4], 16) in WRITER_RECOVERABLE for x in trace),
            'v4 shared recovery count differs from actual transport failures')
    mutations = [g for g in groups if g[0]['event'] == 'unexecuted_mutation_recovery_begin']
    require(len(mutations) == len(faults) == summary['mutation_request_reissues'],
            'mutation faults, recovery witnesses and reissue count differ')
    names = ['unexecuted_mutation_recovery_' + name for name in
             ('begin', 'close_intent', 'reopen_intent')]
    names += ['readonly_recovery_identity_intent', 'readonly_recovery_identity_reply']
    names += ['unexecuted_mutation_recovery_' + name for name in
              ('audit_intent', 'audit_reply', 'reissue_intent', 'reissue_reply')]
    identity_raw = b'\xfc\x78HYW1\1\1' + struct.pack('>II', recovery['slot'], 32768)
    results, keys = [], set()
    for fault_index, group in zip(faults, mutations):
        require([x['event'] for x in group] == names, 'mutation recovery event order differs')
        begin, identity, fresh_event, reissue, reply = (group[i] for i in (0, 4, 6, 7, 8))
        cdb = bytes.fromhex(trace[fault_index]['cdb']); op = int.from_bytes(cdb[:2], 'big')
        require(len(cdb) == 16 and cdb[14:] == b'\xff\xff' and op in MUTATIONS,
                'mutation recovery CDB framing differs')
        token, sequence, address = struct.unpack_from('>III', cdb, 2)
        expected = begin['expected_state']
        prior_raw = bytes.fromhex(begin['prior_audit_hex'])
        fresh_raw = bytes.fromhex(fresh_event['raw_hex'])
        old = validate_audit_record(prior_raw, base=recovery['slot'], build_tag=recovery['build_tag'],
                                    expected_mutations_enabled=True)
        require(fresh_raw == prior_raw and fresh_event['sha256'] == sha(prior_raw),
                'mutation command changed target state; reissue was forbidden')
        require(old['error'] == 0 and old['phase'] == 4 and old['staged'] == old['echoed'] == 1
                and old['raw_receive_return'] == 260 and old['jedec'] == 0xEB6014
                and old['rx_guards_ok'] == old['stack_guards_ok'] == 1
                and old['stack_observed_bytes'] > 0 and not old['sr1'] & 0x7F and not old['sr2'] & 0x40
                and old['sequence'] < 0xFFFFFFFF and sequence == old['sequence'] + 1
                and token == old['token'] and expected['sequence'] == sequence
                and all(old.get(name) == value for name, value in expected.items() if name != 'sequence'),
                'mutation prior audit is not the validated unconsumed sequence')
        sector, page_address = old['sector'], old['page']
        require(APP_START <= sector < APP_END and sector % 4096 == 0
                and sector <= page_address < sector + 4096 and page_address % 256 == 0
                and address == (sector if op == 0xFC7B else page_address),
                'mutation address differs from prior staged sector/page')
        page = candidate[page_address - APP_START:page_address - APP_START + 256]
        require(len(page) == 256 and crc(page) == old['page_crc32'], 'mutation staged candidate differs')
        bit = 1 << ((page_address - sector) // 256)
        require(old['page_bitmap'] == 0 if op == 0xFC7B else not old['page_bitmap'] & bit,
                'mutation was already reflected in the target page bitmap')
        material = json.dumps({'opcode': op, 'cdb': cdb.hex(), 'length': 16,
                               'expected': expected, 'prior_record': prior_raw.hex()},
                              sort_keys=True, separators=(',', ':')).encode()
        require(begin['witness_sha256'] == sha(material) and begin['witness_sha256'] not in keys,
                'mutation witness differs or was reused')
        keys.add(begin['witness_sha256'])
        require(begin['cdb'] == reissue['cdb'] == cdb.hex()
                and begin['read_length'] == reissue['read_length'] == 16
                and begin['win32_error'] == 31 and begin['any_audit_change_forbids_reissue'] is True
                and begin['synthetic_ACK'] is reissue['synthetic_ACK'] is reply['synthetic_ACK'] is False
                and begin['candidate_page_sha256'] == reissue['candidate_page_sha256'] == sha(page)
                and reissue['raw_audit_identical'] is True and reissue['sequence_unconsumed'] is True
                and reissue['sequence_before'] == old['sequence'] and reissue['requested_sequence'] == sequence
                and bytes.fromhex(identity['raw_hex']) == identity_raw
                and reply['subsequent_installer_status_and_mutation_audit_required'] is True,
                'mutation reissue is missing exact nonexecution/identity evidence')
        ack_crc = crc(b'\xff' * 4096) if op == 0xFC7B else crc(page)
        ack = cdb[:2] + bytes((0, 4 if op == 0xFC7B else 3)) + struct.pack('>III', token, sequence, ack_crc)
        require(bytes.fromhex(reply['raw_hex']) == ack and reply['sha256'] == sha(ack),
                'mutation reissue has no actual correct ACK')
        require(fault_index >= 2 and trace[fault_index-2]['state'] == 'after'
                and trace[fault_index-2]['cdb'] == 'fd88' + 'ff' * 14
                and bytes.fromhex(trace[fault_index-2]['response_hex']) == prior_raw,
                'mutation fault lacks immediately preceding raw target audit')
        following = trace[fault_index+1:fault_index+7]
        require(len(following) == 6 and [x['state'] for x in following] == ['before', 'after'] * 3
                and [x['cdb'] for x in following[::2]] == ['fc78'+'ff'*14, 'fd88'+'ff'*14, cdb.hex()]
                and bytes.fromhex(following[1]['response_hex']) == identity_raw
                and bytes.fromhex(following[3]['response_hex']) == prior_raw
                and bytes.fromhex(following[5]['response_hex']) == ack
                and following[5]['response_bytes'] == 16 and following[5]['response_sha256'] == sha(ack),
                'mutation transport proof is not identity/audit/one actual exact reissue')
        intents = [i for i, x in enumerate(journal) if x['event'] == 'command_intent'
                   and x['cdb_hex'] == cdb.hex()]
        require(len(intents) == 1, 'mutation recovery duplicated installer command intent')
        index = intents[0]
        earlier = [x for x in journal[:index] if x['event'] == 'audit_raw']
        require(earlier and bytes.fromhex(earlier[-1]['record_hex']) == prior_raw,
                'mutation witness differs from the preceding installer audit')
        require(journal[index+1]['event'] == 'command_reply' and journal[index+1]['opcode'] == f'{op:04x}'
                and journal[index+1]['bytes'] == 16 and journal[index+1]['sha256'] == sha(ack),
                'installer mutation reply differs from actual target ACK')
        later = journal[index+2:]
        next_audit = next((i for i, x in enumerate(later) if x['event'] == 'audit_raw'), None)
        require(next_audit is not None and all(x.get('opcode') not in ('fc7a', 'fb7c', 'fd87', 'fc7b', 'fc7d', 'fc80')
                for x in later[:next_audit]), 'next stateful command preceded core postmutation audit')
        post_event = later[next_audit]; post_raw = bytes.fromhex(post_event['record_hex'])
        require(post_event['sha256'] == sha(post_raw), 'core postmutation audit hash differs')
        post = validate_audit_record(post_raw, base=recovery['slot'], build_tag=recovery['build_tag'],
                                     expected_mutations_enabled=True)
        changes = {'sequence': sequence, 'wren_attempts': old['wren_attempts']+1, 'last_crc32': ack_crc,
                   'read_bytes': old['read_bytes'] + (8192 if op == 0xFC7B else 512)}
        if op == 0xFC7B:
            changes['erase_attempts'] = old['erase_attempts']+1
        else:
            changes.update(phase=3, staged=0, echoed=0, program_attempts=old['program_attempts']+1,
                           page_bitmap=old['page_bitmap'] | bit)
        for name, value in old.items():
            if name not in ('status_polls', 'sr1', 'sr2', 'stack_observed_bytes', 'record_sha256'):
                require(post[name] == changes.get(name, value), 'postmutation audit differs: ' + name)
        require(1 <= post['status_polls']-old['status_polls'] <= 65536
                and not post['sr1'] & 0x7F and not post['sr2'] & 0x40 and post['stack_observed_bytes'] > 0,
                'postmutation polling/status/stack is not accepted by the core contract')
        wire_after_ack = trace[fault_index+7:]
        next_stateful = next((i for i, x in enumerate(wire_after_ack)
                             if int(x['cdb'][:4], 16) in STATEFUL), len(wire_after_ack))
        require(any(x['state'] == 'after' and x['cdb'] == 'fd88'+'ff'*14
                    and bytes.fromhex(x['response_hex']) == post_raw
                    for x in wire_after_ack[:next_stateful]), 'postmutation audit was not received from target')
        require(later[next_audit+1]['event'] == 'audit_verified'
                and (later[next_audit+1]['wren'], later[next_audit+1]['erase'], later[next_audit+1]['program'])
                == (post['wren_attempts'], post['erase_attempts'], post['program_attempts']),
                'original core did not validate exactly one completed mutation')
        results.append({'opcode': f'{op:04x}', 'address': address, 'token': token,
                        'sequence_before': old['sequence'], 'sequence_after': sequence,
                        'prior_and_fresh_audit_sha256': sha(prior_raw), 'actual_ACK_sha256': sha(ack),
                        'postmutation_audit_sha256': sha(post_raw), 'WREN_delta': 1,
                        'erase_delta': int(op == 0xFC7B), 'program_delta': int(op == 0xFC7D),
                        'synthetic_ACK': False, 'executed_mutation_repeated': False})
    return results


def inspect_finish_recoveries(journal, trace, candidate, recovery):
    """Verify one real FINISH after an unchanged complete-sector audit."""
    faults = [i for i, row in enumerate(trace) if row['state'] == 'error' and row['cdb'].startswith('fc80')]
    if recovery is None or recovery['summary'].get('version') not in (5, 6):
        require(not faults, 'FINISH error requires v5 evidence')
        return []
    groups = validate_v4_policy(recovery)
    finishes = [g for g in groups if g[0]['event'] == 'unexecuted_finish_recovery_begin']
    require(len(finishes) == len(faults) == recovery['summary']['finish_request_reissues'],
            'FINISH faults/witnesses/reissues differ')
    names = ['unexecuted_finish_recovery_' + name for name in ('begin', 'close_intent', 'reopen_intent')]
    names += ['readonly_recovery_identity_intent', 'readonly_recovery_identity_reply']
    names += ['unexecuted_finish_recovery_' + name for name in ('audit_intent', 'audit_reply', 'reissue_intent', 'reissue_reply')]
    identity_raw = b'\xfc\x78HYW1\1\1' + struct.pack('>II', recovery['slot'], 32768)
    results, keys = [], set()
    for fault_index, group in zip(faults, finishes):
        require([x['event'] for x in group] == names, 'FINISH recovery event order differs')
        begin, identity, fresh_event, reissue, reply = (group[i] for i in (0, 4, 6, 7, 8))
        cdb = bytes.fromhex(trace[fault_index]['cdb'])
        require(len(cdb) == 16 and cdb[:2] == b'\xfc\x80' and cdb[14:] == b'\xff\xff',
                'FINISH CDB framing differs')
        token, sequence, sector = struct.unpack_from('>III', cdb, 2)
        require(sector in range(APP_START, APP_END, 4096), 'FINISH sector out of bounds')
        target = candidate[sector-APP_START:sector-APP_START+4096]
        page_address = page_order(sector)[-1]
        page = candidate[page_address-APP_START:page_address-APP_START+256]
        prior_raw, fresh_raw = bytes.fromhex(begin['prior_audit_hex']), bytes.fromhex(fresh_event['raw_hex'])
        old = validate_audit_record(prior_raw, base=recovery['slot'], build_tag=recovery['build_tag'],
                                    expected_mutations_enabled=True)
        expected = begin['expected_state']
        require(fresh_raw == prior_raw and fresh_event['sha256'] == sha(prior_raw),
                'FINISH fresh audit changed; reissue was forbidden')
        require(old['error'] == 0 and old['phase'] == 3 and old['page_bitmap'] == 65535
                and old['staged'] == old['echoed'] == 0 and old['raw_receive_return'] == 260
                and old['rx_guards_ok'] == old['stack_guards_ok'] == 1 and old['stack_observed_bytes'] > 0
                and old['jedec'] == 0xEB6014 and not old['sr1'] & 0x7F and not old['sr2'] & 0x40
                and old['sequence'] == 34 and sequence == expected['sequence'] == 35
                and old['token'] == token and token > 0 and old['sector'] == sector and old['page'] == page_address
                and old['target_crc32'] == crc(target) and old['page_crc32'] == old['last_crc32'] == crc(page)
                and all(old.get(name) == value for name, value in expected.items() if name != 'sequence'),
                'FINISH prior audit is not a complete candidate sector before sequence35')
        material = json.dumps({'opcode': 0xFC80, 'cdb': cdb.hex(), 'length': 16,
                               'expected': expected, 'prior_record': prior_raw.hex()},
                              sort_keys=True, separators=(',', ':')).encode()
        require(begin['witness_sha256'] == sha(material) and begin['witness_sha256'] not in keys,
                'FINISH witness hash differs or repeats')
        keys.add(begin['witness_sha256'])
        require(begin['cdb'] == reissue['cdb'] == cdb.hex() and begin['read_length'] == reissue['read_length'] == 16
                and begin['win32_error'] == 31 and begin['any_audit_change_forbids_reissue'] is True
                and begin['synthetic_ACK'] is reissue['synthetic_ACK'] is reply['synthetic_ACK'] is False
                and begin['NOR_mutation'] is False and reissue['no_WREN_erase_program'] is True
                and begin['candidate_sector_sha256'] == reissue['candidate_sector_sha256'] == sha(target)
                and begin['candidate_last_page_sha256'] == sha(page)
                and reissue['raw_audit_identical'] is True and reissue['sequence_unconsumed'] is True
                and (reissue['sequence_before'], reissue['requested_sequence']) == (34, 35)
                and bytes.fromhex(identity['raw_hex']) == identity_raw
                and reply['subsequent_installer_status_audit_and_sector_readback_required'] is True,
                'FINISH nonexecution/identity/sector evidence differs')
        ack = b'\xfc\x80\0\5' + struct.pack('>III', 0, 35, crc(target))
        require(bytes.fromhex(reply['raw_hex']) == ack and reply['sha256'] == sha(ack),
                'FINISH recovery did not receive the correct real ACK')
        require(fault_index >= 2 and trace[fault_index-2]['state'] == 'after'
                and trace[fault_index-2]['cdb'] == 'fd88'+'ff'*14
                and bytes.fromhex(trace[fault_index-2]['response_hex']) == prior_raw,
                'FINISH lacks immediately preceding target audit')
        following = trace[fault_index+1:fault_index+7]
        require(len(following) == 6 and [x['state'] for x in following] == ['before', 'after']*3
                and [x['cdb'] for x in following[::2]] == ['fc78'+'ff'*14, 'fd88'+'ff'*14, cdb.hex()]
                and bytes.fromhex(following[1]['response_hex']) == identity_raw
                and bytes.fromhex(following[3]['response_hex']) == prior_raw
                and bytes.fromhex(following[5]['response_hex']) == ack
                and following[5]['response_bytes'] == 16 and following[5]['response_sha256'] == sha(ack),
                'FINISH transport proof is not identity/audit/one actual reissue')
        intents = [i for i, x in enumerate(journal) if x['event'] == 'command_intent' and x['cdb_hex'] == cdb.hex()]
        require(len(intents) == 1, 'FINISH command intent repeated')
        index = intents[0]
        earlier = journal[:index]
        audits = [x for x in earlier if x['event'] == 'audit_raw']
        pages = [x for x in earlier if x['event'] == 'page_program_verified' and sector <= x['address'] < sector+4096]
        require(audits and bytes.fromhex(audits[-1]['record_hex']) == prior_raw
                and [x['address'] for x in pages] == page_order(sector)
                and all(x['sha256'] == sha(candidate[x['address']-APP_START:x['address']-APP_START+256]) for x in pages),
                'FINISH lacks all sixteen candidate page readbacks before its intent')
        require(journal[index+1]['event'] == 'command_reply' and journal[index+1]['opcode'] == 'fc80'
                and journal[index+1]['bytes'] == 16 and journal[index+1]['sha256'] == sha(ack),
                'installer FINISH reply differs from real target ACK')
        later = journal[index+2:]
        first_audit = next((i for i, x in enumerate(later) if x['event'] == 'audit_raw'), None)
        require(first_audit is not None and all(int(x.get('opcode', '0'), 16) not in STATEFUL for x in later[:first_audit]),
                'next stateful command preceded FINISH audit')
        post_event = later[first_audit]; post_raw = bytes.fromhex(post_event['record_hex'])
        require(post_event['sha256'] == sha(post_raw), 'post-FINISH audit hash differs')
        post = validate_audit_record(post_raw, base=recovery['slot'], build_tag=recovery['build_tag'], expected_mutations_enabled=True)
        changes = {'phase': 5, 'token': 0, 'sequence': 35, 'last_crc32': crc(target), 'read_bytes': old['read_bytes']+4096}
        for name, value in old.items():
            if name not in ('sr1', 'sr2', 'stack_observed_bytes', 'record_sha256'):
                require(post[name] == changes.get(name, value), 'post-FINISH audit differs: '+name)
        require(not post['sr1'] & 0x7F and not post['sr2'] & 0x40 and post['stack_observed_bytes'] > 0,
                'post-FINISH status/stack invalid')
        wire = trace[fault_index+7:]
        boundary = next((i for i, x in enumerate(wire) if int(x['cdb'][:4], 16) in STATEFUL), len(wire))
        require(any(x['state'] == 'after' and x['cdb'] == 'fd88'+'ff'*14
                    and bytes.fromhex(x['response_hex']) == post_raw for x in wire[:boundary]),
                'post-FINISH audit was not received from target')
        require(later[first_audit+1]['event'] == 'audit_verified'
                and (later[first_audit+1]['wren'], later[first_audit+1]['erase'], later[first_audit+1]['program'])
                    == (old['wren_attempts'], old['erase_attempts'], old['program_attempts']),
                'original core did not confirm unchanged mutation counters after FINISH')
        results.append({'sector': sector, 'sequence_before': 34, 'sequence_after': 35,
                        'prior_and_fresh_audit_sha256': sha(prior_raw), 'actual_ACK_sha256': sha(ack),
                        'postfinish_audit_sha256': sha(post_raw), 'WREN_delta': 0, 'erase_delta': 0,
                        'program_delta': 0, 'synthetic_ACK': False, 'executed_FINISH_repeated': False})
    return results


def inspect_final_nor_read(trace, observed, recovery):
    """Replay final HYRN reads, including real counter/status reconciliation.

    All2048 logical chunks must have one received reply matching the saved
    full NOR. A lost reply can increase the physical counter, but cannot
    replace data, omit a block, hide an extra command or synthesize status.
    """
    require(type(observed) is bytes and len(observed) == CAPACITY, 'final complete immutable NOR required')
    require(recovery is not None and recovery.get('source_pinned') is True,
            'final NOR recovery helper source pin required')
    summary, events = recovery['summary'], recovery['events']
    require(summary['failed'] is False and summary['closed'] is True
            and 0 <= summary['recovery_attempts'] <= summary['max_recoveries'] <= 8
            and summary['mutation_retries_allowed'] is False and summary['lifecycle_retries_allowed'] is False
            and summary['status_replies_synthesized'] is False, 'NOR recovery policy/budget/cleanup differs')
    require(recovery['slot'] == 0x1C28000 and events and events[0]['event'] == 'nor_reader_bound'
            and events[0]['counter'] == 0 and events[0]['transport_assigned'] is True,
            'final reader must bind slotB at counter0')
    require(all(x['slot'] == recovery['slot'] and x['event'] != 'nor_recovery_terminal' for x in events),
            'NOR recovery log has wrong slot or terminal error')
    groups = []
    for row in events[1:]:
        if row['event'] == 'nor_recovery_begin': groups.append([])
        require(groups, 'NOR recovery event has no begin witness')
        groups[-1].append(row)
    require(len(groups) == summary['recovery_attempts'], 'NOR recovery event count differs')
    selected = []
    require(len(trace) % 2 == 0, 'unpaired final NOR transport trace')
    for before, after in zip(trace[::2], trace[1::2]):
        require(before['state'] == 'before' and after['state'] in ('after', 'error')
                and before['cdb'] == after['cdb'] and before['stage'] == after['stage'],
                'final NOR trace pairing differs')
        if before['stage'] in NOR_READ_STAGES:
            selected.append((before, after))
    first = next((i for i, pair in enumerate(selected) if pair[0]['cdb'].startswith('fd71')), None)
    require(first is not None and first >= 3, 'final NOR initialization/read prefix missing')
    identity = b'\xfc\x70HYRN\1\3' + struct.pack('>II', recovery['slot'], 32768)
    cdb_query = lambda op: op.to_bytes(2, 'big').hex() + 'ff' * 14

    def exchange(pair, command, length):
        before, after = pair
        require(before['cdb'] == command and before.get('out_bytes') == 0 and before.get('in_bytes') == length,
                'final NOR command/order/direction/length differs')
        if after['state'] == 'error':
            require(after['native_transfer']['win32_error'] == 31, 'NOR error is not submitted Win31')
            return None
        require(after['response_bytes'] == length, 'NOR reply extent differs')
        if 'response_hex' in after:
            raw = bytes.fromhex(after['response_hex'])
            require(len(raw) == length and sha(raw) == after['response_sha256'], 'NOR reply raw/hash differs')
            return raw
        require(length == 512, 'short NOR reply raw bytes missing')
        return after['response_sha256']

    raw_identity = exchange(selected[first-3], cdb_query(0xFC70), 16)
    raw_init = exchange(selected[first-2], cdb_query(0xFC72), 16)
    initial = exchange(selected[first-1], cdb_query(0xFC73), 16)
    require(raw_identity == identity and raw_init == b'\xfc\x72\0\1\xeb\x60\x14\x0f'
            + struct.pack('>II', CAPACITY, 0), 'final reader identity/JEDEC initialization differs')
    require(type(initial) is bytes and initial[:4] == b'\xfc\x73\0\1' and initial[12:] == bytes(4)
            and bytes.fromhex(events[0]['status_hex']) == initial, 'final reader initial status differs')
    clocks = initial[4:12]

    def status(raw, counts):
        require(type(raw) is bytes and len(raw) == 16 and raw[:4] == b'\xfc\x73\0\1'
                and raw[4:12] == clocks and int.from_bytes(raw[12:], 'big') in counts,
                'NOR sticky error, clock snapshot or physical counter differs')
        return int.from_bytes(raw[12:], 'big')

    wire, position, group_index = selected[first:], 0, 0
    physical, lost_bytes, read_reissues, status_reconciliations = 0, 0, 0, 0
    proofs, used = [], set()

    def next_pair(command, length):
        nonlocal position
        require(position < len(wire), 'final NOR read/status missing')
        value = exchange(wire[position], command, length); position += 1
        return value

    def reconcile(command, length, base, pending):
        nonlocal group_index
        require(group_index < len(groups), 'NOR fault lacks recovery witness')
        group = groups[group_index]; group_index += 1
        names = ['nor_recovery_begin', 'nor_recovery_close_intent', 'nor_recovery_reopen_intent',
                 'nor_recovery_identity', 'nor_recovery_status']
        names += (['nor_read_reissue_intent', 'nor_read_reissue_reply'] if pending is None
                  else ['nor_status_return_real_reply'])
        require([x['event'] for x in group] == names, 'NOR recovery event order differs')
        begin = group[0]
        require(begin['cdb'] == command and begin['read_length'] == length
                and begin['base_counter'] == base and begin['pending_read'] == pending
                and begin['win32_error'] == 31, 'NOR recovery does not describe the pending logical block')
        key = command, base, json.dumps(pending, sort_keys=True)
        require(key not in used, 'same NOR command/counter recovered twice'); used.add(key)
        got_identity = next_pair(cdb_query(0xFC70), 16)
        fresh = next_pair(cdb_query(0xFC73), 16)
        require(got_identity == identity and bytes.fromhex(group[3]['raw_hex']) == identity
                and type(fresh) is bytes and bytes.fromhex(group[4]['raw_hex']) == fresh
                and group[4]['sha256'] == sha(fresh), 'NOR recovery needs real identity and status replies')
        return group, fresh

    for address in range(0, CAPACITY, 512):
        command = (b'\xfd\x71' + struct.pack('>IH', address, 512) + b'\xff' * 8).hex()
        chunk_hash = sha(observed[address:address+512]); base = physical
        data_hash = next_pair(command, 512)
        if data_hash is None:
            group, fresh = reconcile(command, 512, base, None)
            physical = status(fresh, (base, base+512)); lost = physical-base
            intent, reply = group[5:]
            require(intent['cdb'] == command and intent['read_length'] == 512
                    and intent['physical_counter_before_reissue'] == physical and intent['missed_read_bytes'] == lost
                    and intent['host_counter_reconciled_to_real_target'] is True and intent['no_NOR_mutation'] is True,
                    'NOR read retry does not reconcile its actual physical counter')
            data_hash = next_pair(command, 512)
            require(reply['bytes'] == 512 and reply['sha256'] == chunk_hash
                    and reply['following_core_status_still_required'] is True, 'NOR reissued block proof differs')
            lost_bytes += lost; read_reissues += 1
            proofs.append({'opcode': 'fd71', 'address': address, 'counter_before': base,
                           'counter_before_reissue': physical, 'lost_read_bytes': lost,
                           'received_chunk_sha256': chunk_hash})
        require(data_hash is not None and (sha(data_hash) if isinstance(data_hash, bytes) else data_hash) == chunk_hash,
                'actual NOR chunk reply differs from retained complete dump')
        read_base = physical; physical += 512
        raw = next_pair(cdb_query(0xFC73), 16)
        if raw is None:
            pending = {'cdb': command, 'length': 512, 'sha256': chunk_hash, 'base': read_base}
            group, raw = reconcile(cdb_query(0xFC73), 16, read_base, pending)
            final = group[5]
            require(bytes.fromhex(final['raw_hex']) == raw and final['counter'] == physical
                    and final['host_counter_not_modified'] is True and final['status_reply_synthesized'] is False,
                    'NOR status recovery did not return the real target reply')
            status_reconciliations += 1
            proofs.append({'opcode': 'fc73', 'address': address, 'physical_counter': physical,
                           'real_status_sha256': sha(raw)})
        status(raw, (physical,))
    require(position == len(wire) and group_index == len(groups), 'extra NOR command/recovery or incomplete read')
    require((read_reissues, status_reconciliations, lost_bytes) ==
            (summary['read_reissues'], summary['status_reconciliations'], summary['lost_read_bytes'])
            and read_reissues+status_reconciliations == summary['recovery_attempts']
            and recovery['target_read_counter'] == physical == CAPACITY+lost_bytes
            and physical <= CAPACITY+8*512, 'final NOR physical counter or recovery accounting differs')
    return {'logical_bytes': CAPACITY, 'logical_chunks': CAPACITY//512, 'full_NOR_sha256': sha(observed),
            'physical_read_counter': physical, 'lost_read_bytes': lost_bytes,
            'verified_read_recoveries': proofs, 'every_chunk_matches_final_dump': True,
            'status_replies_synthesized': False, 'NOR_mutations_performed_by_reader': False}


def inspect_history(journal, trace, preimage, candidate, order, *, recovery=None,
                    nor_recovery=None, observed_nor=None):
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
    nor_proof = inspect_final_nor_read(trace, observed_nor, nor_recovery) if nor_recovery is not None else None
    observed, errors = [], []
    for before, after in zip(trace[::2], trace[1::2]):
        require(before['state'] == 'before' and after['state'] in ('after', 'error')
                and before['cdb'] == after['cdb'] and before['stage'] == after['stage'], 'trace command pairing differs')
        op = int(before['cdb'][:4], 16)
        if after['state'] == 'error':
            require((op in (0xFD7F, 0xFC7E, 0xFD88, 0xFD87) or
                     op in MUTATIONS and recovery is not None and recovery['summary'].get('version') in (4, 5, 6) or
                     op == 0xFC80 and recovery is not None and recovery['summary'].get('version') in (5, 6) or
                     op in (0xFD71, 0xFC73) and before['stage'] in NOR_READ_STAGES and nor_proof is not None)
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
    echo_proofs = inspect_echo_recoveries(journal, trace, candidate, recovery)
    mutation_proofs = inspect_mutation_recoveries(journal, trace, candidate, recovery)
    finish_proofs = inspect_finish_recoveries(journal, trace, candidate, recovery)
    return {'erase_commands': len(order), 'program_commands': len(pages),
            'expected_WREN_count': len(order) + len(pages), 'program_order': pages,
            'header_sector_last': APP_START not in order or order[-1] == APP_START,
            'header_page_last': APP_START not in order or pages[-1] == APP_START,
            'read_query_errors': sum(int(x['cdb'][:4], 16) in WRITER_RECOVERABLE-MUTATIONS-{0xFC80} for x in errors),
            'finish_request_errors': sum(x['cdb'].startswith('fc80') for x in errors),
            'NOR_read_errors': sum(int(x['cdb'][:4], 16) in (0xFD71, 0xFC73) for x in errors),
            'mutation_request_errors': sum(int(x['cdb'][:4], 16) in MUTATIONS for x in errors),
            'stateful_transport_commands': len(observed),
            'verified_RAM_echo_recoveries': echo_proofs,
            'verified_unexecuted_mutation_recoveries': mutation_proofs,
            'verified_unexecuted_finish_recoveries': finish_proofs,
            'final_NOR_read': nor_proof,
            'automatic_mutation_retries_observed': bool(mutation_proofs),
            'mutation_reissue_scope': 'byte-identical prior raw target audit; one real ACK and one core-validated mutation',
            'completed_NOR_mutations_repeated': False, 'synthetic_mutation_ACK': False}


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
    recovery_path = Path(prefix + '-read-recovery.jsonl')
    recovery = None
    if run.get('read_recovery_final', {}).get('version') in (3, 4, 5, 6):
        recovery = {'summary': run['read_recovery_final'], 'policy': run['read_recovery_policy'],
                    'events': [json.loads(x) for x in recovery_path.read_text().splitlines()] if recovery_path.exists() else [],
                    'slot': run['installation']['slot'], 'build_tag': run['installation']['build_tag'],
                    'v3_source_pinned': 'tools/recover_mini_read_v3.py' in run['source_pins'],
                    'v4_source_pinned': 'tools/recover_mini_read_v4.py' in run['source_pins'],
                    'v5_source_pinned': 'tools/recover_mini_read_v5.py' in run['source_pins'],
                    'v6_source_pinned': 'tools/recover_mini_read_v6.py' in run['source_pins']}
    nor_recovery_path = Path(prefix + '-nor-read-recovery.jsonl')
    nor_recovery = None
    if 'full_after_read_recovery' in run:
        require(nor_recovery_path.exists(), 'final NOR recovery log missing')
        nor_recovery = {'summary': run['full_after_read_recovery'],
                        'events': [json.loads(x) for x in nor_recovery_path.read_text().splitlines()],
                        'slot': 0x1C28000, 'target_read_counter': run['full_after_target_read_counter'],
                        'source_pinned': 'tools/mini_nor_read_recovery.py' in run['source_pins']}
    history = inspect_history(journal, trace, before, candidate, order, recovery=recovery,
                              nor_recovery=nor_recovery, observed_nor=after)
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
    if recovery_path.exists(): inputs += (recovery_path,)
    if nor_recovery_path.exists(): inputs += (nor_recovery_path,)
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
