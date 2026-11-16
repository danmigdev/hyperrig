"""Offline native-I/O witness tests; all serial activity is simulated."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import probe_mini_app_cdc_handshake as tool

VERSION = 'tankm_fw M5.71 rel ble'
PONG = b'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11\r\n'
PORT = {'device': 'COM3', 'vid': 0x3654, 'pid': 0x5155}
MANIFEST = tool.ROOT/'build/hyperrig-mini-audio-v3/firmware-manifest.json'


class Port:
    def __init__(self, responses, *, partial_write=False, read_error=False,
                 slow_write=False, late_before_second=False, close_error=False):
        self.responses = list(responses); self.pending = []; self.writes = []; self.closed = False
        self.now = 0; self.partial_write = partial_write; self.read_error = read_error
        self.slow_write = slow_write; self.late_before_second = late_before_second
        self.close_error = close_error; self.late_injected = False
    def clock(self): return self.now
    def sleep(self, seconds): self.now += seconds
    def write(self, data):
        self.writes.append(data)
        if self.slow_write: self.now += 1.0
        response = self.responses.pop(0)
        if isinstance(response, Exception): raise response
        if response is not None: self.pending.append(response)
        return 2 if self.partial_write else len(data)
    def read(self, size):
        self.now += .05
        if self.read_error and self.writes: raise OSError('fake read timeout')
        if self.late_before_second and len(self.writes) == 1 and self.now >= 1.78 and not self.late_injected:
            self.late_injected = True; return b'PO'
        return self.pending.pop(0) if self.pending else b''
    def close(self):
        if self.close_error: raise OSError('fake close failure')
        self.closed = True


class HandshakeTests(unittest.TestCase):
    def exercise(self, responses, *, queries=(), **faults):
        port = Port(responses, **faults); opens = []; enumerations = []
        def enum(): enumerations.append(True); return [PORT]
        def opening(name): opens.append(name); return port
        with tempfile.TemporaryDirectory(dir=tool.ROOT/'build') as directory:
            args = SimpleNamespace(port='COM3', firmware_manifest=MANIFEST,
                                   log=Path(directory)/'trace.jsonl', queries=list(queries))
            result = error = None
            try:
                result = tool.run(args, enumerate_fn=enum, open_fn=opening, clock=port.clock, sleep_fn=port.sleep)
            except Exception as exc: error = exc
            rows = [json.loads(line) for line in args.log.read_text().splitlines()]
        return SimpleNamespace(port=port, result=result, error=error, rows=rows, opens=opens, enum=enumerations)

    def test_empty_timeout_then_success_same_open_and_native_witness(self):
        result = self.exercise([None, PONG, b"MODEL 'A2'\n"], queries=('MODEL',))
        self.assertIsNone(result.error); self.assertEqual(result.opens, ['COM3'])
        self.assertEqual(result.port.writes, [b'PING\n', b'PING\n', b'MODEL\n'])
        self.assertEqual(result.result['PING_sent'], 2); self.assertTrue(result.port.closed)
        failed = next(r for r in result.rows if r['event'] == 'handshake_attempt_failed')
        self.assertEqual(failed['native_RX_bytes'], 0); self.assertEqual(failed['native_write_results'], [5])
        self.assertGreater(failed['reads_after_completed_write'], 0); self.assertTrue(failed['repeat_permitted'])
        native = [r for r in result.rows if r['event'] == 'native_rx']
        self.assertEqual(native[0]['hex'], PONG.hex()); self.assertEqual(native[0]['handshake_attempt'], 2)
        self.assertIsNone(native[-1]['handshake_attempt'])
        self.assertEqual([r['event'] for r in result.rows][-2:], ['port_closed', 'session_complete'])
        self.assertFalse(result.result['image_hash_attested_by_device'])

    def test_first_or_fifth_pong_stops_loop(self):
        for empty in (0, 4):
            with self.subTest(empty=empty):
                result = self.exercise([None]*empty+[PONG])
                self.assertIsNone(result.error); self.assertEqual(len(result.port.writes), empty+1)
                self.assertEqual(result.opens, ['COM3']); self.assertTrue(result.port.closed)

    def test_five_empty_timeouts_exhaust_without_sixth_or_queries(self):
        result = self.exercise([None]*5, queries=('MODEL',))
        self.assertIsInstance(result.error, tool.Error); self.assertEqual(result.port.writes, [b'PING\n']*5)
        self.assertTrue(result.port.closed); self.assertIsNone(result.result)
        failures = [r for r in result.rows if r['event'] == 'handshake_attempt_failed']
        self.assertEqual([r['repeat_permitted'] for r in failures], [True]*4+[False])

    def test_any_rx_or_invalid_identity_is_terminal(self):
        for response in (b'PO', b'garbage\n', b'\xff\n', b'@event\n', b'\n',
                         b'PONG tankg_fw M5.71 rel ble Nov 12 2026 16:04:11\n'):
            with self.subTest(response=response):
                result = self.exercise([response, PONG])
                self.assertIsInstance(result.error, tool.Error)
                self.assertEqual(result.port.writes, [b'PING\n']); self.assertTrue(result.port.closed)
                failed = next(r for r in result.rows if r['event'] == 'handshake_attempt_failed')
                self.assertFalse(failed['repeat_permitted']); self.assertGreater(failed['native_RX_bytes'], 0)

    def test_partial_write_or_transport_errors_never_repeat(self):
        for response, faults in ((None, {'partial_write': True}), (OSError('fake write timeout'), {}),
                                 (None, {'read_error': True}), (tool.Error('response timeout for PING'), {})):
            with self.subTest(response=response, faults=faults):
                result = self.exercise([response, PONG], **faults)
                self.assertIsInstance(result.error, tool.Error)
                self.assertEqual(result.port.writes, [b'PING\n']); self.assertTrue(result.port.closed)
                self.assertFalse(next(r for r in result.rows if r['event'] == 'handshake_attempt_failed')['repeat_permitted'])

    def test_write_that_consumes_deadline_is_not_an_empty_read_timeout(self):
        result = self.exercise([None, PONG], slow_write=True)
        self.assertEqual(result.port.writes, [b'PING\n']); self.assertIsInstance(result.error, tool.Error)
        failure = next(r for r in result.rows if r['event'] == 'handshake_attempt_failed')
        self.assertEqual(failure['reads_after_completed_write'], 0); self.assertFalse(failure['repeat_permitted'])

    def test_late_partial_before_second_write_stops_without_sending_it(self):
        result = self.exercise([None, PONG], late_before_second=True)
        self.assertTrue(result.port.late_injected); self.assertIsInstance(result.error, tool.Error)
        self.assertEqual(result.port.writes, [b'PING\n'])
        failures = [r for r in result.rows if r['event'] == 'handshake_attempt_failed']
        self.assertEqual(len(failures), 2); self.assertTrue(failures[0]['repeat_permitted'])
        self.assertFalse(failures[1]['repeat_permitted']); self.assertEqual(failures[1]['native_write_calls'], 0)

    def test_read_query_timeout_is_not_handshake_retry(self):
        result = self.exercise([PONG, None], queries=('MODEL', 'MEM'))
        self.assertIsInstance(result.error, tool.Error)
        self.assertEqual(result.port.writes, [b'PING\n', b'MODEL\n']); self.assertTrue(result.port.closed)

    def test_close_error_never_emits_session_complete(self):
        result = self.exercise([PONG], close_error=True)
        self.assertIsInstance(result.error, OSError); self.assertIsNone(result.result)
        self.assertFalse(any(r['event'] == 'session_complete' for r in result.rows))

    def test_default_and_real_manifest_preflight_are_offline(self):
        with (patch.object(tool.readonly, 'enumerate_ports', side_effect=AssertionError('enumeration')),
              patch.object(tool.host.HostOpenTransport, 'open', side_effect=AssertionError('open')),
              tempfile.TemporaryDirectory(dir=tool.ROOT/'build') as tmp,
              redirect_stdout(io.StringIO()) as out):
            self.assertEqual(tool.main([]), 0)
            out.seek(0); out.truncate(0)
            self.assertEqual(tool.main(['--check-only', '--port', 'COM3', '--firmware-manifest', str(MANIFEST),
                                        '--log', str(Path(tmp)/'trace.jsonl'), '--queries']), 0)
            plan = json.loads(out.getvalue())
        self.assertEqual(plan['PING_timeout_seconds'], .7); self.assertEqual(plan['PING_max_attempts'], 5)
        self.assertTrue(plan['automatic_retry']); self.assertIn('PING only', plan['automatic_retry_scope'])
        self.assertEqual(plan['query_retries'], 0); self.assertFalse(plan['device_io'])


if __name__ == '__main__': unittest.main()
