"""Bounded recovery of HYW1 read/query failures, without repeated mutations.

Import is offline. A caller must explicitly supply an identified transport,
durable logger and same-backend reopen factory, then bind the real installer.
The frozen writer, installer and v1 recovery implementation remain unchanged.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import struct
import time

from tools.build_mini_app_writer import validate_audit_record
from tools.install_mini_app import MiniAppInstallerSession, validate_writer_operational_request
from tools.probe_mini_app_writer import simple_cdb
from tools.probe_mini_recovery import RomCommandError


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ReadOnlyStateRecoveryTransport:
    """Reconcile FC7E/FD88 with expected state; FD7F needs unchanged audit.

    At most eight recoveries are allowed across one explicitly bound session.
    A failed recovery exchange is terminal: there is no nested recovery. The
    same CDB and expected-state witness can be recovered only once. FD88's
    fresh, validated audit is returned directly to the installer's normal
    validator; the wrapper never changes installer state or invents replies.
    """

    def __init__(self, transport, *, log, reopen_factory, max_recoveries=8):
        require(callable(log) and callable(reopen_factory), "durable logger and explicit reopen factory required")
        require(type(max_recoveries) is int and 1 <= max_recoveries <= 8, "recovery budget must be 1..8")
        require(getattr(transport, "profile", None) == "app-writer-operational", "operational HYW1 profile required")
        self._transport = transport
        self._transport_type = type(transport)
        self.log, self._reopen = log, reopen_factory
        self.slot, self.profile = transport.slot, transport.profile
        self.path, self.disk, self.inquiry = transport.disk["path"], transport.disk, transport.inquiry
        self.max_recoveries = max_recoveries
        self.session = None
        self.failed = self.closed = self.busy = False
        self.recovery_attempts = self.read_reissues = self.query_reissues = self.audit_reconciliations = 0
        self.exchange_index = 0
        self.last_opcode = self.last_reply = None
        self._used_witnesses = set()

    def bind_session(self, session):
        require(self.session is None and isinstance(session, MiniAppInstallerSession)
                and session.transport is self and session.slot == self.slot,
                "bind exactly this installer/session/slot once")
        self.session = session

    def summary(self):
        return {"version": 2, "max_recoveries": self.max_recoveries,
                "recovery_attempts": self.recovery_attempts, "read_reissues": self.read_reissues,
                "query_reissues": self.query_reissues, "audit_reconciliations": self.audit_reconciliations,
                "failed": self.failed, "closed": self.closed,
                "mutation_retries_allowed": False, "automatic_reset": False}

    def _event(self, event, **details):
        self.log({"event": event, "utc": datetime.now(timezone.utc).isoformat(),
                  "perf_counter_ns": time.perf_counter_ns(), "slot": self.slot,
                  "exchange_index": self.exchange_index, "recovery_attempts": self.recovery_attempts,
                  "read_reissues": self.read_reissues, "query_reissues": self.query_reissues,
                  "audit_reconciliations": self.audit_reconciliations, **details})

    @staticmethod
    def _status_matches(raw, opcode, expected):
        require(isinstance(raw, bytes) and len(raw) == 16 and raw[:2] == opcode.to_bytes(2, "big"),
                "status framing differs during recovery")
        fields = {"error": raw[2], "phase": raw[3], "token": int.from_bytes(raw[4:8], "big"),
                  "sequence": int.from_bytes(raw[8:12], "big"), "last_crc32": int.from_bytes(raw[12:], "big")}
        require(fields["error"] == 0 and all(fields[k] == expected[k]
                for k in ("phase", "token", "sequence", "last_crc32")), "status differs from expected state")
        return fields

    def _audit_matches(self, raw, expected, *, mutation):
        require(isinstance(raw, bytes), "audit must be immutable bytes")
        item = validate_audit_record(raw, base=self.slot, build_tag=self.session.installation.build_tag,
                                     expected_mutations_enabled=True)
        require(item["error"] == 0 and item["rx_guards_ok"] == item["stack_guards_ok"] == 1,
                "fresh audit reports error or guard damage")
        for name, value in expected.items():
            if name == "status_polls" and mutation:
                require(1 <= item[name] - value <= 65536, "mutation WIP polling delta differs")
            else:
                require(item[name] == value, "fresh audit differs from expected state: " + name)
        require(not item["sr1"] & 0x7F and not item["sr2"] & 0x40, "NOR busy/write-enabled/protected in fresh audit")
        require(item["stack_observed_bytes"] > 0, "initialized private stack observation missing")
        return item

    def _witness(self, opcode, cdb, length, previous_opcode, previous_reply):
        session = self.session
        require(session is not None and session.ready and not session.failed,
                "bound live nonfailed installer required")
        require(session.last_record is not None and session.last_audit is not None,
                "previous installer audit required")
        expected = session.expected.copy()
        require(expected["jedec"] == 0xEB6014 and expected["phase"] >= 1,
                "recovery requires initialized verified MINI NOR")
        prior = validate_audit_record(session.last_record, base=self.slot,
                    build_tag=session.installation.build_tag, expected_mutations_enabled=True)
        require(prior == session.last_audit and prior["error"] == 0
                and prior["rx_guards_ok"] == prior["stack_guards_ok"] == 1,
                "previous audit differs from installer validation")
        mutation = bool(session.mutation_completion_unknown)
        if mutation:
            require(opcode == 0xFD88 and previous_opcode in (0xFC7B, 0xFC7D),
                    "only the audit immediately after an acknowledged mutation may reconcile polling")
            require(previous_reply == session.last_status_raw,
                    "preceding mutation reply was not validated by installer")
            status = self._status_matches(previous_reply, previous_opcode, expected)
            require(status == session.last_status, "installer mutation status differs")
        if opcode == 0xFD7F:
            require(not mutation and previous_opcode == 0xFD88 and previous_reply == session.last_record,
                    "FD88 must immediately precede failed FD7F")
            self._audit_matches(previous_reply, expected, mutation=False)
        material = json.dumps({"cdb": cdb.hex(), "length": length, "expected": expected,
                               "mutation_audit": mutation}, sort_keys=True, separators=(",", ":")).encode()
        key = sha(material)
        require(key not in self._used_witnesses, "this command and expected-state witness already used recovery")
        return {"expected": expected, "mutation": mutation, "prior_record": session.last_record, "key": key}

    def _identity(self, new):
        require(type(new) is self._transport_type, "reopened transport backend/class differs")
        require(new.slot == self.slot and new.profile == self.profile
                and new.disk["path"].casefold() == self.path.casefold(), "reopened path/slot/profile differs")
        require(new.inquiry.get("vendor") == "WL82" and new.inquiry.get("product") == "UBOOT1.00",
                "reopened handle has wrong ROM inquiry")
        self._event("readonly_recovery_identity_intent", cdb=simple_cdb(0xFC78).hex())
        raw = new.exchange(simple_cdb(0xFC78), read_length=16)
        self._event("readonly_recovery_identity_reply", raw_hex=raw.hex())
        require(raw == b"\xfc\x78HYW1\1\1" + struct.pack(">II", self.slot, 32768),
                "reopened HYW1 identity/gate/slot differs")

    def _recover(self, opcode, cdb, length, witness, error):
        self.recovery_attempts += 1
        self._used_witnesses.add(witness["key"])
        self._event("readonly_recovery_begin", cdb=cdb.hex(), read_length=length,
                    error=str(error), win32_error=error.errno, transport_details=error.details,
                    expected_state=witness["expected"], mutation_audit=witness["mutation"],
                    prior_audit_hex=witness["prior_record"].hex(), witness_sha256=witness["key"],
                    mutation_retries_allowed=False)
        self._event("readonly_recovery_close_intent", path=self.path)
        self._transport.close()
        self._event("readonly_recovery_reopen_intent", path=self.path)
        new = self._reopen()
        self._transport = new
        self._identity(new)
        self._event("readonly_recovery_audit_intent", cdb=simple_cdb(0xFD88).hex())
        audit = new.exchange(simple_cdb(0xFD88), read_length=128)
        self._event("readonly_recovery_audit_reply", raw_hex=audit.hex(), sha256=sha(audit))
        item = self._audit_matches(audit, witness["expected"], mutation=witness["mutation"])
        require(self.session.expected == witness["expected"] and not self.session.failed,
                "installer state changed while reopening transport")
        if opcode == 0xFD7F:
            require(audit == witness["prior_record"],
                    "failed FD7F changed audit; execution cannot be excluded, no reissue")
            self.read_reissues += 1
            evidence = "exact128-byte identity with preceding validated FD88: FD7F did not increment read counter"
        elif opcode == 0xFD88:
            self.audit_reconciliations += 1
            self._event("readonly_recovery_return_fresh_audit", sha256=sha(audit),
                        mutation_poll_delta=item["status_polls"] - witness["expected"]["status_polls"],
                        subsequent_installer_validation_required=True)
            return audit
        else:
            self.query_reissues += 1
            evidence = "pure FC7E query; live audit equals all expected fields after last acknowledged command"
        self._event("readonly_recovery_reissue_intent", cdb=cdb.hex(), read_length=length,
                    read_only=True, evidence=evidence)
        raw = new.exchange(cdb, read_length=length)
        require(isinstance(raw, bytes) and len(raw) == length, "reissued read/query response is short or nonbyte")
        if opcode == 0xFC7E:
            self._status_matches(raw, opcode, witness["expected"])
        self._event("readonly_recovery_reissue_reply", bytes=len(raw), sha256=sha(raw),
                    subsequent_installer_status_and_audit_still_required=True)
        return raw

    def exchange(self, cdb, data_out=None, read_length=0):
        require(not self.failed and not self.closed and not self.busy, "recovery transport is failed/closed/busy")
        validate_writer_operational_request(cdb, data_out, read_length, slot=self.slot)
        opcode = int.from_bytes(cdb[:2], "big")
        previous_opcode, previous_reply = self.last_opcode, self.last_reply
        self.last_opcode = self.last_reply = None
        self.exchange_index += 1
        self.busy = True
        try:
            try:
                raw = self._transport.exchange(cdb, data_out=data_out, read_length=read_length)
            except RomCommandError as error:
                if (opcode not in (0xFD7F, 0xFC7E, 0xFD88) or data_out is not None
                        or error.errno != 31 or not error.submitted or self.recovery_attempts >= self.max_recoveries):
                    self._event("readonly_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason="only bounded submitted Win31 on FD7F/FC7E/FD88", mutation_retry=False)
                    raise
                try:
                    witness = self._witness(opcode, cdb, read_length, previous_opcode, previous_reply)
                except Exception as cause:
                    self._event("readonly_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason=str(cause), mutation_retry=False)
                    raise error from cause
                raw = self._recover(opcode, cdb, read_length, witness, error)
            self.last_opcode, self.last_reply = opcode, raw
            return raw
        except BaseException as error:
            self.failed = True
            try:
                self._event("readonly_recovery_terminal", cdb=cdb.hex(), error_type=type(error).__name__,
                            error=str(error), further_commands_allowed=False, automatic_reset=False)
            except Exception:
                pass
            raise
        finally:
            self.busy = False

    def close(self):
        if not self.closed:
            self.closed = True
            self._transport.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
