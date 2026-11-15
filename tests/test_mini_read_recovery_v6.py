"""Finite writer budget32; frozen v5 behavior exercised through fake NOR."""
import unittest
from unittest.mock import patch

from tools import install_mini_app as installer
from tools import recover_mini_read_v5 as v5
from tools import recover_mini_read_v6 as recovery
from tools import mini_nor_read_recovery as nor_recovery
from tools.probe_mini_recovery import RomCommandError
from tools.probe_mini_app_writer import simple_cdb
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_read_recovery import Handle, failure
from tests import test_mini_read_recovery_v5 as previous
from tests.test_mini_nor_read_recovery import Handle as NorHandle
from tests.test_mini_recovery import FakeNor


class BudgetRecoveryTests(previous.FinishRecoveryTests):
    def live(self, *, preflight=False, new_configure=None, budget=8):
        # Keep inherited v5 tests' explicit eight-recovery expectations. New
        # tests below also exercise the higher bound with real inherited paths.
        device = FakeOperational(fixture()); old = Handle(device)
        handles, events, journal = [old], [], []
        def reopen():
            new = Handle(device); handles.append(new)
            if new_configure: new_configure(new)
            return new
        wrapper = recovery.BoundedCommandRecoveryTransport(old, log=events.append,
                    reopen_factory=reopen, max_recoveries=budget)
        session = installer.MiniAppInstallerSession(wrapper, fixture(), journal=journal.append, known_free_slot=True)
        wrapper.bind_session(session)
        with patch('time.sleep'): session.upload_and_start(IMAGE, expected_sha256=installer.sha(IMAGE))
        session.initialize_spi()
        if preflight: session.verify_complete_preimage()
        self.addCleanup(wrapper.close)
        return device, old, handles, wrapper, session, events

    def test_unexecuted_finish_first_or_header_sector_uses_real_ACK_and_normal_readback(self):
        # This v5 test's version assertion changes to6, while FINISH behavior
        # is exercised at the new bound32 on both sector/page orderings.
        for sector in (0x5000, 0x4000):
            with self.subTest(sector=hex(sector)):
                device, old, handles, wrapper, session, events = self.live(preflight=True, budget=32)
                old.fail_before = lambda op: failure() if op == 0xFC80 and device.fields[32] == sector else None
                result = session.install_application()
                self.assertTrue(result['application_verified'])
                self.assertEqual((wrapper.recovery_attempts, wrapper.finish_request_reissues), (1, 1))
                self.assertEqual(device.counts[0xFC80], 2)
                self.assertEqual([r[0] for r in handles[1].calls[:5]], [0xFC78, 0xFD88, 0xFC80, 0xFD88, 0xFD7F])
                reply = next(x for x in events if x['event'] == 'unexecuted_finish_recovery_reissue_reply')
                self.assertFalse(reply['synthetic_ACK'])
                self.assertEqual(session.verified_sectors, [0x5000, 0x4000])
                self.assertEqual((wrapper.summary()['version'], wrapper.summary()['max_recoveries']), (6, 32))
                self.assertEqual((len(device.erase_addresses), len(set(device.program_addresses))), (2, 32))

    def test_constructor_accepts_exact_integer1_to32_and_defaults32(self):
        for limit in (1, 8, 9, 31, 32):
            old = Handle(FakeOperational(fixture()))
            wrapper = recovery.BoundedCommandRecoveryTransport(old, log=lambda _: None,
                        reopen_factory=lambda: self.fail('unexpected reopen'), max_recoveries=limit)
            self.assertEqual(wrapper.max_recoveries, limit)
            self.assertEqual(wrapper.summary()['max_recoveries'], limit)
            self.assertTrue(wrapper.summary()['command_witness_policy_unchanged_from_v5'])
            self.assertEqual(wrapper.summary()['command_witness_policy_version'], 5)
            self.assertEqual(wrapper.summary()['separate_NOR_reader_budget_unchanged'], 8)
            self.assertFalse(old.calls)
            wrapper.close()
        wrapper = recovery.BoundedCommandRecoveryTransport(Handle(FakeOperational(fixture())),
                    log=lambda _: None, reopen_factory=lambda: self.fail('unexpected reopen'))
        self.assertEqual(wrapper.max_recoveries, 32)
        wrapper.close()
        for invalid in (0, -1, 33, 100, True, False, 8.0, '32', None):
            old = Handle(FakeOperational(fixture()))
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                recovery.BoundedCommandRecoveryTransport(old, log=lambda _: None,
                    reopen_factory=lambda: self.fail('unexpected reopen'), max_recoveries=invalid)
            self.assertFalse(old.calls)

    def test_parent_initialization_and_NOR_reader_bound_are_not_globally_changed(self):
        inherited = v5.FinishCommandRecoveryTransport(Handle(FakeOperational(fixture())),
                    log=lambda _: None, reopen_factory=lambda: self.fail('unexpected reopen'))
        self.assertEqual(inherited.max_recoveries, 8)
        inherited.close()
        with self.assertRaises(ValueError):
            v5.FinishCommandRecoveryTransport(Handle(FakeOperational(fixture())),
                log=lambda _: None, reopen_factory=lambda: None, max_recoveries=32)
        with self.assertRaises(ValueError):
            nor_recovery.NorReadRecoveryTransport(NorHandle(FakeNor()),
                log=lambda _: None, reopen_factory=lambda: None, max_recoveries=9)
        for name in ('exchange', '_witness', '_echo_witness', '_mutation_witness', '_finish_witness',
                     '_recover', '_recover_echo', '_recover_mutation', '_recover_finish', 'close'):
            self.assertIs(getattr(recovery.BoundedCommandRecoveryTransport, name),
                          getattr(v5.FinishCommandRecoveryTransport, name))

    def many_query_faults(self, *, count=32, by_phase=False):
        seen, phases = set(), {}
        session = None
        limits = {'initialized':12, 'installing':10, 'verifying_final':10}
        def configure(handle):
            def lose(op):
                if op != 0xFC7E: return None
                phase = session.phase
                key = phase, tuple(sorted(session.expected.items()))
                allowed = phases.get(phase, 0) < limits.get(phase, 0) if by_phase else len(seen) < count
                if allowed and key not in seen:
                    seen.add(key); phases[phase] = phases.get(phase, 0) + 1
                    return failure()
            handle.fail_before = lose
        device, old, handles, wrapper, session, events = self.live(new_configure=configure, budget=32)
        configure(old)
        return device, handles, wrapper, session, events, seen, phases

    def test32_distinct_recoveries_succeed_across_preimage_install_and_final_read(self):
        device, handles, wrapper, session, events, seen, phases = self.many_query_faults(by_phase=True)
        session.verify_complete_preimage(); result = session.install_application()
        self.assertTrue(result['application_verified'])
        self.assertEqual(phases, {'initialized':12, 'installing':10, 'verifying_final':10})
        self.assertEqual((len(seen), len(handles), wrapper.recovery_attempts, wrapper.query_reissues), (32, 33, 32, 32))
        self.assertEqual(len(wrapper._used_witnesses), 32)
        self.assertEqual(device.erase_addresses, [0x5000, 0x4000])
        self.assertEqual(len(set(device.program_addresses)), 32)
        self.assertEqual(device.counts[0xFC80], 2)
        self.assertFalse(session.failed or wrapper.failed or session.mutation_completion_unknown)
        self.assertEqual(sum(x['event'] == 'readonly_recovery_begin' for x in events), 32)

    def test33rd_distinct_failure_stops_before_another_reopen_or_reissue(self):
        device, handles, wrapper, session, _, seen, _ = self.many_query_faults(count=33)
        with self.assertRaises(RomCommandError): session.verify_complete_preimage()
        self.assertEqual((len(seen), wrapper.recovery_attempts, wrapper.query_reissues, len(handles)), (33, 32, 32, 33))
        self.assertTrue(session.failed and wrapper.failed)
        self.assertEqual(len(wrapper._used_witnesses), 32)
        self.assertFalse(device.erase_addresses or device.program_addresses)
        self.assertNotIn(0xFC7A, device.commands)

    def test_high_budget_does_not_allow_same_witness_twice(self):
        _, old, handles, wrapper, session, _ = self.live(preflight=True, budget=32)
        old.fail_before = lambda op: failure() if op == 0xFC7E else None
        session._status(0xFC7E, session._exchange(simple_cdb(0xFC7E), read_length=16))
        self.assertEqual(wrapper.recovery_attempts, 1)
        handles[-1].fail_before = lambda op: failure() if op == 0xFC7E else None
        with self.assertRaises(RomCommandError):
            session._exchange(simple_cdb(0xFC7E), read_length=16)
        self.assertEqual((wrapper.recovery_attempts, wrapper.query_reissues, len(handles)), (1, 1, 2))
        self.assertTrue(wrapper.failed)

    def test_high_budget_keeps_nested_recovery_terminal(self):
        for recovery_op in (0xFC78, 0xFD88, 0xFC7E):
            with self.subTest(recovery_op=recovery_op):
                def configure(handle):
                    handle.fail_before = lambda op: failure() if op == recovery_op else None
                _, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure, budget=32)
                old.fail_before = lambda op: failure() if op == 0xFC7E else None
                with self.assertRaises(RomCommandError):
                    session._exchange(simple_cdb(0xFC7E), read_length=16)
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (1, 2))
                self.assertTrue(wrapper.failed)

    def test_high_budget_does_not_replay_executed_PP_or_FINISH(self):
        for op in (0xFC7D, 0xFC80):
            with self.subTest(op=op):
                device, old, handles, wrapper, session, _ = self.live(preflight=True, budget=32)
                old.fail_after = lambda actual: failure() if actual == op else None
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(device.counts[op], 1)
                self.assertEqual((wrapper.recovery_attempts, wrapper.mutation_request_reissues, wrapper.finish_request_reissues), (1, 0, 0))
                self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
                self.assertEqual(session.mutation_completion_unknown, op == 0xFC7D)


if __name__ == '__main__': unittest.main()
