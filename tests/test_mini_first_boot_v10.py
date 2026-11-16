"""Normal boot/PING orchestration with temporary evidence and fake devices."""
from contextlib import ExitStack, redirect_stdout
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

from tests.test_mini_app_mutation import Pedal
from tools.probe_mini_recovery import RomCommandError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('normal_boot_v10_test', ROOT/'analysis/hardware/run_mini_first_boot_v10.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
PORT = {'device':'COM123', 'vid':0x3654, 'pid':0x5155, 'description':'OFFLINE FIXTURE'}
PARENT = r'USB\VID_4C4A&PID_8057\OFFLINE'


class NormalBootTests(unittest.TestCase):
    def run_fake(self, fault=None, *, check_only=False, bootmode='released'):
        handles, calls, ping_args, reset_calls = [], [], [], []
        arrivals_calls = 0
        enum_calls = 0
        class SerialPedal(Pedal):
            def response(self, command):
                if fault == 'wrong_PONG' and command == 'PING':
                    return ['PONG tankg_fw M5.71 rel ble Nov 15 2026']
                return super().response(command)
        pedal = SerialPedal()
        class Transport:
            def __init__(self, path, *, slot, profile='ram-probe'):
                self.slot, self.profile, self.closed = slot, profile, False
                self.disk = {'path':path}; self.inquiry = {'vendor':'WL82','product':'UBOOT1.00'}
                self.adapter_descriptor = {'alignment_mask':0}
                handles.append(self)
            def exchange(self, cdb, data_out=None, read_length=0):
                assert not self.closed
                op = int.from_bytes(cdb[:2], 'big'); calls.append((self.slot,op))
                if self.slot == runner.B:
                    assert data_out is None and read_length == 16
                    if op == 0xFC70:
                        if fault == 'identity': return bytes(16)
                        return b'\xfc\x70HYRN\1\3' + struct.pack('>II',runner.B,32768)
                    assert op == 0xFC73
                    count = 0x100200 if fault == 'counter' else 0x100000
                    return b'\xfc\x73\0\1' + bytes(8) + count.to_bytes(4,'big')
                assert self.slot == runner.A and op == 0xFB08
                if fault in ('reset_presubmit', 'reset_postsubmit'):
                    raise RomCommandError(31,'fake reset transfer failure',submitted=fault=='reset_postsubmit')
                return b'\xfb\x08' + bytes(14)
            def close(self): self.closed=True
            def __enter__(self): return self
            def __exit__(self,*_): self.close()
        class ResetSession:
            def __init__(self, transport, *, slot, known_free_slot):
                assert slot == runner.A and known_free_slot
                assert calls[:2] == [(runner.B,0xFC70),(runner.B,0xFC73)]
                self.transport=transport
            def upload_only(self, payload, *, expected_sha256):
                reset_calls.append('upload')
                assert payload == b'fake-reset' and expected_sha256 == runner.sha(payload)
                if fault == 'upload': raise ValueError('fake upload failure')
                return {'uploaded':True, 'offline_mock':True}
            def start_reset_once(self, payload, *, elf, manifest):
                reset_calls.append('verify_and_jump')
                assert elf == b'fake-elf' and manifest['slot'] == runner.A
                if fault == 'reset_readback': raise ValueError('fake reset readback mismatch')
                try: self.transport.exchange(b'\xfb\x08'+bytes(14),read_length=16)
                except RomCommandError as error:
                    if not error.submitted: raise
                    return {'jump_sent':True,'jump_outcome':'post_submit_transport_error','automatic_retry':False}
                return {'jump_sent':True,'jump_outcome':'fb08_echo_received','automatic_retry':False}
        def arrivals():
            nonlocal arrivals_calls
            arrivals_calls += 1
            stamp = '2026-11-16T00:00:02Z' if fault == 'arrival_changed' and arrivals_calls > 1 else '2026-11-16T00:00:01Z'
            return [{'instance_id':PARENT if fault != 'parent' else PARENT+'DIFFERENT','arrival_utc':stamp}]
        def enumerate_ports():
            nonlocal enum_calls
            enum_calls += 1
            if not any(op==0xFB08 for _,op in calls): return [PORT] if fault=='existing_CDC' else []
            if fault=='missing_CDC': return []
            if fault=='multiple_CDC': return [PORT,{**PORT,'device':'COM124'}]
            if fault=='wrong_COM': return [{**PORT,'device':'not-a-COM'}]
            return [PORT]
        original_run_read = runner.readonly.run_read
        def ping(arguments):
            ping_args.append(arguments)
            self.assertEqual(arguments.queries, [])
            self.assertEqual(arguments.port, PORT['device'])
            return original_run_read(arguments, enumerate_fn=lambda:[PORT], open_fn=lambda _:pedal, clock=pedal.clock)
        with tempfile.TemporaryDirectory(prefix='mini-normal-boot-test-',dir=ROOT/'build') as name:
            folder=Path(name); hardware=folder/'analysis/hardware'; hardware.mkdir(parents=True)
            full_path=folder/'artifacts/my-mini-flash/first-install/full-final-after.bin'
            full_path.parent.mkdir(parents=True); full=bytes((i*7)&255 for i in range(0x100000)); full_path.write_bytes(full)
            install={'phase':'installed_verified_waiting_for_footswitch','full_NOR_verified':True,'installed_image_verified':True,
                'known_live_slot':runner.B,'jump_outcome_unknown':False,'mutation_completion_unknown':False,
                'backend':'IOCTL_SCSI_PASS_THROUGH buffered','installation':{'candidate_sha256':runner.EXPECTED_CANDIDATE_SHA},
                'independent_full_validation':{'external_regions_unchanged':True,'full_NOR_sha256':runner.sha(full)},
                'full_after':{'path':full_path.relative_to(folder).as_posix(),'sha256':runner.sha(full)},
                'full_after_target_read_counter':0x100000,'MCN_pause_started':True,'MCN_pause_closed':True,
                'MCN_explicitly_reenabled':True,'started_utc':'2026-11-16T00:00:00Z','finished_utc':'2026-11-16T00:00:01Z',
                'ROM_disk':{'path':'OFFLINE-DISK'}}
            if fault=='incomplete_install': install['full_NOR_verified']=False
            if fault=='MCN': install['MCN_explicitly_reenabled']=False
            if fault=='recorded_counter': install['full_after_target_read_counter']=0x100200
            if fault=='changed_full': full_path.write_bytes(bytes(len(full)))
            install_path=hardware/'install.json'; install_path.write_text(json.dumps(install),encoding='utf-8')
            events=[]
            for event in ('mcn_open_intent','mcn_disable_intent','mcn_disabled','mcn_enable_intent','mcn_reenabled','mcn_handle_closed'):
                events.append({'event':event,'path':'OFFLINE-DISK','utc':'2026-11-16T00:00:00Z'})
            events[-1].update(close_ok=True,explicit_enable_succeeded=True,windows_file_object_cleanup_required=False,error=None)
            if fault=='MCN_log': events.pop()
            mcn=hardware/'mcn.jsonl'; mcn.write_text('\n'.join(json.dumps(x) for x in events),encoding='utf-8')
            pins=hardware/'pins.json'; pins.write_text('{}',encoding='utf-8')
            base=folder/'base.json'; base.write_text('{}',encoding='utf-8')
            (folder/'reset.bin').write_bytes(b'fake-reset'); (folder/'reset.elf').write_bytes(b'fake-elf')
            research=folder/'research'; research.mkdir()
            reset={'slot':runner.A,'file':'reset.bin','elf':'reset.elf','image_sha256':runner.sha(b'fake-reset')}
            (research/'mini-rom-reset.json').write_text(json.dumps({'source_sha256':{},'artifacts':[reset]}),encoding='utf-8')
            out=hardware/'mini-first-boot-v10-released-run.json'; trace=hardware/'mini-first-boot-v10-released-trace.jsonl'
            ping_path=hardware/'ping.jsonl'
            if fault=='existing_run': out.write_text('{}',encoding='utf-8')
            if fault=='existing_ping': ping_path.write_text('{}',encoding='utf-8')
            profile={'capabilities':{'read':True},'firmware_version':runner.EXPECTED_VERSION,'image_sha256':runner.EXPECTED_CANDIDATE_SHA}
            if fault=='profile': profile['firmware_version']='tankg_fw wrong'
            output=io.StringIO(); thrown=None
            with ExitStack() as stack:
                changes={'ROOT':folder,'INSTALL_RUN':install_path,'MCN_LOG':mcn,'PINS':pins,'BASE_PROFILE':base,
                    'PING_LOG':ping_path,'EXPECTED_COMPLETE_SHA':runner.sha(full),'EXPECTED_PROFILE_SHA':runner.sha(base.read_bytes()),
                    'WindowsBufferedRomTransport':Transport,'MiniRamSession':ResetSession,
                    'discover_windows_rom_disks':lambda:[{'path':'OFFLINE-DISK','usb_ancestor':PARENT}], 'arrivals':arrivals,
                    'verify_recorded_hashes':lambda _:None,'validate_reset_artifact':lambda *a,**k:None}
                for key,value in changes.items(): stack.enter_context(patch.object(runner,key,value))
                stack.enter_context(patch.object(runner.readonly,'load_profile',return_value=profile))
                stack.enter_context(patch.object(runner.readonly,'source_contract',return_value={'offline_fixture':True}))
                stack.enter_context(patch.object(runner.readonly,'enumerate_ports',side_effect=enumerate_ports))
                stack.enter_context(patch.object(runner.readonly,'run_read',side_effect=ping))
                stack.enter_context(patch.object(runner.ctypes,'windll',SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda:1)),create=True))
                stack.enter_context(patch.object(runner.time,'sleep'))
                stack.enter_context(patch('sys.argv',['offline-v10-test',bootmode]+(['--check-only'] if check_only else [])))
                stack.enter_context(redirect_stdout(output))
                try: runner.main()
                except (ValueError,SystemExit) as error: thrown=error
            result=json.loads(out.read_bytes()) if out.exists() else None
            trace_rows=[json.loads(x) for x in trace.read_text().splitlines()] if trace.exists() else []
            ping_rows=[json.loads(x) for x in ping_path.read_text().splitlines()] if ping_path.exists() else []
        self.assertTrue(all(h.closed for h in handles))
        self.assertLessEqual(sum(op==0xFB08 for _,op in calls),1)
        self.assertLessEqual(len(ping_args),1)
        return SimpleNamespace(result=result,calls=calls,handles=handles,reset_calls=reset_calls,ping_args=ping_args,
            ping_rows=ping_rows,trace_rows=trace_rows,pedal=pedal,enum_calls=enum_calls,thrown=thrown,stdout=output.getvalue())

    def test_normal_boot_verifies_reader_once_then_exact_real_parser_PONG(self):
        r=self.run_fake()
        self.assertIsNone(r.thrown)
        self.assertEqual(r.result['phase'],'application_PONG_verified')
        self.assertEqual(r.calls,[(runner.B,0xFC70),(runner.B,0xFC73),(runner.A,0xFB08)])
        self.assertEqual(r.reset_calls,['upload','verify_and_jump'])
        self.assertTrue(r.result['slot_A_inactive_verified'] and r.result['reset_submitted'])
        self.assertTrue(r.result['app_identity_verified'] and r.result['serial_port_closed'] and r.pedal.closed)
        self.assertIs(r.result['buttons_confirmed_by_user'],False)
        self.assertEqual(r.result['buttons_assumed'],'released')
        for key in ('held_button_boot_trial_performed','fresh_ROM_verified','cold_power_cycle_tested',
                    'guard_causality_confirmed','audio_verified','firmware_write','automatic_retry'):
            self.assertIs(r.result[key],False)
        self.assertEqual([x['command'] for x in r.ping_rows if x['event']=='tx'],['PING'])
        self.assertEqual(r.ping_rows[-1]['event'],'port_closed')

    def test_preflight_rejects_incomplete_image_MCN_counter_or_profile_without_device_IO(self):
        for fault in ('incomplete_install','MCN','MCN_log','recorded_counter','changed_full','profile'):
            with self.subTest(fault=fault):
                r=self.run_fake(fault)
                self.assertIsInstance(r.thrown,ValueError)
                self.assertFalse(r.calls or r.handles or r.ping_args)

    def test_wrong_reader_counter_identity_or_arrival_cannot_upload_reset(self):
        for fault in ('counter','identity','arrival_changed','parent'):
            with self.subTest(fault=fault):
                r=self.run_fake(fault)
                self.assertIn('error',r.result)
                self.assertFalse(r.reset_calls or r.ping_args or r.result['reset_submitted'])
                self.assertFalse(any(h.slot==runner.A for h in r.handles))

    def test_CDC_freshness_uniqueness_and_COM_gate_PING(self):
        for fault in ('existing_CDC','missing_CDC','multiple_CDC','wrong_COM'):
            with self.subTest(fault=fault):
                r=self.run_fake(fault)
                self.assertIn('error',r.result)
                self.assertFalse(r.ping_args or r.result['app_identity_verified'])
                self.assertEqual(r.result['reset_submitted'],fault!='existing_CDC')
                self.assertLessEqual(r.enum_calls,31)

    def test_wrong_PONG_is_not_communication_success_and_port_closes(self):
        r=self.run_fake('wrong_PONG')
        self.assertEqual(r.result['error_phase'],'identify_application_PING')
        self.assertTrue(r.result['application_USB_enumerated'])
        self.assertFalse(r.result['app_identity_verified'])
        self.assertTrue(r.pedal.closed)
        self.assertEqual([x['command'] for x in r.ping_rows if x['event']=='tx'],['PING'])
        self.assertEqual(r.ping_rows[-1]['event'],'port_closed')

    def test_upload_or_readback_failure_never_submits_reset(self):
        for fault in ('upload','reset_readback'):
            with self.subTest(fault=fault):
                r=self.run_fake(fault)
                self.assertIn('error',r.result)
                self.assertFalse(r.result['reset_submitted'] or r.ping_args)

    def test_reset_transport_failure_never_retries_or_invents_success(self):
        r=self.run_fake('reset_presubmit')
        self.assertIn('error',r.result)
        self.assertFalse(r.result['app_identity_verified'] or r.ping_args)
        r=self.run_fake('reset_postsubmit')
        self.assertEqual(r.result['reset_request']['jump_outcome'],'post_submit_transport_error')
        self.assertEqual(r.result['phase'],'application_PONG_verified')
        self.assertEqual(sum(op==0xFB08 for _,op in r.calls),1)

    def test_existing_output_stops_all_device_actions(self):
        for fault in ('existing_run','existing_ping'):
            with self.subTest(fault=fault):
                r=self.run_fake(fault)
                self.assertIsInstance(r.thrown,ValueError)
                self.assertFalse(r.calls or r.handles or r.ping_args)

    def test_check_only_and_disallowed_held_mode_open_nothing(self):
        r=self.run_fake(check_only=True)
        self.assertFalse(r.calls or r.handles or r.ping_args)
        check=json.loads(r.stdout)
        self.assertIs(check['buttons_confirmed_by_user'],False)
        self.assertIs(check['held_button_boot_trial_performed'],False)
        r=self.run_fake(bootmode='held')
        self.assertIsInstance(r.thrown,SystemExit)
        self.assertFalse(r.calls or r.handles or r.ping_args)


if __name__=='__main__': unittest.main()
