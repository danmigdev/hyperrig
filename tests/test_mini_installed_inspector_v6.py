"""Verify bounded v6 history with more than eight distinct real-client retries."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import inspect_mini_installed as inspector
from tools.recover_mini_read_v6 import BoundedCommandRecoveryTransport
from tests import test_mini_installed_inspector_v4 as base


def evidence(faults):
    replacement = SimpleNamespace(AuditedCommandRecoveryTransport=BoundedCommandRecoveryTransport)
    with patch.object(base, 'recovery_v4', replacement):
        result = base.recovered_evidence(faults)
    context = result[-1]
    context.update(v5_source_pinned=True, v6_source_pinned=True)
    context['policy'].update(FINISH_reissue_requires_exact_prior_audit_and_complete_candidate_sector=True,
                            command_witness_policy_unchanged_from_v5=True, max_reopens=32)
    return result


class V6InstalledInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = evidence([(0xFC7D, address) for sector in (0x5000, 0x4000)
                             for address in inspector.page_order(sector)])
        cls.mixed = evidence([(0xFC7D, 0x5000), (0xFD87, 0x5100), (0xFC80, 0x5F00)])

    def test_thirty_two_distinct_unexecuted_requests_preserve_exact_mutations(self):
        result = base.verify(self.full)
        self.assertEqual(len(result['verified_unexecuted_mutation_recoveries']), 32)
        self.assertEqual(result['expected_WREN_count'], 34)
        self.assertEqual(result['program_commands'], 32)
        self.assertFalse(result['completed_NOR_mutations_repeated'])

    def test_mixed_inherited_echo_program_finish_proofs(self):
        result = base.verify(self.mixed)
        for name in ('verified_RAM_echo_recoveries', 'verified_unexecuted_mutation_recoveries',
                     'verified_unexecuted_finish_recoveries'):
            self.assertEqual(len(result[name]), 1)

    def test_version_five_still_rejects_more_than_eight(self):
        case = copy.deepcopy(self.full); case[-1]['summary']['version'] = 5
        with self.assertRaises(ValueError): base.verify(case)

    def test_more_than_thirty_two_still_rejected(self):
        case = copy.deepcopy(self.full)
        case[-1]['summary']['max_recoveries'] = case[-1]['policy']['max_reopens'] = 33
        with self.assertRaises(ValueError): base.verify(case)

    def test_v6_source_pin_required(self):
        case = copy.deepcopy(self.full); case[-1]['v6_source_pinned'] = False
        with self.assertRaises(ValueError): base.verify(case)

    def test_inherited_v5_source_pin_required(self):
        case = copy.deepcopy(self.full); case[-1]['v5_source_pinned'] = False
        with self.assertRaises(ValueError): base.verify(case)

    def test_session_limit_must_match_explicit_run_policy(self):
        case = copy.deepcopy(self.full); case[-1]['policy']['max_reopens'] = 8
        with self.assertRaises(ValueError): base.verify(case)

    def test_unchanged_command_witness_requirement_is_mandatory(self):
        for location in ('policy', 'summary'):
            case = copy.deepcopy(self.full); case[-1][location]['command_witness_policy_unchanged_from_v5'] = False
            with self.subTest(location=location), self.assertRaises(ValueError): base.verify(case)

    def test_larger_budget_never_accepts_changed_target_audit(self):
        case = copy.deepcopy(self.full)
        row = next(x for x in case[-1]['events'] if x['event'] == 'unexecuted_mutation_recovery_audit_reply')
        raw = bytearray.fromhex(row['raw_hex']); raw[28] += 1
        row.update(raw_hex=raw.hex(), sha256=inspector.sha(raw))
        with self.assertRaises(ValueError): base.verify(case)


if __name__ == '__main__': unittest.main()
