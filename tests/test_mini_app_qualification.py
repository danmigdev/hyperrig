"""Offline evidence binding tests. Temporary physical-schema fixtures are fake.

No fixture is retained as hardware evidence. No device/browser is opened.
"""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import qualify_mini_app as q
from tools import probe_mini_app as ro
from tools import probe_mini_app_first_preset as first
from tools import build_mini_app as app
from tests.test_mini_app_mutation import Pedal
from tests.test_mini_app_first_preset import FirstPedal

PORT = {'device': 'COM123', 'vid': ro.VID, 'pid': ro.PID, 'description': 'TEST FIXTURE'}


class ReadPedal(Pedal):
    def response(self, cmd):
        extra = {'MEM': ['MEM used=128 free=1024'], 'LVL': ['LVL in=0 out=0'], 'PSTAT': ['PSTAT ok']}
        return extra[cmd] if cmd in extra else super().response(cmd)


def fixture_boot():
    ref = {'path': 'build/TEST-INSTALL.json', 'sha256': 'a'*64}
    common = {'candidate_sha256': q.IMAGE_SHA, 'reset_submitted': True, 'firmware_write': False,
              'automatic_retry': False, 'installation_evidence_path': ref['path'],
              'installation_evidence_sha256': ref['sha256']}
    held = {**common, 'started_utc': '2020-01-01T00:00:01Z', 'finished_utc': '2020-01-01T00:00:02Z',
        'buttons_confirmed_by_user': 'held', 'phase': 'fresh_ROM_observed', 'fresh_ROM_verified': True,
        'arrival_before': {'arrival_utc': '2020-01-01T00:00:00Z'},
        'arrival_after': [{'arrival_utc': '2020-01-01T00:00:02Z'}],
        'fresh_inquiry': {'vendor': 'WL82', 'product': 'UBOOT1.00'}}
    released = {**common, 'started_utc': '2020-01-01T00:00:03Z', 'finished_utc': '2020-01-01T00:00:04Z',
        'buttons_confirmed_by_user': 'released', 'phase': 'application_USB_observed',
        'application_USB_enumerated': True, 'arrival_before': copy.deepcopy(held['arrival_after'][0]),
        'application_ports': [PORT]}
    return {'finished_utc': '2020-01-01T00:00:00Z'}, ref, held, released


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=q.ROOT/'build', prefix='TEST-app-qualification-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def trace(self):
        pedal = ReadPedal()
        path = self.directory/'read.jsonl'
        args = argparse.Namespace(firmware_manifest=q.BASE, log=path, port=PORT['device'], queries=sorted(q.REQUIRED_READS))
        ro.run_read(args, enumerate_fn=lambda: [PORT], open_fn=lambda _: pedal, clock=pedal.clock)
        self.assertTrue(pedal.closed)
        return path.read_bytes()

    def test_default_reads_no_inputs_or_devices(self):
        with (patch.object(q.installed, 'inspect_bundle', side_effect=AssertionError('read evidence')),
              patch.object(ro, 'enumerate_ports', side_effect=AssertionError('device enumeration'))):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(q.main([]), 0)
        value = json.loads(output.getvalue())
        self.assertFalse(value['inputs_read'] or value['device_io'])

    def test_boot_binding_and_each_missing_prerequisite(self):
        base = fixture_boot()
        self.assertEqual(q.validate_boot(*base), PORT)
        changes = [(2, 'candidate_sha256', 'b'*64), (2, 'installation_evidence_sha256', 'b'*64),
            (2, 'reset_submitted', False), (2, 'error', 'failed'), (2, 'fresh_ROM_verified', False),
            (3, 'application_USB_enumerated', False), (3, 'application_ports', [PORT, PORT]),
            (3, 'arrival_before', {'arrival_utc': '2020-01-02T00:00:00Z'}),
            (3, 'started_utc', '2019-01-01T00:00:00Z')]
        for index, name, value in changes:
            broken = copy.deepcopy(base); broken[index][name] = value
            with self.subTest(name=name), self.assertRaises(ValueError): q.validate_boot(*broken)

    def test_exact_read_replay_and_current_saved_preset_path(self):
        result = q.validate_read_trace(self.trace(), PORT, fixture_boot()[3])
        self.assertEqual(result['PLIST']['current'], 0)
        self.assertEqual(result['preset_trial_path'], 'existing-preset-restore')
        self.assertFalse(result['audio_verified'] or result['BLE_verified'] or result['preset_writes_verified'])

    def test_read_trace_rejects_partial_wrong_port_raw_and_claims(self):
        rows = [json.loads(x) for x in self.trace().splitlines()]
        variants = []
        variants.append(rows[:-1])
        for event, key, value in [('start', 'expected_image_sha256', '0'*64),
                ('port_selected', 'device', 'COM999'), ('session_complete', 'audio_verified', True),
                ('session_complete', 'commands', ['PING']), ('identity_accepted', 'pong', 'PONG false')]:
            broken = copy.deepcopy(rows); next(x for x in broken if x['event'] == event)[key] = value
            variants.append(broken)
        broken = copy.deepcopy(rows); next(x for x in broken if x['event'] == 'rx')['hex'] = b'WRONG'.hex(); variants.append(broken)
        broken = copy.deepcopy(rows); broken.insert(-1, {'event': 'session_failed'}); variants.append(broken)
        for index, broken in enumerate(variants):
            with self.subTest(index=index), self.assertRaises((ValueError, ro.AppProbeError, first.Error, KeyError)):
                q.validate_read_trace(b'\n'.join(json.dumps(x).encode() for x in broken), PORT, fixture_boot()[3])

    def test_mock_first_preset_report_cannot_qualify_families(self):
        read_manifest = self.directory/'read-manifest.json'
        evidence = {'kind': 'mini-app-usb-read-qualification', 'boot_USB_read_verified': True,
            'image_sha256': q.IMAGE_SHA, 'evidence': {key: q.reference(q.BASE) for key in ('installation','held','released','read_log')},
            'implementation': q.reference(Path(q.__file__)), 'base_manifest': q.reference(q.BASE),
            'verifier_sources': [q.reference(Path(module.__file__)) for module in (q.installed,ro,first,q.mutation,app)]}
        q.write_new(self.directory/'read-proof.json', evidence)
        spec = json.loads(q.BASE.read_bytes()); spec['hardware_verified'] = True
        spec['hardware_validation'] = q.reference(self.directory/'read-proof.json')
        q.write_new(read_manifest, spec)
        pedal = FirstPedal(empty_chain=True)
        args = argparse.Namespace(firmware_manifest=read_manifest, port=PORT['device'], slot=0,
            operation='auto', block=None, parameter=None, log=self.directory/'first.jsonl',
            backup=self.directory/'before.json', report=self.directory/'trial.json')
        report = first.run_create(args, enumerate_fn=lambda: [PORT], open_fn=lambda _: pedal, clock=pedal.clock)
        self.assertEqual(report['kind'], first.KIND)
        self.assertFalse(report['hardware_executed'])
        with self.assertRaisesRegex(ValueError, 'physical USB trial'):
            q.qualify_families(read_manifest, [args.report], self.directory/'families.json')
        self.assertFalse((self.directory/'families.json').exists())

    def test_validated_schema_fixture_enables_actual_families_only(self):
        # Same fake as above, explicitly converted to temporary schema evidence.
        read_manifest = self.directory/'read-manifest.json'
        evidence = {'kind': 'mini-app-usb-read-qualification', 'boot_USB_read_verified': True,
            'image_sha256': q.IMAGE_SHA, 'evidence': {key: q.reference(q.BASE) for key in ('installation','held','released','read_log')},
            'implementation': q.reference(Path(q.__file__)), 'base_manifest': q.reference(q.BASE),
            'verifier_sources': [q.reference(Path(module.__file__)) for module in (q.installed,ro,first,q.mutation,app)]}
        q.write_new(self.directory/'read-proof.json', evidence)
        spec = json.loads(q.BASE.read_bytes()); spec['hardware_verified'] = True
        spec['hardware_validation'] = q.reference(self.directory/'read-proof.json')
        q.write_new(read_manifest, spec)
        pedal = FirstPedal(empty_chain=True)
        args = argparse.Namespace(firmware_manifest=read_manifest, port=PORT['device'], slot=0,
            operation='auto', block=None, parameter=None, log=self.directory/'first.jsonl',
            backup=self.directory/'before.json', report=self.directory/'trial.json')
        report = first.run_create(args, enumerate_fn=lambda: [PORT], open_fn=lambda _: pedal, clock=pedal.clock)
        rows = [json.loads(x) for x in args.log.read_text().splitlines()]
        rows[0]['hardware_executed'] = True
        args.log.write_bytes(b'\n'.join(json.dumps(x).encode() for x in rows)+b'\n')
        backup = json.loads(args.backup.read_bytes()); backup['hardware_executed'] = True
        args.backup.write_text(json.dumps(backup))
        report = first.first_evidence(report['trial'], app.load_profile(read_manifest), trace=q.reference(args.log),
            backup=q.reference(args.backup), hardware_executed=True)
        args.report.write_text(json.dumps(report))
        output = self.directory/'families.json'
        result = q.qualify_families(read_manifest, [args.report], output)
        self.assertEqual(result['usb_families'], ['GAIN', 'PLOAD', 'PSAVE', 'SNAP', 'SNAPSAVE'])
        self.assertEqual(result['BLE_families'], [])
        self.assertFalse(result['blanket_write'])
        profile = app.load_profile(output)
        self.assertFalse(profile['capabilities']['write'])
        self.assertNotIn('FXP', profile['family_capabilities']['usb-cdc'])
        with self.assertRaisesRegex(ValueError, 'new manifest'): q.qualify_families(read_manifest, [args.report], output)

    def test_manifest_creation_is_separate_and_failure_creates_nothing(self):
        install, _, held, released = fixture_boot()
        install_path, held_path, released_path = [self.directory/name for name in ('install.json','held.json','released.json')]
        q.write_new(install_path, install)
        for item in (held, released):
            ref = q.reference(install_path)
            item.update(installation_evidence_path=ref['path'], installation_evidence_sha256=ref['sha256'],
                source_pins={'tools/probe_mini_app.py':q.sha(Path(ro.__file__).read_bytes())})
        q.write_new(held_path, held); q.write_new(released_path, released)
        self.trace(); output = self.directory/'derived'
        before = q.BASE.read_bytes()
        with patch.object(q.installed, 'inspect_bundle', return_value={'verified':True, 'TEST_FIXTURE':True}) as check:
            result = q.qualify_read(install_path,held_path,released_path,self.directory/'read.jsonl',output)
        check.assert_called_once_with(install_path)
        profile = app.load_profile(output/'firmware-manifest.json')
        self.assertTrue(profile['hardware_verified'] and profile['capabilities']['read'])
        self.assertFalse(profile['capabilities']['write'])
        self.assertEqual(profile['family_capabilities'], {})
        self.assertEqual(q.BASE.read_bytes(), before)
        self.assertEqual(result['preset_trial_path'], 'existing-preset-restore')
        with self.assertRaisesRegex(ValueError, 'new output directory'):
            q.qualify_read(install_path,held_path,released_path,self.directory/'read.jsonl',output)
        with patch.object(q.installed, 'inspect_bundle', side_effect=ValueError('unfinished install')):
            with self.assertRaisesRegex(ValueError, 'unfinished'):
                q.qualify_read(install_path,held_path,released_path,self.directory/'read.jsonl',self.directory/'blocked')
        self.assertFalse((self.directory/'blocked').exists())


if __name__ == '__main__': unittest.main()
