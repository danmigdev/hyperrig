"""First-preset CDC state machine and family evidence tests; never device I/O.

Hardware flags in schema tests below are explicitly labelled temporary fixtures
and are deleted with their temporary directory, never retained as evidence.
"""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from tools import build_mini_app as app
from tools import probe_mini_app_first_preset as first
from tools import probe_mini_app_mutation as mutation
from tools import probe_mini_app as readonly
from tests.test_mini_app_mutation import Pedal, VERSION, reference
from tests.test_mini_app_families import POLICY, fixture_profile, seed
from tests.test_mini_app_protocol import node


class FirstPedal(Pedal):
    def __init__(self, *, empty_chain=False, preexisting=False):
        super().__init__()
        self.current = -1
        self.presets = {4:copy.deepcopy(self.presets[4])} if preexisting else {}
        self.live.update(name='Unsaved',gain=[0,0],scene_data={})
        self.empty_chain = empty_chain

    def fxs(self):
        lines = super().fxs()
        return lines[1:] if self.empty_chain else lines

    def plist(self):
        lines = super().plist()
        return [line.replace(' 1 -1 -1 ', ' 0 -1 -1 ').replace(' t=p2 ', ' t=- ')
                if self.empty_chain and "'HyperRig_Test'" in line else line for line in lines]

    def response(self, cmd):
        if cmd == 'GAIN': return [f"GAIN in={self.live['gain'][0]} out={self.live['gain'][1]} dB"]
        if match := re.fullmatch(r'GAIN (-?\d+) (-?\d+)',cmd):
            self.live['gain'] = [max(-30,min(12,int(v))) for v in match.groups()]
            return self.response('GAIN')
        if match := re.fullmatch(r'PSAVE (\d+) HyperRig_Test',cmd):
            slot = int(match[1]); assert slot not in self.presets
            self.presets[slot] = {**copy.deepcopy(self.live),'name':'HyperRig_Test'}
            self.current = slot
            return [f"PSAVE ok {slot} 'HyperRig_Test' {int(not self.empty_chain)} blocks capture=-1 ir=-1"]
        if cmd == 'SNAPSAVE 0':
            assert self.current in self.presets
            self.live['scenes'] = '1'+self.live['scenes'][1:]; self.live['scene'] = 0
            self.live['scene_data'][0] = {k:copy.deepcopy(self.live[k]) for k in ('value','on','other','gain')}
            self.presets[self.current] = {**copy.deepcopy(self.live),'name':'HyperRig_Test'}
            return [f'SNAPSAVE ok 0 preset={self.current}']
        if cmd == 'SNAP 0':
            assert self.live['scenes'][0] == '1'
            self.live.update(copy.deepcopy(self.live['scene_data'][0]));self.live['scene']=0
            return ['SNAP ok 0 missing=0 ms=1']
        if cmd.startswith('PDEL '): raise AssertionError('first-preset probe must never delete')
        return super().response(cmd)


def capture(pedal=None):
    pedal = pedal or FirstPedal()
    probe = first.FirstPresetProbe(pedal,VERSION,clock=pedal.clock)
    backup = probe.capture()
    return probe,pedal,backup


class FirstPresetTests(unittest.TestCase):
    def test_old_probe_requires_saved_current_but_new_trial_retains_first(self):
        probe,pedal,backup = capture()
        with self.assertRaisesRegex(mutation.Error,'saved current preset'):
            mutation.validate_saved_baseline(probe.baseline,probe.types,{'presets':[]})
        result = probe.create_first(slot=0)
        self.assertTrue(result['roundtrip_passed'] and result['preset_intentionally_retained'])
        self.assertFalse(result['restoration_verified'])
        self.assertEqual(pedal.current,0); self.assertEqual(set(pedal.presets),{0})
        self.assertEqual(pedal.live['value'],backup['state']['fxs']['blocks'][0]['params'][0])
        self.assertEqual(pedal.live['scene'],0)
        self.assertFalse(any(cmd.startswith('PDEL') for cmd in pedal.writes))
        self.assertEqual([cmd for cmd in pedal.writes if cmd.startswith('PLOAD')],['PLOAD 0','PLOAD 0'])
        self.assertEqual([cmd for cmd in pedal.writes if cmd.startswith('FXP')],['FXP 7 0 5','FXP 20 0 5'])

    def test_empty_chain_uses_decreasing_gain_and_proves_saved_scene(self):
        probe,pedal,backup = capture(FirstPedal(empty_chain=True))
        result = probe.create_first(slot=0)
        self.assertTrue(result['persistence_readback_verified'] and result['snapshot_persistence_readback_verified'])
        self.assertEqual(pedal.live['gain'],[0,0])
        self.assertEqual(pedal.presets[0]['scene_data'][0]['gain'],[0,0])
        self.assertEqual([cmd for cmd in pedal.writes if cmd.startswith('GAIN ')],['GAIN 0 -1','GAIN 0 -1'])
        self.assertFalse(any(cmd.startswith(('FXP ','FXE ','PDEL ')) for cmd in pedal.writes))
        self.assertEqual(result['final_state']['fxs'],backup['state']['fxs'])

    def test_free_slot_and_preexisting_inventory_kept_without_loading_it(self):
        probe,pedal,_ = capture(FirstPedal(preexisting=True))
        before = copy.deepcopy(pedal.presets[4])
        result = probe.create_first(slot=5)
        self.assertTrue(result['preexisting_inventory_verified'])
        self.assertEqual(pedal.presets[4],before)
        self.assertNotIn('PLOAD 4',pedal.writes)
        self.assertEqual(set(pedal.presets),{4,5})

    def test_occupied_current_or_changed_state_stops_before_psave(self):
        for mode in ('occupied','current','changed'):
            probe,pedal,_ = capture(FirstPedal(preexisting=True))
            if mode == 'current': probe.baseline['plist']['current']=4
            if mode == 'changed': pedal.live['gain']=[0,-2]
            with self.assertRaises(mutation.Error): probe.create_first(slot=4 if mode=='occupied' else 0)
            self.assertFalse(any(cmd.startswith('PSAVE ') for cmd in pedal.writes))

    def test_gain_marker_never_increases_and_stops_at_both_minima(self):
        for gain,expected in [([0,-30],'GAIN -1 -30'),([12,12],'GAIN 12 11'),([-30,-30],None)]:
            pedal=FirstPedal(empty_chain=True);pedal.live['gain']=gain
            probe,pedal,_=capture(pedal)
            if expected is None:
                with self.assertRaisesRegex(mutation.Error,'no decreasing GAIN'):probe.create_first(slot=0)
                self.assertFalse(any(cmd.startswith('PSAVE ') for cmd in pedal.writes))
            else:
                probe.create_first(slot=0)
                self.assertEqual([cmd for cmd in pedal.writes if cmd.startswith('GAIN ')],[expected,expected])

    def test_false_psave_ack_is_not_persistence(self):
        probe,pedal,_=capture()
        def pretend(p):
            reply=p.response('PSAVE 0 HyperRig_Test');p.presets[0]['value']=99;return reply
        pedal.faults[('PSAVE 0 HyperRig_Test',1)]=pretend
        with self.assertRaises(mutation.Error):probe.create_first(slot=0)
        self.assertFalse(probe.result['persistence_readback_verified'])
        self.assertNotIn('SNAPSAVE 0',pedal.writes)
        self.assertFalse(any(cmd.startswith('PDEL') for cmd in pedal.writes))

    def test_false_snapsave_or_wrong_scene_value_does_not_pass(self):
        for mode in ('not_persisted','wrong_gain'):
            probe,pedal,_=capture(FirstPedal(empty_chain=True))
            def bad_scene(p):
                old=copy.deepcopy(p.presets[0]);reply=p.response('SNAPSAVE 0')
                if mode=='not_persisted':p.presets[0]=old
                else:p.presets[0]['scene_data'][0]['gain']=[0,-9]
                return reply
            pedal.faults[('SNAPSAVE 0',1)]=bad_scene
            with self.assertRaises((mutation.Error,AssertionError)):probe.create_first(slot=0)
            self.assertTrue(probe.result['persistence_readback_verified'])
            self.assertFalse(probe.result['snapshot_persistence_readback_verified'])

    def test_timeout_does_not_retry_load_or_delete_ambiguous_save(self):
        probe,pedal,_=capture();pedal.faults[('PSAVE 0 HyperRig_Test',1)]=None
        with self.assertRaises(mutation.Error):probe.create_first(slot=0)
        self.assertEqual(pedal.counts['PSAVE 0 HyperRig_Test'],1)
        self.assertFalse(any(cmd.startswith(('PLOAD ','PDEL ')) for cmd in pedal.writes))
        with self.assertRaises(mutation.Error):probe.create_first(slot=0)

    def test_default_plan_has_no_serial_import_enumeration_or_io(self):
        original=__import__
        def guard(name,*args,**kwargs):
            if name=='serial' or name.startswith('serial.'):raise AssertionError('serial import')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=guard),patch.object(readonly,'enumerate_ports',side_effect=AssertionError('enumeration')):
            with contextlib.redirect_stdout(io.StringIO()) as output:self.assertEqual(first.main([]),0)
        result=json.loads(output.getvalue())
        self.assertFalse(result['device_io'] or result['PDEL_available'])


class FirstPresetEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='first-preset-test-',dir=app.ROOT/'build')
        self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)
        image=self.path/'fixture.bin';image.write_bytes(b'OFFLINE FIRST PRESET SCHEMA FIXTURE; NOT FIRMWARE')
        self.spec={'target':'tank-mini','architecture':'standalone-ultrarig-port','firmware_version':VERSION,
            'image_path':app.relative(image),'image_sha256':app.sha(image.read_bytes()),'hardware_verified':True,
            'capabilities':{'read':True,'write':False,'panel':False}}
        self.manifest=self.path/'manifest.json';self.manifest.write_text(json.dumps(self.spec),encoding='utf-8')

    def run_fixture(self, *, empty=True):
        pedal=FirstPedal(empty_chain=empty)
        args=argparse.Namespace(port='FAKE',firmware_manifest=self.manifest,slot=0,operation='auto',block=None,parameter=None,
            log=self.path/'trace.jsonl',backup=self.path/'backup.json',report=self.path/'report.json')
        report=first.run_create(args,enumerate_fn=lambda:[{'device':'FAKE','vid':readonly.VID,'pid':readonly.PID}],
            open_fn=lambda _:pedal,clock=pedal.clock)
        self.assertEqual(report['kind'],first.KIND)
        self.assertFalse(report['hardware_executed'] or report['restoration_verified'])
        self.assertTrue(pedal.closed)
        return report,pedal

    def schema_fixture(self, report):
        e=copy.deepcopy(report);e.update(hardware_executed=True,offline_schema_test=True,
            physically_exercised_requests=report['simulated_requests'],simulated_requests={})
        backup=json.loads((self.path/'backup.json').read_text('utf-8'))
        backup.update(hardware_executed=True,offline_schema_test=True)
        e['backup']=reference(self.path/'backup.json',backup)
        rows=[json.loads(line) for line in (self.path/'trace.jsonl').read_text('utf-8').splitlines()]
        rows[0].update(hardware_executed=True,offline_schema_test=True)
        (self.path/'trace.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        e['trace']=mutation.file_reference(self.path/'trace.jsonl')
        return e

    def load(self, report, commands=None, transport='usb-cdc'):
        spec=copy.deepcopy(self.spec)
        commands=commands or list(report.get('physically_exercised_requests') or report['simulated_requests'])
        spec['family_capabilities']={transport:commands}
        spec['family_validation']={transport:[reference(self.path/'proof-input.json',report)]}
        manifest=self.path/'profile.json';manifest.write_text(json.dumps(spec),encoding='utf-8')
        return app.load_profile(manifest)

    def test_real_semantics_schema_replay_allows_gain_save_load_scene_not_untried_fx(self):
        report,_=self.run_fixture();e=self.schema_fixture(report)
        p=self.load(e)
        self.assertEqual(p['family_capabilities']['usb-cdc'],['GAIN','PLOAD','PSAVE','SNAP','SNAPSAVE'])
        self.assertFalse(p['capabilities']['write'])
        with self.assertRaises(ValueError):self.load(e,['FXP'])
        with self.assertRaises(ValueError):self.load(e,transport='ble-nus')

    def test_mock_trial_cannot_qualify_and_fxp_only_when_exercised(self):
        report,_=self.run_fixture(empty=False)
        self.assertIn('FXP',report['simulated_requests']);self.assertNotIn('GAIN',report['simulated_requests'])
        with self.assertRaises(ValueError):self.load(report)
        e=self.schema_fixture(report)
        self.assertIn('FXP',self.load(e)['family_capabilities']['usb-cdc'])

    def test_retained_proof_does_not_accept_restoration_or_false_replay_claims(self):
        report,_=self.run_fixture();e=self.schema_fixture(report)
        for field,value in [('restoration_verified',True),('preset_intentionally_retained',False),
                            ('final_sound_verified',False),('implementation_sha256','0'*64)]:
            bad=copy.deepcopy(e);bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.load(bad)
        for field in ('roundtrip_passed','persistence_readback_verified','snapshot_persistence_readback_verified',
                      'slot_was_free','preexisting_inventory_verified','initial_saved_preset_absent'):
            bad=copy.deepcopy(e);bad['trial'][field]=False
            with self.subTest(field=field),self.assertRaises(ValueError):self.load(bad)

    def test_raw_trace_order_and_sound_backup_are_replayed_not_trusted_flags(self):
        report,_=self.run_fixture();e=self.schema_fixture(report)
        raw=(self.path/'trace.jsonl').read_bytes()
        rows=[json.loads(line) for line in raw.decode().splitlines()]
        # A claimed final state cannot differ even while all success flags remain true.
        bad=copy.deepcopy(e);bad['trial']['final_state']['extra']['gain_db']=[0,-5]
        with self.assertRaises(ValueError):self.load(bad)
        # Reorder whole exchanges: individually valid TX/RX/complete sequences are insufficient.
        first_tx=next(i for i,r in enumerate(rows) if r['event']=='tx' and r.get('command')=='SNAPSAVE 0')
        last=next(i for i in range(first_tx,len(rows)) if rows[i]['event']=='complete')
        segment=rows[first_tx:last+1];del rows[first_tx:last+1]
        position=next(i for i,r in enumerate(rows) if r['event']=='tx' and r.get('command','').startswith('PSAVE '))
        rows[position:position]=segment
        trace=self.path/'reordered.jsonl';trace.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        bad=copy.deepcopy(e);bad['trace']=mutation.file_reference(trace)
        with self.assertRaises(ValueError):self.load(bad)
        backup=json.loads((self.path/'backup.json').read_text('utf-8'))
        backup['state']['extra']['gain_db']=[0,-8]
        bad=copy.deepcopy(e);bad['backup']=reference(self.path/'false-backup.json',backup)
        with self.assertRaises(ValueError):self.load(bad)


class GainFamilyTests(unittest.TestCase):
    def policy(self, actions, profile=None):
        return node(POLICY,{'profile':profile or fixture_profile(),'actions':seed()+actions})[-len(actions):]

    def test_gain_requires_transport_proof_and_actual_gain_readback(self):
        r=self.policy([{'command':'GAIN 0 -1'},{'reply':'GAIN','lines':['GAIN in=0 out=0 dB']},
            {'command':'GAIN -30 12'},{'command':'GAIN -31 0'},{'command':'GAIN 0 13'},
            {'command':'GAIN 00 0'},{'command':'GAIN 0 -1','transport':'ble-nus'}])
        self.assertEqual([r[i]['allowed'] for i in (0,2,3,4,5,6)],[False,True,False,False,False,False])
        p=fixture_profile();p['family_capabilities']['usb-cdc'].remove('GAIN')
        self.assertFalse(self.policy([{'reply':'GAIN','lines':['GAIN in=0 out=0 dB']},{'command':'GAIN 0 -1'}],p)[1]['allowed'])

    def test_original_lvl_updates_gain_and_bad_ack_or_reload_invalidates_it(self):
        r=self.policy([{'reply':'LVL','lines':['LVL in=0 out=0 g=0/-3 b=0 s=0']},{'command':'GAIN 0 -4'},
            {'reply':'GAIN 0 -4','lines':['GAIN in=0 out=-5 dB']},{'command':'GAIN 0 -6'},
            {'reply':'GAIN','lines':['GAIN in=0 out=-3 dB']},{'command':'GAIN 0 -4'},
            {'reply':'PLOAD 0','lines':["PLOAD ok 0 'Original' missing=0 capture=-1 ir=-1 ms=1"]},
            {'command':'GAIN 0 -4'}])
        self.assertEqual([r[i]['allowed'] for i in (1,3,5,7)],[True,False,True,False])

    def test_gain_builder_grammar_is_bounded(self):
        self.assertEqual(app.command_grants({'GAIN':['GAIN -30 12']}),{'GAIN':['GAIN -30 12']})
        for request in ('GAIN -31 0','GAIN 0 13','GAIN 00 0','GAIN 0 0\nPSAVE 0 x'):
            with self.subTest(request=request),self.assertRaises(ValueError):app.command_grants({'GAIN':[request]})

    def test_gain_literal_profile_matches_builder_without_granting_family(self):
        profile=fixture_profile()
        profile.update(family_capabilities={},family_validation={},
            command_capabilities=app.command_grants({'GAIN':['GAIN 0 -1']}),
            command_validation={'path':'offline-test-fixture','sha256':'b'*64})
        actions=[{'pong':'PONG '+VERSION+' Nov 12 2026 16:04:11'},
            {'command':'GAIN 0 -1'},{'command':'GAIN 0 -2'},
            {'command':'GAIN 0 -1','transport':'ble-nus'},
            {'reset':True},{'command':'GAIN 0 -1'}]
        r=node(POLICY,{'profile':profile,'actions':actions})
        self.assertEqual(r[0]['write_scope'],'exact-requests')
        self.assertEqual(r[1]['capability'],'command')
        self.assertEqual([r[i]['allowed'] for i in (1,2,3,5)],[True,False,False,False])
        profile['command_validation']=None
        r=node(POLICY,{'profile':profile,'actions':actions[:2]})
        self.assertFalse(r[1]['allowed'])

    def test_empty_chain_first_save_preflight_needs_no_fxp_family(self):
        pedal=FirstPedal(empty_chain=True)
        initial=[{'pong':'PONG '+VERSION+' Nov 12 2026 16:04:11'},
            {'reply':'FXS','lines':pedal.fxs()},{'reply':'PLIST','lines':pedal.plist()},
            {'reply':'SNAPS','lines':pedal.response('SNAPS')},{'reply':'GAIN','lines':pedal.response('GAIN')}]
        profile=fixture_profile()
        profile['family_capabilities']['usb-cdc']=['GAIN','PLOAD','PSAVE','SNAP','SNAPSAVE']
        actions=[{'command':'GAIN 0 -1'},{'preflight':['PSAVE 0 HyperRig_Test','SNAPSAVE 0']},
                 {'reply':'PSAVE 0 HyperRig_Test','lines':["PSAVE ok 0 'HyperRig_Test' 0 blocks capture=-1 ir=-1"]},
                 {'command':'SNAPSAVE 0'},{'command':'FXP 7 0 5'}]
        r=node(POLICY,{'profile':profile,'actions':initial+actions})[-len(actions):]
        self.assertTrue(r[0]['allowed'] and r[1]['allowed'] and r[3]['allowed'])
        self.assertFalse(r[4]['allowed'])

    def test_original_gain_knob_sends_qualified_command_with_empty_chain(self):
        source=app.checked(app.SOURCE/'web/tankg.html',app.SOURCE_SHA).decode('utf-8')
        begin=source.index('function buildGains()')
        body=source[begin:source.index('/* ============================================================ CRC32',begin)]
        script=r'''
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
const wires=[],knobs={},ctx=vm.createContext({HYPERRIG_MINI_BUILD:v.profile,
 S:{gain:[0,0],chain:{P:[],Q:[]}},ED:{},Date,edMark:()=>{},
 $:id=>({id,innerHTML:''}),knob:(element,options)=>{knobs[element.id]=options;return options;},
 document:{querySelectorAll:()=>[]}});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),ctx);
ctx.HyperRigMini.acceptPong(v.pong,'usb-cdc');
ctx.HyperRigMini.observeReply('LVL',['LVL in=0 out=0 g=0/0 b=0 s=0'],false,'usb-cdc');
ctx.Pedal={cmd:async line=>{if(!ctx.HyperRigMini.commandPolicy(line,'usb-cdc').allowed)throw Error('blocked original gain knob');
 wires.push(line);ctx.HyperRigMini.observeReply(line,['GAIN in=0 out=-1 dB'],false,'usb-cdc');return ['GAIN in=0 out=-1 dB'];}};
vm.runInContext(v.body+'\nbuildGains();',ctx);
(async()=>{knobs.gOut.onChange(-1);await Promise.resolve();await Promise.resolve();
 process.stdout.write(JSON.stringify({wires,gain:ctx.S.gain}));})().catch(e=>{process.stderr.write(String(e));process.exitCode=1});
'''
        profile=fixture_profile();profile['family_capabilities']['usb-cdc']=['GAIN']
        result=node(script,{'profile':profile,'pong':'PONG '+VERSION+' Nov 12 2026 16:04:11','body':body})
        self.assertEqual(result,{'wires':['GAIN 0 -1'],'gain':[0,-1]})


if __name__=='__main__':unittest.main()
