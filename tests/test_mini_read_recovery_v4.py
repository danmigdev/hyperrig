"""Audited command recovery against the frozen installer and fake NOR only."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from tools import install_mini_app as installer
from tools import recover_mini_read_v4 as recovery
from tools.probe_mini_app_writer import simple_cdb
from tools.probe_mini_recovery import RomCommandError
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_app_writer_protocol import changed_record
from tests.test_mini_read_recovery import Handle, failure
from tests import test_mini_read_recovery_v3 as previous


class AuditedCommandTests(previous.EchoRecoveryTests):
    def live(self, *, preflight=False, new_configure=None, budget=8):
        device = FakeOperational(fixture()); old = Handle(device)
        handles, events, journal = [old], [], []
        def reopen():
            new = Handle(device); handles.append(new)
            if new_configure: new_configure(new)
            return new
        wrapper = recovery.AuditedCommandRecoveryTransport(old, log=events.append,
                    reopen_factory=reopen, max_recoveries=budget)
        session = installer.MiniAppInstallerSession(wrapper, fixture(), journal=journal.append, known_free_slot=True)
        wrapper.bind_session(session)
        with patch('time.sleep'): session.upload_and_start(IMAGE, expected_sha256=installer.sha(IMAGE))
        session.initialize_spi()
        if preflight: session.verify_complete_preimage()
        self.addCleanup(wrapper.close)
        return device, old, handles, wrapper, session, events

    def test_every_mutation_and_state_changing_command_is_never_retried(self):
        # FC7B/FC7D now get an audit-only reconciliation attempt, but an
        # executed command is never reissued. Other mutations keep v3 policy.
        for failed_op in (0xFC7A, 0xFB7C, 0xFC7B, 0xFC7D, 0xFC80):
            with self.subTest(failed_op=failed_op):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_after = lambda op: failure() if op == failed_op else None
                with self.assertRaises((RomCommandError, ValueError)):
                    session.install_application()
                self.assertEqual(wrapper.recovery_attempts, int(failed_op in (0xFC7B, 0xFC7D)))
                self.assertEqual(len(handles), 1 + wrapper.recovery_attempts)
                self.assertEqual(wrapper.mutation_request_reissues, 0)
                self.assertEqual(device.counts[failed_op], 1)
                self.assertEqual(device.commands.count(0xFB08), 1)
                self.assertTrue(session.failed)
                if failed_op in (0xFC7B, 0xFC7D):
                    self.assertTrue(session.mutation_completion_unknown)
                    self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])

    def test_unexecuted_erase_first_middle_and_header_program_reissue_exactly_once(self):
        for op, address in ((0xFC7B, 0x5000), (0xFC7B, 0x4000),
                            (0xFC7D, 0x5000), (0xFC7D, 0x5600), (0xFC7D, 0x4000)):
            with self.subTest(op=op, address=hex(address)):
                actual_replies = []
                def configure(handle):
                    def observe(actual, raw):
                        if actual == op: actual_replies.append(raw)
                        return raw
                    handle.reply_change = observe
                device, old, handles, wrapper, session, events = self.live(preflight=True, new_configure=configure)
                def fail(actual):
                    current = device.fields.get(32 if op == 0xFC7B else 36)
                    return failure() if actual == op and current == address else None
                old.fail_before = fail
                result = session.install_application()
                self.assertTrue(result['application_verified'])
                self.assertEqual((wrapper.recovery_attempts, wrapper.mutation_request_reissues), (1, 1))
                self.assertEqual(device.erase_addresses, [0x5000, 0x4000])
                self.assertEqual(len(device.program_addresses), 32)
                self.assertEqual(len(set(device.program_addresses)), 32)
                self.assertEqual((result['wren_attempts'], result['erase_attempts'], result['program_attempts']), (34, 2, 32))
                self.assertEqual([r[0] for r in handles[1].calls[:4]], [0xFC78, 0xFD88, op, 0xFD88])
                failed = next(r for r in old.calls if r[0] == op and int.from_bytes(r[1][10:14], 'big') == address)
                self.assertEqual(failed[1:], handles[1].calls[2][1:])
                ack = next(e for e in events if e['event'] == 'unexecuted_mutation_recovery_reissue_reply')
                self.assertFalse(ack['synthetic_ACK'])
                self.assertEqual(bytes.fromhex(ack['raw_hex']), actual_replies[0])
                self.assertFalse(session.mutation_completion_unknown)
                self.assertEqual(wrapper.summary()['completed_NOR_mutations_repeated'], 0)

    def test_consumed_sequence_without_any_WREN_still_forbids_reissue(self):
        for opcode in (0xFC7B, 0xFC7D):
            with self.subTest(opcode=opcode):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                def fail(op):
                    if op == opcode:
                        device.fields[28] += 1
                        return failure()
                old.fail_before = fail
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.mutation_request_reissues, 0)
                self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
                self.assertTrue(session.mutation_completion_unknown)
                self.assertFalse(device.program_addresses)
                self.assertEqual(device.erase_addresses, [] if opcode == 0xFC7B else [0x5000])

    def test_any_other_audit_change_including_watermark_stops_before_reissue(self):
        changes = ((4, 2), (8, 0x1C28000), (12, 2), (16, 3), (20, 1), (24, 9), (28, 9),
                   (32, 0x6000), (36, 0x5100), (40, 1), (44, 1), (48, 1), (52, 1), (56, 1),
                   (60, 1), (64, 0), (68, 1), (72, 1), (76, 1), (80, 1), (84, 1), (88, 259),
                   (92, 0), (96, 1), (100, 0), (104, 0), (108, 0), (112, 96), (116, 0))
        for offset, value in changes:
            with self.subTest(offset=offset):
                def configure(handle):
                    handle.reply_change = lambda op, raw: changed_record(raw, offset, value) if op == 0xFD88 else raw
                device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC7B else None
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.mutation_request_reissues, 0)
                self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_pending_command_requires_trusted_audit_exact_sequence_and_candidate(self):
        for kind in ('pending', 'submitted', 'sequence', 'expected', 'candidate', 'status', 'audit', 'preflight', 'sector', 'phase'):
            with self.subTest(kind=kind):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                def fail(op):
                    if op != 0xFC7B: return None
                    if kind == 'pending': session.mutation_completion_unknown = False
                    elif kind == 'submitted': session.mutation_command_submitted = False
                    elif kind == 'sequence': session.expected['sequence'] += 1
                    elif kind == 'expected': session.expected['page_crc32'] ^= 1
                    elif kind == 'candidate':
                        data = bytearray(session.installation.candidate)
                        data[session.expected['page'] - installer.APP_START] ^= 1
                        session.installation = replace(session.installation, candidate=bytes(data))
                    elif kind == 'status': session.last_status = {}
                    elif kind == 'audit': session.last_audit = None
                    elif kind == 'preflight': session.preimage_verified = False
                    elif kind == 'sector': session.pending_operation = 'other'
                    else: session.phase = 'complete'
                    return failure()
                old.fail_before = fail
                with self.assertRaises(RomCommandError): session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_invalid_fresh_audit_CRC_never_allows_mutation_reissue(self):
        def configure(handle):
            handle.reply_change = lambda op, raw: raw[:120] + bytes([raw[120] ^ 1]) + raw[121:] if op == 0xFD88 else raw
        device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
        old.fail_before = lambda op: failure() if op == 0xFC7B else None
        with self.assertRaisesRegex(ValueError, 'CRC'): session.install_application()
        self.assertEqual(wrapper.mutation_request_reissues, 0)
        self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_mutation_recovery_requires_immediately_preceding_audit(self):
        _, old, handles, wrapper, session, _ = self.live(preflight=True)
        original = session._exchange
        def exchange(cdb, **kwargs):
            if cdb[:2] == b'\xfc\x7b': wrapper.exchange(simple_cdb(0xFC78), read_length=16)
            return original(cdb, **kwargs)
        session._exchange = exchange
        old.fail_before = lambda op: failure() if op == 0xFC7B else None
        with self.assertRaises(RomCommandError): session.install_application()
        self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_wrong_mutation_cdb_token_sequence_or_address_never_reopens(self):
        for kind in ('token', 'sequence', 'address'):
            with self.subTest(kind=kind):
                _, old, handles, wrapper, session, _ = self.live(preflight=True)
                original = session._exchange
                def exchange(cdb, **kwargs):
                    if cdb[:2] == b'\xfc\x7b':
                        token, sequence, address = session.token, session.sequence, session.expected['sector']
                        if kind == 'token': token += 1
                        elif kind == 'sequence': sequence += 1
                        else: address += 4096
                        cdb = installer.mutation_cdb(0xFC7B, token, sequence, address)
                    return original(cdb, **kwargs)
                session._exchange = exchange
                old.fail_before = lambda op: failure() if op == 0xFC7B else None
                with self.assertRaises(RomCommandError): session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_reissue_requires_actual_correct_ACK_and_then_normal_mutation_audit(self):
        for kind in ('short', 'wrong_opcode', 'wrong_crc', 'error', 'post_audit'):
            with self.subTest(kind=kind):
                def configure(handle):
                    audits = 0
                    def change(op, raw):
                        nonlocal audits
                        if op == 0xFD88:
                            audits += 1
                            if kind == 'post_audit' and audits == 2: return changed_record(raw, 84, 0)
                        if op != 0xFC7B: return raw
                        if kind == 'short': return raw[:-1]
                        if kind == 'wrong_opcode': return b'\xfc\x7d' + raw[2:]
                        if kind == 'wrong_crc': return raw[:12] + bytes(4)
                        if kind == 'error': return raw[:2] + b'\x01' + raw[3:]
                        return raw
                    handle.reply_change = change
                device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC7B else None
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.mutation_request_reissues, 1)
                self.assertEqual(device.erase_addresses, [0x5000])
                self.assertFalse(device.program_addresses)
                self.assertTrue(session.mutation_completion_unknown)
                self.assertEqual(len(handles), 2)

    def test_no_nested_recovery_during_identity_audit_or_real_mutation_reissue(self):
        for failed_op in (0xFC78, 0xFD88, 0xFC7B):
            for after in (False, True):
                with self.subTest(failed_op=failed_op, after=after):
                    def configure(handle):
                        fail = lambda op: failure() if op == failed_op else None
                        if after: handle.fail_after = fail
                        else: handle.fail_before = fail
                    device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                    old.fail_before = lambda op: failure() if op == 0xFC7B else None
                    with self.assertRaises(RomCommandError): session.install_application()
                    self.assertEqual((wrapper.recovery_attempts, len(handles)), (1, 2))
                    self.assertTrue(session.mutation_completion_unknown)
                    self.assertLessEqual(len(device.erase_addresses), 1)
                    self.assertFalse(device.program_addresses)

    def test_mutation_does_not_recover_timeout_other_error_or_unsubmitted_error31(self):
        for error in (failure(5), failure(submitted=False), TimeoutError('mutation timeout')):
            with self.subTest(error=repr(error)):
                _, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_before = lambda op: error if op == 0xFC7B else None
                with self.assertRaises(type(error)): session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_v2_query_and_mutations_share_the_same_eight_recovery_budget(self):
        seen = set()
        def configure(handle):
            def fail(op):
                if op == 0xFC7D and handle.device.fields[36] not in seen:
                    seen.add(handle.device.fields[36]); return failure()
            handle.fail_before = fail
        device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
        old.fail_before = lambda op: failure() if op == 0xFC7E else None
        with self.assertRaises(RomCommandError): session.install_application()
        self.assertEqual((wrapper.recovery_attempts, wrapper.query_reissues, wrapper.mutation_request_reissues), (8, 1, 7))
        self.assertEqual(len(handles), 9)
        self.assertEqual(len(device.program_addresses), 7)
        self.assertEqual(len(set(device.program_addresses)), 7)

    def test_mutation_witness_cannot_change_during_reopen(self):
        for kind in ('expected', 'audit', 'status', 'unknown', 'pending'):
            with self.subTest(kind=kind):
                session = None
                def configure(_handle):
                    if kind == 'expected': session.expected['sequence'] += 1
                    elif kind == 'audit': session.last_record = b'changed'
                    elif kind == 'status': session.last_status_raw = b'changed'
                    elif kind == 'unknown': session.mutation_completion_unknown = False
                    else: session.pending_operation = 'other'
                device, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC7B else None
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.mutation_request_reissues, 0)
                self.assertFalse(device.erase_addresses or device.program_addresses)

    def test_mutation_same_witness_cannot_be_recovered_twice(self):
        _, old, _, wrapper, session, events = self.live(preflight=True)
        old.fail_before = lambda op: failure() if op == 0xFC7B else None
        checked = False
        def log(item):
            nonlocal checked
            events.append(item)
            if item['event'] == 'unexecuted_mutation_recovery_reissue_intent' and not checked:
                checked = True
                cdb = installer.mutation_cdb(0xFC7B, session.token, session.sequence, session.expected['sector'])
                with self.assertRaisesRegex(ValueError, 'witness already used'):
                    wrapper._mutation_witness(0xFC7B, cdb, 16, 0xFD88, session.last_record)
        wrapper.log = log
        session.install_application()
        self.assertTrue(checked)
        self.assertEqual(wrapper.mutation_request_reissues, 1)

    def test_logger_failure_prevents_unlogged_mutation_reissue(self):
        for event in ('unexecuted_mutation_recovery_begin', 'unexecuted_mutation_recovery_reissue_intent'):
            with self.subTest(event=event):
                device, old, handles, wrapper, session, events = self.live(preflight=True)
                old.fail_before = lambda op: failure() if op == 0xFC7B else None
                def log(item):
                    if item['event'] == event: raise OSError('durable log unavailable')
                    events.append(item)
                wrapper.log = log
                with self.assertRaises(OSError): session.install_application()
                self.assertFalse(device.erase_addresses or device.program_addresses)
                if event.endswith('begin'): self.assertEqual(len(handles), 1)
                else: self.assertNotIn(0xFC7B, [r[0] for r in handles[1].calls])


if __name__ == '__main__': unittest.main()
