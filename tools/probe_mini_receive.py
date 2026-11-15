"""HYRX receive observation API; import/default CLI perform no device I/O.

The caller supplies an explicit reviewed transport and RAM-slot lifecycle.
The separately instantiated Windows adapter selects the pinned transport's
ram-receive profile and this module's bounded RAM whitelist. No recovery
mode change, NVM command, automatic retry or implicit receive test exists.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.probe_mini_recovery import MiniRamSession, WindowsRomTransport, RomCommandError, RAM_SLOTS, validate_ram_request
from tools.build_mini_rom_receive import MAX_BYTES, RECORD_BYTES, poison, validate_record


def number(value, low, high, name):
    if type(value) is not int or not low <= value <= high: raise ValueError("invalid "+name)
    return value


def identity_cdb(): return b"\xfc\x82"+b"\xff"*14
def record_cdb(): return b"\xfd\x85"+b"\xff"*14


def arm_cdb(sequence,length,nonce,checksum,seed):
    number(sequence,1,65535,"sequence");number(length,1,MAX_BYTES,"length")
    number(nonce,0,0xFFFFFFFF,"nonce");number(checksum,0,0xFFFFFFFF,"checksum");number(seed,0,255,"seed")
    return b"\xfc\x83"+struct.pack(">HHIIBB",sequence,length,nonce,checksum,seed,255)


def receive_cdb(sequence,length,nonce):
    number(sequence,1,65535,"sequence");number(length,1,MAX_BYTES,"length");number(nonce,0,0xFFFFFFFF,"nonce")
    return b"\xfb\x84"+struct.pack(">HIH",sequence,nonce,length)+b"\xff"*6


def validate_receive_request(cdb,data_out,read_length,*,slot):
    if cdb == bytes((0x12,0,0,0,36,0)) or cdb[:2] in (b"\xfb\x06",b"\xfd\x07",b"\xfb\x08"):
        validate_ram_request(cdb,data_out,read_length,slot=slot);return
    if slot not in RAM_SLOTS or not isinstance(cdb,bytes) or len(cdb)!=16 or type(read_length) is not int:
        raise ValueError("HYRX requires a known slot and exact CDB")
    if cdb[:2]==b"\xfb\x84":
        seq,nonce,n=struct.unpack_from(">HIH",cdb,2)
        expected=receive_cdb(seq,n,nonce)
        if not isinstance(data_out,bytes) or len(data_out)!=n or read_length!=0:
            raise ValueError("HYRX receive is OUT exactly1..260 bytes with no IN phase")
    else:
        if data_out is not None: raise ValueError("HYRX reply commands are IN only")
        if cdb[:2]==b"\xfc\x82" and read_length==16: expected=identity_cdb()
        elif cdb[:2]==b"\xfd\x85" and read_length==512: expected=record_cdb()
        elif cdb[:2]==b"\xfc\x83" and read_length==16:
            seq,n,nonce,checksum,seed,_=struct.unpack_from(">HHIIBB",cdb,2)
            expected=arm_cdb(seq,n,nonce,checksum,seed)
        else: raise ValueError("not a bounded HYRX command")
    if cdb!=expected: raise ValueError("HYRX CDB padding differs")


class WindowsReceiveTransport(WindowsRomTransport):
    """Explicit shared SPTD adapter; never constructed by import/default CLI."""
    def __init__(self,path,*,slot):
        super().__init__(path,slot=slot,profile="ram-receive")


class MiniReceiveSession(MiniRamSession):
    def __init__(self,transport,*,slot,build_tag,expected_raw_return=None,
                 known_free_slot=False,known_uploaded_unstarted=False):
        super().__init__(transport,slot=slot,known_free_slot=known_free_slot,
                         known_uploaded_unstarted=known_uploaded_unstarted)
        self.build_tag=number(build_tag,0,0xFFFFFFFF,"build tag")
        if expected_raw_return is not None: number(expected_raw_return,0,0x7FFFFFFF,"observed return value")
        self.expected_raw_return=expected_raw_return
        self.sequence=0;self.closed_observations=False;self.ambiguous_receive=False
        self.last_records=[];self.last_result=None;self.out_submitted=False

    def _handshake(self):
        reply=self.transport.exchange(identity_cdb(),read_length=16)
        expected=b"\xfc\x82HYRX\1\0"+struct.pack(">II",self.slot,32768)
        if reply!=expected: raise ValueError("HYRX identity/version/slot differs")
        return {"receive_observer_identity_hex":reply.hex(),"receive_called_on_entry":False,
                "NVM_commands_available":False,"mmio_actions":False}

    def read(self,address,length):
        raise ValueError("HYRX permits diagnostic records only, never FD61 arbitrary reads")

    def _capture(self,payload,nonce,seed):
        raw=self.transport.exchange(record_cdb(),read_length=RECORD_BYTES)
        self.last_records.append(raw)
        return validate_record(raw,base=self.slot,build_tag=self.build_tag,sequence=self.sequence,
                               nonce=nonce,payload=payload,seed=seed)

    def receive_once(self,payload,*,nonce,seed=0x55):
        if not self.ready or self.failed or self.closed_observations or self.sequence>=65535:
            raise ValueError("one explicitly identified, unfailed HYRX session required")
        if not isinstance(payload,bytes) or not 1<=len(payload)<=MAX_BYTES:
            raise ValueError("HYRX payload must be1..260 bytes")
        number(nonce,0,0xFFFFFFFF,"nonce");number(seed,0,255,"seed")
        if any(a==b for a,b in zip(payload,poison(len(payload),seed))):
            raise ValueError("diagnostic payload must differ from every initial poison byte")
        seq=self.sequence+1
        arm=arm_cdb(seq,len(payload),nonce,zlib.crc32(payload),seed)
        out=receive_cdb(seq,len(payload),nonce)
        self.sequence=seq;self.last_records=[];self.last_result=None;self.out_submitted=False
        try:
            reply=self.transport.exchange(arm,read_length=16)
            expected=b"\xfc\x83HYRX"+struct.pack(">HIHBB",seq,0,len(payload),1,1)
            if reply!=expected: raise ValueError("HYRX arm echo/sequence/state mismatch")
            self.out_submitted=True  # Set before transport; timeout cannot authorize a retry.
            response=self.transport.exchange(out,data_out=payload)
            if response!=b"": raise ValueError("unexpected IN phase after HYRX OUT")
            first=self._capture(payload,nonce,seed);self.last_result=first
            anomalous=(first["raw_return"]<0 or not first["observed_complete_and_stable"] or
                       self.expected_raw_return is not None and first["raw_return"]!=self.expected_raw_return)
            if anomalous:
                self.failed=True
                first.update(session_failed=True,record_resampled=False,automatic_retry=False)
                return first
            second=self._capture(payload,nonce,seed);self.last_result=second
            a,b=self.last_records
            # The sample counter and envelope CRC are expected to change.
            same=(a[:92]+a[96:504]+a[508:])==(b[:92]+b[96:504]+b[508:])
            if not same or second["sample_count"]!=first["sample_count"]+1 or not second["observed_complete_and_stable"]:
                self.failed=True
                second.update(session_failed=True,record_resampled=True,records_stable=False,automatic_retry=False)
                return second
            # An uncalibrated first observation ends here. An expected return
            # supplied from reviewed evidence enables only another observation,
            # never a writer or an assertion of general return semantics.
            self.closed_observations=self.expected_raw_return is None
            second.update(session_failed=False,record_resampled=True,records_stable=True,automatic_retry=False,
                          observation_session_closed=self.closed_observations,
                          expected_raw_return=self.expected_raw_return,nonce_is_authentication=False)
            return second
        except Exception:
            self.failed=True;self.ambiguous_receive=self.out_submitted
            raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--length",type=int,default=260,help="offline CDB example length")
    a=p.parse_args();number(a.length,1,MAX_BYTES,"length")
    payload=bytes(b^255 for b in poison(a.length,0x55))
    print(json.dumps({"device_io":False,"enumerated":False,"magic":"HYRX","automatic_retry":False,
        "identity_cdb":identity_cdb().hex(),"arm_cdb":arm_cdb(1,a.length,0x1234ABCD,zlib.crc32(payload),0x55).hex(),
        "receive_cdb":receive_cdb(1,a.length,0x1234ABCD).hex(),"record_cdb":record_cdb().hex(),
        "return_semantics_qualified":False,"NVM_commands_available":False},indent=2))


if __name__ == "__main__": main()
