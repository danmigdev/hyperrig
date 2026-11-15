"""HYK1 host API. Default CLI/import never discovers or opens a device.

Uses the existing RAM lifecycle and the separately registered Windows profile
ram-entry-recovery. Snapshot, GPIO check and reset are three explicit methods.
There is no automatic reset, retry, flash command or cold-SPL-state claim.
"""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.probe_mini_recovery import MiniRamSession, RAM_SLOTS, RomCommandError, validate_ram_request
from tools.build_mini_rom_entry_recovery import RECORD_BYTES, validate_record


def _number(value,maximum,name,minimum=0):
    if type(value) is not int or not minimum<=value<=maximum:
        raise ValueError('invalid HYK1 '+name)
    return value


def entry_recovery_identity_cdb():return b'\xfc\x74'+b'\xff'*14
def entry_recovery_snapshot_cdb():return b'\xfc\x75'+b'\xff'*14
def entry_recovery_record_cdb(sequence):
    return b'\xfd\x77'+struct.pack('>I',_number(sequence,65535,'record sequence',1))+b'\xff'*10
def entry_recovery_check_cdb(sequence,crc):
    return b'\xfc\x76'+struct.pack('>II',_number(sequence,65534,'snapshot sequence',1),
                                   _number(crc,0xffffffff,'record CRC'))+b'\xff'*6
def entry_recovery_reset_cdb(sequence,crc):
    return b'\xfc\x81'+struct.pack('>II',_number(sequence,65534,'reset sequence',1),
                                   _number(crc,0xffffffff,'record CRC'))+b'ROM!'+b'\xff'*2


def validate_entry_recovery_request(cdb,data_out,read_length,*,slot):
    if cdb==bytes((0x12,0,0,0,36,0)) or cdb[:2] in (b'\xfb\x06',b'\xfb\x08',b'\xfd\x07'):
        validate_ram_request(cdb,data_out,read_length,slot=slot)
        return
    if slot not in RAM_SLOTS or len(cdb)!=16 or data_out is not None or type(read_length) is not int:
        raise ValueError('HYK1 requires a bounded IN operation and known slot')
    op=cdb[:2]
    if op==b'\xfc\x74' and read_length==16:expected=entry_recovery_identity_cdb()
    elif op==b'\xfc\x75' and read_length==16:expected=entry_recovery_snapshot_cdb()
    elif op==b'\xfd\x77' and read_length==RECORD_BYTES:
        expected=entry_recovery_record_cdb(int.from_bytes(cdb[2:6],'big'))
    elif op in (b'\xfc\x76',b'\xfc\x81') and read_length==16:
        maker=entry_recovery_check_cdb if op==b'\xfc\x76' else entry_recovery_reset_cdb
        expected=maker(*struct.unpack('>II',cdb[2:10]))
    else:raise ValueError('not an allowed HYK1 operation')
    if cdb!=expected:raise ValueError('HYK1 argument or padding mismatch')


class MiniEntryRecoverySession(MiniRamSession):
    """One pinned HYK1 instance. FC81 makes the session terminal before I/O."""
    def __init__(self,transport,*,slot,build_tag,known_free_slot=False,known_uploaded_unstarted=False):
        super().__init__(transport,slot=slot,known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        self.build_tag=_number(build_tag,0xffffffff,'build tag')
        self.sequence=0;self.armed=False;self.reset_submitted=False
        self.last_record=None;self.last_result=None

    def _handshake(self):
        if not self.started or self.failed or self.sequence:raise ValueError('newly started HYK1 required')
        reply=self.transport.exchange(entry_recovery_identity_cdb(),read_length=16)
        expected=b'\xfc\x74HYK1\x01\x07'+struct.pack('>IHH',self.slot,32768,256)
        if reply!=expected:raise ValueError('HYK1 identity/version/slot/size mismatch')
        return {'entry_recovery_identity_hex':reply.hex(),'entry_MMIO':False,
                'snapshot_performed':False,'reset_performed':False}

    def read(self,address,length):
        raise ValueError('HYK1 exposes records, never arbitrary FD61 reads')

    def _active(self):
        if not self.ready or self.failed or self.reset_submitted:
            raise ValueError('identified, unfailed, nonterminal HYK1 session required')

    def _record(self,phase):
        raw=self.transport.exchange(entry_recovery_record_cdb(self.sequence),read_length=256)
        self.last_record=raw
        result=validate_record(raw,base=self.slot,build_tag=self.build_tag,
                               sequence=self.sequence,phase=phase,target=True)
        result.update(record_hex=raw.hex(),gpio_before=list(struct.unpack_from('<9I',raw,64)),
                      gpio_after=list(struct.unpack_from('<9I',raw,100)),
                      clocks_before=list(struct.unpack_from('<12I',raw,136)),
                      clocks_after=list(struct.unpack_from('<12I',raw,184)),
                      consumed_sequence=struct.unpack_from('<I',raw,236)[0],automatic_retry=False)
        self.last_result=result
        return result

    def _operation(self,phase,cdb):
        self.armed=False;self.sequence+=1;self.last_record=self.last_result=None
        try:
            reply=self.transport.exchange(cdb,read_length=16)
            op=b'\xfc\x75' if phase==0 else b'\xfc\x76'
            if len(reply)!=16 or reply[:6]!=op+b'HYK1' or int.from_bytes(reply[6:10],'big')!=self.sequence or reply[14]!=phase or reply[15]>1:
                raise ValueError('HYK1 operation reply mismatch')
            result=self._record(phase)
            if int.from_bytes(reply[10:14],'big',signed=True)!=result['status']:
                raise ValueError('HYK1 reply/record status differs')
            can_check=(phase==0 and result['status']==0 and
                       result['gpio_before'][2]&0x409==0x409 and not result['reset_attempted'])
            if reply[15]!=int(can_check):raise ValueError('HYK1 armed flag differs from snapshot')
            self.armed=can_check
            if result['status'] not in (0,-3):self.failed=True;self.armed=False
            result.update(can_check=self.armed,session_failed=self.failed,GPIO_check_performed=phase==1,
                          reset_performed=False)
            return result
        except Exception:
            self.failed=True;self.armed=False
            raise

    def snapshot(self):
        self._active()
        if self.sequence>=65534:raise ValueError('HYK1 sequence limit')
        return self._operation(0,entry_recovery_snapshot_cdb())

    def check(self):
        self._active()
        if not self.armed or self.last_record is None or self.sequence>=65534:
            raise ValueError('one fresh successful HYK1 snapshot required per GPIO check')
        cdb=entry_recovery_check_cdb(self.sequence,struct.unpack_from('<I',self.last_record,248)[0])
        return self._operation(1,cdb)

    def request_rom_reset_once(self):
        """Submit FC81 once; does NOT establish reset completion or reconnect.

        Root must capture pre-reset USB LastArrivalDate and independently require
        a later arrival plus a fresh WL82/UBOOT INQUIRY. Any hub restart is a
        distinct event, not proof that this command caused a CPU reset.
        """
        self._active()
        if self.last_record is None or self.last_result is None or not self.last_result['stack_guards_ok']:
            raise ValueError('validated exposed HYK1 record required before explicit reset')
        cdb=entry_recovery_reset_cdb(self.sequence,struct.unpack_from('<I',self.last_record,248)[0])
        self.reset_submitted=True;self.ready=False;self.failed=True;self.armed=False
        result={'opcode':'FC81','sequence':self.sequence,'cdb_hex':cdb.hex(),
                'request_attempted':True,'reset_completion_verified':False,'automatic_retry':False,
                'fresh_USB_arrival_and_ROM_INQUIRY_required':True,'token_is_authentication':False}
        try:
            reply=self.transport.exchange(cdb,read_length=16)
        except RomCommandError as error:
            if not error.submitted:raise
            return {**result,'outcome':'post_submit_transport_error','error_type':type(error).__name__,
                    'error':str(error),'transport_details':error.details}
        return {**result,'outcome':'unexpected_reply','reply_hex':reply.hex()}


def main():
    print(json.dumps({'device_io':False,'enumerated':False,'profile':'ram-entry-recovery','magic':'HYK1',
        'identity':entry_recovery_identity_cdb().hex(),'snapshot':entry_recovery_snapshot_cdb().hex(),
        'record_example':entry_recovery_record_cdb(1).hex(),
        'check_example':entry_recovery_check_cdb(1,0).hex(),
        'reset_example_not_submitted':entry_recovery_reset_cdb(1,0).hex(),
        'automatic_retry':False,'NOR_access':False,'cold_SPL_state_verified':False},indent=2))


if __name__=='__main__':main()
