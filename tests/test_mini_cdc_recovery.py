"""Offline recovery proof/selection and original bytecode checks. No browser."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import enter_mini_rom_webserial as target
from tools import audit_mini_cdc_recovery as audit


class CdcRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = json.loads((target.ROOT/'build/mini-desktop-real-03/connected-proof.json').read_bytes())

    def closed(self):
        # TEST fixture derived from a stable real connection proof. This is never
        # persisted as hardware evidence and never authorizes a real invocation.
        last=copy.deepcopy(self.proof['guard']);last.update(closes=1,stopped=True)
        return {'kind':'mini-desktop-readonly-session','phase':'connected_readonly','started_utc':'2026-11-16T00:07:00Z',
                'finished_utc':'2026-11-16T00:10:00Z','identity_verified':True,'serial_port_closed':True,
                'browser_process_stopped':True,'local_server_stopped':True,
                'disconnect':{'native_close_verified':True,'open':False,'closes':1,'closeError':None},
                'last_guard':last,'evidence':{'inputs':self.proof['inputs'],'evidence':{'com':'COM3'}},
                'source_sha256':dict(target.FROZEN_DESKTOP)}

    def test_default_cannot_start_browser_or_read_evidence(self):
        with (patch.object(target,'prepare',side_effect=AssertionError('read')),patch.object(target,'run',side_effect=AssertionError('I/O')),
              contextlib.redirect_stdout(io.StringIO()) as out):
            self.assertEqual(target.main([]),0)
        result=json.loads(out.getvalue());self.assertFalse(result['device_io'] or result['browser_started'] or result['inputs_read'])

    def test_prior_proof_does_not_require_held_and_accepts_safe(self):
        result=target.validate_prior(self.proof,self.closed())
        self.assertEqual(result,{'pong':'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe','com':'COM3'})

    def test_close_must_be_native_and_completed(self):
        for key,value in [('finished_utc',None),('serial_port_closed',False),('browser_process_stopped',False),
                          ('local_server_stopped',False),('identity_verified',False),('error','test')]:
            closed=self.closed();closed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):target.validate_prior(self.proof,closed)
        for key,value in [('native_close_verified',False),('closes',0),('open',True),('closeError','failed')]:
            closed=self.closed();closed['disconnect'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):target.validate_prior(self.proof,closed)

    def test_wrong_or_synthetic_prior_identity_rejected(self):
        for mutate in (lambda p:p['state'].update(demo=True),lambda p:p['state'].update(fw='PONG other'),
                       lambda p:p['guard'].update(replies=[]),lambda p:p['guard'].update(opens=2),
                       lambda p:p['guard'].update(portInfo={'vid':0x3654,'pid':0x4155}),
                       lambda p:p['guard'].update(pongMatched=False)):
            proof=copy.deepcopy(self.proof);mutate(proof)
            with self.assertRaises(ValueError):target.validate_prior(proof,self.closed())

    def test_wrong_port_chronology_or_manifest_rejected(self):
        for mutate in (lambda c:c['evidence']['evidence'].update(com='COM0'),
                       lambda c:c.update(finished_utc='2020-01-01T00:00:00Z'),
                       lambda c:c['evidence']['inputs'].update(manifest={'sha256':'0'*64}),
                       lambda c:c['last_guard'].update(stopped=False)):
            closed=copy.deepcopy(self.closed());mutate(closed)
            with self.assertRaises(ValueError):target.validate_prior(self.proof,closed)

    def selection(self):
        return {'observed_utc':'2026-11-16T00:11:01Z','browser_pid':123,'origin':'http://127.0.0.1:50000',
                'selected_row':'Tank-M HyperRig (COM3)','exact_unique_row_verified':True,'no_other_device_selected':True,
                'method':'Windows UIAutomation SelectionItem and Invoke'}

    def check_selection(self, selection):
        return target.validate_selection(selection,browser_pid=123,origin='http://127.0.0.1:50000',com='COM3',
                                         start='2026-11-16T00:11:00Z',validated_at='2026-11-16T00:11:02Z')

    def test_selection_exact_row_current_browser_and_origin(self):
        self.assertTrue(self.check_selection(self.selection()))
        for key,value in [('selected_row','Tank-M HyperRig (COM33)'),('browser_pid',124),('origin','http://127.0.0.1:1'),
                          ('exact_unique_row_verified',False),('no_other_device_selected',False),('method','CDP guess'),
                          ('observed_utc','2020-01-01T00:00:00Z'),('observed_utc','2099-01-01T00:00:00Z')]:
            record=self.selection();record[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.check_selection(record)

    def test_ACK_disconnect_and_close_do_not_promote_ROM(self):
        for ack in (False,True):
            for closed in (False,True):
                report={};state={'tx':[{'line':'UBOOT\n','hex':'55424f4f540a','utc':'2026-11-16T00:11:01Z'}],
                                 'ubootAttempted':True,'ubootWriteCompleted':False,
                                 'actualACKObserved':ack,'disconnectObserved':True,'nativeCloseVerified':closed}
                target.apply_observation(report,state)
                self.assertEqual(report['ack_observed'],ack);self.assertEqual(report['serial_port_closed'],closed)
                self.assertTrue(report['command_submitted_once']);self.assertFalse(report['ROM_verified'])
                self.assertEqual(report['command_submitted_utc'],'2026-11-16T00:11:01Z')
        with self.assertRaises(ValueError):target.apply_observation({}, {'tx':[{'line':'UBOOT\n'}]*2})

    def test_prepare_reads_only_pinned_local_files(self):
        with tempfile.TemporaryDirectory(dir=target.ROOT/'build',prefix='TEST-cdc-recovery-') as directory:
            directory=Path(directory);proof=directory/'connected-proof.json';closed=directory/'session.json'
            proof.write_text(json.dumps(self.proof));closed.write_text(json.dumps(self.closed()))
            with patch.object(audit,'inspect',return_value={'installed_candidate_sha256':audit.CANDIDATE_SHA,
                             'safe_flag_not_read_on_audited_UBOOT_dispatch_path':True}):
                prepared=target.prepare(proof,target.sha(proof.read_bytes()),closed,target.sha(closed.read_bytes()))
            self.assertFalse(prepared['firmware_write'] or prepared['automatic_retry'] or prepared['ROM_verified'])
            self.assertEqual(prepared['max_UBOOT'],1)
            with self.assertRaises(ValueError):target.prepare(proof,'0'*64,closed,target.sha(closed.read_bytes()))

    def test_actual_original_bytecode_UBOOT_path_without_safe_RAM_reads(self):
        result=audit.inspect()
        self.assertEqual([p['result'] for p in result['dispatch_paths']],[0,0,0,'UBOOT handler'])
        self.assertTrue(all(p['target_RAM_reads']==0 for p in result['dispatch_paths']))
        self.assertEqual(result['command_hex'],b'UBOOT\n'.hex())
        self.assertEqual(result['actual_ACK_hex'],b'OK UBOOT\n'.hex())
        self.assertEqual(result['NOR_operations_in_command_handler'],[])


if __name__=='__main__':unittest.main()
