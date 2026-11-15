"""V5 command witnesses with a finite writer-only recovery budget up to32.

No exchange, witness, reissue or cleanup implementation is overridden. This
revision only permits more distinct independently validated recoveries across
one writer session. The separate NOR-reader recovery remains bounded by8.
"""
from __future__ import annotations

from tools.recover_mini_read_v5 import FinishCommandRecoveryTransport
from tools.recover_mini_read_v2 import require


class BoundedCommandRecoveryTransport(FinishCommandRecoveryTransport):
    def __init__(self, transport, *, log, reopen_factory, max_recoveries=32):
        require(type(max_recoveries) is int and 1 <= max_recoveries <= 32,
                "writer recovery budget must be an integer1..32")
        # Run every frozen parent constructor with its original accepted bound.
        # All inherited recovery paths consult the instance bound below.
        super().__init__(transport, log=log, reopen_factory=reopen_factory,
                         max_recoveries=min(max_recoveries, 8))
        self.max_recoveries = max_recoveries

    def summary(self):
        return {**super().summary(), "version": 6,
                "max_recoveries": self.max_recoveries,
                "recovery_limit_scope": "one writer session; shared across all inherited v5 command families",
                "maximum_supported_writer_recoveries": 32,
                "command_witness_policy_version": 5,
                "command_witness_policy_unchanged_from_v5": True,
                "separate_NOR_reader_budget_unchanged": 8}
