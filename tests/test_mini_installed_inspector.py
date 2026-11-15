"""Offline image/order evidence checks; no hardware classes or commands."""
import copy
import struct
import unittest
from unittest.mock import patch

from tools import inspect_mini_installed as inspector
from tools import install_mini_app as installer
from tools import recover_mini_read_v3 as recovery_v3
from tests.test_mini_app_install import FakeOperational, fixture as installation_fixture, IMAGE
from tests.test_mini_read_recovery import Handle, failure
from tests.test_mini_app_writer_protocol import changed_record


def fixture():
    stock = b'\x35' * inspector.CAPACITY
    candidate = bytearray(stock[inspector.APP_START:inspector.APP_END])
    candidate[:4096] = b'\x45' * 4096
    candidate[4096:8192] = b'\x67' * 4096
    candidate = bytes(candidate)
    observed = stock[:inspector.APP_START] + candidate + stock[inspector.APP_END:]
    return stock, stock, candidate, observed


def evidence(preimage, candidate, order):
    journal, trace = [], []
    for cdb, data_hash, expected_reply in inspector.expected_stateful_commands(preimage, candidate, order):
        opcode = int.from_bytes(cdb[:2], 'big')
        address = int.from_bytes(cdb[2:6] if opcode == 0xFC7A else cdb[10:14], 'big')
        if opcode == 0xFB7C:
            reply = b''
        elif opcode == 0xFD87:
            reply = candidate[address - inspector.APP_START:address - inspector.APP_START + 256]
        else:
            reply = cdb[:2] + bytes(14)
        digest = inspector.sha(reply)
        assert expected_reply is None or digest == expected_reply
        journal.extend(({'event':'command_intent', 'opcode':f'{opcode:04x}',
                         'cdb_hex':cdb.hex(), 'data_out_sha256':data_hash},
                        {'event':'command_reply', 'opcode':f'{opcode:04x}',
                         'sha256':digest, 'bytes':len(reply)}))
        trace.extend(({'stage':'writer', 'state':'before', 'cdb':cdb.hex()},
                      {'stage':'writer', 'state':'after', 'cdb':cdb.hex(),
                       'response_bytes':len(reply), 'response_sha256':digest, 'response_hex':reply.hex()}))
        if opcode in (0xFD87, 0xFC7D, 0xFC80):
            width = 4096 if opcode == 0xFC80 else 256
            raw = candidate[address - inspector.APP_START:address - inspector.APP_START + width]
            event = {0xFD87:'page_echo_verified', 0xFC7D:'page_program_verified', 0xFC80:'sector_verified'}[opcode]
            entry = {'event':event, 'address':address, 'sha256':inspector.sha(raw)}
            if width == 4096: entry['program_page_order'] = inspector.page_order(address)
            journal.append(entry)
    return journal, trace


class InstalledInspectorTests(unittest.TestCase):
    def test_complete_NOR_and_external_regions_compared_byte_for_byte(self):
        stock, before, candidate, observed = fixture()
        result = inspector.compare_nor(stock, before, candidate, observed)
        self.assertEqual(result['sector_order'], [0x5000, 0x4000])
        self.assertEqual(sum(x['bytes'] for x in result['preserved_regions']), inspector.CAPACITY - len(candidate))
        self.assertEqual(len(result['already_matching_sectors']), 124)

    def test_modified_external_regions_or_candidate_page_are_rejected(self):
        stock, before, candidate, observed = fixture()
        for offset in (0, 0x3FFF, 0x4000, 0x81FFF, 0x82000, 0xBE000, 0xBF000, 0xFF000, 0xFFFFF):
            changed = bytearray(observed);changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                inspector.compare_nor(stock, before, candidate, bytes(changed))

    def test_preimage_outside_app_must_match_unit_backup(self):
        stock, before, candidate, observed = fixture()
        changed = bytearray(before);changed[0xBE000] ^= 1
        with self.assertRaises(ValueError): inspector.compare_nor(stock, bytes(changed), candidate, observed)

    def test_exact_staging_echo_erase_program_finish_header_last(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        journal, trace = evidence(before, candidate, order)
        result = inspector.inspect_history(journal, trace, before, candidate, order)
        self.assertEqual((result['erase_commands'], result['program_commands'], result['expected_WREN_count']), (2, 32, 34))
        self.assertEqual(result['program_order'][-16:], list(range(0x4100, 0x5000, 256)) + [0x4000])
        self.assertTrue(result['header_sector_last'] and result['header_page_last'])

    def test_fifth_install_54_sector_geometry_and_counters(self):
        stock = b'\x35' * inspector.CAPACITY
        candidate = b'\x67' * (inspector.APP_END - inspector.APP_START)
        before = bytearray(stock)
        before[0x5000:0x4DA00] = candidate[0x1000:0x49A00]
        before[0x4DA00:0x4E000] = b'\xff' * 0x600
        before = bytes(before)
        observed = stock[:0x4000] + candidate + stock[0x82000:]
        images = inspector.compare_nor(stock, before, candidate, observed)
        order = list(range(0x4D000, 0x82000, 4096)) + [0x4000]
        self.assertEqual(images['sector_order'], order)
        self.assertEqual(len(images['already_matching_sectors']), 72)
        journal, trace = evidence(before, candidate, order)
        result = inspector.inspect_history(journal, trace, before, candidate, order)
        self.assertEqual((result['erase_commands'], result['program_commands'], result['expected_WREN_count']),
                         (54, 864, 918))
        self.assertEqual(result['program_order'][-1], 0x4000)
        self.assertEqual(2 * len(candidate) + 40960 * len(order), 3244032)

    def test_changed_stage_payload_or_echo_response_rejected(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        for opcode, event, field in (('fb7c','command_intent','data_out_sha256'), ('fd87','command_reply','sha256')):
            journal, trace = evidence(before, candidate, order)
            target = next(x for x in journal if x['event'] == event and x['opcode'] == opcode)
            target[field] = '0' * 64
            with self.subTest(opcode=opcode), self.assertRaises(ValueError):
                inspector.inspect_history(journal, trace, before, candidate, order)

    def test_duplicate_mutation_or_missing_reply_is_rejected(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        for mode in ('duplicate', 'missing'):
            journal, trace = evidence(before, candidate, order)
            index = next(i for i, x in enumerate(journal) if x['event']=='command_intent' and x['opcode']=='fc7b')
            if mode == 'duplicate': journal[index:index] = copy.deepcopy(journal[index:index+2])
            else: del journal[index+1]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                inspector.inspect_history(journal, trace, before, candidate, order)

    def test_header_first_or_out_of_range_sector_rejected(self):
        _, before, candidate, _ = fixture()
        journal, trace = evidence(before, candidate, [0x5000, 0x4000])
        for order in ([0x4000,0x5000], [0x5000,0x5000,0x4000], [0x3000,0x4000]):
            with self.subTest(order=order), self.assertRaises(ValueError):
                inspector.inspect_history(journal, trace, before, candidate, order)

    def test_transport_mutation_failure_not_hidden_by_successful_journal(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        journal, trace = evidence(before, candidate, order)
        row = next(x for x in trace if x['state']=='after' and x['cdb'].startswith('fc7d'))
        row.update(state='error', native_transfer={'win32_error':31})
        with self.assertRaises(ValueError): inspector.inspect_history(journal, trace, before, candidate, order)

    def test_read_query_failure_is_reported_but_never_counted_as_mutation(self):
        _, before, candidate, _ = fixture();order = [0x5000, 0x4000]
        journal, trace = evidence(before, candidate, order)
        command = 'fc7e' + 'ff' * 14
        trace.extend(({'state':'before','stage':'writer','cdb':command},
                      {'state':'error','stage':'writer','cdb':command,'native_transfer':{'win32_error':31}}))
        result = inspector.inspect_history(journal, trace, before, candidate, order)
        self.assertEqual(result['read_query_errors'], 1)
        self.assertEqual(result['program_commands'], 32)


def recovered_echo_evidence(*, executed):
    """Run real installer/v3 against fake NOR and independently retained wire log."""
    plan=installation_fixture();device=FakeOperational(plan)
    trace, events, journal = [], [], []
    def logged_handle():
        handle=Handle(device);original=handle.exchange
        def exchange(cdb,data_out=None,read_length=0):
            row={'state':'before','stage':'writer','cdb':cdb.hex()}
            trace.append(row.copy())
            try: raw=original(cdb,data_out=data_out,read_length=read_length)
            except Exception as error:
                row.update(state='error',native_transfer={'win32_error':error.errno})
                trace.append(row);raise
            row.update(state='after',response_bytes=len(raw),response_sha256=inspector.sha(raw))
            if len(raw)<=128:row['response_hex']=raw.hex()
            trace.append(row);return raw
        handle.exchange=exchange
        return handle
    old=logged_handle()
    wrapper=recovery_v3.ReadOnlyStateRecoveryTransport(old,log=events.append,reopen_factory=logged_handle)
    session=installer.MiniAppInstallerSession(wrapper,plan,journal=journal.append,known_free_slot=True)
    wrapper.bind_session(session)
    try:
        with patch('time.sleep'):
            session.upload_and_start(IMAGE,expected_sha256=installer.sha(IMAGE))
        session.initialize_spi();session.verify_complete_preimage()
        fail=lambda op:failure() if op==0xFD87 and device.fields[36]==0x5000 else None
        if executed:old.fail_after=fail
        else:old.fail_before=fail
        session.install_application()
        context={'summary':wrapper.summary(),'slot':plan.slot,'build_tag':plan.build_tag,
            'events':events,'v3_source_pinned':True,'policy':{'enabled':True,'only_Windows_error':31,
                'FD87_requires_same_staged_page_and_exact_audit_except_echoed_and_record_CRC':True,
                'FD87_reissue_requires_exact_candidate_page_bytes':True,
                'mutation_retries_allowed':False,'OUT_retries_allowed':False,
                'jump_or_reset_retries_allowed':False,'backend_fallback_allowed':False}}
        return journal,trace,device.original,plan.candidate,list(plan.sector_order),context
    finally:wrapper.close()


class EchoRecoveryInspectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=[recovered_echo_evidence(executed=value) for value in (False,True)]

    def test_real_fake_installer_recovers_echo_before_or_after_execution_once(self):
        for executed,args in enumerate(self.cases):
            journal,trace,before,candidate,order,context=args
            result=inspector.inspect_history(journal,trace,before,candidate,order,recovery=context)
            self.assertEqual(len(result['verified_RAM_echo_recoveries']),1)
            self.assertEqual(result['verified_RAM_echo_recoveries'][0]['already_echoed'],bool(executed))
            self.assertEqual((result['erase_commands'],result['program_commands']), (2,32))

    def test_echo_error_needs_v3_pin_log_and_exact_policy(self):
        journal,trace,before,candidate,order,context=self.cases[0]
        for kind in ('missing','v2','unpinned','empty_log','policy','counter'):
            changed=copy.deepcopy(context)
            if kind=='missing':changed=None
            elif kind=='v2':changed['summary']['version']=2
            elif kind=='unpinned':changed['v3_source_pinned']=False
            elif kind=='empty_log':changed['events']=[]
            elif kind=='policy':changed['policy']['OUT_retries_allowed']=True
            else:changed['summary']['echo_reissues']=2
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                inspector.inspect_history(journal,trace,before,candidate,order,recovery=changed)

    def test_changed_stack_counter_page_identity_or_reissue_proof_rejected(self):
        journal,trace,before,candidate,order,context=self.cases[1]
        for kind in ('stack','counter','identity','page','reissue_CDB','witness','already_count'):
            changed=copy.deepcopy(context)
            audit=next(x for x in changed['events'] if x['event']=='readonly_recovery_audit_reply')
            reissue=next(x for x in changed['events'] if x['event']=='readonly_recovery_reissue_intent')
            if kind in ('stack','counter'):
                offset=112 if kind=='stack' else 80
                raw=bytes.fromhex(audit['raw_hex']);value=struct.unpack_from('<I',raw,offset)[0]
                raw=changed_record(raw,offset,value+4);audit.update(raw_hex=raw.hex(),sha256=inspector.sha(raw))
            elif kind=='identity':
                next(x for x in changed['events'] if x['event']=='readonly_recovery_identity_reply')['raw_hex']='00'*16
            elif kind=='page':reissue['candidate_page_sha256']='0'*64
            elif kind=='reissue_CDB':reissue['cdb']='fd87'+'ff'*14
            elif kind=='witness':changed['events'][0]['witness_sha256']='0'*64
            else:changed['summary']['echo_already_emitted']=0
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                inspector.inspect_history(journal,trace,before,candidate,order,recovery=changed)

    def test_transport_or_installer_proof_cannot_be_omitted_or_swapped(self):
        journal,trace,before,candidate,order,context=self.cases[1]
        for kind in ('trace_identity','trace_audit','prior_audit','extra_reissue','post_audit'):
            changed_trace=copy.deepcopy(trace);changed_journal=copy.deepcopy(journal)
            fault=next(i for i,x in enumerate(changed_trace) if x['state']=='error')
            if kind=='trace_identity':changed_trace[fault+2]['response_hex']='00'*16
            elif kind=='trace_audit':changed_trace[fault+4]['response_hex']=changed_trace[fault-2]['response_hex']
            elif kind=='prior_audit':changed_trace[fault-2]['response_hex']='00'*128
            elif kind=='extra_reissue':changed_trace[fault+7:fault+7]=copy.deepcopy(changed_trace[fault+5:fault+7])
            else:
                start=next(i for i,x in enumerate(changed_journal) if x['event']=='command_intent' and x.get('opcode')=='fd87')
                item=next(x for x in changed_journal[start:] if x['event']=='audit_raw')
                item['record_hex']=changed_record(bytes.fromhex(item['record_hex']),104,0).hex()
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                inspector.inspect_history(changed_journal,changed_trace,before,candidate,order,recovery=context)


if __name__ == '__main__': unittest.main()

