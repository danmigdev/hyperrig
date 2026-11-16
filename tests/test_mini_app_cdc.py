"""Offline CDC opener tests: fake serial port/clock, no OS enumeration."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import probe_mini_app_cdc as tool
from tests.test_mini_app_host_open import DiagnosticPedal, PORT

MANIFEST = tool.ROOT/'build/hyperrig-mini-audio-v3/firmware-manifest.json'
IMAGE = '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c'


class CDCProbeTests(unittest.TestCase):
    def exercise(self, *, fault=None, queries=(), native_factory=False):
        pedal = DiagnosticPedal(); events = []; enum = []; opens = []
        if fault == 'timeout': pedal.faults[('PING', 1)] = None
        if fault == 'write': pedal.faults[('PING', 1)] = OSError('fake write timeout')
        if fault == 'identity': pedal.faults[('PING', 1)] = ['PONG tankg_fw M5.71 rel ble Nov 12 2026 16:04:11']
        if fault == 'query': pedal.faults[('MODEL', 1)] = ['ERR MODEL fake']
        if fault == 'close': pedal.close = lambda: (_ for _ in ()).throw(OSError('fake close failure'))
        def enumerate_fn():
            enum.append(True)
            if fault == 'missing': return []
            if fault == 'multiple': return [PORT, {**PORT, 'device': 'COM4'}]
            if fault == 'wrong_port': return [{**PORT, 'device': 'COM4'}]
            return [PORT]
        def open_fn(name):
            opens.append(name)
            if fault == 'open': raise OSError('fake open failure')
            return pedal
        def sleep(seconds): events.append(('wait', seconds)); pedal.clock.now += seconds
        class Port:
            def __setattr__(self, k, v): events.append(('set', k, v)); object.__setattr__(self, k, v)
            def open(self): opens.append(self.port); events.append(('open',))
            def read(self, n): return pedal.read(n)
            def write(self, b): return pedal.write(b)
            def close(self): events.append(('close',)); pedal.close()
        def factory(**kwargs):
            self.assertIsNone(kwargs['port']); self.assertFalse(kwargs['dsrdtr'] or kwargs['rtscts'])
            return Port()
        with tempfile.TemporaryDirectory(dir=tool.ROOT/'build') as directory, ExitStack() as stack:
            args = SimpleNamespace(port='COM3', firmware_manifest=MANIFEST,
                                   log=Path(directory)/'trace.jsonl', queries=list(queries))
            stack.enter_context(patch.object(tool.host, 'preflight', side_effect=AssertionError('historical v2 preflight')))
            if fault == 'no_read':
                stack.enter_context(patch.object(tool.readonly, 'load_profile', return_value={'capabilities': {'read': False}}))
            if fault == 'expected_version':
                profile = tool.readonly.load_profile(MANIFEST); profile['firmware_version'] = 'tankm_fw M5.72 rel ble'
                stack.enter_context(patch.object(tool.readonly, 'load_profile', return_value=profile))
            if native_factory:
                stack.enter_context(patch.dict(sys.modules, {'serial': SimpleNamespace(Serial=factory,
                    EIGHTBITS=8, PARITY_NONE='N', STOPBITS_ONE=1)}))
            summary = error = None
            try:
                summary = tool.run(args, enumerate_fn=enumerate_fn, open_fn=None if native_factory else open_fn,
                                   clock=pedal.clock, sleep_fn=sleep)
            except Exception as exc: error = exc
            rows = [json.loads(row) for row in args.log.read_text().splitlines()] if args.log.exists() else []
        return SimpleNamespace(summary=summary, error=error, rows=rows, pedal=pedal, events=events, enum=enum, opens=opens)

    def test_real_v3_preflight_no_enumeration_or_open(self):
        with tempfile.TemporaryDirectory(dir=tool.ROOT/'build') as tmp, redirect_stdout(io.StringIO()) as output:
            with (patch.object(tool.readonly, 'enumerate_ports', side_effect=AssertionError('enumeration')),
                  patch.object(tool.host.HostOpenTransport, 'open', side_effect=AssertionError('open'))):
                code = tool.main(['--check-only', '--port', 'COM3', '--firmware-manifest', str(MANIFEST),
                                  '--log', str(Path(tmp)/'new.jsonl'), '--queries'])
            self.assertEqual(code, 0)
            value = json.loads(output.getvalue())
            self.assertEqual(value['expected_image_sha256'], IMAGE)
            self.assertTrue(value['dtr_requested_before_open']); self.assertFalse(value['device_io'])
            self.assertEqual(value['queries_after_exact_PONG'], [])

    def test_native_dtr_true_before_open_and_close_before_complete(self):
        value = self.exercise(queries=('MODEL', 'PLIST'), native_factory=True)
        self.assertIsNone(value.error)
        self.assertEqual(value.events, [('set', 'dtr', True), ('set', 'rts', False),
            ('set', 'port', 'COM3'), ('open',), ('wait', 1.0), ('close',)])
        self.assertEqual(value.pedal.writes, ['PING', 'MODEL', 'PLIST'])
        self.assertTrue(value.summary['serial_port_closed'])
        self.assertEqual(value.summary['expected_image_sha256'], IMAGE)
        self.assertEqual([r['event'] for r in value.rows][-2:], ['port_closed', 'session_complete'])
        ping = next(r for r in value.rows if r['event'] == 'tx')
        self.assertEqual(ping['timeout_seconds'], 3.0); self.assertEqual(ping['hex'], b'PING\n'.hex())
        self.assertTrue(any(r['event'] == 'rx' and r['hex'] for r in value.rows))
        self.assertFalse(value.rows[0]['DTR_control_delivery_verified'])
        self.assertFalse(value.summary['image_hash_attested_by_device'])

    def test_failed_ping_never_retries_or_sends_queries(self):
        for fault in ('timeout', 'write', 'identity', 'expected_version'):
            with self.subTest(fault=fault):
                value = self.exercise(fault=fault, queries=('MODEL',))
                self.assertIsInstance(value.error, tool.Error)
                self.assertEqual(value.pedal.writes, ['PING']); self.assertEqual(value.opens, ['COM3'])
                self.assertTrue(value.pedal.closed)
                self.assertEqual(value.rows[-1]['event'], 'session_failed')
                self.assertFalse(any(r['event'] == 'session_complete' for r in value.rows))

    def test_query_error_stops_later_queries(self):
        value = self.exercise(fault='query', queries=('MODEL', 'MEM'))
        self.assertIsInstance(value.error, tool.Error); self.assertEqual(value.pedal.writes, ['PING', 'MODEL'])
        self.assertTrue(value.pedal.closed)

    def test_port_selection_error_does_not_open(self):
        for fault in ('missing', 'multiple', 'wrong_port'):
            with self.subTest(fault=fault):
                value = self.exercise(fault=fault)
                self.assertIsInstance(value.error, tool.Error); self.assertFalse(value.opens or value.pedal.writes)

    def test_open_or_close_error_is_not_success(self):
        for fault in ('open', 'close'):
            with self.subTest(fault=fault):
                value = self.exercise(fault=fault)
                self.assertIsInstance(value.error, OSError); self.assertIsNone(value.summary)
                self.assertFalse(any(r['event'] == 'session_complete' for r in value.rows))
                if fault == 'close': self.assertTrue(any(r['event'] == 'port_close_failed' for r in value.rows))

    def test_bad_profile_or_query_is_rejected_before_enumeration(self):
        value = self.exercise(fault='no_read')
        self.assertIsInstance(value.error, tool.Error); self.assertFalse(value.enum)
        for queries in (('PSAVE 0 x',), ('PING',), ('MODEL', 'MODEL')):
            with self.subTest(queries=queries):
                value = self.exercise(queries=queries)
                self.assertIsInstance(value.error, tool.Error); self.assertFalse(value.enum or value.opens)

    def test_log_existing_and_dependency_change_are_rejected_offline(self):
        with tempfile.TemporaryDirectory(dir=tool.ROOT/'build') as tmp:
            path = Path(tmp)/'old.jsonl'; path.write_bytes(b'original evidence')
            args = SimpleNamespace(port='COM3', firmware_manifest=MANIFEST, log=path, queries=[])
            with self.assertRaisesRegex(tool.Error, 'new workspace log'): tool.prepare(args)
            self.assertEqual(path.read_bytes(), b'original evidence')
            with patch.dict(tool.PINS, {'tools/probe_mini_app_host_open.py': '0'*64}):
                with self.assertRaisesRegex(tool.Error, 'dependency differs'): tool.prepare(args)

    def test_default_does_not_read_or_enumerate(self):
        with (patch.object(tool, 'prepare', side_effect=AssertionError('file read')),
              patch.object(tool.readonly, 'enumerate_ports', side_effect=AssertionError('enumeration')),
              redirect_stdout(io.StringIO()) as output):
            self.assertEqual(tool.main([]), 0)
        self.assertFalse(json.loads(output.getvalue())['inputs_read'])


if __name__ == '__main__': unittest.main()
