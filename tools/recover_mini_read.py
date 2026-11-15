"""One bounded recovery of an unexecuted HYW1 FD7F after Win32 error31.

Composition only: no frozen writer/installer/Windows transport is changed.
The caller explicitly provides an open identified operational transport, binds
the installer session, and persists every recovery event. Import does no I/O.
There is at most one reopen and one read reissue in this wrapper's lifetime.
No OUT, erase, program, finish, jump, reset or other error is ever retried.
"""
from __future__ import annotations

from datetime import datetime,timezone
import hashlib
import struct
import time

from tools.install_mini_app import MiniAppInstallerSession,validate_writer_operational_request
from tools.build_mini_app_writer import validate_audit_record
from tools.probe_mini_recovery import WindowsRomTransport,RomCommandError
from tools.probe_mini_app_writer import simple_cdb


def require(condition,message):
    if not condition:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()


class ReadOnlyFailureRecoveryTransport:
    """Wrap one existing handle; bind before upload, close the wrapper finally.

    `session=MiniAppInstallerSession(wrapper,...); wrapper.bind_session(session)`
    ensures the prior audit comes from the real, nonfailed installer validation.
    The last successful transport command must itself be that exact FD88.
    A separate reopen factory is supported for fake tests; the default repeats
    the frozen Windows constructor's PnP ancestry and INQUIRY checks.
    """
    def __init__(self,transport,*,log,reopen_factory=None):
        require(callable(log),"durable recovery logger required")
        require(getattr(transport,"profile",None)=="app-writer-operational","operational HYW1 profile required")
        self._transport=transport;self.log=log;self.slot=transport.slot;self.profile=transport.profile
        self.path=transport.disk["path"];self.inquiry=transport.inquiry;self.disk=transport.disk
        self._reopen=reopen_factory or (lambda:WindowsRomTransport(self.path,slot=self.slot,profile=self.profile))
        self.session=None;self.failed=False;self.closed=False;self.busy=False
        self.recovery_attempts=0;self.read_reissues=0;self.last_opcode=None;self.last_reply=None

    def bind_session(self,session):
        require(self.session is None and isinstance(session,MiniAppInstallerSession)
                and session.transport is self and session.slot==self.slot,"bind exactly this installer/session/slot once")
        self.session=session

    def _event(self,event,**details):
        self.log({"event":event,"utc":datetime.now(timezone.utc).isoformat(),
                  "perf_counter_ns":time.perf_counter_ns(),"slot":self.slot,
                  "recovery_attempts":self.recovery_attempts,"read_reissues":self.read_reissues,**details})

    def _validated_snapshot(self,previous_opcode,previous_reply):
        session=self.session
        require(session is not None and session.ready and not session.failed,"bound live nonfailed installer required")
        require(previous_opcode==0xFD88 and isinstance(previous_reply,bytes),"FD88 must immediately precede failed FD7F")
        require(session.last_record==previous_reply and session.last_audit is not None,"installer did not validate the previous wire record")
        parsed=validate_audit_record(previous_reply,base=self.slot,build_tag=session.installation.build_tag,
                                     expected_mutations_enabled=True)
        require(parsed==session.last_audit and parsed["error"]==0 and parsed["rx_guards_ok"]==parsed["stack_guards_ok"]==1,
                "previous audit failed or differs from installer validation")
        require(all(parsed[name]==value for name,value in session.expected.items()),"installer expected state differs from prior audit")
        return previous_reply

    def _identity(self,new):
        require(new.slot==self.slot and new.profile==self.profile and new.disk["path"].casefold()==self.path.casefold(),
                "reopened transport changed path/slot/profile")
        require(new.inquiry.get("vendor")=="WL82" and new.inquiry.get("product")=="UBOOT1.00",
                "reopened transport has wrong ROM inquiry")
        self._event("read_recovery_reopened",path=self.path,inquiry=new.inquiry)
        self._event("read_recovery_identity_intent",cdb=simple_cdb(0xFC78).hex())
        identity=new.exchange(simple_cdb(0xFC78),read_length=16)
        self._event("read_recovery_identity_reply",raw_hex=identity.hex())
        require(identity==b"\xfc\x78HYW1\1\1"+struct.pack(">II",self.slot,32768),"reopened HYW1 identity/gate/slot differs")

    def _recover(self,cdb,read_length,snapshot,error):
        self.recovery_attempts+=1
        self._event("read_recovery_begin",cdb=cdb.hex(),read_length=read_length,error=str(error),
                    win32_error=error.errno,transport_details=error.details,prior_audit_sha256=sha(snapshot),
                    prior_audit_hex=snapshot.hex(),mutation_retries_allowed=False)
        self._transport.close()
        self._event("read_recovery_old_handle_closed",path=self.path)
        new=self._reopen();self._transport=new
        self._identity(new)
        self._event("read_recovery_audit_intent",cdb=simple_cdb(0xFD88).hex())
        audit=new.exchange(simple_cdb(0xFD88),read_length=128)
        self._event("read_recovery_audit_reply",raw_hex=audit.hex(),sha256=sha(audit))
        validate_audit_record(audit,base=self.slot,build_tag=self.session.installation.build_tag,expected_mutations_enabled=True)
        require(audit==snapshot,"reopened audit changed; the failed read/job may have executed, no reissue")
        self._event("read_recovery_unchanged_audit",sha256=sha(audit),evidence="exact128-byte identity with immediately preceding validated audit")
        # Consume the one reissue before the exchange: another error cannot
        # cause recursion, a second reopen, or any repeated mutation.
        self.read_reissues+=1
        self._event("read_recovery_reissue_intent",cdb=cdb.hex(),read_length=read_length,read_only=True)
        raw=new.exchange(cdb,read_length=read_length)
        require(isinstance(raw,bytes) and len(raw)==read_length,"reissued FD7F returned a short/nonbyte response")
        self._event("read_recovery_reissue_reply",bytes=len(raw),sha256=sha(raw),
                    subsequent_installer_status_and_audit_still_required=True)
        return raw

    def exchange(self,cdb,data_out=None,read_length=0):
        require(not self.failed and not self.closed and not self.busy,"read recovery transport is failed/closed/busy")
        validate_writer_operational_request(cdb,data_out,read_length,slot=self.slot)
        opcode=int.from_bytes(cdb[:2],"big");previous_opcode,previous_reply=self.last_opcode,self.last_reply
        self.last_opcode=self.last_reply=None;self.busy=True
        try:
            try:raw=self._transport.exchange(cdb,data_out=data_out,read_length=read_length)
            except RomCommandError as error:
                if opcode!=0xFD7F or data_out is not None or error.errno!=31 or not error.submitted or self.recovery_attempts:
                    self._event("read_recovery_not_permitted",cdb=cdb.hex(),error=str(error),
                                reason="only first Win31 on FD7F can enter recovery",mutation_retry=False)
                    raise
                try:snapshot=self._validated_snapshot(previous_opcode,previous_reply)
                except Exception as cause:
                    self._event("read_recovery_not_permitted",cdb=cdb.hex(),error=str(error),reason=str(cause),mutation_retry=False)
                    raise error from cause
                raw=self._recover(cdb,read_length,snapshot,error)
            self.last_opcode,self.last_reply=opcode,raw
            return raw
        except BaseException as error:
            self.failed=True
            try:self._event("read_recovery_terminal",cdb=cdb.hex(),error_type=type(error).__name__,error=str(error),
                            further_commands_allowed=False,automatic_reset=False)
            except Exception:pass
            raise
        finally:self.busy=False

    def close(self):
        if not self.closed:
            self.closed=True;self._transport.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
