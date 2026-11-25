"""The pi32v2 simulator of upstream/pi32v2-isa with the hardware loop that application code uses. Offline.

Upstream's model of `rep` is the one of its own hardware test, whose loop body adds 1 to r7; run on application code it
changes r7 and does not repeat the body. Here the body runs as many times as the count says and the count register is 0
afterwards, as the same hardware test found (isa/pi32v2.toml, "rep"). A count of 0 was not tried there; it runs the body no
time, which is what the application's memset needs to write no byte too many.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in ('upstream/pi32v2-isa/tools/hwtest', 'upstream/pi32v2-isa/tools/llvm', 'upstream/pi32v2-isa'):
    if str(ROOT / path) not in sys.path:
        sys.path.insert(0, str(ROOT / path))
import check as _check  # noqa: E402
import sim as _sim  # noqa: E402

RETURN, STACK_TOP, M, Memory = _sim.RETURN, _sim.STACK_TOP, _sim.M, _sim.Memory


class CPU(_sim.CPU):
    repeating = False

    def step(self):
        insn, raw, size = self.decode(self.pc)
        if insn.id not in ('rep', 'rep.i'):
            return super().step()
        if self.repeating:
            raise RuntimeError(f'{self.pc:#x}: a loop inside a loop')
        op = _check.operands(insn, raw)
        count, body = (self.R[op['r']], op['n']) if insn.id == 'rep' else (op['n'], op['b'])
        start = self.pc + size
        end = start + body
        self.steps += 1
        self.repeating = True
        try:
            for _ in range(count):
                self.pc = start
                while self.pc != end:
                    if not start <= self.pc < end:
                        raise RuntimeError(f'{start:#x}: a jump out of a loop')
                    self.step()
        finally:
            self.repeating = False
        if insn.id == 'rep':
            self.R[op['r']] = 0
        self.pc = end
        return None
