"""Real installer + bounded v2 recovery, with fake handles/NOR exclusively."""
import unittest
from unittest.mock import patch

from tools import recover_mini_read_v2 as recovery
from tools import install_mini_app as installer
from tools.probe_mini_app_writer import read_cdb, simple_cdb
from tools.probe_mini_recovery import RomCommandError
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_app_writer_protocol import changed_record
from tests.test_mini_read_recovery import Handle, failure


class ReconciledReadRecoveryTests(unittest.TestCase):
    def live(self, *, preflight=False, new_configure=None, budget=8):
        device = FakeOperational(fixture())
        old = Handle(device)
        handles, events, journal = [old], [], []

        def reopen():
            new = Handle(device)
            handles.append(new)
            if new_configure:
                new_configure(new)
            return new

        wrapper = recovery.ReadOnlyStateRecoveryTransport(old, log=events.append,
                    reopen_factory=reopen, max_recoveries=budget)
        session = installer.MiniAppInstallerSession(wrapper, fixture(), journal=journal.append, known_free_slot=True)
        wrapper.bind_session(session)
        with patch("time.sleep"):
            session.upload_and_start(IMAGE, expected_sha256=installer.sha(IMAGE))
        session.initialize_spi()
        if preflight:
            session.verify_complete_preimage()
        self.addCleanup(wrapper.close)
        return device, old, handles, wrapper, session, events

    def test_fc7e_after_successful_read_matches_current_expected_not_previous_record(self):
        device, old, handles, wrapper, session, events = self.live()
        before = session.last_record
        old.fail_before = lambda op: failure() if op == 0xFC7E else None
        raw = session._read(0x4000, 512, session.installation.preimage[:512])
        self.assertEqual(raw, session.installation.preimage[:512])
        self.assertEqual(device.fields[80], 512)
        self.assertEqual(wrapper.query_reissues, 1)
        self.assertEqual(wrapper.read_reissues, 0)
        self.assertNotEqual(before, session.last_record)
        self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88, 0xFC7E, 0xFD88])
        self.assertEqual(events[-2]["event"], "readonly_recovery_reissue_intent")

    def test_lost_fc7e_reply_is_safe_when_query_already_executed(self):
        device, old, _, wrapper, session, _ = self.live()
        old.fail_after = lambda op: failure() if op == 0xFC7E else None
        session._read(0x4000, 512, session.installation.preimage[:512])
        self.assertEqual(device.fields[80], 512)
        self.assertEqual(wrapper.query_reissues, 1)
        self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd88_returns_fresh_validated_audit_without_a_third_audit_exchange(self):
        device, old, handles, wrapper, session, _ = self.live()
        old.fail_before = lambda op: failure() if op == 0xFD88 else None
        session._read(0x4000, 512, session.installation.preimage[:512])
        self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
        self.assertEqual(wrapper.audit_reconciliations, 1)
        self.assertEqual(device.fields[80], session.expected["read_bytes"])

    def test_lost_fd88_reply_is_safe_when_audit_already_executed(self):
        _, old, _, wrapper, session, _ = self.live()
        old.fail_after = lambda op: failure() if op == 0xFD88 else None
        session._read(0x4000, 512, session.installation.preimage[:512])
        self.assertEqual(wrapper.audit_reconciliations, 1)

    def test_fc7e_after_acknowledged_stage_does_not_repeat_stage(self):
        device, old, _, wrapper, session, _ = self.live(preflight=True)
        old.fail_before = lambda op: failure() if op == 0xFC7E and device.staged else None
        session.install_application()
        self.assertEqual(device.counts[0xFB7C], 32)
        self.assertEqual(len(device.program_addresses), 32)
        self.assertEqual(wrapper.query_reissues, 1)
        self.assertTrue(session.image_verified)

    def test_audit_after_acknowledged_erase_or_program_reconciles_only_poll_delta(self):
        for kind in ("erase", "program"):
            with self.subTest(kind=kind):
                device, old, _, wrapper, session, events = self.live(preflight=True)
                def fail(op):
                    target = bool(device.erase_addresses) if kind == "erase" else bool(device.program_addresses)
                    return failure() if op == 0xFD88 and target else None
                old.fail_before = fail
                session.install_application()
                self.assertTrue(session.image_verified)
                self.assertFalse(session.mutation_completion_unknown)
                self.assertEqual(wrapper.audit_reconciliations, 1)
                self.assertEqual(device.erase_addresses, [0x5000, 0x4000])
                self.assertEqual(len(device.program_addresses), 32)
                matched = [e for e in events if e["event"] == "readonly_recovery_return_fresh_audit"]
                self.assertEqual(matched[0]["mutation_poll_delta"], 2)

    def test_unexecuted_fd7f_keeps_strict_exact_snapshot_rule(self):
        device, old, handles, wrapper, session, _ = self.live()
        old.fail_before = lambda op: failure() if op == 0xFD7F else None
        session._read(0x4000, 512, session.installation.preimage[:512])
        self.assertEqual(device.fields[80], 512)
        self.assertEqual([r[0] for r in handles[1].calls[:3]], [0xFC78, 0xFD88, 0xFD7F])
        self.assertEqual(wrapper.read_reissues, 1)

    def test_executed_fd7f_lost_reply_stops_without_reissue(self):
        device, old, handles, wrapper, session, _ = self.live()
        old.fail_after = lambda op: failure() if op == 0xFD7F else None
        with self.assertRaises(ValueError):
            session.verify_complete_preimage()
        self.assertEqual(device.fields[80], 512)
        self.assertEqual(wrapper.read_reissues, 0)
        self.assertNotIn(0xFD7F, [r[0] for r in handles[1].calls])
        self.assertTrue(wrapper.failed and session.failed)

    def test_multiple_different_state_witnesses_recover_with_total_bound(self):
        failed_counts = set()
        device = None
        def configure(handle):
            def fail(op):
                n = device.fields.get(80, 0)
                if op == 0xFC7E and n not in failed_counts:
                    failed_counts.add(n)
                    return failure()
            handle.fail_before = fail
        device, old, handles, wrapper, session, _ = self.live(new_configure=configure, budget=2)
        configure(old)
        with self.assertRaises(RomCommandError):
            session.verify_complete_preimage()
        self.assertEqual((wrapper.recovery_attempts, wrapper.query_reissues, len(handles)), (2, 2, 3))
        self.assertEqual(failed_counts, {512, 1024, 1536})
        self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_identical_cdb_and_state_cannot_start_another_recovery(self):
        _, old, handles, wrapper, session, _ = self.live()
        old.fail_before = lambda op: failure() if op == 0xFC7E else None
        session._read(0x4000, 512, session.installation.preimage[:512])
        handles[-1].fail_before = old.fail_before
        with self.assertRaises(RomCommandError):
            wrapper.exchange(simple_cdb(0xFC7E), read_length=16)
        self.assertEqual((wrapper.recovery_attempts, len(handles)), (1, 2))

    def test_failure_during_identity_audit_or_reissue_never_recurses(self):
        for failed_op in (0xFC78, 0xFD88, 0xFC7E):
            with self.subTest(failed_op=failed_op):
                def configure(handle):
                    handle.fail_before = lambda op: failure() if op == failed_op else None
                _, old, handles, wrapper, session, _ = self.live(new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC7E else None
                with self.assertRaises(RomCommandError):
                    session.verify_complete_preimage()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (1, 2))
                self.assertTrue(wrapper.failed and session.failed)

    def test_every_mutation_and_state_changing_command_is_never_retried(self):
        for failed_op in (0xFC7A, 0xFB7C, 0xFD87, 0xFC7B, 0xFC7D, 0xFC80):
            with self.subTest(failed_op=failed_op):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_after = lambda op: failure() if op == failed_op else None
                with self.assertRaises(RomCommandError):
                    session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))
                self.assertEqual(device.counts[failed_op], 1)
                self.assertEqual(device.commands.count(0xFB08), 1)
                self.assertTrue(session.failed)

    def test_wrong_error_unsubmitted_and_timeout_never_recover(self):
        for error in (failure(5), failure(submitted=False), TimeoutError("ambiguous timeout")):
            with self.subTest(error=repr(error)):
                _, old, handles, wrapper, session, _ = self.live()
                old.fail_before = lambda op: error if op == 0xFC7E else None
                with self.assertRaises(type(error)):
                    session.verify_complete_preimage()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_fresh_audit_stable_fields_guards_protection_and_crc_must_match(self):
        changes = ((12, 1), (24, 1), (28, 1), (68, 1), (72, 1), (76, 1),
                   (80, 513), (84, 1), (60, 1), (64, 0x40), (92, 0), (108, 0), (112, 0), (116, 0))
        for offset, value in changes:
            with self.subTest(offset=offset):
                def configure(handle):
                    handle.reply_change = lambda op, raw: changed_record(raw, offset, value) if op == 0xFD88 else raw
                _, old, handles, wrapper, session, _ = self.live(new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC7E else None
                with self.assertRaises(ValueError):
                    session.verify_complete_preimage()
                self.assertEqual(wrapper.query_reissues, 0)
                self.assertNotIn(0xFC7E, [r[0] for r in handles[1].calls])

    def test_post_mutation_poll_delta_zero_too_large_or_other_state_change_rejected(self):
        for offset, value in ((84, 0), (84, 65537), (68, 2), (80, 1)):
            with self.subTest(offset=offset, value=value):
                def configure(handle):
                    handle.reply_change = lambda op, raw: changed_record(raw, offset, value) if op == 0xFD88 else raw
                device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFD88 and device.erase_addresses else None
                with self.assertRaises(ValueError):
                    session.install_application()
                self.assertEqual(device.erase_addresses, [0x5000])
                self.assertFalse(device.program_addresses)
                self.assertTrue(session.mutation_completion_unknown)
                self.assertEqual(wrapper.audit_reconciliations, 0)

    def test_changed_transport_identity_or_path_stops_recovery(self):
        for field in ("slot", "path", "inquiry", "gate", "backend"):
            with self.subTest(field=field):
                def configure(handle):
                    if field == "slot": handle.slot += 32768
                    elif field == "path": handle.disk = {"path": "different"}
                    elif field == "inquiry": handle.inquiry = {"vendor": "OTHER", "product": "UBOOT1.00"}
                    elif field == "backend": handle.__class__ = type("OtherBackend", (Handle,), {})
                    else: handle.reply_change = lambda op, raw: raw[:7] + b"\0" + raw[8:] if op == 0xFC78 else raw
                _, old, _, wrapper, session, _ = self.live(new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC7E else None
                with self.assertRaises(ValueError):
                    session.verify_complete_preimage()
                self.assertEqual(wrapper.query_reissues, 0)

    def test_reissued_status_is_checked_against_expected(self):
        def configure(handle):
            handle.reply_change = lambda op, raw: raw[:8] + (99).to_bytes(4, "big") + raw[12:] if op == 0xFC7E else raw
        _, old, _, wrapper, session, _ = self.live(new_configure=configure)
        old.fail_before = lambda op: failure() if op == 0xFC7E else None
        with self.assertRaises(ValueError):
            session.verify_complete_preimage()
        self.assertTrue(wrapper.failed and session.failed)

    def test_logger_failure_prevents_reopen_or_reissue(self):
        for event in ("readonly_recovery_begin", "readonly_recovery_reissue_intent"):
            with self.subTest(event=event):
                _, old, handles, wrapper, session, events = self.live()
                old.fail_before = lambda op: failure() if op == 0xFC7E else None
                def log(item):
                    if item["event"] == event: raise OSError("durable log unavailable")
                    events.append(item)
                wrapper.log = log
                with self.assertRaises(OSError):
                    session.verify_complete_preimage()
                if event.endswith("begin"):
                    self.assertEqual(len(handles), 1)
                else:
                    self.assertNotIn(0xFC7E, [r[0] for r in handles[1].calls])

    def test_session_change_while_reopening_is_rejected(self):
        session = None
        def configure(_handle):
            session.expected["read_bytes"] += 1
        _, old, _, wrapper, session, _ = self.live(new_configure=configure)
        old.fail_before = lambda op: failure() if op == 0xFC7E else None
        with self.assertRaises(ValueError):
            session.verify_complete_preimage()
        self.assertEqual(wrapper.query_reissues, 0)

    def test_policy_bounds_and_explicit_backend_factory(self):
        old = Handle(FakeOperational(fixture()))
        for budget in (0, 9, True, 1.5):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                recovery.ReadOnlyStateRecoveryTransport(old, log=lambda _: None,
                                                       reopen_factory=lambda: old, max_recoveries=budget)
        with self.assertRaises(ValueError):
            recovery.ReadOnlyStateRecoveryTransport(old, log=lambda _: None, reopen_factory=None)


if __name__ == "__main__":
    unittest.main()
