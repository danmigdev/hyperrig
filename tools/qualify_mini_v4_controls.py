"""Bounded v4 USB controls trial with a new temporary preset and state readback.

No device access on import or without --execute. Existing presets are never
written or deleted. A failed or ambiguous exchange stops without a retry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_app_cdc_handshake as cdc
from tools import probe_mini_app_mutation as protocol

IMAGE = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
VERSION = 'tankm_fw M5.71 rel ble'
FAMILIES = ['GAIN', 'PLOAD', 'PSAVE', 'SNAPSAVE', 'FXA', 'FXP', 'FXE', 'FXR', 'SNAP']
require = protocol.require
NAME = 'HyperRig_USB_Test'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True)
        stream.write('\n')


def plan(snapshot, types):
    require(snapshot['plist']['ok'] and snapshot['plist']['current'] >= 0,
            'A coherent saved current preset is required')
    require(not snapshot['fxs']['blocks'] and not snapshot['fxs']['mix'] and not snapshot['fxs']['xo'],
            'This bounded trial requires the observed empty serial chain')
    require(snapshot['snaps']['current'] in (1, 2, 3) and snapshot['snaps']['present'] == '1111',
            'Four existing scenes and a selected scene other than zero are required')
    occupied = {p['slot'] for p in snapshot['plist']['presets']}
    slot = next((n for n in range(31, -1, -1) if n not in occupied), None)
    require(slot is not None, 'A free temporary preset is required')
    gate = types.get('gate', {}).get('params', {})
    require(gate.get(0, {}).get('name') == 'umbral_db' and gate[0]['min'] <= -69 <= gate[0]['max']
            and gate[0]['default'] == -70, 'The observed gate catalog differs')
    gain = snapshot['extra']['gain_db']
    require(all(type(n) is int and -29 <= n <= 12 for n in gain), 'Cannot safely attenuate the observed gain')
    return {'slot': slot, 'original_slot': snapshot['plist']['current'],
            'original_scene': snapshot['snaps']['current'], 'gain': gain,
            'trial_gain': [gain[0], gain[1] - 1], 'temporary_name': NAME}


class Trial:
    def __init__(self, wire, directory):
        self.probe = protocol.PresetMutationProbe(wire.transport, VERSION, log=wire.log)
        self.probe.wire = wire
        self.directory = directory
        self.observations = []

    def snapshot(self):
        return self.probe._snapshot()[0]

    def command(self, command, pattern, *, end=None, timeout=4):
        wire = self.probe.wire
        try:
            require(wire.identity is not None and not wire.failed, 'An identified healthy session is required')
            spec = FxQuery(command, timeout, ()) if command == 'FXA Q 99 gate' else cdc.readonly.Query(command, timeout, (end or command.split()[0],))
            response = wire._exchange(spec)
            require(not response['asynchronous_lines'], 'Unexpected asynchronous activity')
            require(re.fullmatch(pattern, '\n'.join(response['lines'])), 'Unexpected acknowledgement for ' + command)
            record = {'command': command, 'response': response['lines'], 'readback_verified': False}
            self.observations.append(record)
            return record
        except Exception:
            wire.failed = True
            raise

    def check(self, record, observed, expected):
        require(observed == expected, 'Unrelated state changed or requested state was not read back: ' + record['command'])
        record.update(readback_verified=True, state_sha256=protocol.digest(observed))

    def gain(self, before, values):
        record = self.command(f'GAIN {values[0]} {values[1]}', rf'GAIN in={values[0]} out={values[1]} dB')
        expected = copy.deepcopy(before)
        expected['extra']['gain_db'] = list(values)
        after = self.snapshot()
        self.check(record, after, expected)
        return after

    def load(self, slot, name, scene, expected):
        record = self.command(f'PLOAD {slot}', rf"PLOAD ok {slot} '{re.escape(name)}' missing=0 capture=(-?\d+) ir=(-?\d+) ms=\d+", timeout=8)
        loaded = self.snapshot()
        require(loaded['plist']['current'] == slot and loaded['plist']['presets'] == expected['plist']['presets'],
                'PLOAD inventory or selected slot differs')
        snap = self.command(f'SNAP {scene}', rf'SNAP ok {scene} missing=0 ms=\d+')
        after = self.snapshot()
        self.check(snap, after, expected)
        self.check(record, after, expected)
        return after

    def run(self):
        catalog = self.probe._query('FXT')
        types = protocol.parse_fxt(catalog['lines'])
        baseline = self.snapshot()
        selection = plan(baseline, types)
        write_json(self.directory / 'baseline.json', {'state': baseline, 'FXT': catalog, 'plan': selection})
        require(self.snapshot() == baseline, 'State changed before the trial')
        state = self.gain(baseline, selection['trial_gain'])
        self.gain(state, selection['gain'])

        added = self.command('FXA Q 99 gate', r'FXA id=\d+ gate\nFX cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+ B', end='FX cpu=')
        # The shared FX resource line completes this two-line response.
        state = self.snapshot()
        require(len(state['fxs']['blocks']) == 1, 'Expected exactly one newly added effect')
        block = state['fxs']['blocks'][0]
        require(added['response'][0] == f"FXA id={block['id']} gate" and block['bank'] == 'Q'
                and block['position'] == 0 and block['type'] == 'gate' and block['on'] == 1
                and block['params'][:2] == [-70, 120], 'Added effect differs from FXT and acknowledgement')
        expected = copy.deepcopy(baseline)
        expected['fxs']['blocks'] = [copy.deepcopy(block)]
        self.check(added, state, expected)
        for value in (-69, -70):
            record = self.command(f"FXP {block['id']} 0 {value}", rf'FXP ok {value}')
            expected['fxs']['blocks'][0]['params'][0] = value
            state = self.snapshot()
            self.check(record, state, expected)
        for value in (0, 1):
            record = self.command(f"FXE {block['id']} {value}", r'FXE ok cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+ B')
            expected['fxs']['blocks'][0]['on'] = value
            state = self.snapshot()
            self.check(record, state, expected)
        record = self.command(f"FXR {block['id']}", r'FXR ok cpu=\d+/\d+ ticks \(\d+%\) mem_fx=\d+ B')
        self.check(record, self.snapshot(), baseline)

        slot = selection['slot']
        require(all(p['slot'] != slot for p in self.snapshot()['plist']['presets']), 'Temporary slot became occupied')
        saved = self.command(f'PSAVE {slot} {NAME}', rf"PSAVE ok {slot} '{NAME}' 0 blocks capture=(-?\d+) ir=(-?\d+)", timeout=8)
        state = self.snapshot()
        entry = [p for p in state['plist']['presets'] if p['slot'] == slot]
        require(len(entry) == 1 and entry[0]['name'] == NAME and entry[0]['blocks'] == 0, 'Temporary preset is missing')
        expected = copy.deepcopy(baseline)
        expected['plist']['current'] = slot
        expected['plist']['presets'] = sorted(baseline['plist']['presets'] + entry, key=lambda p: p['slot'])
        expected['extra']['color_preset'] = slot
        self.check(saved, state, expected)
        self.gain(state, selection['trial_gain'])
        state = self.load(slot, NAME, selection['original_scene'], expected)
        saved['persistence_readback_verified'] = True

        state = self.gain(state, selection['trial_gain'])
        scene = self.command('SNAPSAVE 0', rf'SNAPSAVE ok 0 preset={slot}')
        scene_expected = copy.deepcopy(state)
        scene_expected['snaps']['current'] = 0
        state = self.snapshot()
        self.check(scene, state, scene_expected)
        self.gain(state, selection['gain'])
        state = self.load(slot, NAME, 0, scene_expected)
        scene['persistence_readback_verified'] = True

        restore_expected = copy.deepcopy(baseline)
        restore_expected['plist']['presets'] = expected['plist']['presets']
        original_name = next(p['name'] for p in baseline['plist']['presets'] if p['slot'] == selection['original_slot'])
        self.load(selection['original_slot'], original_name, selection['original_scene'], restore_expected)
        require(self.snapshot() == restore_expected and slot != selection['original_slot'], 'Cleanup witness differs')
        deleted = self.command(f'PDEL {slot}', rf'PDEL ok {slot}')
        final = self.snapshot()
        self.check(deleted, final, baseline)
        require({x['command'].split()[0] for x in self.observations} == set(FAMILIES) | {'PDEL'}, 'Trial family coverage differs')
        return {'kind': 'hyperrig-mini-v4-controls-trial', 'result': 'pass', 'hardware_executed': True,
                'image_sha256': IMAGE, 'firmware_version': VERSION, 'device_binary_hash_attestation': False,
                'baseline_restoration_verified': True, 'temporary_slot_deleted': True,
                'preexisting_presets_written': False, 'observations': self.observations,
                'enabled_families': FAMILIES, 'baseline_sha256': protocol.digest(baseline),
                'final_sha256': protocol.digest(final), 'final_state': final,
                'physical_UI_tested': False, 'audio_tested': False, 'automatic_retry': False,
                'source_sha256': {str(Path(__file__).relative_to(ROOT)).replace('\\', '/'): sha(Path(__file__).read_bytes()),
                                  'tools/probe_mini_app_mutation.py': sha(Path(protocol.__file__).read_bytes())}}


class FxQuery(cdc.readonly.Query):
    def complete(self, line):
        return line.startswith('FX cpu=')


def execute(directory, port):
    require(not directory.exists() and directory.parent.is_dir(), 'Use a new report directory')
    association_path = ROOT / 'build/mini-first-user-install-04/hardware-summary.json'
    association_raw = association_path.read_bytes()
    association = json.loads(association_raw)
    dump = Path(association['GUI_session']) / 'full-after.bin'
    raw = dump.read_bytes()
    require(association['firmware_sha256'] == IMAGE and sha(raw) == association['full_after_sha256']
            and sha(raw[0x4000:0x82000]) == IMAGE and association['normal_USB_observed'],
            'Verified installation association differs')
    candidates = [p for p in cdc.readonly.enumerate_ports() if (p['vid'], p['pid']) == (0x3654, 0x5155)]
    require(len(candidates) == 1 and candidates[0]['device'] == port, 'Exactly one matching CDC port is required')
    directory.mkdir()
    log = cdc.readonly.Journal(directory / 'wire.jsonl')
    transport = None
    trial = None
    try:
        transport = cdc.host.HostOpenTransport.open(port)
        time.sleep(1)
        wire, _, _ = cdc.identify(transport, VERSION, log=log)
        trial = Trial(wire, directory)
        result = trial.run()
        result['installation_association'] = {'path': association_path.relative_to(ROOT).as_posix(),
            'sha256': sha(association_raw), 'verified_flash_sha256': sha(raw)}
        return result
    except Exception as error:
        result = {'kind': 'hyperrig-mini-v4-controls-trial', 'result': 'failed', 'hardware_executed': True,
                  'error': str(error), 'observations': trial.observations if trial else [],
                  'baseline_restoration_verified': False}
        raise
    finally:
        if transport is not None:
            transport.close()
            log('port_closed')
        log.close()
        if 'result' in locals():
            result['wire_sha256'] = sha((directory / 'wire.jsonl').read_bytes())
            result['serial_port_closed'] = True
            write_json(directory / 'report.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--port', default='COM3')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/mini-v4-controls-01')
    args = parser.parse_args()
    if args.execute:
        report = execute(args.output.resolve(), args.port)
        print(json.dumps({k: report[k] for k in ('result', 'enabled_families', 'baseline_restoration_verified', 'serial_port_closed')}))
    else:
        print(json.dumps({'device_io': False, 'execute_required': True, 'image_sha256': IMAGE, 'families': FAMILIES}))
