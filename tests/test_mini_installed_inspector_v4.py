"""Independent retained-log verification using a fake NOR; no device I/O."""
import copy
import struct
import unittest
from unittest.mock import patch

from tools import inspect_mini_installed as inspector
from tools import install_mini_app as installer
from tools import recover_mini_read_v4 as recovery_v4
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_read_recovery import Handle, failure
from tests.test_mini_app_writer_protocol import changed_record


def recovered_evidence(faults):
    plan = fixture(); device = FakeOperational(plan)
    trace, events, journal, remaining = [], [], [], list(faults)
    def logged_handle():
        handle = Handle(device); original = handle.exchange
        def before(op):
            if not remaining:
                return None
            expected_op, address = remaining[0]
            current = device.fields.get(32 if op == 0xFC7B else 36)
            if (op, current) == (expected_op, address):
                remaining.pop(0)
                return failure()
        handle.fail_before = before
        def exchange(cdb, data_out=None, read_length=0):
            row = {'state': 'before', 'stage': 'writer', 'cdb': cdb.hex()}
            trace.append(row.copy())
            try:
                raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                row.update(state='error', native_transfer={'win32_error': error.errno})
                trace.append(row); raise
            row.update(state='after', response_bytes=len(raw), response_sha256=inspector.sha(raw))
            if len(raw) <= 128:
                row['response_hex'] = raw.hex()
            trace.append(row)
            return raw
        handle.exchange = exchange
        return handle
    wrapper = recovery_v4.AuditedCommandRecoveryTransport(logged_handle(), log=events.append,
                                                         reopen_factory=logged_handle)
    session = installer.MiniAppInstallerSession(wrapper, plan, journal=journal.append, known_free_slot=True)
    wrapper.bind_session(session)
    try:
        with patch('time.sleep'):
            session.upload_and_start(IMAGE, expected_sha256=installer.sha(IMAGE))
        session.initialize_spi(); session.verify_complete_preimage(); session.install_application()
        assert not remaining
        context = {'summary': wrapper.summary(), 'events': events, 'slot': plan.slot,
                   'build_tag': plan.build_tag, 'v3_source_pinned': True, 'v4_source_pinned': True,
                   'policy': {'enabled': True, 'only_Windows_error': 31,
                       'FD87_requires_same_staged_page_and_exact_audit_except_echoed_and_record_CRC': True,
                       'FD87_reissue_requires_exact_candidate_page_bytes': True,
                       'mutation_retries_allowed': True,
                       'mutation_request_reissue_requires_exact_prior_audit': True,
                       'one_recovery_per_command_and_expected_state': True,
                       'executed_mutation_retries_allowed': False, 'OUT_retries_allowed': False,
                       'jump_or_reset_retries_allowed': False, 'backend_fallback_allowed': False}}
        return journal, trace, device.original, plan.candidate, list(plan.sector_order), context
    finally:
        wrapper.close()


def verify(case):
    journal, trace, before, candidate, order, context = case
    return inspector.inspect_history(journal, trace, before, candidate, order, recovery=context)


class V4InstalledInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mixed = recovered_evidence([(0xFC7B, 0x5000), (0xFC7D, 0x5000),
                                       (0xFD87, 0x5100), (0xFC7D, 0x5400), (0xFC7D, 0x4000)])
        cls.program = recovered_evidence([(0xFC7D, 0x5000)])
        cls.no_errors = recovered_evidence([])

    def test_mixed_echo_erase_first_middle_and_header_program_preserve_exact_counts(self):
        result = verify(self.mixed)
        self.assertEqual(len(result['verified_RAM_echo_recoveries']), 1)
        proofs = result['verified_unexecuted_mutation_recoveries']
        self.assertEqual([(p['opcode'], p['address']) for p in proofs],
                         [('fc7b', 0x5000), ('fc7d', 0x5000), ('fc7d', 0x5400), ('fc7d', 0x4000)])
        self.assertEqual((result['erase_commands'], result['program_commands'], result['expected_WREN_count']),
                         (2, 32, 34))
        self.assertEqual((result['read_query_errors'], result['mutation_request_errors']), (1, 4))
        self.assertTrue(result['automatic_mutation_retries_observed'])
        self.assertFalse(result['completed_NOR_mutations_repeated'] or result['synthetic_mutation_ACK'])
        self.assertTrue(result['header_sector_last'] and result['header_page_last'])

    def test_v4_without_errors_remains_valid_and_claims_no_observed_retry(self):
        result = verify(self.no_errors)
        self.assertFalse(result['automatic_mutation_retries_observed'])
        self.assertEqual(result['verified_unexecuted_mutation_recoveries'], [])

    def test_first_program_after_erase_uses_last_read_CRC_and_known_page_CRC_separately(self):
        result = verify(self.program)
        begin = next(x for x in self.program[-1]['events'] if x['event'] == 'unexecuted_mutation_recovery_begin')
        expected = begin['expected_state']
        self.assertEqual(expected['last_crc32'], inspector.crc(b'\xff' * 512))
        self.assertNotEqual(expected['last_crc32'], expected['page_crc32'])
        self.assertEqual(result['verified_unexecuted_mutation_recoveries'][0]['program_delta'], 1)

    def test_policy_pins_counts_and_budget_are_required(self):
        for kind in ('no_context', 'v3', 'unpin4', 'unpin3', 'no_log', 'budget', 'retry_count',
                     'executed', 'synthetic', 'policy', 'OUT', 'jump', 'backend', 'reused_witness'):
            case = copy.deepcopy(self.program); context = case[-1]
            if kind == 'no_context': case = (*case[:-1], None)
            elif kind == 'v3': context['summary']['version'] = 3
            elif kind == 'unpin4': context['v4_source_pinned'] = False
            elif kind == 'unpin3': context['v3_source_pinned'] = False
            elif kind == 'no_log': context['events'] = []
            elif kind == 'budget': context['summary']['max_recoveries'] = 9
            elif kind == 'retry_count': context['summary']['mutation_request_reissues'] = 2
            elif kind == 'executed': context['summary']['completed_NOR_mutations_repeated'] = 1
            elif kind == 'synthetic': context['summary']['synthetic_mutation_ACK'] = True
            elif kind == 'policy': context['policy']['mutation_request_reissue_requires_exact_prior_audit'] = False
            elif kind == 'OUT': context['policy']['OUT_retries_allowed'] = True
            elif kind == 'jump': context['policy']['jump_or_reset_retries_allowed'] = True
            elif kind == 'backend': context['policy']['backend_fallback_allowed'] = True
            else: context['policy']['one_recovery_per_command_and_expected_state'] = False
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify(case)

    def test_all_v4_failures_share_one_bounded_recovery_count(self):
        case = copy.deepcopy(self.program)
        command = 'fc7e' + 'ff' * 14
        case[1].extend(({'state': 'before', 'stage': 'writer', 'cdb': command},
                        {'state': 'error', 'stage': 'writer', 'cdb': command,
                         'native_transfer': {'win32_error': 31}}))
        with self.assertRaisesRegex(ValueError, 'shared recovery count'):
            verify(case)

    def test_every_fresh_audit_word_change_forbids_mutation_reissue(self):
        for offset in range(4, 120, 4):
            case = copy.deepcopy(self.program)
            audit = next(x for x in case[-1]['events'] if x['event'] == 'unexecuted_mutation_recovery_audit_reply')
            raw = bytes.fromhex(audit['raw_hex']); value = struct.unpack_from('<I', raw, offset)[0]
            raw = changed_record(raw, offset, value ^ 1)
            audit.update(raw_hex=raw.hex(), sha256=inspector.sha(raw))
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                verify(case)

    def test_synthetic_ACK_or_wrong_cdb_identity_witness_or_page_rejected(self):
        for kind in ('synthetic', 'ack_missing', 'ack_wrong', 'identity', 'witness', 'page', 'sequence', 'address'):
            case = copy.deepcopy(self.program); events = case[-1]['events']
            begin, reissue, reply = events[0], events[-2], events[-1]
            if kind == 'synthetic': reply['synthetic_ACK'] = True
            elif kind == 'ack_missing': reply['raw_hex'] = ''
            elif kind == 'ack_wrong': reply['raw_hex'] = '00' * 16
            elif kind == 'identity': events[4]['raw_hex'] = '00' * 16
            elif kind == 'witness': begin['witness_sha256'] = '0' * 64
            elif kind == 'page': reissue['candidate_page_sha256'] = '0' * 64
            elif kind == 'sequence': reissue['requested_sequence'] += 1
            else: reissue['cdb'] = reissue['cdb'][:20] + '00005100' + 'ffff'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify(case)

    def test_missing_or_duplicate_actual_reissue_and_installer_intent_rejected(self):
        for kind in ('no_prior', 'no_fresh', 'no_ACK', 'duplicate_ACK', 'duplicate_intent', 'fake_journal_ACK'):
            case = copy.deepcopy(self.program); journal, trace = case[:2]
            fault = next(i for i, x in enumerate(trace) if x['state'] == 'error')
            cdb = trace[fault]['cdb']
            if kind == 'no_prior': trace[fault-2]['response_hex'] = '00' * 128
            elif kind == 'no_fresh': trace[fault+4]['response_hex'] = '00' * 128
            elif kind == 'no_ACK': del trace[fault+5:fault+7]
            elif kind == 'duplicate_ACK': trace[fault+7:fault+7] = copy.deepcopy(trace[fault+5:fault+7])
            else:
                index = next(i for i, x in enumerate(journal) if x['event'] == 'command_intent' and x['cdb_hex'] == cdb)
                if kind == 'duplicate_intent': journal[index:index] = copy.deepcopy(journal[index:index+2])
                else: journal[index+1]['sha256'] = '0' * 64
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify(case)

    def test_postmutation_core_audit_must_count_exactly_one_operation(self):
        changes = ((28, 2), (68, 99), (72, 99), (76, 99), (80, 0), (84, 0),
                   (96, 0), (100, 1), (104, 1), (108, 0), (112, 0))
        for offset, value in changes:
            case = copy.deepcopy(self.program); journal, trace = case[:2]
            cdb = next(x['cdb'] for x in trace if x['state'] == 'error')
            index = next(i for i, x in enumerate(journal) if x['event'] == 'command_intent' and x['cdb_hex'] == cdb)
            audit = next(x for x in journal[index+2:] if x['event'] == 'audit_raw')
            old = bytes.fromhex(audit['record_hex']); raw = changed_record(old, offset, value)
            audit.update(record_hex=raw.hex(), sha256=inspector.sha(raw))
            # Keep transport/journal hashes internally consistent so the
            # independent semantic delta, not merely a stale digest, rejects.
            fault = next(i for i, x in enumerate(trace) if x['state'] == 'error')
            actual = next(x for x in trace[fault+7:] if x['state'] == 'after' and x['cdb'].startswith('fd88'))
            actual.update(response_hex=raw.hex(), response_sha256=inspector.sha(raw))
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                verify(case)


if __name__ == '__main__':
    unittest.main()
