"""Offline transport and real-editor contracts; never enumerate/open a device."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import probe_mini_app as app
from tools.build_mini_app import build, load_profile

PONG = b'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11\r\n'
VERSION = 'tankm_fw M5.71 rel ble'


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class Transport:
    def __init__(self, responses, clock, initial=()):
        self.responses = dict(responses)
        self.clock = clock
        self.pending = list(initial)
        self.writes, self.closed, self.short = [], False, False

    def write(self, value):
        self.writes.append(value)
        response = self.responses.get(value, ())
        if isinstance(response, Exception):
            raise response
        self.pending += [response] if isinstance(response, bytes) else list(response)
        return len(value)-1 if self.short else len(value)

    def read(self, size):
        self.clock.now += .01
        if self.pending:
            result = self.pending.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        return b''

    def close(self):
        self.closed = True


def make_probe(responses=None, initial=()):
    clock, events = Clock(), []
    transport = Transport({b'PING\n': PONG, **(responses or {})}, clock, initial)
    probe = app.ReadOnlyProbe(transport, VERSION, clock=clock,
                             log=lambda event, **fields: events.append({'event': event, **fields}))
    return probe, transport, clock, events


class MiniAppTransportTests(unittest.TestCase):
    def test_import_and_default_cli_have_no_serial_side_effect(self):
        # Fresh module import with serial imports turned into hard failures.
        original = __import__
        def guarded(name, *args, **kwargs):
            if name == 'serial' or name.startswith('serial.'):
                raise AssertionError('serial imported during offline default')
            return original(name, *args, **kwargs)
        spec = importlib.util.spec_from_file_location('mini_probe_import_check', app.__file__)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            with patch('builtins.__import__', side_effect=guarded):
                spec.loader.exec_module(module)
                with patch.object(module, 'enumerate_ports', side_effect=AssertionError('enumerated')):
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        self.assertEqual(module.main([]), 0)
            result = json.loads(output.getvalue())
            self.assertFalse(result['device_io'])
            self.assertFalse(result['enumerated'])
        finally:
            del sys.modules[spec.name]

    def test_exact_usb_identity_separates_stock_and_rom_before_open(self):
        rows = [app.port_record(SimpleNamespace(device='COM8', vid=0x3654, pid=0x5155)),
                app.port_record(SimpleNamespace(device='COM9', vid=0x4c4a, pid=0xc755)),
                app.port_record(SimpleNamespace(device='COM10', vid=0x4c4a, pid=0x8057)),
                app.port_record(SimpleNamespace(device='COM11', vid=0x3654, pid=0x4155))]
        self.assertEqual(app.select_port(rows, 'COM8')['pid'], 0x5155)
        self.assertIn('stock', rows[1]['role'])
        for name in ('COM9', 'COM10', 'COM11', 'COM404'):
            with self.subTest(name=name), self.assertRaises(app.AppProbeError):
                app.select_port(rows, name)
        with self.assertRaises(app.AppProbeError):
            app.select_port(rows+rows[:1], 'COM8')

    def test_queries_require_accepted_mini_and_never_accept_command_arguments(self):
        probe, tr, _, _ = make_probe({b'MEM\n': b'MEM used=128 free=1024\n'})
        self.assertEqual(tr.writes, [])
        with self.assertRaises(app.AppProbeError):
            probe.query('MEM')
        probe.identify()
        for request in ('PSAVE 0 test', 'FXP 1 0 50', 'SNAPNAME 0 x', 'GAIN 0 0', 'UBOOT',
                        'MEM\nPSAVE 0 test', 'MEM\0', ' MEM', 'MEM ', 'PING'):
            with self.subTest(request=request), self.assertRaises(app.AppProbeError):
                probe.query(request)
        self.assertEqual(tr.writes, [b'PING\n'])
        probe.query('MEM')
        self.assertEqual(tr.writes, [b'PING\n', b'MEM\n'])

    def test_wrong_board_version_and_unstructured_pong_prevent_all_queries(self):
        responses = [b'PONG tankg_fw M5.71 rel ble Nov 12 2026 16:04:11\n',
                     b'PONG tankb_fw M5.71 rel ble Nov 12 2026 16:04:11\n',
                     b'PONG tankm_fw M5.70 rel ble Nov 12 2026 16:04:11\n',
                     b'PONG tankm_fw M5.71 rel ble tankb Nov 12 2026 16:04:11\n',
                     b'PONG tankm_fw\n', b'TANK MINI_009\n']
        for response in responses:
            probe, tr, _, _ = make_probe({b'PING\n': response})
            with self.subTest(response=response), self.assertRaises(app.AppProbeError):
                probe.identify()
            with self.assertRaises(app.AppProbeError):
                probe.query('MEM')
            self.assertEqual(tr.writes, [b'PING\n'])

    def test_fragmented_utf8_crlf_and_original_async_lines_are_separate(self):
        text = "@L c=4\r\nNOISE ms=10\nCALIB db=-30\nERR CALIB stopped\nMODEL Café\r\n".encode()
        chunks = [text[i:i+1] for i in range(len(text))]
        probe, tr, _, events = make_probe({b'MODEL\n': chunks})
        probe.identify()
        result = probe.query('MODEL')
        self.assertEqual(result['lines'], ['MODEL Café'])
        self.assertEqual(len(result['asynchronous_lines']), 4)
        self.assertEqual(sum(e['event'] == 'async_line' for e in events), 4)
        self.assertEqual(tr.writes[-1], b'MODEL\n')

    def test_real_fxs_terminator_is_peak_or_pico_not_end(self):
        for terminal in (b'FXS peak=0\n', b'FXS pico=0\n'):
            probe, _, _, _ = make_probe({b'FXS\n': [b'FXS end\n', b'FXS peaks=bad\n', terminal]})
            probe.identify()
            result = probe.query('FXS')
            self.assertEqual(result['lines'][-1], terminal.decode().strip())
            self.assertEqual(len(result['lines']), 3)

    def test_timeout_is_terminal_and_late_reply_cannot_satisfy_another_query(self):
        probe, tr, _, events = make_probe({b'FXS\n': b'FXS end\n'})
        probe.identify()
        with self.assertRaisesRegex(app.AppProbeError, 'timeout'):
            probe.query('FXS')
        tr.pending.append(b'FXS peak=0\n')
        with self.assertRaisesRegex(app.AppProbeError, 'already failed'):
            probe.query('MODEL')
        self.assertEqual(tr.writes, [b'PING\n', b'FXS\n'])
        self.assertTrue(any(e['event'] == 'failed' and e['retries'] == 0 for e in events))

    def test_stale_complete_and_partial_data_are_logged_then_discarded(self):
        probe, tr, _, events = make_probe(
            {b'MEM\n': b'MEM used=7\nMODEL stale partial', b'MODEL\n': b'MODEL fresh\n'},
            initial=(PONG.replace(b'tankm', b'tankg'),))
        probe.identify()
        probe.query('MEM')
        result = probe.query('MODEL')
        self.assertEqual(result['lines'], ['MODEL fresh'])
        self.assertTrue(any(e['event'] == 'stale_rx' for e in events))
        self.assertTrue(any(e['event'] == 'stale_buffer' for e in events))
        self.assertEqual(len(tr.writes), 3)

    def test_error_short_write_bad_utf8_oversize_and_disconnect_poison_session(self):
        failures = [b'ERR MEM unavailable\n', b'MEM \xff\n', b'MEM\0bad\n',
                    b'x'*(app.MAX_LINE+1), OSError('USB disconnected')]
        for response in failures:
            probe, tr, _, _ = make_probe({b'MEM\n': response})
            probe.identify()
            with self.subTest(response=str(response)[:30]), self.assertRaises(app.AppProbeError):
                probe.query('MEM')
            self.assertTrue(probe.failed)
            with self.assertRaises(app.AppProbeError):
                probe.query('MODEL')
            self.assertEqual(len(tr.writes), 2)
        probe, tr, _, _ = make_probe()
        tr.short = True
        with self.assertRaisesRegex(app.AppProbeError, 'partial'):
            probe.identify()
        self.assertTrue(probe.failed)

    def test_incoherent_preset_list_is_never_treated_as_empty_or_retried(self):
        cases = [b'PLIST end current=4\n', b"PRE 0 1 0 0 'one'\nPRE 0 1 0 0 'two'\nPLIST end current=0\n",
                 b"PRE 32 1 0 0 'outside'\nPLIST end current=-1\n", b'PLIST end truncated\n']
        for response in cases:
            probe, tr, _, _ = make_probe({b'PLIST\n': response})
            probe.identify()
            with self.assertRaisesRegex(app.AppProbeError, 'preset list'):
                probe.query('PLIST')
            self.assertEqual(tr.writes, [b'PING\n', b'PLIST\n'])
            self.assertTrue(probe.failed)

    def test_plist_parser_matches_executed_original_javascript(self):
        source = app.checked(app.SOURCE/'web/tankg.html', app.SOURCE_SHA).decode('utf-8')
        snippet = source.split('/*PLIST-BEGIN*/', 1)[1].split('/*PLIST-END*/', 1)[0]
        cases = [["PRE 0 2 -1 0 'Café' t=p1,q2a s=3 col=a1b2c3 amp=1", 'PLIST end current=0'],
                 ['PLIST fin actual=-1'], ["PRE 1 0 0 0 'x'", 'PLIST end current=0'],
                 ["PRE 0 0 0 0 '"+'😀'*12+"'", 'PLIST end current=-1'],
                 ["PRE 1 0 0 0 'a'", "PRE 0 0 0 0 'b'", 'PLIST end current=1'],
                 ['PLIST end current=-1', 'PLIST end current=-1']]
        script = "const fs=require('fs');"+snippet+"\nprocess.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(parsePlist)));"
        run = subprocess.run(['node', '-e', script], input=json.dumps(cases), text=True,
                             encoding='utf-8', capture_output=True, check=True, cwd=app.ROOT)
        original = json.loads(run.stdout)
        for lines, expected in zip(cases, original):
            parsed = app.parse_plist(lines)
            self.assertEqual((parsed['ok'], parsed['reason'], parsed['current']),
                             (expected['ok'], expected['why'], expected['cur']))
            self.assertEqual([p['slot'] for p in parsed['presets']], [p[0] for p in expected['list']])

    def test_actual_candidate_build_manifest_enables_reads_without_hardware_gate(self):
        image = app.ROOT/'build/mini-ultrarig/hyperrig-mini-g-derived.app.bin'
        self.assertTrue(image.is_file(), 'offline complete-application candidate missing')
        with tempfile.TemporaryDirectory(prefix='mini-cdc-readcheck-', dir=app.ROOT/'build') as temp:
            root = Path(temp).resolve()
            self.assertTrue(root.is_relative_to((app.ROOT/'build').resolve()))
            manifest = root/'firmware-manifest.json'
            spec = {'target': 'tank-mini', 'architecture': 'standalone-ultrarig-port',
                    'firmware_version': VERSION, 'image_path': image.relative_to(app.ROOT).as_posix(),
                    'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                    'capabilities': {'read': True, 'write': False, 'panel': False}, 'hardware_verified': False}
            manifest.write_text(json.dumps(spec), encoding='utf-8')
            result = build(root/'editor', manifest, root/'build-report.json')
            self.assertTrue(result['profile']['capabilities']['read'])
            self.assertFalse(result['profile']['capabilities']['write'])
            self.assertFalse(result['profile']['hardware_verified'])
            self.assertFalse(result['profile']['write_validation'])
            self.assertEqual(load_profile(manifest)['image_sha256'], spec['image_sha256'])
            script = r"""
const fs=require('fs'),vm=require('vm');
const context=vm.createContext({HYPERRIG_MINI_BUILD:JSON.parse(fs.readFileSync(0,'utf8'))});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),context);
const m=context.HyperRigMini;
process.stdout.write(JSON.stringify({pong:m.acceptPong('PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'),
 read:m.commandPolicy('PLIST'),write:m.commandPolicy('PSAVE 0 test')}));
"""
            run = subprocess.run(['node', '-e', script], input=json.dumps(result['profile']),
                                 text=True, capture_output=True, check=True, cwd=app.ROOT)
            policy = json.loads(run.stdout)
            self.assertTrue(policy['pong']['ok'] and policy['read']['allowed'])
            self.assertFalse(policy['write']['allowed'])

    def test_cli_session_logs_and_closes_on_success_and_wrong_identity(self):
        profile = {'firmware_version': VERSION, 'image_sha256': 'a'*64,
                   'capabilities': {'read': True}}
        with tempfile.TemporaryDirectory(prefix='mini-cdc-log-', dir=app.ROOT/'build') as temp:
            root = Path(temp).resolve()
            self.assertTrue(root.is_relative_to((app.ROOT/'build').resolve()))
            args = argparse.Namespace(firmware_manifest=root/'unused.json', port='COM8',
                                      log=root/'success.jsonl', queries=['MEM'])
            ports = [app.port_record(SimpleNamespace(device='COM8', vid=app.VID, pid=app.PID))]
            clock = Clock()
            transport = Transport({b'PING\n': PONG, b'MEM\n': b'MEM used=64\n'}, clock)
            with patch.object(app, 'load_profile', return_value=profile):
                result = app.run_read(args, enumerate_fn=lambda: ports,
                                      open_fn=lambda name: transport, clock=clock)
            self.assertTrue(result['read_only_session_completed'] and transport.closed)
            events = [json.loads(l) for l in args.log.read_text().splitlines()]
            self.assertEqual(events[-1]['event'], 'port_closed')
            self.assertFalse(result['image_hash_attested_by_device'])
            with self.assertRaises(FileExistsError), patch.object(app, 'load_profile', return_value=profile):
                app.run_read(args, enumerate_fn=lambda: self.fail('enumeration before logfile refusal'))
            args.log = root/'wrong.jsonl'
            clock = Clock(); transport = Transport({b'PING\n': PONG.replace(b'tankm', b'tankg')}, clock)
            with patch.object(app, 'load_profile', return_value=profile), self.assertRaises(app.AppProbeError):
                app.run_read(args, enumerate_fn=lambda: ports, open_fn=lambda name: transport, clock=clock)
            self.assertTrue(transport.closed)
            self.assertEqual(transport.writes, [b'PING\n'])

    def test_pyserial_open_is_explicit_configured_and_closes_on_error(self):
        calls = []
        class Port:
            def __init__(self, **settings):
                self.settings = settings; calls.append('construct')
                self.is_open = False
            def open(self):
                self.assertions = (self.port, self.dtr, self.rts, self.settings)
                calls.append('open'); self.is_open = True
            def close(self): calls.append('close')
        module = SimpleNamespace(Serial=Port, EIGHTBITS=8, PARITY_NONE='N', STOPBITS_ONE=1)
        with patch.dict(sys.modules, serial=module):
            self.assertEqual(calls, [])
            transport = app.SerialTransport.open('COM8')
        self.assertEqual(calls, ['construct', 'open'])
        name, dtr, rts, settings = transport.port.assertions
        self.assertEqual((name, dtr, rts), ('COM8', False, False))
        self.assertIsNone(settings['port'])
        self.assertEqual((settings['baudrate'], settings['timeout'], settings['write_timeout']), (115200, .05, 1))
        transport.close()
        self.assertEqual(calls[-1], 'close')


if __name__ == '__main__':
    unittest.main()
