"""Independent v5 retained-log checks using fake NOR and real client logic."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import inspect_mini_installed as inspector
from tools.recover_mini_read_v5 import FinishCommandRecoveryTransport
from tests import test_mini_installed_inspector_v4 as base


def evidence(faults):
    replacement = SimpleNamespace(AuditedCommandRecoveryTransport=FinishCommandRecoveryTransport)
    with patch.object(base, 'recovery_v4', replacement):
        result = base.recovered_evidence(faults)
    result[-1]['v5_source_pinned'] = True
    result[-1]['policy']['FINISH_reissue_requires_exact_prior_audit_and_complete_candidate_sector'] = True
    return result


def event(case, name):
    return next(x for x in case[-1]['events'] if x['event'] == name)


class V5InstalledInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.both = evidence([(0xFC80, 0x5F00), (0xFC80, 0x4000)])
        cls.mixed = evidence([(0xFC7D, 0x5000), (0xFD87, 0x5100), (0xFC80, 0x5F00)])
        cls.clean = evidence([])

    def test_no_errors_v5_has_no_recovery_proofs(self):
        result = base.verify(self.clean)
        self.assertEqual(result['verified_unexecuted_finish_recoveries'], [])

    def test_normal_and_header_finish_each_have_real_ack_and_no_mutations(self):
        result = base.verify(self.both)
        proofs = result['verified_unexecuted_finish_recoveries']
        self.assertEqual([x['sector'] for x in proofs], [0x5000, 0x4000])
        self.assertTrue(all(x['WREN_delta'] == x['erase_delta'] == x['program_delta'] == 0 for x in proofs))
        self.assertEqual(result['finish_request_errors'], 2)
        self.assertEqual(result['expected_WREN_count'], 34)

    def test_mixed_v3_v4_v5_proofs_use_one_shared_budget(self):
        result = base.verify(self.mixed)
        self.assertEqual(len(result['verified_RAM_echo_recoveries']), 1)
        self.assertEqual(len(result['verified_unexecuted_mutation_recoveries']), 1)
        self.assertEqual(len(result['verified_unexecuted_finish_recoveries']), 1)

    def test_missing_v5_source_pin_rejected(self):
        case = copy.deepcopy(self.both); case[-1]['v5_source_pinned'] = False
        with self.assertRaises(ValueError): base.verify(case)

    def test_policy_without_nonexecution_requirement_rejected(self):
        case = copy.deepcopy(self.both)
        case[-1]['policy']['FINISH_reissue_requires_exact_prior_audit_and_complete_candidate_sector'] = False
        with self.assertRaises(ValueError): base.verify(case)

    def test_executed_finish_permission_rejected(self):
        case = copy.deepcopy(self.both); case[-1]['summary']['executed_or_ambiguous_FINISH_retry'] = True
        with self.assertRaises(ValueError): base.verify(case)

    def test_changed_fresh_audit_rejected_even_with_updated_hash(self):
        case = copy.deepcopy(self.both)
        row = event(case, 'unexecuted_finish_recovery_audit_reply')
        raw = bytearray.fromhex(row['raw_hex']); raw[28] += 1
        row.update(raw_hex=raw.hex(), sha256=inspector.sha(raw))
        with self.assertRaises(ValueError): base.verify(case)

    def test_sector_hash_different_from_candidate_rejected(self):
        case = copy.deepcopy(self.both)
        event(case, 'unexecuted_finish_recovery_begin')['candidate_sector_sha256'] = '0'*64
        with self.assertRaises(ValueError): base.verify(case)

    def test_synthetic_ack_claim_rejected(self):
        case = copy.deepcopy(self.both)
        event(case, 'unexecuted_finish_recovery_reissue_reply')['synthetic_ACK'] = True
        with self.assertRaises(ValueError): base.verify(case)

    def test_wrong_actual_ack_token_rejected(self):
        case = copy.deepcopy(self.both)
        row = event(case, 'unexecuted_finish_recovery_reissue_reply')
        raw = bytearray.fromhex(row['raw_hex']); raw[7] = 1
        row.update(raw_hex=raw.hex(), sha256=inspector.sha(raw))
        with self.assertRaises(ValueError): base.verify(case)

    def test_missing_transport_reissue_rejected(self):
        case = copy.deepcopy(self.both)
        trace = case[1]
        index = next(i for i, row in enumerate(trace) if row['state'] == 'error' and row['cdb'].startswith('fc80'))
        del trace[index+5:index+7]
        with self.assertRaises(ValueError): base.verify(case)

    def test_missing_last_page_readback_proof_rejected(self):
        case = copy.deepcopy(self.both)
        journal = case[0]
        index = next(i for i, row in enumerate(journal) if row['event'] == 'page_program_verified' and row['address'] == 0x5F00)
        del journal[index]
        with self.assertRaises(ValueError): base.verify(case)

    def test_postfinish_counter_change_rejected(self):
        case = copy.deepcopy(self.both)
        journal = case[0]
        finish = next(i for i, x in enumerate(journal) if x['event'] == 'command_intent' and x['opcode'] == 'fc80')
        row = next(x for x in journal[finish:] if x['event'] == 'audit_verified')
        row['wren'] += 1
        with self.assertRaises(ValueError): base.verify(case)

    def test_excess_recovery_budget_rejected(self):
        case = copy.deepcopy(self.both); case[-1]['summary']['max_recoveries'] = 9
        with self.assertRaises(ValueError): base.verify(case)


if __name__ == '__main__': unittest.main()
