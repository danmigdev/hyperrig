"""One FC80 FINISH reissue only after exact proof of unconsumed sequence.

Import is offline. V4, the installer, and the target writer remain unchanged.
FINISH reads the completed sector and commits its RAM state; it does not issue
WREN/erase/program. An already consumed FINISH is never replayed, including
one that completed successfully. The returned ACK must come from the target.
"""
from __future__ import annotations

import json

from tools import recover_mini_read_v4 as v4
from tools import recover_mini_read_v2 as v2
from tools.install_mini_app import mutation_cdb
from tools.build_mini_app_writer import crc
from tools.build_mini_app_writer_operational import page_order
from tools.probe_mini_app_writer import simple_cdb

require, sha = v2.require, v2.sha
FINISH = 0xFC80


class FinishCommandRecoveryTransport(v4.AuditedCommandRecoveryTransport):
    """Add FC80 to v4 using the same shared maximum of eight recoveries."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.finish_request_reissues = 0

    def summary(self):
        return {**super().summary(), "version": 5,
                "finish_request_reissues": self.finish_request_reissues,
                "finish_retry_condition": "only FC80 with identical immediately preceding validated raw audit",
                "completed_FINISH_requests_repeated": 0,
                "executed_or_ambiguous_FINISH_retry": False,
                "synthetic_FINISH_ACK": False}

    def _finish_witness(self, cdb, length, previous_opcode, previous_reply):
        session = self.session
        require(session is not None and session.ready and not session.failed
                and session.preimage_verified and session.phase == "installing",
                "bound preflighted live installer required")
        require(session.mutation_command_submitted and not session.mutation_completion_unknown,
                "all preceding NOR mutations must already be verified")
        require(session.last_record is not None and session.last_audit is not None
                and previous_opcode == 0xFD88 and previous_reply == session.last_record,
                "validated FD88 must immediately precede failed FINISH")
        expected = session.expected.copy()
        prior = v2.validate_audit_record(session.last_record, base=self.slot,
                    build_tag=session.installation.build_tag, expected_mutations_enabled=True)
        require(prior == session.last_audit and prior["error"] == 0
                and prior["rx_guards_ok"] == prior["stack_guards_ok"] == 1,
                "previous audit differs from installer validation")
        require(prior["sequence"] == 34 and expected["sequence"] == 35,
                "FINISH must be the next sequence after sixteen verified pages")
        previous_expected = {**expected, "sequence": prior["sequence"]}
        self._audit_matches(session.last_record, previous_expected, mutation=False)
        require(expected["phase"] == 3 and expected["page_bitmap"] == 0xFFFF
                and expected["staged"] == expected["echoed"] == 0
                and expected["raw_receive_return"] == 260 and expected["jedec"] == 0xEB6014,
                "FINISH requires all sixteen programmed pages and no pending stage")
        sector = expected["sector"]
        require(session.pending_operation == f"sector_{sector:08x}", "pending FINISH sector differs")
        plan = session.installation
        index = len(session.verified_sectors)
        require(tuple(session.verified_sectors) == plan.sector_order[:index]
                and index < len(plan.sector_order) and plan.sector_order[index] == sector,
                "FINISH sector is not the current planned unverified sector")
        require(length == 16 and cdb == mutation_cdb(FINISH, expected["token"], expected["sequence"], sector),
                "FINISH token/sequence/address differs from pending command")
        status = self._status_matches(session.last_status_raw, 0xFC7E, previous_expected)
        require(status == session.last_status, "last page readback status was not validated")
        require(expected["page"] == page_order(sector)[-1], "FINISH does not follow the last planned page")
        page, target, old = plan.page(expected["page"]), plan.new_sector(sector), plan.old_sector(sector)
        require(isinstance(page, bytes) and len(page) == 256
                and crc(page) == expected["page_crc32"] == expected["last_crc32"]
                and session.last_page_readback == page and session.last_echo == page,
                "last candidate page lacks matching echo and verified readback")
        require(isinstance(target, bytes) and len(target) == 4096 and crc(target) == expected["target_crc32"]
                and isinstance(old, bytes) and len(old) == 4096 and crc(old) == expected["preimage_crc32"],
                "FINISH sector CRC differs from immutable installation plan")
        material = json.dumps({"opcode": FINISH, "cdb": cdb.hex(), "length": length,
                               "expected": expected, "prior_record": session.last_record.hex()},
                              sort_keys=True, separators=(",", ":")).encode()
        key = sha(material)
        require(key not in self._used_witnesses, "this FINISH/state witness already used recovery")
        return {"key": key, "expected": expected, "previous_expected": previous_expected,
                "prior_record": session.last_record, "prior_audit": prior,
                "status_raw": session.last_status_raw, "status": status, "page": page,
                "target": target, "old": old, "plan": plan,
                "verified_sectors": tuple(session.verified_sectors), "pending_operation": session.pending_operation}

    def _recover_finish(self, cdb, witness, error):
        self.recovery_attempts += 1
        self._used_witnesses.add(witness["key"])
        self._event("unexecuted_finish_recovery_begin", cdb=cdb.hex(), read_length=16,
                    error=str(error), win32_error=error.errno, transport_details=error.details,
                    expected_state=witness["expected"], prior_audit_hex=witness["prior_record"].hex(),
                    witness_sha256=witness["key"], candidate_sector_sha256=sha(witness["target"]),
                    candidate_last_page_sha256=sha(witness["page"]),
                    any_audit_change_forbids_reissue=True, synthetic_ACK=False, NOR_mutation=False)
        self._event("unexecuted_finish_recovery_close_intent", path=self.path)
        self._transport.close()
        self._event("unexecuted_finish_recovery_reopen_intent", path=self.path)
        new = self._reopen()
        self._transport = new
        self._identity(new)
        self._event("unexecuted_finish_recovery_audit_intent", cdb=simple_cdb(0xFD88).hex())
        audit = new.exchange(simple_cdb(0xFD88), read_length=128)
        require(isinstance(audit, bytes), "fresh audit must be immutable bytes")
        self._event("unexecuted_finish_recovery_audit_reply", raw_hex=audit.hex(), sha256=sha(audit))
        self._audit_matches(audit, witness["previous_expected"], mutation=False)
        require(audit == witness["prior_record"], "FINISH audit changed; command may have executed, no reissue")
        session = self.session
        require(session.expected == witness["expected"] and not session.failed and session.ready
                and session.preimage_verified and session.mutation_command_submitted
                and not session.mutation_completion_unknown and session.phase == "installing"
                and session.last_record == witness["prior_record"] and session.last_audit == witness["prior_audit"]
                and session.last_status_raw == witness["status_raw"] and session.last_status == witness["status"]
                and session.last_page_readback == session.last_echo == witness["page"]
                and session.pending_operation == witness["pending_operation"]
                and tuple(session.verified_sectors) == witness["verified_sectors"]
                and session.installation == witness["plan"],
                "installer FINISH witness changed while reopening transport")
        self.finish_request_reissues += 1
        self._event("unexecuted_finish_recovery_reissue_intent", cdb=cdb.hex(), read_length=16,
                    raw_audit_identical=True, sequence_unconsumed=True, synthetic_ACK=False,
                    sequence_before=witness["prior_audit"]["sequence"], requested_sequence=35,
                    candidate_sector_sha256=sha(witness["target"]),
                    no_WREN_erase_program=True,
                    evidence="writer consumes FINISH sequence before run_job/status/sector reads; all128 audit bytes unchanged")
        raw = new.exchange(cdb, read_length=16)
        completed = {**witness["expected"], "phase": 5, "token": 0, "last_crc32": crc(witness["target"])}
        self._status_matches(raw, FINISH, completed)
        self._event("unexecuted_finish_recovery_reissue_reply", raw_hex=raw.hex(), sha256=sha(raw),
                    synthetic_ACK=False, subsequent_installer_status_audit_and_sector_readback_required=True)
        return raw

    def exchange(self, cdb, data_out=None, read_length=0):
        v2.validate_writer_operational_request(cdb, data_out, read_length, slot=self.slot)
        opcode = int.from_bytes(cdb[:2], "big")
        if opcode != FINISH:
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
                    self._event("unexecuted_finish_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason="only bounded submitted Win31 on FC80")
                    raise
                try:
                    witness = self._finish_witness(cdb, read_length, previous_opcode, previous_reply)
                except Exception as cause:
                    self._event("unexecuted_finish_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason=str(cause))
                    raise error from cause
                raw = self._recover_finish(cdb, witness, error)
            self.last_opcode, self.last_reply = opcode, raw
            return raw
        except BaseException as error:
            self.failed = True
            try:
                self._event("unexecuted_finish_recovery_terminal", cdb=cdb.hex(), error_type=type(error).__name__,
                            error=str(error), further_commands_allowed=False, automatic_reset=False)
            except Exception:
                pass
            raise
        finally:
            self.busy = False
