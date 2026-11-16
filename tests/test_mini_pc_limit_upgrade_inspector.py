"""Actual frozen images and fake HYW1/HYRN only; no device enumeration or I/O."""
import copy
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import inspect_mini_pc_limit_upgrade as inspect
from tools import install_mini_app as install
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_app_writer_protocol import changed_record
from tests.test_mini_installed_nor_inspector import nor_evidence
from tests import test_mini_installed_nor_inspector as nor_fixture
from tools.recover_mini_read_v6 import BoundedCommandRecoveryTransport


class UpgradeInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = (inspect.ROOT/inspect.upgrade.BACKUP_PATH).read_bytes()
        cls.old = (inspect.ROOT/inspect.upgrade.revision.BASELINE_IMAGE).read_bytes()
        cls.target = (inspect.upgrade.NEW_DIR/'hyperrig-mini.app-area.bin').read_bytes()
        before = bytearray(cls.stock); before[0x4000:0x82000] = cls.old
        for address in (0x82020,0xBE020,0xBF020): before[address] ^= 0x55
        cls.before = bytes(before)
        cls.after = cls.before[:0x4000]+cls.target+cls.before[0x82000:]
        plan = replace(fixture(),preimage=cls.old,candidate=cls.target,sector_order=(0x4000,))
        fake = FakeOperational(plan); fake.flash = bytearray(cls.before)
        cls.plan, cls.trace, cls.journal = plan, [], []
        original = fake.exchange
        def exchange(cdb,data_out=None,read_length=0):
            row = {'stage':'writer','state':'before','cdb':cdb.hex(),
                   'out_bytes':len(data_out) if data_out is not None else 0,'in_bytes':read_length}
            cls.trace.append(dict(row)); raw = original(cdb,data_out,read_length)
            row.update(state='after',response_bytes=len(raw),response_sha256=inspect.sha(raw))
            if len(raw) <= 128: row['response_hex'] = raw.hex()
            cls.trace.append(row); return raw
        fake.exchange = exchange
        session = install.MiniAppInstallerSession(fake,plan,journal=cls.journal.append,known_free_slot=True)
        with patch('time.sleep'): session.upload_and_start(IMAGE,expected_sha256=install.sha(IMAGE))
        session.initialize_spi(); session.verify_complete_preimage(); session.install_application()
        cls.final_audit = session.last_audit

    def audit(self,journal=None):
        return inspect.writer_audits(self.journal if journal is None else journal,self.before,self.target,
                                     slot=self.plan.slot,build_tag=self.plan.build_tag)

    def test_full_NOR_preserves_actual_runtime_differences(self):
        result = inspect.compare_images(self.stock,self.before,self.target,self.after)
        self.assertEqual(result['changed_sectors'],[0x4000])
        self.assertEqual(len([r for r in result['preserved_regions'] if r['differs_from_stock_backup']]),3)
        self.assertTrue(result['external_regions_unchanged_from_fresh_read'])

    def test_stock_restoration_or_any_external_change_is_rejected(self):
        for address in (0,0x3fff,0x82000,0xBE000,0xBF000,0xFF000,0xfffff):
            damaged = bytearray(self.after); damaged[address] ^= 1
            with self.subTest(address=address), self.assertRaises(ValueError):
                inspect.compare_images(self.stock,self.before,self.target,bytes(damaged))
        wrong = self.after[:0x82000]+self.stock[0x82000:]
        with self.assertRaises(ValueError): inspect.compare_images(self.stock,self.before,self.target,wrong)

    def test_wrong_parent_candidate_unit_or_extent_is_rejected(self):
        for index in range(4):
            values = [self.stock,self.before,self.target,self.after]
            raw = bytearray(values[index]); raw[0x4000 if index == 1 else 0] ^= 1; values[index] = bytes(raw)
            with self.subTest(index=index), self.assertRaises(ValueError): inspect.compare_images(*values)
        with self.assertRaises(ValueError): inspect.compare_images(self.stock,self.before,self.target,self.after[:-1])

    def test_every_raw_audit_matches_independent_wire_model(self):
        result = self.audit()
        self.assertEqual(result['final_raw_audit'],self.final_audit)
        self.assertEqual((result['erase'],result['program'],result['wren']),(1,16,17))
        self.assertEqual(result['program_order'],list(range(0x4100,0x5000,256))+[0x4000])
        self.assertTrue(result['virtual_NOR_matches_candidate'])
        inspect.bind_writer_replies(self.journal,self.trace)
        proof = inspect.history.inspect_history(self.journal,self.trace,self.before,self.target,[0x4000])
        self.assertEqual(proof['program_commands'],16)

    def test_valid_CRC_cannot_hide_changed_target_state(self):
        for offset,value in ((24,1),(28,34),(68,18),(72,2),(76,15),(80,1),(84,123),
                             (88,259),(92,0),(96,0x7fff),(108,0),(60,1),(64,0x40)):
            journal = copy.deepcopy(self.journal)
            index = max(i for i,row in enumerate(journal) if row['event'] == 'audit_raw')
            raw = changed_record(bytes.fromhex(journal[index]['record_hex']),offset,value)
            journal[index].update(record_hex=raw.hex(),sha256=inspect.sha(raw))
            journal[index-1]['sha256'] = inspect.sha(raw)
            with self.subTest(offset=offset), self.assertRaises(ValueError): self.audit(journal)

    def test_raw_audit_must_be_the_received_FD88_response(self):
        journal = copy.deepcopy(self.journal)
        row = next(row for row in journal if row['event'] == 'audit_raw'); row['sha256'] = '0'*64
        with self.assertRaises(ValueError): self.audit(journal)
        trace = copy.deepcopy(self.trace); del trace[-2:]
        with self.assertRaises(ValueError): inspect.bind_writer_replies(self.journal,trace)

    def test_page_readback_hash_cannot_be_invented(self):
        journal = copy.deepcopy(self.journal)
        reply = next(row for row in journal if row['event'] == 'command_reply' and row['opcode'] == 'fd7f')
        reply['sha256'] = '0'*64
        with self.assertRaises(ValueError): self.audit(journal)

    def test_header_page_first_is_rejected(self):
        journal = copy.deepcopy(self.journal)
        intent = next(row for row in journal if row['event'] == 'command_intent' and row['opcode'] == 'fb7c')
        raw = bytearray.fromhex(intent['cdb_hex']); raw[10:14] = (0x4000).to_bytes(4,'big')
        intent['cdb_hex'] = raw.hex()
        with self.assertRaises(ValueError): self.audit(journal)

    def test_terminal_or_missing_audit_is_not_success(self):
        for kind in ('terminal','missing'):
            journal = copy.deepcopy(self.journal)
            if kind == 'terminal': journal.append({'event':'terminal_error'})
            else: del journal[max(i for i,row in enumerate(journal) if row['event'] == 'audit_raw')]
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.audit(journal)

    def test_two_real_reader_counter_streams_are_split_without_synthesis(self):
        first_trace, first_raw, first_context = nor_evidence([])
        last_trace, last_raw, last_context = nor_evidence([(0xFD71,0x200,True)])
        for row in first_trace:
            if row['stage'] == 'full_after': row['stage'] = 'full_before'
        trace = first_trace+self.trace+last_trace
        events = first_context['events']+last_context['events']
        initial,remaining,groups = inspect.split_reader_evidence(trace,events)
        first_context['events'],last_context['events'] = groups
        a = inspect.history.inspect_final_nor_read(initial,first_raw,first_context)
        b = inspect.history.inspect_final_nor_read(remaining,last_raw,last_context)
        self.assertEqual(a['physical_read_counter'],0x100000)
        self.assertEqual(b['physical_read_counter'],0x100200)
        self.assertEqual(b['lost_read_bytes'],512)
        self.assertEqual(first_trace[0]['stage'],'full_before')
        with self.assertRaises(ValueError): inspect.split_reader_evidence(trace,events+[events[0]])

    def test_active_run_is_refused_before_reading_logs_or_sources(self):
        with patch.object(inspect,'read_shared_bytes',return_value=json.dumps({'phase':'installing'}).encode()), \
             patch.object(inspect.upgrade,'prepare_upgrade',side_effect=AssertionError('should not read inputs')):
            with self.assertRaises(ValueError): inspect.inspect_bundle()

    def test_complete_file_bundle_uses_actual_counter_and_empty_optional_writer_log(self):
        def reader_evidence(data, faults):
            def exchange(device,cdb,data_out=None,read_length=0):
                raw = nor_fixture.FakeNor.exchange(device,cdb,data_out,read_length)
                if cdb[:2] == b'\xfd\x71':
                    address = int.from_bytes(cdb[2:6],'big'); device.last_address = address
                    return data[address:address+read_length]
                return raw
            with patch.object(nor_fixture.VaryingNor,'exchange',exchange): return nor_evidence(faults)
        first_trace, _, first = reader_evidence(self.before,[])
        last_trace, _, last = reader_evidence(self.after,[(0xFD71,0x200,True)])
        for row in first_trace:
            if row['stage'] == 'full_after': row['stage'] = 'full_before'
        policy = {'enabled':True,'only_Windows_error':31,'mutation_retries_allowed':True,
            'mutation_request_reissue_requires_exact_prior_audit':True,
            'one_recovery_per_command_and_expected_state':True,'executed_mutation_retries_allowed':False,
            'OUT_retries_allowed':False,'jump_or_reset_retries_allowed':False,'backend_fallback_allowed':False,
            'FINISH_reissue_requires_exact_prior_audit_and_complete_candidate_sector':True,
            'command_witness_policy_unchanged_from_v5':True,'max_reopens':32}
        wrapper = BoundedCommandRecoveryTransport(SimpleNamespace(close=lambda:None,
            profile='app-writer-operational',slot=self.plan.slot,disk={'path':'OFFLINE_FAKE'},
            inquiry={'vendor':'WL82','product':'UBOOT1.00'}),log=lambda row:None,
                                                   reopen_factory=lambda:None)
        wrapper.close()
        with tempfile.TemporaryDirectory(prefix='TEST-upgrade-inspector-',dir=inspect.ROOT/'build') as folder:
            directory = Path(folder).resolve(); self.assertTrue(directory.is_relative_to(inspect.ROOT/'build'))
            before_path, after_path = directory/'fixture-before.bin',directory/'fixture-after.bin'
            before_path.write_bytes(self.before); after_path.write_bytes(self.after)
            raw_plan = b'{"offline_fixture":true}\n'; plan_path = directory/'fixture-plan.json'; plan_path.write_bytes(raw_plan)
            spec = replace(self.plan,plan_sha256=inspect.sha(raw_plan))
            planned = SimpleNamespace(installation=spec,plan_bytes=raw_plan)
            source_names = [f'tools/recover_mini_read_v{n}.py' for n in (3,4,5,6)]+['tools/mini_nor_read_recovery.py']
            run = {'finished_utc':'2026-11-16T00:00:00Z','phase':'upgraded_verified_waiting_for_normal_boot',
                'installed_image_verified':True,'full_NOR_verified':True,'known_live_slot':0x1C28000,
                'jump_outcome_unknown':False,'mutation_completion_unknown':False,'MCN_pause_closed':True,
                'MCN_explicitly_reenabled':True,'automatic_reset':False,'fresh_ROM_verified':True,
                'candidate_sha256':inspect.NEW_SHA,'source_pins':{
                    name:inspect.sha((inspect.ROOT/name).read_bytes()) for name in source_names},
                'full_before':inspect.ref(before_path,self.before),'full_after':inspect.ref(after_path,self.after),
                'new_preimage_plan':plan_path.relative_to(inspect.ROOT).as_posix(),
                'upgrade_plan':inspect.ref(plan_path,raw_plan),'installation':spec.summary(),
                'read_recovery_final':wrapper.summary(),'read_recovery_policy':policy,
                'writer_final':{'failed':False,'phase':'complete','image_verified':True,'preimage_verified':True,
                    'mutation_completion_unknown':False,'verified_sectors':[0x4000],'journal_error':None,
                    'ambiguous_operation':None,'last_audit':self.final_audit}}
            for label,context in (('full_before',first),('full_after',last)):
                run[label+'_read_recovery'] = context['summary']
                run[label+'_target_read_counter'] = context['target_read_counter']
                run[label+'_lost_read_bytes'] = context['summary']['lost_read_bytes']
            prefix = directory/'fixture'
            for suffix,rows in (('-trace.jsonl',first_trace+self.trace+last_trace),
                                ('-journal.jsonl',self.journal),
                                ('-nor-read-recovery.jsonl',first['events']+last['events']),
                                ('-mcn.jsonl',[{'event':'mcn_disabled'},{'event':'mcn_reenabled'}])):
                Path(str(prefix)+suffix).write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
            run_path = Path(str(prefix)+'-run.json'); run_path.write_text(json.dumps(run),encoding='utf-8')
            with patch.object(inspect.upgrade,'prepare_upgrade',return_value=planned):
                result = inspect.inspect_bundle(run_path)
                self.assertEqual(result['final_reader_counter'],0x100200)
                self.assertEqual(result['final_read_lost_bytes'],512)
                self.assertTrue(result['verified'] and result['application_exact'])
                self.assertFalse(result['boot_attempted'] or result['audio_verified'])
                run['full_after_lost_read_bytes'] = 0; run_path.write_text(json.dumps(run),encoding='utf-8')
                with self.assertRaises(ValueError): inspect.inspect_bundle(run_path)

    def test_default_CLI_reads_no_logs_or_device(self):
        with patch.object(inspect,'inspect_bundle',side_effect=AssertionError('no implicit inspection')), \
             patch('sys.stdout',new_callable=io.StringIO) as out:
            inspect.main([])
        self.assertEqual(json.loads(out.getvalue()),{'device_io':False,'logs_read':False})


if __name__ == '__main__': unittest.main()
