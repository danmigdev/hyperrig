"""Frozen installer with v3 recovery; fake handles and fake NOR exclusively."""
import unittest
from unittest.mock import patch

from tools import install_mini_app as installer
from tools import recover_mini_read_v3 as recovery
from tools.probe_mini_app_writer import echo_cdb, simple_cdb
from tools.probe_mini_recovery import RomCommandError
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_app_writer_protocol import changed_record
from tests.test_mini_read_recovery import Handle, failure
from tests import test_mini_read_recovery_v2 as previous


class EchoRecoveryTests(previous.ReconciledReadRecoveryTests):
    """Run the prior recovery cases against v3 as well as FD87-specific cases."""

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

    def test_every_mutation_and_state_changing_command_is_never_retried(self):
        # FD87 is the sole deliberate difference from v2. Stage OUT, ARM,
        # erase, program and finish remain terminal even after device execution.
        for failed_op in (0xFC7A, 0xFB7C, 0xFC7B, 0xFC7D, 0xFC80):
            with self.subTest(failed_op=failed_op):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_after = lambda op: failure() if op == failed_op else None
                with self.assertRaises(RomCommandError):
                    session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))
                self.assertEqual(device.counts[failed_op], 1)
                self.assertEqual(device.commands.count(0xFB08), 1)
                self.assertTrue(session.failed)

    def test_fd87_before_or_after_execution_before_erase_and_mid_sector(self):
        for after in (False, True):
            for address in (0x5000, 0x5600):
                with self.subTest(after=after, address=hex(address)):
                    device, old, handles, wrapper, session, events = self.live(preflight=True)
                    fail = lambda op: failure() if op == 0xFD87 and device.fields[36] == address else None
                    if after:
                        old.fail_after = fail
                    else:
                        old.fail_before = fail
                    result = session.install_application()
                    self.assertTrue(result["application_verified"])
                    self.assertEqual((wrapper.recovery_attempts, wrapper.echo_reissues), (1, 1))
                    self.assertEqual(wrapper.echo_already_emitted, int(after))
                    self.assertEqual(device.echo_addresses.count(address), 1 + int(after))
                    self.assertEqual(device.erase_addresses, [0x5000, 0x4000])
                    self.assertEqual(len(device.program_addresses), 32)
                    self.assertEqual(len(set(device.program_addresses)), 32)
                    self.assertEqual((result["wren_attempts"], result["erase_attempts"], result["program_attempts"]), (34, 2, 32))
                    self.assertEqual(device.counts[0xFB7C], 32)
                    self.assertEqual(device.counts[0xFC7A], 2)
                    self.assertEqual(device.counts[0xFC80], 2)
                    self.assertEqual(device.commands.count(0xFB08), 1)
                    self.assertEqual([r[0] for r in handles[1].calls[:4]], [0xFC78, 0xFD88, 0xFD87, 0xFD88])
                    failed = next(r for r in old.calls if r[0] == 0xFD87 and int.from_bytes(r[1][10:14], "big") == address)
                    self.assertEqual(failed[1:], handles[1].calls[2][1:])
                    reissue = next(e for e in events if e["event"] == "readonly_recovery_reissue_intent")
                    self.assertEqual(reissue["fresh_echoed"], int(after))
                    self.assertEqual(reissue["candidate_page_sha256"], installer.sha(session.installation.page(address)))
                    self.assertFalse(session.mutation_completion_unknown)

    def test_fd87_exact_audit_rejects_any_unrelated_word_including_stack_change(self):
        changes = ((4, 2), (8, 0x1C28000), (12, 2), (16, 3), (20, 1), (24, 9), (28, 9),
                   (32, 0x6000), (36, 0x5100), (40, 1), (44, 1), (48, 1), (52, 1), (56, 1),
                   (60, 1), (64, 0), (68, 1), (72, 1), (76, 1), (80, 1), (84, 1), (88, 259),
                   (92, 0), (96, 1), (100, 0), (104, 2), (108, 0), (112, 96), (116, 0))
        for offset, value in changes:
            with self.subTest(offset=offset):
                def configure(handle):
                    handle.reply_change = lambda op, raw: changed_record(raw, offset, value) if op == 0xFD88 else raw
                device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_after = lambda op: failure() if op == 0xFD87 else None
                with self.assertRaises(ValueError):
                    session.install_application()
                self.assertEqual(wrapper.echo_reissues, 0)
                self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd87_audit_crc_cannot_be_normalized_into_success(self):
        def configure(handle):
            handle.reply_change = lambda op, raw: raw[:120] + bytes([raw[120] ^ 1]) + raw[121:] if op == 0xFD88 else raw
        device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
        old.fail_before = lambda op: failure() if op == 0xFD87 else None
        with self.assertRaisesRegex(ValueError, "CRC"):
            session.install_application()
        self.assertFalse(device.erase_addresses or device.program_addresses)
        self.assertEqual(wrapper.echo_reissues, 0)

    def test_fd87_bad_echo_short_or_mutable_reply_stops_before_mutation(self):
        for kind in ("corrupt", "short", "mutable"):
            with self.subTest(kind=kind):
                def configure(handle):
                    def change(op, raw):
                        if op != 0xFD87:
                            return raw
                        if kind == "corrupt":
                            return bytes([raw[0] ^ 1]) + raw[1:]
                        return raw[:-1] if kind == "short" else bytearray(raw)
                    handle.reply_change = change
                device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_after = lambda op: failure() if op == 0xFD87 else None
                with self.assertRaises(ValueError):
                    session.install_application()
                self.assertTrue(wrapper.failed and session.failed)
                self.assertFalse(device.erase_addresses or device.program_addresses)
                self.assertEqual(wrapper.echo_reissues, 1)

    def test_fd87_still_requires_normal_installer_audit_after_reissued_echo(self):
        def configure(handle):
            audits = 0
            def change(op, raw):
                nonlocal audits
                if op == 0xFD88:
                    audits += 1
                    if audits == 2:
                        return changed_record(raw, 68, 1)
                return raw
            handle.reply_change = change
        device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
        old.fail_before = lambda op: failure() if op == 0xFD87 else None
        with self.assertRaisesRegex(ValueError, "wren_attempts"):
            session.install_application()
        self.assertEqual(wrapper.echo_reissues, 1)
        self.assertTrue(session.failed)
        self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd87_failure_during_recovery_does_not_recurse(self):
        for failed_op in (0xFC78, 0xFD88, 0xFD87):
            with self.subTest(failed_op=failed_op):
                def configure(handle):
                    handle.fail_before = lambda op: failure() if op == failed_op else None
                device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFD87 else None
                with self.assertRaises(RomCommandError):
                    session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (1, 2))
                self.assertTrue(wrapper.failed and session.failed)
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd87_never_recovers_wrong_error_timeout_or_presubmission_failure(self):
        for error in (failure(5), failure(submitted=False), TimeoutError("ambiguous timeout")):
            with self.subTest(error=repr(error)):
                _, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_before = lambda op: error if op == 0xFD87 else None
                with self.assertRaises(type(error)):
                    session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_fd87_trusted_witness_and_immediate_audit_are_required(self):
        for kind in ("intervening", "audit", "status", "unknown_mutation", "preflight", "phase", "crc", "already_echoed"):
            with self.subTest(kind=kind):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                if kind == "intervening":
                    original_exchange = session._exchange
                    def intervening(cdb, **kwargs):
                        if cdb[:2] == b"\xfd\x87":
                            wrapper.exchange(simple_cdb(0xFC78), read_length=16)
                        return original_exchange(cdb, **kwargs)
                    session._exchange = intervening
                def fail(op):
                    if op != 0xFD87:
                        return None
                    if kind == "audit": session.last_audit = None
                    elif kind == "status": session.last_status = {"error": 1}
                    elif kind == "unknown_mutation": session.mutation_completion_unknown = True
                    elif kind == "preflight": session.preimage_verified = False
                    elif kind == "phase": session.phase = "complete"
                    elif kind == "crc": session.expected["page_crc32"] ^= 1
                    elif kind == "already_echoed": session.expected["echoed"] = 1
                    return failure()
                old.fail_before = fail
                with self.assertRaises(RomCommandError):
                    session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd87_reopen_cannot_change_installer_witness(self):
        for kind in ("expected", "audit", "status", "unknown_mutation"):
            with self.subTest(kind=kind):
                session = None
                def configure(_handle):
                    if kind == "expected": session.expected["sequence"] += 1
                    elif kind == "audit": session.last_record = b"stale"
                    elif kind == "status": session.last_status_raw = b"stale"
                    else: session.mutation_completion_unknown = True
                device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFD87 else None
                with self.assertRaises(ValueError):
                    session.install_application()
                self.assertEqual(wrapper.echo_reissues, 0)
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd87_token_sequence_and_page_must_match_validated_stage(self):
        for field in ("token", "sequence", "address"):
            with self.subTest(field=field):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                real_exchange = session._exchange
                def wrong(cdb, **kwargs):
                    if cdb[:2] == b"\xfd\x87":
                        token, sequence, address = session.token, session.sequence, session.expected["page"]
                        if field == "token": token += 1
                        elif field == "sequence": sequence += 1
                        else: address += 256
                        cdb = echo_cdb(token, sequence, address)
                    return real_exchange(cdb, **kwargs)
                session._exchange = wrong
                old.fail_before = lambda op: failure() if op == 0xFD87 else None
                with self.assertRaises(RomCommandError):
                    session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_fd87_and_v2_queries_share_one_budget_and_allow_no_ninth_recovery(self):
        failed_pages = set()
        def configure(handle):
            def fail(op):
                if op == 0xFD87 and handle.device.fields[36] not in failed_pages:
                    failed_pages.add(handle.device.fields[36])
                    return failure()
            handle.fail_before = fail
        device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
        query_failed = False
        def first_fail(op):
            nonlocal query_failed
            if op == 0xFC7E and not query_failed:
                query_failed = True
                return failure()
        old.fail_before = first_fail
        with self.assertRaises(RomCommandError):
            session.install_application()
        self.assertEqual((wrapper.recovery_attempts, wrapper.query_reissues, wrapper.echo_reissues), (8, 1, 7))
        self.assertEqual(len(handles), 9)
        self.assertEqual(len(device.program_addresses), 7)
        self.assertEqual(len(set(device.program_addresses)), 7)
        self.assertEqual(len(failed_pages), 8)

    def test_fd87_same_command_witness_cannot_be_recovered_twice(self):
        _, old, _, wrapper, session, events = self.live(preflight=True)
        old.fail_before = lambda op: failure() if op == 0xFD87 else None
        attempted = False
        def log(item):
            nonlocal attempted
            events.append(item)
            if item["event"] == "readonly_recovery_reissue_reply" and not attempted:
                attempted = True
                cdb = echo_cdb(session.token, session.sequence, session.expected["page"])
                with self.assertRaisesRegex(ValueError, "witness already used recovery"):
                    wrapper._echo_witness(cdb, 256, 0xFD88, session.last_record)
        wrapper.log = log
        session.install_application()
        self.assertTrue(attempted)
        self.assertEqual(wrapper.recovery_attempts, 1)

    def test_fd87_logger_failure_prevents_unlogged_reissue(self):
        for event in ("readonly_recovery_begin", "readonly_recovery_reissue_intent"):
            with self.subTest(event=event):
                device, old, handles, wrapper, session, events = self.live(preflight=True)
                old.fail_before = lambda op: failure() if op == 0xFD87 else None
                def log(item):
                    if item["event"] == event:
                        raise OSError("durable logger unavailable")
                    events.append(item)
                wrapper.log = log
                with self.assertRaises(OSError):
                    session.install_application()
                if event.endswith("begin"):
                    self.assertEqual(len(handles), 1)
                else:
                    self.assertNotIn(0xFD87, [r[0] for r in handles[1].calls])
                self.assertFalse(device.erase_addresses or device.program_addresses)


if __name__ == "__main__":
    unittest.main()
