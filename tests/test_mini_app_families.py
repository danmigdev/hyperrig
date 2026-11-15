"""Offline family qualification and original editor/queue tests; no device I/O.

All reports which assert hardware execution below are temporary schema fixtures,
explicitly labelled as such. They are never retained as research evidence.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import build_mini_app as app
from tools import probe_mini_app_mutation as mutation
from tools import probe_mini_app as readonly
from tests.test_mini_app_mutation import FXT, Pedal, VERSION, reference
from tests.test_mini_app_protocol import node


PONG = 'PONG '+VERSION+' Nov 12 2026 16:04:11'
POLICY = r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
const context=vm.createContext({HYPERRIG_MINI_BUILD:v.profile});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),context);
const mini=context.HyperRigMini,out=[];
for(const a of v.actions){
 const tr=a.transport===undefined?'usb-cdc':a.transport;
 if(a.pong)out.push(mini.acceptPong(a.pong,tr));
 else if(a.reply){mini.observeReply(a.reply,a.lines,!!a.timeout,tr);out.push(null);}
 else if(a.reset){mini.resetIdentity();out.push(null);}
 else if(a.preflight)out.push(mini.preflight(a.preflight,tr));
 else out.push(mini.commandPolicy(a.command,tr));
}
process.stdout.write(JSON.stringify(out));
"""


def fixture_profile():
    p = app.load_profile()
    p.update(firmware_version=VERSION, image_sha256='a'*64, hardware_verified=True,
             family_capabilities={'usb-cdc': sorted(app.FAMILY_COMMANDS)},
             family_validation={'usb-cdc': [{'path':'offline-schema-fixture','sha256':'b'*64}]})
    p['capabilities']['read'] = True
    return p


def seed(*, scenes=False):
    pedal = Pedal(scenes=scenes)
    return [{'pong': PONG}, {'reply':'FXT','lines':FXT}, {'reply':'FXS','lines':pedal.fxs()},
            {'reply':'PLIST','lines':pedal.plist()}, {'reply':'SNAPS','lines':pedal.response('SNAPS')}]


class FamilyRuntimeTests(unittest.TestCase):
    def policy(self, actions, profile=None, *, initial=None):
        return node(POLICY, {'profile':profile or fixture_profile(), 'actions':(seed() if initial is None else initial)+actions})[-len(actions):]

    def test_representative_family_allows_actual_fxt_range_and_current_ids(self):
        values = [-12, -1, 0, 6, 7, 24]
        results = self.policy([{'command':f'FXP 7 0 {v}'} for v in values]+[{'command':'FXE 7 0'},{'command':'FXE 7 1'}])
        self.assertTrue(all(r['allowed'] and r['capability']=='family' for r in results))
        bad = ['FXP 7 0 -13','FXP 7 0 25','FXP 8 0 6','FXP 7 1 6','FXP 07 0 6','FXP 7 0 6.0',
               'FXP 7 0 2147483648','FXE 7 2','FXE 8 0','PDEL 31','LDBEGIN 12','FSA 0']
        self.assertTrue(all(not r['allowed'] for r in self.policy([{'command':c} for c in bad])))

    def test_new_fxt_parameter_is_protocol_bounded_not_probe_selection_limited(self):
        types = [FXT[0], *FXT[1:-1], 'FXT  3 release_ms 5..1000 (120)', FXT[-1]]
        results = self.policy([{'reply':'FXT','lines':types}, {'command':'FXP 7 3 1000'}, {'command':'FXP 7 3 1001'}])
        self.assertTrue(results[1]['allowed']); self.assertFalse(results[2]['allowed'])

    def test_context_needs_complete_valid_responses_and_recovers_after_readback(self):
        for query, lines, command in [('FXT',FXT,'FXP 7 0 7'), ('FXS',Pedal().fxs(),'FXE 7 1'),
                                       ('PLIST',Pedal().plist(),'PLOAD 0'), ('SNAPS',['SNAPS 0000 current=-1'],'SNAPSAVE 3')]:
            for invalid in [lines[:-1], ['ERR query'], [*lines,lines[-1]]]:
                with self.subTest(query=query,invalid=invalid):
                    r = self.policy([{'reply':query,'lines':invalid},{'command':command},
                                     {'reply':query,'lines':lines},{'command':command}])
                    self.assertFalse(r[1]['allowed']); self.assertTrue(r[3]['allowed'])
        duplicate = [Pedal().fxs()[0], *Pedal().fxs()]
        self.assertFalse(self.policy([{'reply':'FXS','lines':duplicate},{'command':'FXE 7 1'}])[1]['allowed'])
        self.assertFalse(self.policy([{'reply':'FXT','lines':FXT,'timeout':True},{'command':'FXP 7 0 7'}])[1]['allowed'])

    def test_load_invalidates_old_ids_until_new_fxs_arrives(self):
        next_fxs = [line.replace('id=7 ','id=22 ') for line in Pedal().fxs()]
        r = self.policy([{'reply':'PLOAD 4','lines':["PLOAD ok 4 'Other' missing=0 capture=-1 ir=-1 ms=1"]},
                         {'command':'FXP 7 0 6'}, {'reply':'FXS','lines':next_fxs},
                         {'command':'FXP 7 0 6'}, {'command':'FXP 22 0 10'}])
        self.assertFalse(r[1]['allowed'] or r[3]['allowed']); self.assertTrue(r[4]['allowed'])

    def test_presets_and_names_are_operational_with_original_overwrite_flow(self):
        good = ['PLOAD 0','PLOAD 4','PSAVE 12 Another name','PSAVE 0 Original','PSAVE 31 '+('é'*23),
                'PSAVE 30 '+('😀'*11)]
        bad = ['PLOAD 12','PLOAD 32','PSAVE 32 name','PSAVE 1 '+('a'*24),'PSAVE 1 '+('😀'*12),
               'PSAVE 1 name\nPDEL 0','PSAVE 1 a\tb','PSAVE 1 name ','PSAVE 01 name']
        result = self.policy([{'command':c} for c in good+bad])
        self.assertEqual([r['allowed'] for r in result], [True]*len(good)+[False]*len(bad))

    def test_snapshot_selection_and_creation_use_current_context(self):
        result = self.policy([{'command':c} for c in ['SNAP 1','SNAP 0','SNAPSAVE 0','SNAPSAVE 2','SNAPSAVE 3','SNAPSAVE 4']],initial=seed(scenes=True))
        self.assertEqual([r['allowed'] for r in result], [True,False,True,True,True,False])

    def test_save_preflight_plans_new_slot_but_only_actual_ack_changes_context(self):
        initial = seed()
        initial[-2]['lines'] = ['PLIST end current=-1']
        r = self.policy([{'preflight':['PSAVE 12 Any name','SNAPSAVE 0']},{'command':'SNAPSAVE 0'},
                         {'reply':'PSAVE 12 Any name','lines':["PSAVE ok 12 'Any name' 1 blocks capture=-1 ir=-1"]},
                         {'command':'SNAPSAVE 3'}],initial=initial)
        self.assertTrue(r[0]['allowed']); self.assertFalse(r[1]['allowed']); self.assertTrue(r[3]['allowed'])
        p = fixture_profile(); p['family_capabilities']['usb-cdc'].remove('SNAPSAVE')
        self.assertFalse(self.policy([{'preflight':['PSAVE 12 Any name','SNAPSAVE 0']}],p)[0]['allowed'])

    def test_mismatched_or_failed_save_ack_does_not_open_scene_save(self):
        for lines in [["PSAVE ok 13 'Wrong' 1 blocks capture=-1 ir=-1"], ['ERR PSAVE failed'], ['PSAVE ok 12']]:
            r=self.policy([{'reply':'PSAVE 12 Name','lines':lines},{'command':'SNAPSAVE 0'}])
            self.assertFalse(r[1]['allowed'])
        self.assertFalse(self.policy([{'reply':'SNAPSAVE 0','lines':['SNAPSAVE ok 0 preset=31']},
                                      {'command':'SNAP 0'}])[1]['allowed'])

    def test_usb_proof_does_not_enable_ble_and_disconnect_forgets_context(self):
        for tr in ('ble-nus',None,'usb-midi'):
            self.assertFalse(self.policy([{'command':'FXP 7 0 7','transport':tr}])[0]['allowed'])
        result = self.policy([{'reset':True},{'pong':PONG},{'command':'FXP 7 0 7'}])
        self.assertFalse(result[2]['allowed'])
        initial=seed()
        for a in initial:a['transport']='ble-nus'
        self.assertFalse(self.policy([{'command':'FXP 7 0 7','transport':'ble-nus'}],initial=initial)[0]['allowed'])


class FamilyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mini-family-test-',dir=app.ROOT/'build')
        self.addCleanup(self.temp.cleanup); self.path=Path(self.temp.name)
        image=self.path/'fixture.bin';image.write_bytes(b'OFFLINE SCHEMA TEST; NOT FIRMWARE')
        self.spec={'target':'tank-mini','architecture':'standalone-ultrarig-port','firmware_version':VERSION,
                   'image_path':app.relative(image),'image_sha256':app.sha(image.read_bytes()),'hardware_verified':True,
                   'capabilities':{'read':True,'write':False,'panel':False}}
        self.manifest=self.path/'manifest.json'; self.manifest.write_text(json.dumps(self.spec),encoding='utf-8')

    def report(self, action='live', operation='FXP'):
        path=self.path/(action+'-'+operation);path.mkdir()
        pedal=Pedal(scenes=True);bank=reference(path/'bank.json',pedal.bank())
        args=argparse.Namespace(action=action,port='FAKE',firmware_manifest=self.manifest,log=path/'trace.jsonl',
            backup=path/'backup.json',report=path/'proof.json',operation=operation,block=7,
            parameter=0 if operation=='FXP' else None,value=None,slot=31,
            bank_backup=bank['path'],bank_sha256=bank['sha256'])
        evidence=mutation.run_live(args,enumerate_fn=lambda:[{'device':'FAKE','vid':readonly.VID,'pid':readonly.PID}],
                                   open_fn=lambda _:pedal,clock=pedal.clock)
        self.assertFalse(evidence['hardware_executed']); self.assertEqual(evidence['physically_exercised_requests'],{})
        return evidence,path

    def schema_fixture(self, evidence, path):
        """Exercise the validator with explicitly labelled in-memory fake provenance."""
        e=copy.deepcopy(evidence);e.update(hardware_executed=True,offline_schema_test=True,
            physically_exercised_requests=evidence['simulated_requests'],simulated_requests={})
        backup=json.loads((path/'backup.json').read_text('utf-8'))
        backup.update(hardware_executed=True,offline_schema_test=True)
        e['backup']=reference(path/'backup.json',backup)
        rows=[json.loads(line) for line in (path/'trace.jsonl').read_text('utf-8').splitlines()]
        rows[0].update(hardware_executed=True,offline_schema_test=True)
        (path/'trace.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        e['trace']=mutation.file_reference(path/'trace.jsonl')
        return e

    def load(self, reports, commands, *, transport='usb-cdc'):
        spec=copy.deepcopy(self.spec);spec['family_capabilities']={transport:commands}
        spec['family_validation']={transport:[reference(self.path/f'input-{i}.json',e) for i,e in enumerate(reports)]}
        p=self.path/'qualified.json';p.write_text(json.dumps(spec),encoding='utf-8')
        return app.load_profile(p)

    def test_mock_output_never_qualifies_families(self):
        evidence,_=self.report()
        with self.assertRaises(ValueError):self.load([evidence],['FXP'])

    def test_combine_representative_trials_without_requiring_all_values(self):
        e,p=self.report('save');e=self.schema_fixture(e,p)
        f,q=self.report('live','FXE');f=self.schema_fixture(f,q)
        profile=self.load([e,f],sorted(app.FAMILY_COMMANDS))
        qual=profile['family_qualification']['usb-cdc']
        self.assertEqual(qual['enabled_families'],sorted(app.FAMILY_COMMANDS))
        self.assertFalse(qual['every_value_physically_tested'] or profile['capabilities']['write'])
        self.assertEqual(qual['physically_exercised_requests']['PSAVE'],['PSAVE 31 HyperRig_Test'])
        result=node(POLICY,{'profile':profile,'actions':seed()+[{'command':'PSAVE 12 A different preset'}, {'command':'FXP 7 0 -12'}]})
        self.assertTrue(result[-1]['allowed'] and result[-2]['allowed'])

    def test_wrong_image_version_protocol_transport_or_restoration_rejected(self):
        e,p=self.report();e=self.schema_fixture(e,p)
        for field,value in [('image_sha256','0'*64),('firmware_version',VERSION+' other'),('hardware_executed',False),
                            ('editor_source_sha256','0'*64),('protocol_binding',{}),('transport','ble-nus'),
                            ('restoration_verified',False),('every_value_physically_tested',True),
                            ('simulated_requests',{'FXP':['FXP 7 0 7']})]:
            bad=copy.deepcopy(e);bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.load([bad],['FXP'])
        with self.assertRaises(ValueError):self.load([e],['FXP'],transport='ble-nus')
        with self.assertRaises(ValueError):self.load([e],['FXE'])

    def test_trace_must_back_actual_tx_raw_reply_completion_and_identity(self):
        e,p=self.report();e=self.schema_fixture(e,p)
        source=[json.loads(line) for line in (p/'trace.jsonl').read_text('utf-8').splitlines()]
        changes=[('tx','hex','00'),('rx','bytes',99999),('complete','lines',99999),
                 ('mutation_start','hardware_executed',False),('line','line','invented')]
        for event,key,value in changes:
            rows=copy.deepcopy(source);next(r for r in rows if r['event']==event)[key]=value
            trace=p/'tampered.jsonl';trace.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
            bad=copy.deepcopy(e);bad['trace']=mutation.file_reference(trace)
            with self.subTest(event=event),self.assertRaises(ValueError):self.load([bad],['FXP'])
        for field in ('ack_verified','readback_verified','ack','state_sha256'):
            bad=copy.deepcopy(e)
            for o in bad['representative_observations']:o[field]=False
            with self.subTest(field=field),self.assertRaises(ValueError):self.load([bad],['FXP'])

    def test_persistence_requires_reload_scene_and_cleanup_not_ack_only(self):
        e,p=self.report('save');e=self.schema_fixture(e,p)
        for field in ('persistence_readback_verified','snapshot_persistence_readback_verified','temporary_slot_deleted'):
            bad=copy.deepcopy(e);bad['trial'][field]=False
            with self.subTest(field=field),self.assertRaises(ValueError):self.load([bad],['PSAVE','SNAPSAVE'])
        bad=copy.deepcopy(e)
        for o in bad['representative_observations']:o['persistence_readback_verified']=False
        with self.assertRaises(ValueError):self.load([bad],['PSAVE'])

    def test_closed_family_schema_keeps_upload_and_panel_distinct(self):
        for bad in ({'usb-cdc':['PDEL']},{'usb-cdc':['FXP','FXP']},{'usb-cdc':[]},{'usb-cdc':['*']},
                    {'usb-cdc':['FXA']},{'ble-nus':['LDBEGIN']},{'usb-midi':['FXP']}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):app.family_grants(bad)


class OriginalFamilyFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=app.checked(app.SOURCE/'web/tankg.html',app.SOURCE_SHA).decode('utf-8')
        cls.html=app.derive_html(source,fixture_profile())[0]

    def test_original_queue_rechecks_ids_after_preceding_preset_load(self):
        code=r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8')),wires=[];let c;
const tr={isOpen:()=>true,write:text=>{wires.push(text);queueMicrotask(()=>c.Pedal.onLine("PLOAD ok 4 'Other' missing=0 capture=-1 ir=-1 ms=1"));return Promise.resolve();}};
c=vm.createContext({HYPERRIG_MINI_BUILD:v.profile,DEMO:false,S:{},SerialTransport:tr,pickTransport:()=>tr,
 Log:{ev:()=>{},cmd:()=>{}},gdSent:()=>null,gdDone:()=>{},strayLines:()=>[],setAlert:()=>{},blePairLine:()=>false,
 noAnswer:()=>{},performance,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),c);
c.HyperRigMini.acceptPong(v.seed[0].pong,'usb-cdc');for(const a of v.seed.slice(1))c.HyperRigMini.observeReply(a.reply,a.lines,false,'usb-cdc');
const start=v.html.indexOf('const Pedal = {'),end=v.html.indexOf('/* ============================================================ estado',start);
vm.runInContext(v.html.slice(start,end)+'\nglobalThis.Pedal=Pedal;',c);
(async()=>{const results=await Promise.all([c.Pedal.cmd('PLOAD 4','PLOAD'),c.Pedal.cmd('FXP 7 0 8','FXP')]);process.stdout.write(JSON.stringify({wires,results}));})()
 .catch(e=>{process.stderr.write(String(e));process.exitCode=1});
"""
        r=node(code,{'profile':fixture_profile(),'html':self.html,'seed':seed()})
        self.assertEqual(r['wires'],['PLOAD 4\n']);self.assertTrue(r['results'][1][0].startswith('ERR MINI_APP'))

    def test_original_save_preset_sends_new_name_slot_then_automatic_scene(self):
        code=r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8')),wires=[],toasts=[];let c;
const state={preset:0,saved:false,snap:false};
const tr={isOpen:()=>true,write:text=>{
 wires.push(text);const line=text.trimEnd();let answer;
 if(line==='PSAVE 12 Another preset'){state.preset=12;state.saved=true;answer="PSAVE ok 12 'Another preset' 1 blocks capture=-1 ir=-1";}
 else if(line==='SNAPS')answer='SNAPS 0000 current=-1';
 else if(line==='SNAPSAVE 0'){state.snap=true;answer='SNAPSAVE ok 0 preset=12';}
 else throw Error('unexpected '+line);
 queueMicrotask(()=>c.Pedal.onLine(answer));return Promise.resolve();}};
c=vm.createContext({HYPERRIG_MINI_BUILD:v.profile,DEMO:false,PH:false,curPreset:0,SerialTransport:tr,pickTransport:()=>tr,
 S:{snap:-1,snaps:[0,0,0,0],pendName:''},ED:{ep:0,seq:0,p:new Map(),on:false,aeq:false},
 Log:{act:()=>{},ev:()=>{},cmd:()=>{}},toast:(...a)=>toasts.push(a),renderPresets:()=>{},
 readPlist:async()=>({ok:true,list:[]}),presetName:()=> 'Another preset',SLOT:i=>'ABCD'[i%4],
 aeqSettle:async()=>{},evSince:async()=>null,edFresh:async()=>{},edMoved:()=>false,
 evMoves:()=>false,edClearUpTo:()=>{},loadPresets:()=>{},loadSnaps:async()=>{},
 reply:(lines,p)=>lines.find(l=>l.startsWith(p))||'',plist:[],plistHave:false,
 gdSent:()=>null,gdDone:()=>{},strayLines:()=>[],setAlert:()=>{},blePairLine:()=>false,
 noAnswer:()=>{},performance,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),c);
c.HyperRigMini.acceptPong(v.seed[0].pong,'usb-cdc');for(const a of v.seed.slice(1))c.HyperRigMini.observeReply(a.reply,a.lines,false,'usb-cdc');
let start=v.html.indexOf('const Pedal = {'),end=v.html.indexOf('/* ============================================================ estado',start);
vm.runInContext(v.html.slice(start,end)+'\nglobalThis.Pedal=Pedal;',c);
start=v.html.indexOf('async function sceneAOnSave(');end=v.html.indexOf('/*PRESET-IO-BEGIN*/',start);
vm.runInContext(v.html.slice(start,end),c);
(async()=>{await c.savePreset(12,null);process.stdout.write(JSON.stringify({wires,toasts,state}));})()
 .catch(e=>{process.stderr.write(String(e));process.exitCode=1});
"""
        r=node(code,{'profile':fixture_profile(),'html':self.html,'seed':seed()})
        self.assertEqual(r['wires'],['PSAVE 12 Another preset\n','SNAPS\n','SNAPSAVE 0\n'])
        self.assertTrue(r['state']['saved'] and r['state']['snap'])
        self.assertFalse(any('unavailable' in str(t) for t in r['toasts']))


if __name__ == '__main__':
    unittest.main()
