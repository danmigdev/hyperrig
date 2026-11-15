"""Bounded HYRN read recovery with real target counter reconciliation.

Import is offline. Only submitted Win31 failures on FD71 and the FC73 directly
following received FD71 data are recoverable. No upload/jump/init/OUT recovery.
NOR reads may be repeated once after an exact fresh identity/status witness;
the physical counter includes any read whose reply was lost. Status replies
are never synthesized. The frozen MiniNorSession still validates every block.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import struct
import time

from tools.probe_mini_recovery import MiniNorSession, RomCommandError, validate_nor_request
from tools.mini_windows_quiet import RomDiskAttestation


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def query(op):return op.to_bytes(2,'big')+b'\xff'*14


def parse_status(raw):
    require(type(raw) is bytes and len(raw)==16 and raw[:4]==b'\xfc\x73\0\1',
            'HYRN status must be initialized/error0 with exact framing')
    return dict(zip(('sys_div','clk_con2','successful_read_bytes'),struct.unpack_from('>III',raw,4)))


class NorReadRecoveryTransport:
    def __init__(self,transport,*,log,reopen_factory,max_recoveries=8):
        require(callable(log) and callable(reopen_factory),'durable log and explicit reopen factory required')
        require(type(max_recoveries) is int and 1<=max_recoveries<=8,'recovery budget must be1..8')
        require(transport.profile=='nor-reader' and transport.slot in (0x1c20000,0x1c28000),
                'identified HYRN transport profile/slot required')
        require(type(transport.attestation) is RomDiskAttestation
                and transport.attestation.interface_path is not None,'bound immutable USB attestation required')
        self._transport,self._transport_type=transport,type(transport)
        self.attestation=transport.attestation
        self.slot,self.profile=transport.slot,transport.profile
        self.disk,self.inquiry=transport.disk,transport.inquiry
        self.log,self.reopen_factory=log,reopen_factory
        self.max_recoveries=max_recoveries
        self.recovery_attempts=self.read_reissues=self.status_reconciliations=self.lost_read_bytes=0
        self.session=None;self.last_status_raw=None;self.clock=None;self.pending=None
        self.failed=self.closed=self.busy=False
        self._used=set()

    def _event(self,event,**details):
        self.log({'event':event,'utc':datetime.now(timezone.utc).isoformat(),
            'perf_counter_ns':time.perf_counter_ns(),'slot':self.slot,
            'recovery_attempts':self.recovery_attempts,'read_reissues':self.read_reissues,
            'status_reconciliations':self.status_reconciliations,'lost_read_bytes':self.lost_read_bytes,**details})

    def summary(self):
        return {'max_recoveries':self.max_recoveries,'recovery_attempts':self.recovery_attempts,
            'read_reissues':self.read_reissues,'status_reconciliations':self.status_reconciliations,
            'lost_read_bytes':self.lost_read_bytes,'failed':self.failed,'closed':self.closed,
            'mutation_retries_allowed':False,'lifecycle_retries_allowed':False,'status_replies_synthesized':False}

    def _identity(self,raw):
        require(raw==b'\xfc\x70HYRN\1\3'+struct.pack('>II',self.slot,32768),
                'HYRN identity/slot/version/read-only flags differ')

    def bind_session(self,reader,*,status_raw):
        require(self.session is None and not self.failed and not self.closed and not self.busy,
                'bind once to a fresh recovery wrapper')
        require(isinstance(reader,MiniNorSession) and (reader.transport is self._transport or reader.transport is self)
                and reader.slot==self.slot and reader.ready and reader.initialized and not reader.failed
                and reader.capacity==0x100000,'live initialized one-MiB MiniNorSession required')
        status=parse_status(status_raw)
        require(status['successful_read_bytes']==reader.successful_bytes,'initial physical counter differs from reader')
        self.clock=(status['sys_div'],status['clk_con2'])
        self.last_status_raw=status_raw;self.session=reader
        reader.transport=self
        self._event('nor_reader_bound',status_hex=status_raw.hex(),counter=reader.successful_bytes,
                    transport_assigned=True)

    def attach_retained(self,reader,*,expected_counters,expected_clock):
        """Caller must independently prove this exact reader is already live."""
        require(self.session is None and isinstance(reader,MiniNorSession) and reader.transport is self
                and reader.slot==self.slot and not reader.started and not reader.ready
                and not reader.initialized and not reader.failed,'fresh host object for retained HYRN required')
        require(type(expected_counters) is tuple and 1<=len(expected_counters)<=2
                and all(type(n) is int and 0<=n<=0xffffffff for n in expected_counters)
                and type(expected_clock) is tuple and len(expected_clock)==2,'explicit retained counter/clock witness required')
        identity=self.exchange(query(0xfc70),read_length=16);self._identity(identity)
        raw=self.exchange(query(0xfc73),read_length=16);status=parse_status(raw)
        require(status['successful_read_bytes'] in expected_counters
                and (status['sys_div'],status['clk_con2'])==expected_clock,'retained reader state differs')
        reader.started=reader.ready=reader.initialized=True
        reader.known_free_slot=False;reader.capacity=0x100000;reader.successful_bytes=status['successful_read_bytes']
        self.bind_session(reader,status_raw=raw)
        return {'identity_hex':identity.hex(),'status_hex':raw.hex(),**status,
                'upload_performed':False,'jump_performed':False,'SPI_initialization_performed':False}

    def _status_matches(self,raw,counts):
        item=parse_status(raw)
        require((item['sys_div'],item['clk_con2'])==self.clock,'HYRN clock snapshot changed')
        require(item['successful_read_bytes'] in counts,'HYRN physical read counter differs')
        return item

    def _live(self):
        require(self.session is not None and self.session.transport is self and self.session.ready
                and self.session.initialized and not self.session.failed and self.session.capacity==0x100000,
                'bound live reader required')

    def _reopen(self):
        self._event('nor_recovery_close_intent')
        self._transport.close()
        self._event('nor_recovery_reopen_intent')
        new=self.reopen_factory();self._transport=new
        require(type(new) is self._transport_type and new.slot==self.slot and new.profile==self.profile
                and new.attestation==self.attestation and new.disk['path'].casefold()==self.disk['path'].casefold()
                and new.inquiry.get('vendor')=='WL82' and new.inquiry.get('product')=='UBOOT1.00',
                'reopened class/USB attestation/path/profile/identity differs')
        identity=new.exchange(query(0xfc70),read_length=16)
        self._event('nor_recovery_identity',raw_hex=identity.hex());self._identity(identity)
        raw=new.exchange(query(0xfc73),read_length=16)
        self._event('nor_recovery_status',raw_hex=raw.hex(),sha256=sha(raw))
        return new,raw

    def _recover(self,op,cdb,length,error,base,pending):
        self._live()
        require(error.errno==31 and error.submitted and self.recovery_attempts<self.max_recoveries,
                'only bounded submitted Win31 read/status failures can recover')
        require(op==0xfd71 or op==0xfc73 and pending is not None,
                'only FD71 or FC73 immediately after received FD71 can recover')
        key=(cdb,base,None if pending is None else (pending['cdb'],pending['length'],pending['sha256']))
        require(key not in self._used,'this read and counter witness already used recovery')
        require(self.session.successful_bytes==base,'reader counter changed during failed command')
        self.recovery_attempts+=1;self._used.add(key)
        self._event('nor_recovery_begin',cdb=cdb.hex(),read_length=length,base_counter=base,
                    pending_read=pending,win32_error=error.errno,transport_details=error.details)
        new,raw=self._reopen()
        self._live();require(self.session.successful_bytes==base and self.pending==pending,
                            'reader witness changed while reopening')
        if op==0xfd71:
            require(base+2*length<=0xffffffff,'physical read counter would overflow')
            item=self._status_matches(raw,(base,base+length));actual=item['successful_read_bytes']
            lost=actual-base
            self.session.successful_bytes=actual
            self.last_status_raw=raw;self.lost_read_bytes+=lost
            self.read_reissues+=1
            self._event('nor_read_reissue_intent',cdb=cdb.hex(),read_length=length,
                        physical_counter_before_reissue=actual,missed_read_bytes=lost,
                        host_counter_reconciled_to_real_target=True,no_NOR_mutation=True)
            reply=new.exchange(cdb,read_length=length)
            require(type(reply) is bytes and len(reply)==length,'reissued NOR read is short/nonbyte')
            self._event('nor_read_reissue_reply',bytes=len(reply),sha256=sha(reply),
                        following_core_status_still_required=True)
            return reply
        expected=base+pending['length']
        self._status_matches(raw,(expected,))
        self.status_reconciliations+=1
        self._event('nor_status_return_real_reply',raw_hex=raw.hex(),counter=expected,
                    host_counter_not_modified=True,status_reply_synthesized=False)
        return raw

    def exchange(self,cdb,data_out=None,read_length=0):
        validate_nor_request(cdb,data_out,read_length,slot=self.slot)
        require(not self.failed and not self.closed and not self.busy,'NOR recovery transport failed/closed/busy')
        op=int.from_bytes(cdb[:2],'big');base=None
        pending=None if self.pending is None else self.pending.copy()
        self.busy=True
        try:
            if self.session is not None:
                self._live();base=self.session.successful_bytes
                require(op in (0xfc70,0xfc73,0xfd71) and data_out is None,
                        'bound read session cannot change plugin lifecycle or reinitialize SPI')
                if op==0xfd71:
                    require(pending is None and self._status_matches(self.last_status_raw,(base,))
                            and base+2*read_length<=0xffffffff,'prior read not confirmed or counter overflow')
                elif op==0xfc73 and pending is not None:
                    require(pending['base']==base,'host counter changed between received NOR data and status')
                    original=bytes.fromhex(pending['cdb'])
                    require(original[:2]==b'\xfd\x71','pending status is not paired with an NOR read')
                    validate_nor_request(original,None,pending['length'],slot=self.slot)
                elif op==0xfc70:require(pending is None,'identity query cannot interrupt a pending read/status pair')
            try:raw=self._transport.exchange(cdb,data_out=data_out,read_length=read_length)
            except RomCommandError as error:
                if self.session is None or data_out is not None or op not in (0xfd71,0xfc73):raise
                raw=self._recover(op,cdb,read_length,error,base,pending)
            if self.session is not None:
                require(type(raw) is bytes and len(raw)==read_length,'read-only response is short/nonbyte')
                if op==0xfd71:
                    self.pending={'cdb':cdb.hex(),'length':read_length,'sha256':sha(raw),
                                  'base':self.session.successful_bytes}
                elif op==0xfc73:
                    expected=self.session.successful_bytes+(pending['length'] if pending else 0)
                    self._status_matches(raw,(expected,))
                    self.last_status_raw=raw;self.pending=None
                elif op==0xfc70:self._identity(raw)
            return raw
        except BaseException as error:
            self.failed=True
            try:self._event('nor_recovery_terminal',cdb=cdb.hex(),error_type=type(error).__name__,
                            error=str(error),automatic_reset=False,further_commands_allowed=False)
            except Exception:pass
            raise
        finally:self.busy=False

    def close(self):
        if not self.closed:
            self.closed=True;self._transport.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
