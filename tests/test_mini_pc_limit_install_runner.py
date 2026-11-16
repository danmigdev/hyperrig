"""Upgrade orchestration with real protocol sessions and fake RAM/NOR only."""
from contextlib import ExitStack, redirect_stdout
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import copy
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.test_mini_app_install import FakeOperational, fixture
from tests.test_mini_recovery import FakeNor
from tools.probe_mini_recovery import RomCommandError
from tools.mini_windows_quiet import RomDiskAttestation as BoundAttestation

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pc_limit_install_runner_test', ROOT/'analysis/hardware/run_mini_pc_limit_install.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def entry_fixture():
    return {'started_utc':'2026-11-16T01:00:00Z', 'finished_utc':'2026-11-16T01:00:04Z',
        'command':'UBOOT', 'command_submitted_once':True, 'command_invocations':1,
        'command_submitted_utc':'2026-11-16T01:00:02Z', 'automatic_retry':False,
        'firmware_write':False, 'ROM_verified':False, 'serial_port_closed':True,
        'native_close_verified':True, 'browser_process_stopped':True, 'local_server_stopped':True,
        'pong':'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe', 'prior_port':'COM3',
        'browser_state':{'tx':[{'line':'PING\n','utc':'2026-11-16T01:00:01Z'},
            {'line':'UBOOT\n','hex':'55424f4f540a','utc':'2026-11-16T01:00:02Z'}],
            'identityVerified':True,'ubootAttempted':True},
        'source_sha256':{}, 'evidence':{'inputs':{
            'desktop_connection':{'path':'proof.json','sha256':'1'*64},
            'desktop_closed':{'path':'closed.json','sha256':'2'*64}}}}


class UpgradeRunnerTests(unittest.TestCase):
    def run_fake(self, fault=None, recover=False, check_only=False):
        base = fixture()
        candidate = bytes(x ^ 7 for x in base.preimage[:4096]) + base.preimage[4096:]
        installation = replace(base, candidate=candidate, sector_order=(0x4000,))
        core = FakeOperational(installation)
        # Distinct current runtime bytes must survive both final comparisons.
        core.flash[0x82010:0x82014] = b'LIVE'
        before = bytes(core.flash)
        expected = before[:0x4000]+candidate+before[0x82000:]
        handles, pauses, trace, calls, reads = [], [], [], [], []
        active, failed = None, False
        arrived = datetime(2026,11,16,1,0,3,tzinfo=timezone.utc)
        arrival_ticks = int(arrived.timestamp()*10000000)+116444736000000000
        class Attestation:
            @classmethod
            def from_discovery(cls, disk):
                return BoundAttestation(r'\\.\PhysicalDrive42',r'USBSTOR\MINI',
                    r'USB\VID_4C4A&PID_8057\UNIT',(r'USBSTOR\MINI',r'USB\VID_4C4A&PID_8057\UNIT'),
                    'WL82 UBOOT1.00',r'\\?\USBSTOR#MINI',arrival_ticks)
        class ReaderDevice(FakeNor):
            def __init__(self):
                super().__init__(); self.slot=runner.B
            def exchange(self,cdb,data_out=None,read_length=0):
                raw=super().exchange(cdb,data_out,read_length)
                if cdb[:2] == b'\xfd\x71':
                    address,n=struct.unpack_from('>IH',cdb,2)
                    return bytes(core.flash[address:address+n])
                return raw
        class Handle:
            def __init__(self,attestation,*,slot,profile):
                self.attestation,self.slot,self.profile=attestation,slot,profile
                self.disk=attestation.discovery_dict();self.inquiry={'vendor':'WL82','product':'UBOOT1.00'}
                self.adapter_descriptor={};self.closed=False
                self.device=ReaderDevice() if profile=='nor-reader' else core
                handles.append(self)
            def exchange(self,cdb,data_out=None,read_length=0):
                nonlocal active,failed
                assert not self.closed
                op=int.from_bytes(cdb[:2],'big'); calls.append((self.slot,op))
                if op==0xFB06: assert active != self.slot, 'must never overwrite active plugin'
                if op==0xFB08:
                    assert active != self.slot
                    active=self.slot
                    if fault=='initial_jump' and self.slot==runner.B and len(reads)==0:
                        raise RomCommandError(31,'fake uncertain jump',submitted=True)
                if op==0xFD71:
                    if self.device.count==0: reads.append('before' if not core.program_addresses else 'after')
                    if fault=='before_read' and not core.program_addresses: raise ValueError('fake preimage read error')
                    if fault=='after_read' and core.program_addresses: raise ValueError('fake final read error')
                    if fault=='outside_corruption' and core.program_addresses: core.flash[0x82010] ^= 1
                if self.slot==runner.A and op==0xFC7D and fault in ('unexecuted_program','executed_program') and not failed:
                    failed=True
                    if fault=='executed_program': self.device.exchange(cdb,data_out,read_length)
                    raise RomCommandError(31,'fake lost program response',submitted=True)
                return self.device.exchange(cdb,data_out,read_length)
            def close(self): self.closed=True
            def __enter__(self): return self
            def __exit__(self,*_): self.close()
        class Pause:
            def __init__(self,transport,*,log):
                self.log,self.disabled,self.closed=log,True,False;pauses.append(self)
                log({'event':'mcn_disabled'})
            def close(self):
                if not self.closed:
                    self.disabled=False;self.log({'event':'mcn_reenabled'});self.closed=True
        def plan_current(path,**kw):
            assert path.read_bytes()==before
            assert kw['expected_full_sha256']==runner.sha(before)
            assert kw['expected_target_sha256']==runner.TARGET_SHA
            if fault=='unit_preimage': raise ValueError('fake current unit mismatch')
            def retain(path):
                path.write_bytes(b'offline-plan')
                return {'path':path.relative_to(folder).as_posix(),'sha256':runner.sha(b'offline-plan')}
            return SimpleNamespace(installation=installation,retain_plan=retain)
        def validate(plan, raw):
            if raw != expected: raise ValueError('fresh runtime bytes changed')
            return {'full_NOR_sha256':runner.sha(raw),'external_regions_unchanged_from_fresh_read':True}
        with tempfile.TemporaryDirectory(prefix='mini-upgrade-runner-',dir=ROOT/'build') as name:
            folder=Path(name);entry_path=folder/'entry.json';entry=entry_fixture()
            entry_path.write_text(json.dumps(entry),encoding='utf-8')
            pins={'entry.json':runner.sha(entry_path.read_bytes())}
            out=folder/'run.json'
            with ExitStack() as stack:
                overrides={'ROOT':folder,'OUT':out,'ENTRY':entry_path,'TRACE':folder/'trace.jsonl',
                    'JOURNAL':folder/'journal.jsonl','RECOVERY':folder/'recover.jsonl',
                    'MCN_LOG':folder/'mcn.jsonl','NOR_RECOVERY_LOG':folder/'nor.jsonl',
                    'FULL_BEFORE':folder/'before.bin','FULL_AFTER':folder/'after.bin','PLAN':folder/'plan.json',
                    'WindowsBufferedRomTransport':Handle,'QuietBufferedRomTransport':Handle,
                    'RomDiskAttestation':Attestation,'MiniMediaChangePause':Pause,
                    'prepare_upgrade':plan_current,'validate_completed_full':validate,
                    'prepare_rom_entry':lambda *a:entry['evidence'], 'verify_recorded_hashes':lambda _:None,
                    'attach_native_diagnostic':lambda _:SimpleNamespace(last_failure=None),
                    'now':lambda:'2026-11-16T01:00:05Z',
                    'append':lambda path,item,durable=False:trace.append((path.name,copy.deepcopy(item)))}
                for k,v in overrides.items(): stack.enter_context(patch.object(runner,k,v))
                stack.enter_context(patch.object(runner,'prepare',return_value=(pins,candidate,{'flat_sha256':runner.sha(b'reader')},b'reader')))
                discovery=stack.enter_context(patch.object(runner,'discover_windows_rom_disks',return_value=[{'path':'FAKE-DISK'}]))
                stack.enter_context(patch.object(runner.readonly,'enumerate_ports',return_value=[] if fault!='existing_CDC' else [{'vid':0x3654,'pid':0x5155}]))
                stack.enter_context(patch.object(runner.ctypes,'windll',SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda:1)),create=True))
                stack.enter_context(patch.object(runner.time,'sleep'))
                stack.enter_context(patch.object(runner.os,'fsync'))
                stack.enter_context(patch('sys.argv',['offline-upgrade']+(['--recover-audited-commands'] if recover else [])+(['--check-only'] if check_only else [])))
                stack.enter_context(redirect_stdout(io.StringIO()))
                runner.main()
            report=json.loads(out.read_text()) if out.exists() else None
            post=(folder/'after.bin').read_bytes() if (folder/'after.bin').exists() else None
            self.assertLessEqual(discovery.call_count,1)
        self.assertTrue(all(h.closed for h in handles))
        self.assertTrue(all(p.closed and not p.disabled for p in pauses))
        return report,core,calls,post,expected,reads

    def test_success_fresh_preimage_one_sector_then_independent_read(self):
        r,c,calls,post,expected,reads=self.run_fake(recover=True)
        self.assertNotIn('error',r)
        self.assertEqual(r['phase'],'upgraded_verified_waiting_for_normal_boot')
        self.assertEqual(reads,['before','after'])
        self.assertEqual(c.erase_addresses,[0x4000])
        self.assertEqual(c.program_addresses,list(range(0x4100,0x5000,256))+[0x4000])
        self.assertEqual([slot for slot,op in calls if op==0xFB08],[runner.B,runner.A,runner.B])
        self.assertEqual(post,expected)
        self.assertEqual(r['full_before_target_read_counter'],0x100000)
        self.assertEqual(r['full_after_target_read_counter'],0x100000)
        self.assertFalse(r['automatic_reset'] or r['jump_outcome_unknown'] or r['mutation_completion_unknown'])

    def test_before_failures_never_start_writer(self):
        for fault in ('existing_CDC','initial_jump','before_read','unit_preimage'):
            with self.subTest(fault=fault):
                r,c,calls,post,_,_=self.run_fake(fault)
                self.assertIn('error',r);self.assertFalse(c.erase_addresses or c.program_addresses)
                self.assertFalse(any(slot==runner.A for slot,_ in calls));self.assertIsNone(post)
                if fault=='initial_jump': self.assertTrue(r['jump_outcome_unknown'])

    def test_final_read_failure_or_runtime_corruption_cannot_claim_success(self):
        for fault in ('after_read','outside_corruption'):
            with self.subTest(fault=fault):
                r,_,_,_,_,_=self.run_fake(fault)
                self.assertTrue(r['installed_image_verified'])
                self.assertFalse(r['full_NOR_verified']);self.assertIn('error',r)

    def test_unexecuted_program_reconciled_without_duplicate_mutations(self):
        r,c,_,post,expected,_=self.run_fake('unexecuted_program',recover=True)
        self.assertNotIn('error',r);self.assertEqual(post,expected)
        self.assertEqual(len(c.program_addresses),16);self.assertEqual(c.erase_addresses,[0x4000])
        self.assertEqual(r['read_recovery_final']['recovery_attempts'],1)

    def test_executed_program_lost_response_is_not_repeated(self):
        r,c,_,post,_,_=self.run_fake('executed_program',recover=True)
        self.assertIn('error',r);self.assertEqual(c.program_addresses,[0x4100]);self.assertIsNone(post)
        self.assertFalse(r['full_NOR_verified'])

    def test_check_only_never_discovers_or_opens(self):
        r,c,calls,post,_,_=self.run_fake(check_only=True)
        self.assertIsNone(r);self.assertEqual(calls,[]);self.assertFalse(c.program_addresses)

    def test_entry_requires_real_submission_and_close_not_ACK(self):
        entry=entry_fixture();runner.validate_entry(entry)
        for key in ('command_submitted_once','serial_port_closed','native_close_verified','browser_process_stopped'):
            changed=copy.deepcopy(entry);changed[key]=False;changed['ack_observed']=True
            with self.assertRaises(ValueError): runner.validate_entry(changed)
        changed=copy.deepcopy(entry);changed['browser_state']['tx'].append(changed['browser_state']['tx'][-1])
        with self.assertRaises(ValueError): runner.validate_entry(changed)

    def test_arrival_after_command_and_bounded_age(self):
        sent=runner.stamp('2026-11-16T01:00:02Z')
        def att(seconds):
            return SimpleNamespace(last_arrival_filetime=int((sent+timedelta(seconds=seconds)).timestamp()*10000000)+116444736000000000)
        runner.require_fresh_arrival(att(1),sent,sent+timedelta(seconds=3))
        for a,now in ((att(-1),sent+timedelta(seconds=3)),(att(4),sent+timedelta(seconds=3)),(att(1),sent+timedelta(seconds=901))):
            with self.assertRaises(ValueError):runner.require_fresh_arrival(a,sent,now)


if __name__=='__main__':unittest.main()
