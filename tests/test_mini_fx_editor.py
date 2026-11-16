"""Offline evidence replay and original UI tests. No browser or pedal I/O.

Mutated reports are temporary negative fixtures, never hardware evidence.
"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import qualify_mini_fx_editor as fx
from tests.test_mini_app_protocol import node


BASE = 'build/hyperrig-mini-qualified-editor'
REMOVAL = {'path':'build/mini-fx-remove-01/report.json',
           'sha256':'307cf07fd35120c59a34d2045dcf4799abba0ec46af32f34ea5c84ffa0a70356'}


class FXEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = fx.baseline.validate_bundle(BASE)
        cls.report = json.loads(fx.read_ref(fx.BENCHMARK))

    def test_actual_archived_benchmark_roundtrip(self):
        result = fx.inspect_benchmark(self.report, self.bundle)
        self.assertTrue(result['replay_verified'])
        self.assertEqual(len(result['actual_readback_instances']), 9)
        self.assertEqual(result['measurement_instance_counts'], [0, 4, 8])
        self.assertEqual(result['rejected_requests_not_claimed_as_success'][0]['request'], 'FXE 9 1')
        self.assertFalse(result['UI_FX_interactions_physically_tested'])
        self.assertFalse(result['hardware_execution_attested_by_this_pure_function'])

    def test_raw_response_cannot_be_forged(self):
        report = copy.deepcopy(self.report)
        command = next(c for c in report['guard']['commands'] if c['line'] == 'FXP 3 0 -1')
        command['lines'] = ['FXP ok 11']
        with self.assertRaises(ValueError): fx.inspect_benchmark(report, self.bundle)

    def test_readback_wrong_type_parameter_or_enable_rejected(self):
        for before, after in [('boost', 'gate'), ('on=1', 'on=0'), ('p=-1,', 'p=1,')]:
            report = copy.deepcopy(self.report)
            rows = report['last_admitted_state']['FXS']
            index = next(i for i, line in enumerate(rows) if 'id=3 ' in line)
            self.assertIn(before, rows[index])
            rows[index] = rows[index].replace(before, after)
            with self.subTest(change=before), self.assertRaises(ValueError):
                fx.inspect_benchmark(report, self.bundle)

    def test_provenance_scope_restore_and_identity_rejected(self):
        for alter in (
            lambda r: r['source_sha256'].update({'tools/probe_mini_browser_latency.py': '0'*64}),
            lambda r: r.update(baseline_restoration_verified=False),
            lambda r: r['prepared'].update(image_sha256='0'*64),
            lambda r: r.update(automatic_retry=True),
            lambda r: r.update(result='fail'),
        ):
            report = copy.deepcopy(self.report); alter(report)
            with self.assertRaises(ValueError): fx.inspect_benchmark(report, self.bundle)

    def test_actual_qualification_has_no_removal_or_blanket_grant(self):
        value = fx.qualify(BASE)
        self.assertEqual(value['enabled_families'], fx.CORE_FAMILIES+fx.FX_FAMILIES)
        self.assertIsNone(value['removal_evidence'])
        self.assertFalse(value['blanket_write'])
        self.assertFalse(value['FX_persistence_physically_tested'])
        with self.assertRaises(ValueError): fx.inspect_removal({}, self.bundle)

    def test_actual_removal_report_enables_only_single_instance_family(self):
        report=json.loads(fx.read_ref(REMOVAL))
        proof=fx.inspect_removal(report,self.bundle)
        self.assertEqual(proof['actual_mutation_requests'],
                         ['GAIN 0 -12','FXA Q 99 boost','FXP 0 0 -1','FXR 0','PLOAD 0'])
        self.assertEqual(proof['native_RX_bytes'],15124)
        value=fx.qualify(BASE,removal_ref=REMOVAL)
        self.assertEqual(value['enabled_families'],fx.CORE_FAMILIES+fx.FX_FAMILIES+['FXR'])
        self.assertFalse(value['UI_FX_interactions_physically_tested'])
        self.assertEqual(value,fx.validate_qualification(value))

    def test_removal_failed_report_missing_raw_and_bad_snapshot_cannot_qualify(self):
        original=json.loads(fx.read_ref(REMOVAL))
        for case in ('failed','raw','snapshot','verification'):
            report=copy.deepcopy(original)
            if case=='failed': report['result']='fail'
            elif case=='raw': report['guard']['rx']=[]
            elif case=='snapshot': report['removed']=copy.deepcopy(report['added'])
            else: report['verification']['saved_baseline_restored']=False
            with self.subTest(case=case),self.assertRaises(ValueError): fx.inspect_removal(report,self.bundle)


POLICY = r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
const ctx=vm.createContext({HYPERRIG_MINI_BUILD:v.profile});
vm.runInContext(fs.readFileSync('app/mini/mini-profile-fx.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('app/mini/mini-fx-ui.js','utf8'),ctx);
const mini=ctx.HyperRigMini,out=[];
for(const action of v.actions){
 if(action.pong)out.push(mini.acceptPong(action.pong,action.transport||'usb-cdc'));
 else if(action.reply){mini.observeReply(action.reply,action.lines,!!action.timeout,'usb-cdc');out.push(null);}
 else if(action.add)out.push(ctx.HyperRigMiniFX.add(...action.add,'usb-cdc'));
 else out.push(mini.commandPolicy(action.command,action.transport||'usb-cdc'));
}
process.stdout.write(JSON.stringify(out));
"""


class FXPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = fx.baseline.validate_bundle(BASE)
        report = json.loads(fx.read_ref(fx.BENCHMARK))
        cls.fxt = report['plan']['actual_catalog']
        cls.fxs = report['last_admitted_state']['FXS']

    def run_policy(self, actions, *, remove=False, initial=None):
        profile = copy.deepcopy(self.bundle['profile'])
        profile['family_capabilities']['usb-cdc'] += fx.FX_FAMILIES+(['FXR'] if remove else [])
        # This in-memory policy fixture is not a qualification or a build input.
        seed = [{'pong': self.bundle['pong']}, {'reply':'FXT', 'lines':self.fxt},
                {'reply':'FXS', 'lines':self.fxs}] if initial is None else initial
        return node(POLICY, {'profile':profile, 'actions':seed+actions})[-len(actions):]

    def test_catalog_family_not_fixed_to_benchmark_types_or_values(self):
        result = self.run_policy([{'command':s} for s in ('FXA Q 99 delay', 'FXP 3 0 12', 'FXE 3 0', 'FXE 3 1')])
        self.assertTrue(all(x['allowed'] for x in result))
        bad = ('FXA Q 98 delay', 'FXA R 99 delay', 'FXA P 99 invented', 'FXP 3 0 999',
               'FXP 55 0 1', 'FXE 55 1', 'FXR 3', 'FXM 3 Q 0', 'FXL 3 1', 'PDEL 0', 'BOOT')
        self.assertTrue(all(not x['allowed'] for x in self.run_policy([{'command':s} for s in bad])))

    def test_removal_needs_its_family_and_current_serial_id(self):
        result = self.run_policy([{'command':s} for s in ('FXR 3', 'FXR 55', 'FXR 03')],remove=True)
        self.assertEqual([x['allowed'] for x in result], [True,False,False])
        rows = [s.replace('l=0', 'l=1') if 'id=3 ' in s else s for s in self.fxs]
        self.assertNotEqual(rows, self.fxs)
        result = self.run_policy([{'reply':'FXS','lines':rows}, {'command':'FXR 3'}, {'command':'FXA Q 99 delay'}], remove=True)
        self.assertFalse(result[1]['allowed'] or result[2]['allowed'])

    def test_added_or_removed_ids_require_fresh_fxs(self):
        result = self.run_policy([{'reply':'FXA Q 99 delay','lines':['FXA id=9 delay','FX cpu=1/10 ticks (10%) mem_fx=0 B']},
                                  {'command':'FXE 3 0'}, {'reply':'FXS','lines':self.fxs}, {'command':'FXE 3 0'}])
        self.assertFalse(result[1]['allowed']); self.assertTrue(result[3]['allowed'])
        result = self.run_policy([{'reply':'FXR 3','lines':['FXR ok cpu=1/10 ticks (10%) mem_fx=0 B']}, {'command':'FXR 3'}],remove=True)
        self.assertFalse(result[1]['allowed'])

    def test_add_location_checked_before_any_command(self):
        segs=[{'k':'fx','id':0},{'k':'amp'},{'k':'fx','id':7}]
        locations=[None, {'t':'serial','si':1}, {'t':'serial','si':0}, {'t':'serial','si':2},
                   {'t':'lane','si':0,'lane':'A'}, {'t':'newgrp','si':1}]
        result=self.run_policy([{'add':['boost',segs,loc]} for loc in locations])
        self.assertEqual([r['allowed'] for r in result], [True,True,False,False,False,False])

    def test_identity_transport_and_complete_fxt_still_required(self):
        result=self.run_policy([{'command':'FXA Q 99 boost','transport':'ble-nus'},
                                {'reply':'FXT','lines':self.fxt[:-1]}, {'command':'FXA Q 99 boost'}])
        self.assertFalse(result[0]['allowed'] or result[2]['allowed'])
        result=self.run_policy([{'command':'FXA Q 99 boost'}],initial=[])
        self.assertFalse(result[0]['allowed'])

    def test_original_per_bank_and_total_limits_without_an_extra_budget_gate(self):
        example=next(row for row in self.fxs if row.startswith('FX P0 '))
        footer=[row for row in self.fxs if not row.startswith('FX ')]
        import re
        def rows(p,q):
            return [re.sub(r'^FX P0 id=\d+',f'FX {bank}{pos} id={bid}',example)
                    for bank,count,start in [('P',p,0),('Q',q,p)]
                    for pos,bid in enumerate(range(start,start+count))]+footer
        result=self.run_policy([{'reply':'FXS','lines':rows(10,0)},
                                {'command':'FXA P 99 boost'},{'command':'FXA Q 99 boost'},
                                {'reply':'FXS','lines':rows(10,6)},{'command':'FXA Q 99 boost'}])
        self.assertEqual([result[i]['allowed'] for i in (1,2,4)],[False,True,False])

    def test_new_preset_one_save_scene_and_reload_are_not_tied_to_trial_zero(self):
        report=json.loads(fx.read_ref(fx.BENCHMARK))
        before=report['before']['responses']
        initial=[{'pong':self.bundle['pong']},{'reply':'FXT','lines':self.fxt},
                 {'reply':'FXS','lines':self.fxs},{'reply':'PLIST','lines':before['PLIST']},
                 {'reply':'SNAPS','lines':before['SNAPS']}]
        next_list=[*before['PLIST'][:-1], "PRE 1 9 0 -1 'HyperRig Test' t=- s=1 amp=1",'PLIST end current=1']
        actions=[{'command':'PLOAD 1'}, {'command':'PSAVE 1 HyperRig Test'},
                 {'reply':'PSAVE 1 HyperRig Test','lines':["PSAVE ok 1 'HyperRig Test' 9 blocks capture=0 ir=-1"]},
                 {'command':'SNAPSAVE 0'},{'reply':'PLIST','lines':next_list}, {'command':'PLOAD 1'}]
        result=self.run_policy(actions,initial=initial)
        self.assertEqual([result[i]['allowed'] for i in (0,1,3,5)],[False,True,True,True])


UI_ORIGINAL = r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
const html=v.html;
function piece(a,b){return html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));}
const sent=[],toasts=[];
const ctx=vm.createContext({HYPERRIG_MINI_BUILD:v.profile,console});
vm.runInContext(fs.readFileSync('app/mini/mini-profile-fx.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('app/mini/mini-fx-ui.js','utf8'),ctx);
ctx.HyperRigMini.acceptPong(v.pong,'usb-cdc');
ctx.HyperRigMini.observeReply('FXT',v.fxt,false,'usb-cdc');
ctx.HyperRigMini.observeReply('FXS',v.fxs,false,'usb-cdc');
Object.assign(ctx,{DEMO:false,txn:0,SerialTransport:{},Log:{act(){}},toast:(m)=>toasts.push(m),
 S:{chain:{P:[{id:0,lane:0}],Q:[]}}, edQ:()=>1,edMark:()=>{},
 curSegs:()=>[{k:'fx',id:0},{k:'amp'}],
 commitSegs:async(segs,o)=>{sent.push({plan:ctx.planCommands(o.cur,ctx.flatten(segs,o.cur))});},
 isCpuErr:()=>false,isMemErr:()=>false,isIrErr:()=>false});
ctx.Pedal={tr:ctx.SerialTransport,cmd:async line=>{sent.push(line);return ['FXA id=9 boost','FX cpu=1/2 ticks (50%) mem_fx=0 B'];}};
vm.runInContext('const PQ=["P","Q"];'+piece('function cloneSegs(', 'function applyFlat(')+
 piece('function lisKeep(', 'function planMix(')+piece('async function addFx(', '/* el bloque vecino')+
 piece('async function replaceFx(', '/* alta en loc'),ctx);
(async()=>{
 await ctx.addFx('boost',{t:'serial',si:0});
 const before=sent.length;
 await ctx.replaceFx(0,'boost');
 const afterReplacement=sent.length;
 await ctx.addFx('boost',{t:'serial',si:1});
 process.stdout.write(JSON.stringify({before,afterReplacement,sent,toasts}));
})().catch(e=>{console.error(e);process.exit(1);});
"""

COMPOUND_ORIGINAL = r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
function piece(a,b){return v.html.slice(v.html.indexOf(a),v.html.indexOf(b,v.html.indexOf(a)));}
const sent=[],changes=[];
const ctx=vm.createContext({HYPERRIG_MINI_BUILD:v.profile,console});
vm.runInContext(fs.readFileSync('app/mini/mini-profile-fx.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('app/mini/mini-fx-ui.js','utf8'),ctx);
ctx.HyperRigMini.acceptPong(v.pong,'usb-cdc');
ctx.HyperRigMini.observeReply('FXT',v.fxt,false,'usb-cdc');
ctx.HyperRigMini.observeReply('FXS',v.fxs,false,'usb-cdc');
Object.assign(ctx,{DEMO:false,txn:0,FX_MAXGRP:3,SerialTransport:{},toast:()=>{},
 S:{chain:{P:[{id:0,lane:0}],Q:[{id:7,lane:0}]},mix:{},xo:{},xeq:{},xoOk:false},
 planMix:()=>[],applyFlat:()=>{changes.push('optimistic UI');return {};},
 fxGone:new Set(),edQ:()=>1,render:()=>{},edDropBlock:()=>{},edMark:()=>{},
 loadChain:async()=>{},reply:(rows)=>rows[0]});
ctx.Pedal={tr:ctx.SerialTransport,cmd:async line=>{sent.push(line);return ['FXR ok'];}};
vm.runInContext('const PQ=["P","Q"];'+piece('function cloneSegs(', 'function applyFlat(')+
 piece('function lisKeep(', 'function planMix(')+piece('async function commitSegs(', 'async function mutate('),ctx);
(async()=>{
 const result=await ctx.commitSegs([{k:'fx',id:7},{k:'amp'}],{remove:[0]});
 process.stdout.write(JSON.stringify({result,sent,changes}));
})().catch(e=>{console.error(e);process.exit(1);});
"""


class FXOriginalUITests(unittest.TestCase):
    def test_real_original_add_preflight_and_append_have_no_hidden_move(self):
        bundle=fx.baseline.validate_bundle(BASE)
        profile=copy.deepcopy(bundle['profile'])
        profile['family_capabilities']['usb-cdc']+=fx.FX_FAMILIES
        source=(fx.ROOT/bundle['app_directory']/'tankmini.html').read_text('utf-8')
        html,_=fx.derive_html(source,bundle['profile'],profile)
        report=json.loads(fx.read_ref(fx.BENCHMARK))
        result=node(UI_ORIGINAL,{'html':html,'profile':profile,'pong':bundle['pong'],
            'fxt':report['plan']['actual_catalog'],'fxs':report['before']['responses']['FXS']})
        self.assertEqual(result['before'],0)
        self.assertEqual(result['afterReplacement'],0)
        self.assertEqual(result['sent'],['FXA P 99 boost',{'plan':[]}])

    def test_original_composite_remove_move_rejected_before_remove_or_optimistic_ui(self):
        bundle=fx.baseline.validate_bundle(BASE)
        profile=copy.deepcopy(bundle['profile'])
        profile['family_capabilities']['usb-cdc']+=fx.FX_FAMILIES+['FXR']
        html,_=fx.derive_html((fx.ROOT/bundle['app_directory']/'tankmini.html').read_text('utf-8'),bundle['profile'],profile)
        report=json.loads(fx.read_ref(fx.BENCHMARK))
        result=node(COMPOUND_ORIGINAL,{'html':html,'profile':profile,'pong':bundle['pong'],
            'fxt':report['plan']['actual_catalog'],'fxs':report['last_admitted_state']['FXS']})
        self.assertEqual(result,{'result':False,'sent':[],'changes':[]})

    def test_real_bundle_sealed_and_runtime_does_not_replay_benchmark(self):
        with tempfile.TemporaryDirectory(dir=fx.ROOT/'build',prefix='fx-editor-test-') as temp:
            output=Path(temp)/'bundle'
            proof=fx.build_bundle(BASE,output)
            self.assertFalse(proof['historical_evidence_replayed_on_launch'])
            with patch.object(fx,'inspect_benchmark',side_effect=AssertionError('runtime replay forbidden')):
                self.assertEqual(proof,fx.validate_bundle(output))
            self.assertEqual(proof['profile']['family_capabilities']['usb-cdc'],fx.CORE_FAMILIES+fx.FX_FAMILIES)
            with self.assertRaises(ValueError): fx.build_bundle(BASE,output)
            (output/'app/web/mini-profile.js').write_text('altered',encoding='utf-8')
            with self.assertRaises(ValueError): fx.validate_bundle(output)

    def test_real_removal_bundle_preserves_attribution_and_eight_families(self):
        with tempfile.TemporaryDirectory(dir=fx.ROOT/'build',prefix='fx-editor-test-') as temp:
            output=Path(temp)/'bundle'
            proof=fx.build_bundle(BASE,output,removal_ref=REMOVAL)
            self.assertEqual(proof['profile']['family_capabilities'],
                             {'usb-cdc':fx.CORE_FAMILIES+fx.FX_FAMILIES+['FXR']})
            base=fx.ROOT/BASE/'app'
            licenses=[p for p in base.rglob('*') if p.is_file() and p.name in fx.baseline.app.LICENSES]
            self.assertTrue(licenses)
            for path in licenses:
                self.assertEqual(path.read_bytes(),(output/'app'/path.relative_to(base)).read_bytes())


if __name__=='__main__': unittest.main()
