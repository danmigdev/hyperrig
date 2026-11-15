"""HYW1 v2 query recovery plus one bounded reissue of a known FD87 RAM echo.

Import is offline. No transport is opened here. The existing installer remains
responsible for status/audit checks and NOR mutations. Neither the frozen v2
implementation nor its behavior for other commands is changed.
"""
from __future__ import annotations

from tools import recover_mini_read_v2 as v2
from tools.build_mini_app_writer import crc
from tools.probe_mini_app_writer import echo_cdb, simple_cdb

require, sha = v2.require, v2.sha


class ReadOnlyStateRecoveryTransport(v2.ReadOnlyStateRecoveryTransport):
    """Reissue FD87 only after an exact staged-page witness is reconciled.

    FD87 sends frozen RAM and can set echoed=1. It neither runs a private-stack
    job nor touches NOR, counters or sequence. Therefore only record bytes
    104..107 (echoed) and 120..123 (record CRC) may differ after a lost reply.
    The total recovery budget, including inherited v2 paths, remains at most8.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.echo_reissues = self.echo_already_emitted = 0

    def summary(self):
        return {**super().summary(), "version": 3,
                "echo_reissues": self.echo_reissues,
                "echo_already_emitted": self.echo_already_emitted,
                "echo_requires_known_candidate_page": True}

    def _echo_witness(self, cdb, length, previous_opcode, previous_reply):
        witness = super()._witness(0xFD87, cdb, length, previous_opcode, previous_reply)
        session, expected = self.session, witness["expected"]
        require(not witness["mutation"] and session.preimage_verified and session.phase == "installing",
                "FD87 recovery requires a preflighted installation without unknown mutation")
        require(previous_opcode == 0xFD88 and previous_reply == session.last_record,
                "validated staged-page FD88 must immediately precede failed FD87")
        prior = self._audit_matches(previous_reply, expected, mutation=False)
        require(expected["phase"] == 4 and expected["staged"] == 1 and expected["echoed"] == 0
                and expected["raw_receive_return"] == 260,
                "FD87 recovery requires a freshly staged, not yet host-verified page")
        require(length == 256 and cdb == echo_cdb(expected["token"], expected["sequence"], expected["page"]),
                "FD87 token/staging sequence/address differs from trusted audit")
        status = self._status_matches(session.last_status_raw, 0xFC7E, expected)
        require(status == session.last_status, "preceding STAGE status was not validated by installer")
        page = session.installation.page(expected["page"])
        require(isinstance(page, bytes) and len(page) == 256
                and crc(page) == expected["page_crc32"] == expected["last_crc32"],
                "staged CRC differs from the known candidate page")
        return {**witness, "prior_audit": prior, "page": page, "status_raw": session.last_status_raw}

    def _recover_echo(self, cdb, witness, error):
        self.recovery_attempts += 1
        self._used_witnesses.add(witness["key"])
        self._event("readonly_recovery_begin", cdb=cdb.hex(), read_length=256,
                    error=str(error), win32_error=error.errno, transport_details=error.details,
                    expected_state=witness["expected"], mutation_audit=False,
                    prior_audit_hex=witness["prior_record"].hex(), witness_sha256=witness["key"],
                    candidate_page_sha256=sha(witness["page"]), mutation_retries_allowed=False)
        self._event("readonly_recovery_close_intent", path=self.path)
        self._transport.close()
        self._event("readonly_recovery_reopen_intent", path=self.path)
        new = self._reopen()
        self._transport = new
        self._identity(new)
        self._event("readonly_recovery_audit_intent", cdb=simple_cdb(0xFD88).hex())
        audit = new.exchange(simple_cdb(0xFD88), read_length=128)
        require(isinstance(audit, bytes), "fresh audit must be immutable bytes")
        self._event("readonly_recovery_audit_reply", raw_hex=audit.hex(), sha256=sha(audit))
        item = v2.validate_audit_record(audit, base=self.slot, build_tag=self.session.installation.build_tag,
                                        expected_mutations_enabled=True)
        expected = {**witness["expected"], "echoed": item["echoed"]}
        self._audit_matches(audit, expected, mutation=False)
        prior = witness["prior_record"]
        require(audit[:104] == prior[:104] and audit[108:120] == prior[108:120] and audit[124:] == prior[124:],
                "FD87 changed audit beyond echoed and record CRC; no reissue")
        require(self.session.expected == witness["expected"] and not self.session.failed
                and not self.session.mutation_completion_unknown
                and self.session.last_record == prior and self.session.last_audit == witness["prior_audit"]
                and self.session.last_status_raw == witness["status_raw"]
                and self.session.installation.page(expected["page"]) == witness["page"],
                "installer witness changed while reopening transport")
        self.echo_reissues += 1
        self.echo_already_emitted += item["echoed"]
        self._event("readonly_recovery_reissue_intent", cdb=cdb.hex(), read_length=256,
                    read_only=True, no_NOR_access=True, prior_echoed=0, fresh_echoed=item["echoed"],
                    stack_observed_bytes_unchanged=item["stack_observed_bytes"],
                    candidate_page_sha256=sha(witness["page"]),
                    evidence="exact128-byte audit except echoed0/1 and CRC; FD87 only sends unchanged frozen RAM")
        raw = new.exchange(cdb, read_length=256)
        require(isinstance(raw, bytes) and len(raw) == 256, "reissued FD87 response is short or nonbyte")
        require(raw == witness["page"] and crc(raw) == expected["page_crc32"],
                "reissued FD87 differs byte-for-byte from candidate; no WREN allowed")
        self._event("readonly_recovery_reissue_reply", bytes=256, sha256=sha(raw),
                    echo_already_emitted=bool(item["echoed"]),
                    subsequent_installer_status_and_audit_still_required=True)
        return raw

    def exchange(self, cdb, data_out=None, read_length=0):
        # Delegate every existing v2 path without changing its validation or
        # retry policy. The extra branch uses the same counters and witnesses.
        v2.validate_writer_operational_request(cdb, data_out, read_length, slot=self.slot)
        opcode = int.from_bytes(cdb[:2], "big")
        if opcode != 0xFD87:
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
                    self._event("readonly_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason="only bounded submitted Win31 on known FD87 echo", mutation_retry=False)
                    raise
                try:
                    witness = self._echo_witness(cdb, read_length, previous_opcode, previous_reply)
                except Exception as cause:
                    self._event("readonly_recovery_not_permitted", cdb=cdb.hex(), error=str(error),
                                reason=str(cause), mutation_retry=False)
                    raise error from cause
                raw = self._recover_echo(cdb, witness, error)
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
