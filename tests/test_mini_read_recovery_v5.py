"""FINISH recovery through the frozen installer, fake NOR and fake handles."""
from dataclasses import replace
import struct
import unittest
from unittest.mock import patch

from tools import install_mini_app as installer
from tools import recover_mini_read_v5 as recovery
from tools.probe_mini_app_writer import simple_cdb
from tools.probe_mini_recovery import RomCommandError
from tests.test_mini_app_install import FakeOperational, fixture, IMAGE
from tests.test_mini_app_writer_protocol import changed_record
from tests.test_mini_read_recovery import Handle, failure
from tests import test_mini_read_recovery_v4 as previous


class FinishRecoveryTests(previous.AuditedCommandTests):
    def live(self, *, preflight=False, new_configure=None, budget=8):
        device = FakeOperational(fixture()); old = Handle(device)
        handles, events, journal = [old], [], []
        def reopen():
            new = Handle(device); handles.append(new)
            if new_configure: new_configure(new)
            return new
        wrapper = recovery.FinishCommandRecoveryTransport(old, log=events.append,
                    reopen_factory=reopen, max_recoveries=budget)
        session = installer.MiniAppInstallerSession(wrapper, fixture(), journal=journal.append, known_free_slot=True)
        wrapper.bind_session(session)
        with patch('time.sleep'): session.upload_and_start(IMAGE, expected_sha256=installer.sha(IMAGE))
        session.initialize_spi()
        if preflight: session.verify_complete_preimage()
        self.addCleanup(wrapper.close)
        return device, old, handles, wrapper, session, events

    def test_every_mutation_and_state_changing_command_is_never_retried(self):
        # V5 may inspect a lost FINISH, but never replay an executed command.
        for op in (0xFC7A, 0xFB7C, 0xFC7B, 0xFC7D, 0xFC80):
            with self.subTest(op=op):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_after = lambda actual: failure() if actual == op else None
                with self.assertRaises((RomCommandError, ValueError)): session.install_application()
                attempts = int(op in (0xFC7B, 0xFC7D, 0xFC80))
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (attempts, 1 + attempts))
                self.assertEqual(wrapper.finish_request_reissues + wrapper.mutation_request_reissues, 0)
                self.assertEqual(device.counts[op], 1)
                self.assertEqual(device.commands.count(0xFB08), 1)
                self.assertTrue(session.failed)
                if attempts: self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
                self.assertEqual(session.mutation_completion_unknown, op in (0xFC7B, 0xFC7D))

    def test_unexecuted_finish_first_or_header_sector_uses_real_ACK_and_normal_readback(self):
        for sector in (0x5000, 0x4000):
            with self.subTest(sector=hex(sector)):
                actual = []
                def configure(handle):
                    def observe(op, raw):
                        if op == 0xFC80: actual.append(raw)
                        return raw
                    handle.reply_change = observe
                device, old, handles, wrapper, session, events = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC80 and device.fields[32] == sector else None
                result = session.install_application()
                self.assertTrue(result['application_verified'])
                self.assertEqual((wrapper.recovery_attempts, wrapper.finish_request_reissues), (1, 1))
                self.assertEqual(wrapper.mutation_request_reissues, 0)
                self.assertEqual(device.counts[0xFC80], 2)
                self.assertEqual(device.erase_addresses, [0x5000, 0x4000])
                self.assertEqual(len(device.program_addresses), 32)
                self.assertEqual(len(set(device.program_addresses)), 32)
                self.assertEqual([r[0] for r in handles[1].calls[:5]], [0xFC78, 0xFD88, 0xFC80, 0xFD88, 0xFD7F])
                failed = next(r for r in old.calls if r[0] == 0xFC80 and int.from_bytes(r[1][10:14], 'big') == sector)
                self.assertEqual(failed[1:], handles[1].calls[2][1:])
                begin = next(e for e in events if e['event'] == 'unexecuted_finish_recovery_begin')
                reply = next(e for e in events if e['event'] == 'unexecuted_finish_recovery_reissue_reply')
                self.assertEqual(bytes.fromhex(reply['raw_hex']), actual[0])
                self.assertFalse(reply['synthetic_ACK'])
                prior = bytes.fromhex(begin['prior_audit_hex'])
                post_index = session.raw_records.index(prior) + 1
                post = session.raw_records[post_index]
                self.assertEqual(struct.unpack_from('<IIII', post, 68),
                    (*struct.unpack_from('<III', prior, 68), struct.unpack_from('<I', prior, 80)[0] + 4096))
                self.assertEqual((struct.unpack_from('<I', post, 16)[0], struct.unpack_from('<I', post, 24)[0]), (5, 0))
                self.assertFalse(session.mutation_completion_unknown)
                self.assertEqual(session.verified_sectors, [0x5000, 0x4000])
                self.assertEqual(wrapper.summary()['version'], 5)

    def test_consumed_partial_or_completed_finish_never_reissues(self):
        for kind in ('sequence_only', 'partial_read', 'failed_crc', 'completed'):
            with self.subTest(kind=kind):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                def lose(op):
                    if op != 0xFC80: return None
                    if kind == 'completed':
                        cdb = installer.mutation_cdb(op, session.token, session.sequence, session.expected['sector'])
                        device.exchange(cdb, read_length=16)
                    else:
                        device.fields[28] += 1
                        if kind != 'sequence_only': device.fields[80] += 512
                        if kind == 'failed_crc': device.fields.update({16:6, 20:9})
                    return failure()
                old.fail_before = lose
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.finish_request_reissues, 0)
                self.assertEqual([r[0] for r in handles[1].calls], [0xFC78, 0xFD88])
                self.assertEqual(len(device.program_addresses), 16)
                self.assertEqual(device.erase_addresses, [0x5000])
                self.assertFalse(session.mutation_completion_unknown)
                self.assertEqual(session.verified_sectors, [])

    def test_every_changed_fresh_audit_word_rejects_even_with_valid_record_CRC(self):
        for offset in range(0, 128, 4):
            with self.subTest(offset=offset):
                def configure(handle):
                    def change(op, raw):
                        if op != 0xFD88: return raw
                        value = struct.unpack_from('<I', raw, offset)[0]
                        return changed_record(raw, offset, value ^ 1)
                    handle.reply_change = change
                device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC80 else None
                # changed_record recomputes offset120, so corrupt that CRC explicitly.
                if offset == 120:
                    def configure_crc(handle):
                        handle.reply_change = lambda op, raw: raw[:120] + bytes((raw[120] ^ 1,)) + raw[121:] if op == 0xFD88 else raw
                    wrapper._reopen = lambda: self.configured_handle(device, handles, configure_crc)
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.finish_request_reissues, 0)
                self.assertNotIn(0xFC80, [r[0] for r in handles[1].calls])

    @staticmethod
    def configured_handle(device, handles, configure):
        handle = Handle(device); handles.append(handle); configure(handle); return handle

    def test_finish_requires_exact_pending_planned_completed_sector(self):
        for kind in ('unknown', 'preflight', 'phase', 'sector', 'sequence', 'bitmap', 'staged', 'echoed',
                     'readback', 'echo', 'candidate', 'status', 'audit', 'verified', 'last_page'):
            with self.subTest(kind=kind):
                device, old, handles, wrapper, session, _ = self.live(preflight=True)
                def lose(op):
                    if op != 0xFC80: return None
                    if kind == 'unknown': session.mutation_completion_unknown = True
                    elif kind == 'preflight': session.preimage_verified = False
                    elif kind == 'phase': session.phase = 'complete'
                    elif kind == 'sector': session.pending_operation = 'other'
                    elif kind == 'sequence': session.expected['sequence'] += 1
                    elif kind == 'bitmap': session.expected['page_bitmap'] ^= 1
                    elif kind in ('staged', 'echoed'): session.expected[kind] = 1
                    elif kind == 'readback': session.last_page_readback = b'wrong'
                    elif kind == 'echo': session.last_echo = b'wrong'
                    elif kind == 'candidate':
                        data = bytearray(session.installation.candidate); data[4096] ^= 1
                        session.installation = replace(session.installation, candidate=bytes(data))
                    elif kind == 'status': session.last_status = {}
                    elif kind == 'audit': session.last_audit = None
                    elif kind == 'verified': session.verified_sectors.append(0x5000)
                    else: session.expected['page'] -= 256
                    return failure()
                old.fail_before = lose
                with self.assertRaises(RomCommandError): session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))
                self.assertEqual(wrapper.finish_request_reissues, 0)

    def test_finish_requires_immediately_previous_validated_audit_and_exact_CDB(self):
        for kind in ('interposed', 'token', 'sequence', 'address'):
            with self.subTest(kind=kind):
                _, old, handles, wrapper, session, _ = self.live(preflight=True)
                original = session._exchange
                def exchange(cdb, **kwargs):
                    if cdb[:2] == b'\xfc\x80':
                        if kind == 'interposed': wrapper.exchange(simple_cdb(0xFC78), read_length=16)
                        else:
                            token, seq, address = session.token, session.sequence, session.expected['sector']
                            if kind == 'token': token += 1
                            elif kind == 'sequence': seq += 1
                            else: address += 4096
                            cdb = installer.mutation_cdb(0xFC80, token, seq, address)
                    return original(cdb, **kwargs)
                session._exchange = exchange
                old.fail_before = lambda op: failure() if op == 0xFC80 else None
                with self.assertRaises(RomCommandError): session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_finish_witness_must_remain_unchanged_during_reopen(self):
        for kind in ('expected', 'prior', 'status', 'unknown', 'pending', 'readback', 'verified', 'plan', 'ready'):
            with self.subTest(kind=kind):
                session = None
                def configure(_):
                    if kind == 'expected': session.expected['sequence'] += 1
                    elif kind == 'prior': session.last_record = b'changed'
                    elif kind == 'status': session.last_status = {}
                    elif kind == 'unknown': session.mutation_completion_unknown = True
                    elif kind == 'pending': session.pending_operation = 'other'
                    elif kind == 'readback': session.last_page_readback = b'changed'
                    elif kind == 'verified': session.verified_sectors.append(0x5000)
                    elif kind == 'plan': session.installation = replace(session.installation, plan_sha256='f'*64)
                    else: session.ready = False
                _, old, _, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC80 else None
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.finish_request_reissues, 0)

    def test_finish_real_ACK_and_post_audit_cannot_be_missing_or_changed(self):
        for kind in ('short', 'opcode', 'token', 'sequence', 'phase', 'crc', 'error', 'post_audit', 'readback'):
            with self.subTest(kind=kind):
                def configure(handle):
                    audits = 0
                    def change(op, raw):
                        nonlocal audits
                        if op == 0xFD88:
                            audits += 1
                            if kind == 'post_audit' and audits == 2: return changed_record(raw, 80, 0)
                        if op == 0xFD7F and kind == 'readback': return bytes(len(raw))
                        if op != 0xFC80: return raw
                        if kind == 'short': return raw[:-1]
                        offset = {'opcode':1, 'token':7, 'sequence':11, 'phase':3, 'crc':15, 'error':2}.get(kind)
                        if offset is not None:
                            data = bytearray(raw); data[offset] ^= 1; return bytes(data)
                        return raw
                    handle.reply_change = change
                device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                old.fail_before = lambda op: failure() if op == 0xFC80 else None
                with self.assertRaises(ValueError): session.install_application()
                self.assertEqual(wrapper.finish_request_reissues, 1)
                self.assertEqual(device.counts[0xFC80], 1)
                self.assertEqual(session.verified_sectors, [])
                self.assertFalse(session.mutation_completion_unknown)

    def test_finish_identity_audit_or_reissue_failure_is_terminal_without_recursion(self):
        for failed_op in (0xFC78, 0xFD88, 0xFC80):
            for after in (False, True):
                with self.subTest(op=failed_op, after=after):
                    def configure(handle):
                        lose = lambda op: failure() if op == failed_op else None
                        if after: handle.fail_after = lose
                        else: handle.fail_before = lose
                    device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
                    old.fail_before = lambda op: failure() if op == 0xFC80 else None
                    with self.assertRaises(RomCommandError): session.install_application()
                    self.assertEqual((wrapper.recovery_attempts, len(handles)), (1, 2))
                    self.assertLessEqual(device.counts.get(0xFC80, 0), 1)
                    self.assertEqual(len(device.program_addresses), 16)

    def test_finish_does_not_recover_other_errors_unsubmitted_or_timeout(self):
        for error in (failure(5), failure(submitted=False), TimeoutError('FINISH timeout')):
            with self.subTest(error=repr(error)):
                _, old, handles, wrapper, session, _ = self.live(preflight=True)
                old.fail_before = lambda op: error if op == 0xFC80 else None
                with self.assertRaises(type(error)): session.install_application()
                self.assertEqual((wrapper.recovery_attempts, len(handles)), (0, 1))

    def test_finish_shares_eight_recovery_budget_with_v4_mutations(self):
        seen = set()
        def configure(handle):
            def lose(op):
                address = handle.device.fields.get(32 if op == 0xFC80 else 36)
                key = op, address
                if (op == 0xFC7D and 0x5000 <= address < 0x5700 or op == 0xFC80) and key not in seen:
                    seen.add(key); return failure()
            handle.fail_before = lose
        device, old, handles, wrapper, session, _ = self.live(preflight=True, new_configure=configure)
        configure(old)
        with self.assertRaises(RomCommandError): session.install_application()
        self.assertEqual((wrapper.recovery_attempts, wrapper.mutation_request_reissues, wrapper.finish_request_reissues), (8, 7, 1))
        self.assertEqual(len(handles), 9)
        self.assertEqual(device.counts[0xFC80], 1)
        self.assertEqual(len(set(device.program_addresses)), 32)
        self.assertEqual(session.verified_sectors, [0x5000])

    def test_finish_same_witness_cannot_be_used_twice(self):
        _, old, _, wrapper, session, events = self.live(preflight=True)
        old.fail_before = lambda op: failure() if op == 0xFC80 else None
        checked = False
        def log(event):
            nonlocal checked
            events.append(event)
            if event['event'] == 'unexecuted_finish_recovery_reissue_intent':
                checked = True
                cdb = installer.mutation_cdb(0xFC80, session.token, session.sequence, session.expected['sector'])
                with self.assertRaisesRegex(ValueError, 'witness already used'):
                    wrapper._finish_witness(cdb, 16, 0xFD88, session.last_record)
        wrapper.log = log
        session.install_application()
        self.assertTrue(checked)

    def test_finish_durable_log_failure_prevents_unlogged_reissue(self):
        for name in ('unexecuted_finish_recovery_begin', 'unexecuted_finish_recovery_reissue_intent'):
            with self.subTest(event=name):
                device, old, handles, wrapper, session, events = self.live(preflight=True)
                old.fail_before = lambda op: failure() if op == 0xFC80 else None
                def log(event):
                    if event['event'] == name: raise OSError('durable FINISH log unavailable')
                    events.append(event)
                wrapper.log = log
                with self.assertRaises(OSError): session.install_application()
                self.assertEqual(device.counts.get(0xFC80, 0), 0)
                self.assertEqual(len(handles), 1 if name.endswith('begin') else 2)


# Optional native check compiled separately with ASan/UBSan. Including the
# unchanged operational source exposes its private state to fake callbacks;
# this neither patches target code nor substitutes a Python state model.
NATIVE_FINISH_HARNESS = r'''
#include "writer.c"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t nor_bytes[0x100000],goal[4096],incoming[260],sent[512],cbw[31],answer[16];
static hyw_handler handler;
static unsigned sent_bytes,wren_calls,erase_calls,program_calls,sr;
static unsigned watch_finish,status_calls,read_calls,fail_status,fail_read;
static void consumed(void){if(watch_finish)assert(state.sequence==35&&state.busy&&state.job==0xfc80);}
static int io_init(void *u,uint32_t *id){(void)u;*id=0xeb6014;return 0;}
static int io_status(void *u,uint8_t *a,uint8_t *b)
{(void)u;consumed();if(watch_finish){++status_calls;if(fail_status)return -1;}*a=(uint8_t)sr;*b=2;return 0;}
static int io_read(void *u,uint32_t a,uint8_t *p,unsigned n)
{(void)u;consumed();assert(hyw_range(a,n)&&n<=512);if(watch_finish){++read_calls;if(fail_read==read_calls)return -1;}memcpy(p,nor_bytes+a,n);return 0;}
static int io_wren(void *u)
{(void)u;assert(!watch_finish&&(state.job==0xfc7b||state.job==0xfc7d));++wren_calls;sr=2;return 0;}
static int io_erase(void *u,uint32_t a)
{(void)u;assert(!watch_finish&&sr==2&&a==0x5000);++erase_calls;memset(nor_bytes+a,255,4096);sr=0;return 0;}
static int io_program(void *u,uint32_t a,const uint8_t *p)
{unsigned i;(void)u;assert(!watch_finish&&sr==2&&a>=0x5000&&a<0x6000);++program_calls;for(i=0;i<256;++i)nor_bytes[a+i]&=p[i];sr=0;return 0;}
static void io_delay(void *u){(void)u;}
static int io_send(const void *p,uint32_t n){assert(n<=sizeof(sent));memcpy(sent,p,n);sent_bytes=n;return 0;}
static int io_receive(void *p,uint32_t n){assert(n==260);memcpy(p,incoming,n);return 260;}
static void request(unsigned op,unsigned n)
{
    memset(cbw,0,sizeof(cbw));memset(cbw+15,255,16);put32(cbw,0x43425355);put32(cbw+8,n);
    cbw[12]=op==0xfb7c?0:128;cbw[14]=16;cbw[15]=(uint8_t)(op>>8);cbw[16]=(uint8_t)op;sent_bytes=0;
}
static void invoke(void){assert(handler(cbw,answer)==1);}
static void action(unsigned op,uint32_t address)
{request(op,16);putbe32(cbw+17,state.token);putbe32(cbw+21,state.sequence+1);putbe32(cbw+25,address);}
static void audit(uint8_t *out)
{request(0xfd88,128);invoke();assert(sent_bytes==128&&le32(sent+120)==hyw_crc32(sent,120));memcpy(out,sent,128);}
static void completed_pages(void)
{
    unsigned i,page;hyw_services s={io_send,io_receive,&handler};
    hyw_nor n={0,io_init,io_status,io_read,io_wren,io_erase,io_program,io_delay,4};
    wren_calls=erase_calls=program_calls=sr=watch_finish=status_calls=read_calls=fail_status=fail_read=0;
    for(i=0;i<sizeof(nor_bytes);++i)nor_bytes[i]=(uint8_t)(i*7+(i>>8));
    for(i=0;i<sizeof(goal);++i)goal[i]=(uint8_t)(i*13+19+(i>>8));
    assert(!hyperrig_writer_initialize(&s,&n,0x1c20000));request(0xfc79,16);invoke();assert(!state.error);
    request(0xfc7a,16);putbe32(cbw+17,0x5000);putbe32(cbw+21,hyw_crc32(nor_bytes+0x5000,4096));putbe32(cbw+25,hyw_crc32(goal,4096));invoke();
    for(page=0;page<16;++page){
        memcpy(incoming,goal+page*256,256);putbe32(incoming+256,hyw_crc32(incoming,256));
        request(0xfb7c,260);putbe32(cbw+17,state.token);putbe32(cbw+21,state.sequence+1);putbe32(cbw+25,0x5000+page*256);cbw[29]=1;cbw[30]=0;invoke();
        request(0xfd87,256);putbe32(cbw+17,state.token);putbe32(cbw+21,state.stage_sequence);putbe32(cbw+25,0x5000+page*256);invoke();
        if(!page){action(0xfc7b,0x5000);invoke();}
        action(0xfc7d,0x5000+page*256);invoke();assert(!state.error);
    }
    assert(state.sequence==34&&state.bitmap==0xffff&&state.phase==HYW_ERASED&&!state.staged&&!state.echoed);
    assert(wren_calls==17&&erase_calls==1&&program_calls==16&&!memcmp(nor_bytes+0x5000,goal,4096));
}
int main(void)
{
    uint8_t before[128],fresh[128],saved[31];unsigned cases=0,kind;uint32_t reads;
    completed_pages();audit(before);action(0xfc80,0x5000);memcpy(saved,cbw,31);
    request(0xfc78,16);invoke();audit(fresh);assert(!memcmp(before,fresh,128));
    memcpy(cbw,saved,31);reads=state.read_bytes;watch_finish=1;invoke();watch_finish=0;
    assert(!state.error&&state.sequence==35&&state.phase==HYW_VERIFIED&&!state.token&&!state.erased);
    assert(read_calls==8&&status_calls==1&&state.read_bytes==reads+4096&&state.last_crc==hyw_crc32(goal,4096));
    assert(answer[0]==0xfc&&answer[1]==0x80&&!answer[2]&&answer[3]==HYW_VERIFIED&&be32(answer+4)==0&&be32(answer+8)==35);
    assert(wren_calls==17&&erase_calls==1&&program_calls==16);audit(fresh);assert(memcmp(before,fresh,128));++cases;
    memcpy(cbw,saved,31);invoke();assert(state.error==HYW_STATE&&state.sequence==35&&read_calls==8&&wren_calls==17);++cases;
    for(kind=0;kind<5;++kind){
        completed_pages();audit(before);reads=state.read_bytes;
        if(kind==0)fail_status=1;
        if(kind==1)fail_read=1;
        if(kind==2)fail_read=4;
        if(kind==3)nor_bytes[0x5000]^=1;
        if(kind==4)state.bitmap^=1;
        action(0xfc80,0x5000);watch_finish=1;invoke();watch_finish=0;
        assert(state.sequence==35&&state.error&&state.phase==HYW_FAILED&&state.token);
        assert(wren_calls==17&&erase_calls==1&&program_calls==16);
        assert(state.read_bytes==reads+(kind==2?1536u:kind==3?4096u:0u));
        audit(fresh);assert(memcmp(before,fresh,128));++cases;
    }
    printf("{\"cases\":%u,\"FINISH_sequence_checked_in_status_and_read_callbacks\":true,\"no_FINISH_WREN_erase_program\":true,\"fake_NOR_only\":true,\"hardware\":false}\n",cases);
    return 0;
}
'''


if __name__ == '__main__': unittest.main()
