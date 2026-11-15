"""Stateful fake CDC tests. No serial driver, pedal, NOR or network is used."""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import probe_mini_app_mutation as mutation
from tools import probe_mini_app as readonly
from tools.build_mini_app import load_profile

ROOT = mutation.ROOT
VERSION = 'tankm_fw M5.71 rel ble'
TONE = dict.fromkeys(('volume','bass','mid','treble','presence','drive'), 0)
FXT = ['FXT 2 boost cost=340 cat=drive mem=64', 'FXT  0 ganancia_db -12..24 (6)', 'FXT end']


class Clock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now


class Pedal:
    """The fake stores presets separately from live values; PLOAD reallocates IDs."""
    def __init__(self, *, scenes=False):
        self.clock = Clock()
        self.pending, self.writes, self.closed, self.loads = [], [], False, 0
        self.counts, self.faults, self.hooks = {}, {}, {}
        self.current, self.ids = 0, 7
        self.live = {'name': 'Original', 'value': 6, 'on': 1, 'other': 0,
                     'scene': 1 if scenes else -1, 'scenes': '0100' if scenes else '0000'}
        self.presets = {0: copy.deepcopy(self.live), 4: {**self.live, 'name': 'Other', 'value': 5}}
        self.saved_value_reloaded = False

    def fxs(self):
        p = [self.live['value'], self.live['other'], 0, 0, 0, 0, 0]
        return [f"FX P0 id={self.ids} boost on={self.live['on']} p={','.join(map(str,p))} ticks=340 l=0 g=-1 fu=0 mem=64",
                'FXS amp=0 on=0', 'FXS cpu=340/13300 ticks (3%) mem_fx=64 B', 'FXS peak=340 ticks skipped=0']

    def plist(self):
        lines = []
        for slot, preset in sorted(self.presets.items()):
            mask = sum((ch == '1') << i for i,ch in enumerate(preset['scenes']))
            lines.append(f"PRE {slot} 1 -1 -1 '{preset['name']}' t=p2 s={mask} amp=0")
        return lines+[f'PLIST end current={self.current}']

    def bank(self):
        presets = []
        for _, p in sorted(self.presets.items()):
            scenes = []
            if p['scenes'] == '0100':
                scenes = [{'index': 1, 'name': 'Lead', 'gain_db': {'in': 0, 'out': 0}, 'amp_on': False,
                           'amp_tone': TONE.copy(), 'blocks': {'b1': {'on': bool(p['on']), 'params': {'ganancia_db': p['value']}}}}]
            presets.append({'meta': {'name': p['name']}, 'sound': {
                'chain': [{'id': 'b1', 'type': 'boost', 'on': bool(p['on']), 'params': {'ganancia_db': p['value']}}, {'amp': True}],
                'amp': {'present': False, 'on': False, 'capture': None, 'tone': TONE.copy()}, 'cab_ir': None,
                'gain_db': {'in': 0, 'out': 0}, 'tempo_bpm_x10': 1200, 'color': None, 'stereo': False,
                'scenes': scenes, 'active_scene': p['scene']}})
        return {'format': 'ultrarig-preset', 'version': 1, 'kind': 'bank', 'presets': presets}

    def response(self, cmd):
        if cmd == 'PING': return [f'PONG {VERSION} Nov 12 2026 16:04:11']
        if cmd == 'FXT': return FXT
        if cmd == 'FXS': return self.fxs()
        if cmd == 'PLIST': return self.plist()
        if cmd == 'SNAPS': return [f"SNAPS {self.live['scenes']} current={self.live['scene']}"]
        if cmd == 'GAIN': return ['GAIN in=0 out=0 dB']
        if cmd == 'AMPEQ': return ['AMPEQ '+' '.join(f'{k}=0' for k in TONE)]
        if cmd == 'BPM': return ['BPM 120.0']
        if cmd == 'PCOLOR': return [f'PCOLOR none preset={self.current}']
        if cmd == 'STW': return ['STW w=0 cur=0 live=0 cpu=340/13300 deg=0']
        if cmd == 'MODEL': return ["MODEL 'none' layers=0 channels=0 fused=0 engine=none trim=0"]
        if cmd == 'SNAPNAME': return (["SNAPNAME 1 'Lead'"] if self.live['scenes'][1] == '1' else [])+['SNAPNAME end']
        if match := re.fullmatch(r'FXP (\d+) 0 (-?\d+)', cmd):
            assert int(match[1]) == self.ids
            self.live['value'] = max(-12, min(24, int(match[2])))
            return [f"FXP ok {self.live['value']}"]
        if match := re.fullmatch(r'FXE (\d+) ([01])', cmd):
            assert int(match[1]) == self.ids
            self.live['on'] = int(match[2])
            return ['FXE ok cpu=340/13300 ticks (3%) mem_fx=64 B']
        if match := re.fullmatch(r'PSAVE (\d+) HyperRig_Test', cmd):
            slot = int(match[1]); assert slot not in self.presets
            self.presets[slot] = {**copy.deepcopy(self.live), 'name': 'HyperRig_Test'}
            self.current = slot
            return [f"PSAVE ok {slot} 'HyperRig_Test' 1 blocks capture=-1 ir=-1"]
        if match := re.fullmatch(r'PLOAD (\d+)', cmd):
            slot = int(match[1]); assert slot in self.presets
            previous = self.live['value']
            self.live = copy.deepcopy(self.presets[slot]); self.current = slot
            self.ids = 20+self.loads; self.loads += 1
            self.saved_value_reloaded |= previous != self.live['value']
            return [f"PLOAD ok {slot} '{self.live['name']}' missing=0 capture=-1 ir=-1 ms=1"]
        if cmd == 'SNAPSAVE 0':
            assert self.current == 31
            self.live['scenes'] = '1'+self.live['scenes'][1:]
            self.live['scene'] = 0
            self.presets[31] = {**copy.deepcopy(self.live), 'name': 'HyperRig_Test'}
            return ['SNAPSAVE ok 0 preset=31']
        if match := re.fullmatch(r'SNAP ([0-3])', cmd):
            scene = int(match[1]); assert self.live['scenes'][scene] == '1'
            self.live['scene'] = scene
            return [f'SNAP ok {scene} missing=0 ms=1']
        if match := re.fullmatch(r'PDEL (\d+)', cmd):
            slot = int(match[1]); assert slot == 31 and slot in self.presets and self.current != slot
            del self.presets[slot]
            return [f'PDEL ok {slot}']
        raise AssertionError('unexpected command '+cmd)

    def write(self, packet):
        assert packet.endswith(b'\n') and packet.count(b'\n') == 1
        cmd = packet[:-1].decode('ascii')
        self.writes.append(cmd); self.counts[cmd] = self.counts.get(cmd, 0)+1
        key = (cmd, self.counts[cmd])
        if key in self.hooks: self.hooks[key](self)
        if key in self.faults:
            reply = self.faults[key]
            if isinstance(reply, Exception): raise reply
            if reply is None: return len(packet)
        else:
            reply = self.response(cmd)
        if callable(reply): reply = reply(self)
        data = ('\r\n'.join(reply)+'\r\n').encode('utf-8')
        self.pending.extend([data[i:i+11] for i in range(0, len(data), 11)])
        return len(packet)

    def read(self, size):
        self.clock.now += .001
        return self.pending.pop(0) if self.pending else b''

    def close(self): self.closed = True


def probe_for(pedal=None, *, persistent=False):
    pedal = pedal or Pedal()
    cls = mutation.PresetMutationProbe if persistent else mutation.MutationProbe
    probe = cls(pedal, VERSION, clock=pedal.clock)
    backup = probe.capture()
    return probe, pedal, backup


def reference(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')
    return mutation.file_reference(path)


class MutationTests(unittest.TestCase):
    def test_default_cli_has_no_enumeration_or_serial_import(self):
        original = __import__
        def guarded(name, *args, **kwargs):
            if name == 'serial' or name.startswith('serial.'): raise AssertionError('serial imported')
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=guarded), patch.object(readonly, 'enumerate_ports', side_effect=AssertionError('enumeration')):
            with contextlib.redirect_stdout(io.StringIO()) as stream: self.assertEqual(mutation.main([]), 0)
        result = json.loads(stream.getvalue())
        self.assertFalse(result['device_io']); self.assertFalse(result['enumerated'])
        self.assertTrue(result['contract']['PSAVE_execution_implemented'])

    def test_original_reply_strings_and_fxt_bounds(self):
        self.assertEqual(mutation.source_contract()['reply_strings']['0x35cd1'], 'FXP ok %d\n')
        types = mutation.parse_fxt(FXT)
        self.assertEqual(types['boost']['params'][0]['max'], 24)
        for lines in (FXT[:-1], [FXT[1], 'FXT end'], [*FXT[:-1], FXT[1], 'FXT end'],
                      [FXT[0], 'FXT  0 ganancia_db 24..-12 (6)', 'FXT end']):
            with self.subTest(lines=lines), self.assertRaises(mutation.Error): mutation.parse_fxt(lines)

    def test_fxs_rejects_missing_duplicate_unknown_state(self):
        lines = Pedal().fxs()
        for bad in (lines[:-1], [lines[0], *lines], [*lines[:-1], 'FXS other=1', lines[-1]],
                    [lines[0].replace('p=6,0,0,0,0,0,0', 'p=6,0'), *lines[1:]]):
            with self.subTest(lines=bad), self.assertRaises(mutation.Error): mutation.parse_fxs(bad)

    @unittest.skipUnless(shutil.which('node'), 'Node required for original JS parser comparison')
    def test_actual_original_js_parsers_match_fixture(self):
        source = (mutation.SOURCE/'web/tankg.html').read_text(encoding='utf-8')
        fxs = source[source.index('function parseFxs(lines)'):source.index('/* M5.6: nota del bloque')]
        fxthead = source[source.index('function fxtHead(l)'):source.index('function parseMemLine(l)')]
        load = source[source.index('async function loadTypes()'):source.index('/* contador de cambios de la cadena')]
        script = 'const S={}; const FXT_END=()=>true;const FXS_END=l=>/^FXS (?:peak|pico)\\b/.test(l);\n'+fxs+fxthead+load
        script += '\nconst Pedal={cmd:async()=>'+json.dumps(FXT)+'};\n'
        script += '(async()=>{await loadTypes(); console.log(JSON.stringify({types:S.types,fxs:parseFxs('+json.dumps(Pedal().fxs())+')}));})()'
        process = subprocess.run(['node'], input=script, text=True, capture_output=True, check=True)
        result = json.loads(process.stdout)
        native = mutation.parse_fxs(Pedal().fxs())['blocks'][0]
        self.assertEqual(result['fxs']['chain']['P'][0]['p'], native['params'])
        self.assertEqual(result['types']['boost']['params'][0]['min'], mutation.parse_fxt(FXT)['boost']['params'][0]['min'])

    def test_one_live_fxp_roundtrip_and_single_use(self):
        probe, pedal, backup = probe_for()
        plan = probe.plan(block_id=7, parameter_index=0)
        self.assertEqual((plan.original, plan.requested), (6, 7))
        result = probe.roundtrip(plan)
        self.assertTrue(result['roundtrip_passed']); self.assertTrue(result['restoration_verified'])
        self.assertEqual([s for s in pedal.writes if s.startswith('FXP ')], ['FXP 7 0 7', 'FXP 7 0 6'])
        self.assertEqual(result['observed_after_restore'], backup['state'])
        with self.assertRaises(mutation.Error): probe.roundtrip(plan)

    def test_fxe_ack_without_state_echo_requires_actual_fxs(self):
        probe, pedal, _ = probe_for()
        plan = probe.plan(block_id=7, operation='FXE')
        result = probe.roundtrip(plan)
        self.assertTrue(result['roundtrip_passed'])
        self.assertEqual([s for s in pedal.writes if s.startswith('FXE ')], ['FXE 7 0', 'FXE 7 1'])

    def test_plans_reject_missing_parameters_modes_and_large_changes(self):
        probe, pedal, _ = probe_for()
        before = pedal.writes.copy()
        for args in ({'block_id': 8,'parameter_index': 0}, {'block_id': 7,'parameter_index': 1},
                     {'block_id': 7,'parameter_index': 0,'value': 25}, {'block_id': 7,'parameter_index': 0,'value': 6},
                     {'block_id': 7,'parameter_index': 0,'operation': 'NAM'}, {'block_id': True,'parameter_index': 0}):
            with self.subTest(args=args), self.assertRaises(mutation.Error): probe.plan(**args)
        self.assertEqual(pedal.writes, before)
        probe.types['boost']['params'][0]['name'] = 'os_n'
        with self.assertRaises(mutation.Error): probe.plan(block_id=7, parameter_index=0)

    def test_state_change_before_write_stops_before_mutation(self):
        probe, pedal, _ = probe_for(); plan = probe.plan(block_id=7, parameter_index=0)
        pedal.live['value'] = 8
        with self.assertRaises(mutation.Error): probe.roundtrip(plan)
        self.assertFalse(any(c.startswith('FXP ') for c in pedal.writes))

    def test_clamped_effective_value_is_read_then_restored_without_grant(self):
        probe, pedal, _ = probe_for(); plan = probe.plan(block_id=7, parameter_index=0)
        pedal.faults[('FXP 7 0 7', 1)] = ['FXP ok 6']
        result = probe.roundtrip(plan)
        self.assertFalse(result['roundtrip_passed']); self.assertTrue(result['restoration_verified'])
        self.assertEqual(pedal.live['value'], 6)

    def test_out_of_range_effective_value_is_not_treated_as_a_valid_clamp(self):
        probe, pedal, _ = probe_for(); plan = probe.plan(block_id=7, parameter_index=0)
        pedal.faults[('FXP 7 0 7', 1)] = ['FXP ok 2147483647']
        with self.assertRaises(mutation.Error): probe.roundtrip(plan)
        self.assertNotIn('FXP 7 0 6', pedal.writes)

    def test_err_kept_and_malformed_ack_never_trigger_blind_restore(self):
        for response in (['ERR FXP out of memory: kept 6'], ['FXP ok 7 garbage'], ['FXP ok'], ['@P 4', 'FXP ok 7']):
            probe, pedal, _ = probe_for(); plan = probe.plan(block_id=7, parameter_index=0)
            pedal.faults[('FXP 7 0 7', 1)] = response
            with self.subTest(response=response), self.assertRaises(mutation.Error): probe.roundtrip(plan)
            self.assertNotIn('FXP 7 0 6', pedal.writes)
            self.assertFalse(probe.result['restoration_verified'])

    def test_unrelated_readback_change_stops_without_replay(self):
        probe, pedal, _ = probe_for(); plan = probe.plan(block_id=7, parameter_index=0)
        pedal.hooks[('FXP 7 0 7', 1)] = lambda p: p.live.update(other=1)
        with self.assertRaises(mutation.Error): probe.roundtrip(plan)
        self.assertNotIn('FXP 7 0 6', pedal.writes)

    def test_timeouts_after_apply_or_restore_are_terminal(self):
        for key in (('FXP 7 0 7',1), ('FXS',3), ('FXP 7 0 6',1), ('FXS',4)):
            probe, pedal, _ = probe_for(); plan = probe.plan(block_id=7, parameter_index=0)
            pedal.faults[key] = None
            with self.subTest(key=key), self.assertRaises(mutation.Error): probe.roundtrip(plan)
            self.assertEqual(pedal.writes[-1], key[0]); self.assertFalse(probe.result['restoration_verified'])

    def test_persistent_roundtrip_with_and_without_scene_and_new_runtime_ids(self):
        for scenes in (False, True):
            with self.subTest(scenes=scenes), tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
                pedal = Pedal(scenes=scenes); original = copy.deepcopy(pedal.presets)
                bank = reference(Path(temp)/'bank.json', pedal.bank())
                probe, _, _ = probe_for(pedal, persistent=True)
                plan = probe.plan(block_id=7, parameter_index=0)
                result = probe.save_roundtrip(slot=31, bank_backup=bank, marker_plan=plan)
                self.assertTrue(result['roundtrip_passed']); self.assertTrue(result['persistence_readback_verified'])
                self.assertTrue(result['temporary_slot_deleted']); self.assertTrue(pedal.saved_value_reloaded)
                self.assertEqual(pedal.presets, original); self.assertEqual(pedal.current, 0)
                self.assertEqual([c for c in pedal.writes if c.startswith('PDEL ')], ['PDEL 31'])
                self.assertNotEqual(pedal.ids, 7)
                self.assertEqual(pedal.writes.count('SNAP 1'), 2 if scenes else 0)

    def test_persistent_fxe_marker_is_reloaded_from_storage(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            pedal = Pedal(); bank = reference(Path(temp)/'bank.json', pedal.bank())
            probe, _, _ = probe_for(pedal, persistent=True)
            result = probe.save_roundtrip(slot=31, bank_backup=bank,
                                         marker_plan=probe.plan(block_id=7, operation='FXE'))
            self.assertTrue(result['roundtrip_passed']); self.assertEqual(pedal.live['on'],1)
            self.assertIn('FXE 7 0',pedal.writes); self.assertEqual(pedal.loads,3)

    def test_save_rechecks_inventory_immediately_before_writing(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            pedal = Pedal(); bank = reference(Path(temp)/'bank.json', pedal.bank())
            probe, _, _ = probe_for(pedal, persistent=True); plan = probe.plan(block_id=7,parameter_index=0)
            pedal.presets[31] = {**pedal.live,'name':'New external preset'}
            with self.assertRaises(mutation.Error):probe.save_roundtrip(slot=31,bank_backup=bank,marker_plan=plan)
            self.assertFalse(any(c.startswith(('PSAVE ', 'PDEL ')) for c in pedal.writes))

    def test_save_requires_free_slot_matching_bank_and_no_unrepresented_edits(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            for mode in ('occupied','bad_backup','dirty','scene_unknown'):
                pedal = Pedal(scenes=mode=='scene_unknown'); bank_data = pedal.bank()
                if mode == 'bad_backup': bank_data['presets'].pop()
                if mode == 'dirty': pedal.live['value'] = 9
                if mode == 'scene_unknown': pedal.live['scene'] = -1
                bank = reference(Path(temp)/(mode+'.json'), bank_data)
                probe, _, _ = probe_for(pedal, persistent=True)
                plan = probe.plan(block_id=7, parameter_index=0)
                with self.subTest(mode=mode), self.assertRaises(mutation.Error):
                    probe.save_roundtrip(slot=4 if mode=='occupied' else 31, bank_backup=bank, marker_plan=plan)
                self.assertFalse(any(c.startswith(('PSAVE ', 'PDEL ')) for c in pedal.writes))

    def test_no_cleanup_after_ambiguous_save_or_reload_failure(self):
        for key, response in ((('PSAVE 31 HyperRig_Test',1),None),
                              (('PSAVE 31 HyperRig_Test',1),["PSAVE ok 30 'HyperRig_Test' 1 blocks capture=-1 ir=-1"]),
                              (('PLOAD 31',1),["PLOAD ok 31 'HyperRig_Test' missing=1 capture=-1 ir=-1 ms=1"]),
                              (('PLOAD 0',1),None)):
            with self.subTest(key=key,response=response), tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
                pedal = Pedal(); bank = reference(Path(temp)/'bank.json', pedal.bank())
                probe, _, _ = probe_for(pedal, persistent=True); plan = probe.plan(block_id=7, parameter_index=0)
                pedal.faults[key] = response
                with self.assertRaises(mutation.Error): probe.save_roundtrip(slot=31, bank_backup=bank, marker_plan=plan)
                self.assertFalse(probe.result['restoration_verified']); self.assertNotIn('PDEL 31', pedal.writes)

    def test_slot_changed_by_another_actor_is_never_deleted(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            pedal = Pedal(); bank = reference(Path(temp)/'bank.json', pedal.bank())
            probe, _, _ = probe_for(pedal, persistent=True); plan = probe.plan(block_id=7, parameter_index=0)
            pedal.hooks[('PLOAD 0',1)] = lambda p: p.presets[31].update(name='External')
            with self.assertRaises(mutation.Error): probe.save_roundtrip(slot=31, bank_backup=bank, marker_plan=plan)
            self.assertNotIn('PDEL 31', pedal.writes); self.assertIn(31, pedal.presets)

    def test_snapsave_wrong_target_timeout_or_missing_persistence_never_qualifies(self):
        for mode in ('wrong_target','timeout','wrong_reload'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
                pedal=Pedal(); bank=reference(Path(temp)/'bank.json',pedal.bank())
                probe,_,_=probe_for(pedal,persistent=True); plan=probe.plan(block_id=7,parameter_index=0)
                if mode=='wrong_target':pedal.faults[('SNAPSAVE 0',1)]=['SNAPSAVE ok 0 preset=0']
                elif mode=='timeout':pedal.faults[('SNAPSAVE 0',1)]=None
                else:pedal.hooks[('PLOAD 31',2)]=lambda p:p.presets[31].update(value=10)
                with self.assertRaises(mutation.Error):probe.save_roundtrip(slot=31,bank_backup=bank,marker_plan=plan)
                self.assertFalse(probe.result['restoration_verified']);self.assertNotIn('PDEL 31',pedal.writes)

    def test_cleanup_ack_without_deletion_does_not_qualify_persistence(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            pedal = Pedal(); bank = reference(Path(temp)/'bank.json', pedal.bank())
            probe, _, _ = probe_for(pedal, persistent=True); plan = probe.plan(block_id=7, parameter_index=0)
            pedal.faults[('PDEL 31',1)] = ['PDEL ok 31']
            with self.assertRaises(mutation.Error): probe.save_roundtrip(slot=31, bank_backup=bank, marker_plan=plan)
            self.assertFalse(probe.result['roundtrip_passed']); self.assertFalse(probe.result['restoration_verified'])
            self.assertTrue(probe.result['original_sound_restored']); self.assertIn(31,pedal.presets)

    def test_cli_fake_run_and_existing_builder_evidence_contract(self):
        for action in ('live','save'):
            with self.subTest(action=action), tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
                path=Path(temp); image=path/'image.bin'; image.write_bytes(b'test-only-candidate')
                spec={'target':'tank-mini','architecture':'standalone-ultrarig-port','firmware_version':VERSION,
                      'image_path':image.relative_to(ROOT).as_posix(),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                      'capabilities':{'read':True,'write':False,'panel':False},'hardware_verified':True}
                manifest=path/'manifest.json'; manifest.write_text(json.dumps(spec),encoding='utf-8')
                pedal=Pedal(scenes=True); bank=reference(path/'bank.json',pedal.bank())
                args=argparse.Namespace(action=action,port='FAKE',firmware_manifest=manifest,log=path/'trace.jsonl',
                    backup=path/'state.json',report=path/'proof.json',operation='FXP',block=7,parameter=0,value=None,
                    slot=31,bank_backup=bank['path'],bank_sha256=bank['sha256'])
                result=mutation.run_live(args,enumerate_fn=lambda:[{'device':'FAKE','vid':readonly.VID,'pid':readonly.PID}],
                                         open_fn=lambda _:pedal,clock=pedal.clock)
                self.assertEqual(result['kind'],'mini-app-command-validation', result)
                self.assertFalse(result['hardware_executed']); self.assertTrue(pedal.closed)
                self.assertEqual(result['physically_exercised_requests'],{})
                self.assertTrue(result['simulated_requests']);self.assertFalse(result['every_value_physically_tested'])
                expected={'PSAVE':['PSAVE 31 HyperRig_Test'],'SNAPSAVE':['SNAPSAVE 0']} if action=='save' else {'FXP':['FXP 7 0 6','FXP 7 0 7']}
                self.assertEqual(result['verified_requests'],expected)
                spec.update(command_capabilities=expected,command_validation=mutation.file_reference(args.report))
                manifest.write_text(json.dumps(spec),encoding='utf-8')
                with self.assertRaises(ValueError):load_profile(manifest)
                # Schema-only hardware assertion fixture in a temporary dir:
                # never a retained physical evidence artifact.
                result.update(hardware_executed=True,test_fixture=True)
                args.report.write_text(json.dumps(result),encoding='utf-8')
                spec['command_validation']=mutation.file_reference(args.report)
                manifest.write_text(json.dumps(spec),encoding='utf-8')
                self.assertEqual(load_profile(manifest)['command_capabilities'],expected)
                self.assertFalse(result['all_required_editor_mutations_verified'])
                self.assertFalse(result['BLE_verified'])


if __name__ == '__main__': unittest.main()
