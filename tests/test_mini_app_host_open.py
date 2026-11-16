"""Offline CDC diagnostic tests; no serial driver or device is opened."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import probe_mini_app_host_open as host
from tests.test_mini_app_mutation import Pedal

PORT = {'device': 'COM3', 'vid': 0x3654, 'pid': 0x5155, 'description': 'OFFLINE FIXTURE'}


class DiagnosticPedal(Pedal):
    def response(self, command):
        if command == 'MEM': return ['MEM free=12345']
        if command == 'LVL': return ['LVL in=0 out=0']
        if command == 'PSTAT': return ['PSTAT preset=0 dirty=0']
        return super().response(command)


class HostOpenTests(unittest.TestCase):
    def exercise(self, *, fault=None, queries=None, check_only=False):
        pedal = DiagnosticPedal()
        if fault == 'timeout': pedal.faults[('PING', 1)] = None
        if fault == 'write': pedal.faults[('PING', 1)] = OSError('fake write timeout')
        if fault == 'wrong_PONG': pedal.faults[('PING', 1)] = ['PONG tankg_fw M5.71 rel ble Nov 15 2026']
        if fault == 'query': pedal.faults[('MODEL', 1)] = ['ERR MODEL fake']
        opened, enumerated, sleeps = [], [], []
        def enum():
            enumerated.append(True)
            if fault == 'missing': return []
            if fault == 'multiple': return [PORT, {**PORT, 'device': 'COM4'}]
            if fault == 'wrong_COM': return [{**PORT, 'device': 'COM4'}]
            return [PORT]
        def opening(name):
            opened.append(name)
            if fault == 'open': raise OSError('fake open error')
            return pedal
        def sleep(seconds): sleeps.append(seconds); pedal.clock.now += seconds
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'analysis/hardware').mkdir(parents=True); (root/'tools').mkdir()
            boot = {'finished_utc': '2026-11-16T00:00:00Z', 'reset_submitted': True,
                    'application_USB_enumerated': True, 'app_identity_verified': False,
                    'candidate_sha256': host.IMAGE_SHA, 'boot_mode': 'normal-software-boot',
                    'buttons_confirmed_by_user': False, 'held_button_boot_trial_performed': False,
                    'application_ports': [PORT]}
            if fault == 'unfinished': boot.pop('finished_utc')
            if fault == 'boot_image': boot['candidate_sha256'] = '0'*64
            (root/host.BOOT).write_text(json.dumps(boot), encoding='utf-8')
            for name in host.FAILED_LOGS:
                rows = [{'event': 'start', 'expected_image_sha256': host.IMAGE_SHA, 'expected_firmware': host.VERSION},
                        {'event': 'port_selected', 'device': 'COM3'}, {'event': 'port_opened'},
                        {'event': 'tx', 'command': 'PING'}, {'event': 'session_failed'}, {'event': 'port_closed'}]
                if fault == 'unclosed': rows.pop()
                if fault == 'old_wrong_COM': rows[1]['device'] = 'COM4'
                (root/name).write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
            (root/'tools/probe_mini_app.py').write_bytes(b'offline immutable source fixture')
            hashes = {name: host.sha((root/name).read_bytes()) for name in host.HISTORICAL_SHA}
            if fault == 'hash': hashes[host.BOOT] = '0'*64
            profile_path = root/'profile.json'; profile_path.write_bytes(b'{}')
            profile = {'image_sha256': host.IMAGE_SHA, 'firmware_version': host.VERSION, 'capabilities': {'read': True}}
            if fault == 'profile': profile['capabilities']['read'] = False
            args = SimpleNamespace(port='COM3', queries=list(host.QUERIES if queries is None else queries), log=root/'new.jsonl')
            if fault == 'existing': args.log.write_text('earlier evidence', encoding='utf-8')
            if fault == 'close': pedal.close = lambda: (_ for _ in ()).throw(OSError('fake close failure'))
            result, error, output = None, None, io.StringIO()
            with ExitStack() as stack:
                for key, value in {'ROOT': root, 'PROFILE': profile_path, 'PROFILE_SHA': host.sha(b'{}'),
                                   'HISTORICAL_SHA': hashes}.items():
                    stack.enter_context(patch.object(host, key, value))
                stack.enter_context(patch.object(host.readonly, 'load_profile', return_value=profile))
                stack.enter_context(patch.object(host.readonly, 'source_contract', return_value={'offline_fixture': True}))
                try:
                    if check_only:
                        stack.enter_context(patch.object(host.readonly, 'enumerate_ports', side_effect=AssertionError('enumeration')))
                        stack.enter_context(patch.object(host.HostOpenTransport, 'open', side_effect=AssertionError('serial open')))
                        stack.enter_context(redirect_stdout(output))
                        result = host.main(['--check-only', '--log', str(args.log)])
                    else:
                        result = host.run(args, enumerate_fn=enum, open_fn=opening, clock=pedal.clock, sleep_fn=sleep)
                except Exception as exc: error = exc
            rows = ([json.loads(x) for x in args.log.read_text().splitlines()]
                    if args.log.exists() and fault != 'existing' else [])
        return SimpleNamespace(result=result, error=error, rows=rows, pedal=pedal, opened=opened,
                               enumerated=enumerated, sleeps=sleeps, stdout=output.getvalue())

    def test_check_only_never_enumerates_or_opens(self):
        r = self.exercise(check_only=True)
        self.assertEqual(r.result, 0); self.assertFalse(r.enumerated or r.opened or r.pedal.writes)
        p = json.loads(r.stdout)
        self.assertIs(p['device_io'], False)
        self.assertIs(p['dtr_requested_before_open'], True)
        self.assertEqual(p['PING_timeout_seconds'], 3.0)

    def test_one_open_exact_PONG_then_all_literal_queries_with_raw_log_and_close(self):
        r = self.exercise()
        self.assertIsNone(r.error); self.assertEqual(r.opened, ['COM3']); self.assertEqual(r.sleeps, [1.0])
        self.assertEqual(r.pedal.writes, ['PING', *host.QUERIES])
        self.assertTrue(r.pedal.closed and r.result['serial_port_closed'])
        self.assertIs(r.result['audio_verified'], False)
        self.assertIs(r.result['held_button_boot_trial_performed'], False)
        self.assertIs(r.result['image_hash_attested_by_device'], False)
        tx = [row for row in r.rows if row['event'] == 'tx']
        self.assertEqual(tx[0]['timeout_seconds'], 3.0); self.assertEqual(tx[0]['hex'], b'PING\n'.hex())
        self.assertTrue(any(row['event'] == 'rx' and row['hex'] for row in r.rows))
        self.assertEqual(r.rows[-1]['event'], 'port_closed')
        self.assertEqual(host.readonly.PING.timeout, .7)

    def test_PING_timeout_write_error_and_wrong_identity_close_without_queries_or_retry(self):
        for fault in ('timeout', 'write', 'wrong_PONG'):
            with self.subTest(fault=fault):
                r = self.exercise(fault=fault)
                self.assertIsInstance(r.error, host.Error)
                self.assertEqual(r.pedal.writes, ['PING']); self.assertTrue(r.pedal.closed)
                self.assertEqual(r.opened, ['COM3']); self.assertEqual(r.rows[-1]['event'], 'port_closed')
                self.assertFalse(any(row['event'] == 'session_complete' for row in r.rows))

    def test_query_failure_stops_subsequent_queries(self):
        r = self.exercise(fault='query')
        self.assertIsInstance(r.error, host.Error); self.assertEqual(r.pedal.writes, ['PING', 'MODEL'])
        self.assertTrue(r.pedal.closed)

    def test_bad_evidence_or_query_stops_before_enumeration(self):
        for fault in ('unfinished', 'boot_image', 'unclosed', 'old_wrong_COM', 'hash', 'profile', 'existing'):
            with self.subTest(fault=fault):
                r = self.exercise(fault=fault)
                self.assertIsInstance(r.error, host.Error); self.assertFalse(r.enumerated or r.opened)
        for queries in (['MODEL', 'MODEL'], ['PSAVE 0 x'], ['PING']):
            r = self.exercise(queries=queries)
            self.assertIsInstance(r.error, host.Error); self.assertFalse(r.enumerated or r.opened)

    def test_unique_current_CDC_and_exact_COM_required(self):
        for fault in ('missing', 'multiple', 'wrong_COM'):
            with self.subTest(fault=fault):
                r = self.exercise(fault=fault)
                self.assertIsInstance(r.error, host.Error); self.assertFalse(r.opened or r.pedal.writes)

    def test_open_and_close_errors_are_not_reported_as_completed_return(self):
        r = self.exercise(fault='open'); self.assertIsInstance(r.error, OSError)
        self.assertFalse(r.pedal.writes); self.assertEqual(len(r.opened), 1)
        r = self.exercise(fault='close'); self.assertIsInstance(r.error, OSError)
        self.assertIsNone(r.result); self.assertEqual(r.rows[-1]['event'], 'port_close_failed')

    def test_serial_settings_before_single_open_and_cleanup_on_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                events = []
                class Port:
                    def __setattr__(self, key, value): events.append(('set', key, value)); object.__setattr__(self, key, value)
                    def open(self):
                        events.append(('open',))
                        if fail: raise OSError('mock failure')
                    def close(self): events.append(('close',))
                def factory(**kwargs):
                    self.assertIsNone(kwargs['port']); self.assertFalse(kwargs['dsrdtr'] or kwargs['rtscts'])
                    self.assertEqual(kwargs['write_timeout'], 1)
                    return Port()
                serial = SimpleNamespace(Serial=factory, EIGHTBITS=8, PARITY_NONE='N', STOPBITS_ONE=1)
                with patch.dict(sys.modules, {'serial': serial}):
                    if fail:
                        with self.assertRaises(OSError): host.HostOpenTransport.open('COM3')
                    else: host.HostOpenTransport.open('COM3').close()
                self.assertEqual(events, [('set', 'dtr', True), ('set', 'rts', False),
                                          ('set', 'port', 'COM3'), ('open',), ('close',)])


if __name__ == '__main__': unittest.main()
