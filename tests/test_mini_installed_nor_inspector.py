"""Replay a fake complete NOR acquisition through the frozen reader client."""
import copy
import struct
import unittest

from tools import inspect_mini_installed as inspector
from tools.mini_nor_read_recovery import NorReadRecoveryTransport, query
from tools.probe_mini_recovery import MiniNorSession
from tests.test_mini_nor_read_recovery import Handle, failure
from tests.test_mini_recovery import FakeNor
from tests.test_mini_installed_inspector_v4 import recovered_evidence


class VaryingNor(FakeNor):
    def exchange(self, cdb, data_out=None, read_length=0):
        raw = super().exchange(cdb, data_out, read_length)
        if cdb[:2] == b'\xfd\x71':
            self.last_address = int.from_bytes(cdb[2:6], 'big')
            raw = bytes(value ^ ((self.last_address >> 9) & 255) for value in raw)
        return raw


def nor_evidence(faults):
    device = VaryingNor(); device.slot = 0x1C28000
    trace, events, remaining = [], [], list(faults)
    def logged_handle(label):
        handle = Handle(device); original = handle.exchange
        def exchange(cdb, data_out=None, read_length=0):
            op = int.from_bytes(cdb[:2], 'big')
            address = int.from_bytes(cdb[2:6], 'big') if op == 0xFD71 else getattr(device, 'last_address', None)
            row = {'state': 'before', 'stage': label, 'cdb': cdb.hex(), 'out_bytes': 0, 'in_bytes': read_length}
            trace.append(row.copy())
            try:
                if remaining and remaining[0] == (op, address, False):
                    remaining.pop(0); raise failure()
                raw = original(cdb, data_out, read_length)
                if remaining and remaining[0] == (op, address, True):
                    remaining.pop(0); raise failure()
            except Exception as error:
                row.update(state='error', native_transfer={'win32_error': error.errno})
                trace.append(row); raise
            row.update(state='after', response_bytes=len(raw), response_sha256=inspector.sha(raw))
            if len(raw) <= 128: row['response_hex'] = raw.hex()
            trace.append(row)
            return raw
        handle.exchange = exchange
        return handle
    old = logged_handle('full_after')
    reader = MiniNorSession(old, slot=device.slot); reader.ready = True
    reader._handshake(); reader.initialize_spi()
    initial = bytes.fromhex(trace[-1]['response_hex'])
    wrapper = NorReadRecoveryTransport(old, log=events.append,
                                      reopen_factory=lambda: logged_handle('full-read-recovery-reopen'))
    wrapper.bind_session(reader, status_raw=initial)
    try:
        raw = reader.read_flash(0, inspector.CAPACITY)
        assert not remaining
    finally:
        wrapper.close()
    context = {'source_pinned': True, 'slot': device.slot, 'events': events,
               'summary': wrapper.summary(), 'target_read_counter': reader.successful_bytes}
    return trace, raw, context


def verify(case):
    return inspector.inspect_final_nor_read(*case)


class NorInstalledInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plain = nor_evidence([])
        cls.mixed = nor_evidence([(0xFD71, 0x200, False), (0xFD71, 0x600, True),
                                 (0xFC73, 0x800, False), (0xFC73, 0xA00, True)])

    def test_complete_read_has_all2048_chunks_and_real_statuses(self):
        result = verify(self.plain)
        self.assertEqual((result['logical_chunks'], result['logical_bytes'], result['physical_read_counter']),
                         (2048, 0x100000, 0x100000))
        self.assertTrue(result['every_chunk_matches_final_dump'])
        self.assertEqual(result['verified_read_recoveries'], [])

    def test_reads_lost_before_and_after_execution_and_status_losses_are_accounted(self):
        result = verify(self.mixed)
        self.assertEqual(result['physical_read_counter'], 0x100200)
        self.assertEqual(result['lost_read_bytes'], 512)
        proofs = result['verified_read_recoveries']
        self.assertEqual([p['opcode'] for p in proofs], ['fd71', 'fd71', 'fc73', 'fc73'])
        self.assertEqual([p['lost_read_bytes'] for p in proofs[:2]], [0, 512])
        self.assertFalse(result['status_replies_synthesized'] or result['NOR_mutations_performed_by_reader'])

    def test_missing_duplicated_out_of_order_or_corrupted_logical_chunk_is_rejected(self):
        for kind in ('missing', 'duplicate', 'order', 'hash', 'short', 'dump'):
            case = copy.deepcopy(self.plain); trace = case[0]
            index = next(i for i, x in enumerate(trace) if x['state'] == 'before' and x['cdb'].startswith('fd71'))
            if kind == 'missing': del trace[index:index+4]
            elif kind == 'duplicate': trace[index:index] = copy.deepcopy(trace[index:index+4])
            elif kind == 'order': trace[index:index+4], trace[index+4:index+8] = trace[index+4:index+8], trace[index:index+4]
            elif kind == 'hash': trace[index+1]['response_sha256'] = '0' * 64
            elif kind == 'short': trace[index+1]['response_bytes'] = 511
            else:
                raw = bytearray(case[1]); raw[0x23456] ^= 1; case = (case[0], bytes(raw), case[2])
            with self.subTest(kind=kind), self.assertRaises(ValueError): verify(case)

    def test_fresh_identity_error_clock_counter_or_synthetic_status_rejected(self):
        for kind in ('identity', 'sticky', 'clock', 'counter', 'status_synthetic', 'pending', 'source'):
            case = copy.deepcopy(self.mixed); events = case[2]['events']
            if kind == 'source': case[2]['source_pinned'] = False
            elif kind == 'identity': next(x for x in events if x['event']=='nor_recovery_identity')['raw_hex'] = '00'*16
            elif kind == 'status_synthetic':
                next(x for x in events if x['event']=='nor_status_return_real_reply')['status_reply_synthesized'] = True
            elif kind == 'pending':
                item = next(x for x in events if x['event']=='nor_recovery_begin' and x['pending_read'] is not None)
                item['pending_read']['sha256'] = '0'*64
            else:
                item = next(x for x in events if x['event']=='nor_recovery_status')
                raw = bytearray.fromhex(item['raw_hex']); raw[{'sticky':2,'clock':7,'counter':15}[kind]] ^= 1
                item.update(raw_hex=raw.hex(), sha256=inspector.sha(raw))
                fault = next(i for i, x in enumerate(case[0]) if x['state']=='error')
                wire = case[0][fault+4]
                wire.update(response_hex=raw.hex(), response_sha256=inspector.sha(raw))
            with self.subTest(kind=kind), self.assertRaises(ValueError): verify(case)

    def test_budget_summary_real_counter_and_no_lifecycle_changes_are_required(self):
        for kind in ('budget', 'count', 'lost', 'final_counter', 'failed', 'unclosed', 'synthetic', 'extra_init'):
            case = copy.deepcopy(self.mixed); summary = case[2]['summary']
            if kind == 'budget': summary['max_recoveries'] = 9
            elif kind == 'count': summary['recovery_attempts'] -= 1
            elif kind == 'lost': summary['lost_read_bytes'] = 0
            elif kind == 'final_counter': case[2]['target_read_counter'] = 0x100000
            elif kind == 'failed': summary['failed'] = True
            elif kind == 'unclosed': summary['closed'] = False
            elif kind == 'synthetic': summary['status_replies_synthesized'] = True
            else: case[0].extend(copy.deepcopy(case[0][2:4]))
            with self.subTest(kind=kind), self.assertRaises(ValueError): verify(case)

    def test_reissue_must_have_real_chunk_and_following_real_core_status(self):
        for kind in ('no_reissue', 'extra_reissue', 'wrong_bytes', 'no_status', 'extra_recovery_error'):
            case = copy.deepcopy(self.mixed); trace = case[0]
            fault = next(i for i, x in enumerate(trace) if x['state']=='error')
            if kind == 'no_reissue': del trace[fault+5:fault+7]
            elif kind == 'extra_reissue': trace[fault+7:fault+7] = copy.deepcopy(trace[fault+5:fault+7])
            elif kind == 'wrong_bytes': trace[fault+6]['response_sha256'] = '0'*64
            elif kind == 'no_status': del trace[fault+7:fault+9]
            else: trace[fault+6].update(state='error',native_transfer={'win32_error':31})
            with self.subTest(kind=kind), self.assertRaises(ValueError): verify(case)

    def test_writer_v4_and_NOR_recovery_have_separate_budgets_and_proofs(self):
        journal, writer_trace, before, candidate, order, writer_context = recovered_evidence([(0xFC7D,0x5000)])
        trace, raw, nor_context = self.mixed
        result = inspector.inspect_history(journal, writer_trace+trace, before, candidate, order,
                    recovery=writer_context, nor_recovery=nor_context, observed_nor=raw)
        self.assertEqual(result['mutation_request_errors'], 1)
        self.assertEqual(result['NOR_read_errors'], 4)
        self.assertEqual(len(result['verified_unexecuted_mutation_recoveries']), 1)
        self.assertEqual(result['final_NOR_read']['physical_read_counter'], 0x100200)
        with self.assertRaises(ValueError):
            inspector.inspect_history(journal, writer_trace+trace, before, candidate, order, recovery=writer_context)


if __name__ == '__main__':
    unittest.main()
