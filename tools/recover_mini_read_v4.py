"""Bounded HYW1 state reconciliation, including provably unconsumed mutations.

Import is offline. V1..v3, the target writer and the installer stay unchanged.
FC7B/FC7D can be resubmitted once only if a fresh raw audit is byte-identical
to the immediately preceding validated audit: the target has not consumed the
command's sequence at the observation point. Any delta stops, even if a
mutation appears fully completed. No replies are synthesized.
"""
from __future__ import annotations

import json

from tools import recover_mini_read_v3 as v3
from tools import recover_mini_read_v2 as v2
from tools.install_mini_app import mutation_cdb
from tools.build_mini_app_writer import crc
from tools.probe_mini_app_writer import simple_cdb

require, sha = v2.require, v2.sha
MUTATION_OPCODES = (0xFC7B, 0xFC7D)


class AuditedCommandRecoveryTransport(v3.ReadOnlyStateRecoveryTransport):
    """V4 additionally reconciles unexecuted mutation requests.

    The frozen writer increments sequence before run_job and before WREN.
    Matching all128 preceding audit bytes is mandatory, not just matching
    counters. One recovery per CDB/state, at most8 total across all paths.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mutation_request_reissues = 0

    def summary(self):
        return {**super().summary(), "version": 4,
                "mutation_request_reissues": self.mutation_request_reissues,
                "completed_NOR_mutations_repeated": 0,
                "mutation_retries_allowed": True,
                "mutation_retry_condition": "only FC7B/FC7D with identical immediately preceding validated raw audit",
                "executed_or_ambiguous_mutation_retry": False, "synthetic_mutation_ACK": False}

    def _mutation_witness(self, opcode, cdb, length, previous_opcode, previous_reply):
        session = self.session
        require(session is not None and session.ready and not session.failed
                and session.preimage_verified and session.phase == "installing",
                "bound preflighted live installer required")
        require(session.mutation_command_submitted and session.mutation_completion_unknown,
                "submitted pending mutation required")
        require(session.last_record is not None and session.last_audit is not None
                and previous_opcode == 0xFD88 and previous_reply == session.last_record,
                "validated FD88 must immediately precede failed mutation")
        expected = session.expected.copy()
        prior = v2.validate_audit_record(session.last_record, base=self.slot,
                    build_tag=session.installation.build_tag, expected_mutations_enabled=True)
        require(prior == session.last_audit and prior["error"] == 0
                and prior["rx_guards_ok"] == prior["stack_guards_ok"] == 1,
                "previous audit differs from installer validation")
        require(prior["sequence"] < 0xFFFFFFFF and expected["sequence"] == prior["sequence"] + 1,
                "host must have consumed exactly the next operation sequence")
        previous_expected = {**expected, "sequence": prior["sequence"]}
        self._audit_matches(session.last_record, previous_expected, mutation=False)
        require(expected["phase"] == 4 and expected["staged"] == expected["echoed"] == 1
                and expected["raw_receive_return"] == 260 and expected["jedec"] == 0xEB6014,
                "validated staged and echoed candidate page required")
        require(session.pending_operation == f"sector_{expected['sector']:08x}",
                "pending installer sector differs")
        address = expected["sector"] if opcode == 0xFC7B else expected["page"]
        require(length == 16 and cdb == mutation_cdb(opcode, expected["token"], expected["sequence"], address),
                "mutation token/sequence/address differs from pending command")
        status = self._status_matches(session.last_status_raw, 0xFC7E, previous_expected)
        require(status == session.last_status, "preceding status was not validated by installer")
        page = session.installation.page(expected["page"])
        require(isinstance(page, bytes) and len(page) == 256 and crc(page) == expected["page_crc32"],
                "staged page CRC differs from known candidate")
        # Last CRC may describe erased NOR after FC7B's readback; it is not
        # necessarily the frozen page CRC before the first FC7D in a sector.
        material = json.dumps({"opcode": opcode, "cdb": cdb.hex(), "length": length,
                               "expected": expected, "prior_record": session.last_record.hex()},
                              sort_keys=True, separators=(",", ":")).encode()
        key = sha(material)
        require(key not in self._used_witnesses, "this mutation/state witness already used recovery")
        return {"key": key, "expected": expected, "previous_expected": previous_expected,
                "prior_record": session.last_record, "prior_audit": prior,
                "status_raw": session.last_status_raw, "page": page,
                "pending_operation": session.pending_operation}

    def _recover_mutation(self, opcode, cdb, witness, error):
        self.recovery_attempts += 1
        self._used_witnesses.add(witness["key"])
        self._event("unexecuted_mutation_recovery_begin", cdb=cdb.hex(), read_length=16,
                    error=str(error), win32_error=error.errno, transport_details=error.details,
                    expected_state=witness["expected"], prior_audit_hex=witness["prior_record"].hex(),
                    witness_sha256=witness["key"], candidate_page_sha256=sha(witness["page"]),
                    any_audit_change_forbids_reissue=True, synthetic_ACK=False)
        self._event("unexecuted_mutation_recovery_close_intent", path=self.path)
        self._transport.close()
        self._event("unexecuted_mutation_recovery_reopen_intent", path=self.path)
        new = self._reopen()
        self._transport = new
        self._identity(new)
        self._event("unexecuted_mutation_recovery_audit_intent", cdb=simple_cdb(0xFD88).hex())
        audit = new.exchange(simple_cdb(0xFD88), read_length=128)
        require(isinstance(audit, bytes), "fresh audit must be immutable bytes")
        self._event("unexecuted_mutation_recovery_audit_reply", raw_hex=audit.hex(), sha256=sha(audit))
        self._audit_matches(audit, witness["previous_expected"], mutation=False)
        require(audit == witness["prior_record"],
                "mutation audit changed; command may have executed, no reissue")
        session = self.session
        require(session.expected == witness["expected"] and not session.failed
                and session.mutation_command_submitted and session.mutation_completion_unknown
                and session.last_record == witness["prior_record"] and session.last_audit == witness["prior_audit"]
                and session.last_status_raw == witness["status_raw"]
                and session.pending_operation == witness["pending_operation"] and session.phase == "installing"
                and session.installation.page(witness["expected"]["page"]) == witness["page"],
                "installer witness changed while reopening transport")
        self.mutation_request_reissues += 1
        self._event("unexecuted_mutation_recovery_reissue_intent", cdb=cdb.hex(), read_length=16,
                    raw_audit_identical=True, sequence_unconsumed=True, synthetic_ACK=False,
                    sequence_before=witness["prior_audit"]["sequence"],
                    requested_sequence=witness["expected"]["sequence"],
                    candidate_page_sha256=sha(witness["page"]),
                    evidence="writer consumes sequence before run_job/WREN; all128 preceding audit bytes unchanged")
        raw = new.exchange(cdb, read_length=16)
        completed = {**witness["expected"], "phase": 4 if opcode == 0xFC7B else 3,
                     "last_crc32": crc(b"\xff" * 4096) if opcode == 0xFC7B else crc(witness["page"])}
        self._status_matches(raw, opcode, completed)
        self._event("unexecuted_mutation_recovery_reissue_reply", raw_hex=raw.hex(), sha256=sha(raw),
                    synthetic_ACK=False, subsequent_installer_status_and_mutation_audit_required=True)
        return raw

    def exchange(self, cdb, data_out=None, read_length=0):
        v2.validate_writer_operational_request(cdb, data_out, read_length, slot=self.slot)
        opcode = int.from_bytes(cdb[:2], "big")
        if opcode not in MUTATION_OPCODES:
            return super().exchange(cdb, data_out=data_out, read_length=read_length)
        require(not self.failed and not self.closed and not self.busy, "recovery transport is failed/closed/busy")
        previous_opcode, previous_reply = self.last_opcode, self.last_reply
        self.last_opcode = self.last_reply = None
        self.exchange_index += 1
        self.busy = True
        try:
            try:
                raw = self._transport.exchange(cdb, data_out=data_out, read_length=read_length)
            except v2.RomCommandError as error:
                if (data_out is not None or error.errno != 31 or not error.submitted
                        or self.recovery_attempts >= self.max_recoveries):
                    self._event("unexecuted_mutation_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason="only bounded submitted Win31 on FC7B/FC7D")
                    raise
                try:
                    witness = self._mutation_witness(opcode, cdb, read_length, previous_opcode, previous_reply)
                except Exception as cause:
                    self._event("unexecuted_mutation_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason=str(cause))
                    raise error from cause
                raw = self._recover_mutation(opcode, cdb, witness, error)
            self.last_opcode, self.last_reply = opcode, raw
            return raw
        except BaseException as error:
            self.failed = True
            try:
                self._event("unexecuted_mutation_recovery_terminal", cdb=cdb.hex(), error_type=type(error).__name__,
                            error=str(error), further_commands_allowed=False, automatic_reset=False)
            except Exception:
                pass
            raise
        finally:
            self.busy = False
