"""The simulator's hardware loop, and the facts of the cab IR check (offline)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'upstream/pi32v2-isa/tools/llvm/sim.py').is_file():
    pytest.skip('no simulator here', allow_module_level=True)
sys.path.insert(0, str(ROOT / 'tools'))
import check_mini_library as library  # noqa: E402
import mini_sim  # noqa: E402
from pi32v2isa import codec  # noqa: E402

AT, LOOP = 0x01C50000, bytes.fromhex('0403')      # rep 2 r4 {


def encoded(cpu, text):
    """The two bytes of an instruction, found by decoding."""
    for half in range(0x10000):
        raw = half.to_bytes(2, 'little')
        got = codec.decode(cpu.tab, raw + bytes(4))
        if got and got[2] == 2 and codec.format(got[0], got[1]) == text:
            return raw
    raise AssertionError(text)


@pytest.mark.parametrize('count', [0, 1, 2, 7, 600])
def test_the_body_runs_as_often_as_the_count_says(count):
    cpu = mini_sim.CPU()
    cpu.mem.write(AT, LOOP + encoded(cpu, 'r7 += 1'))
    cpu.pc, cpu.R[4], cpu.R[7] = AT, count, 5
    cpu.step()
    assert (cpu.R[7], cpu.R[4], cpu.pc) == (5 + count, 0, AT + 4)


def test_a_body_of_memory_writes_leaves_the_other_registers():
    """As in the application's memset; upstream's model wrote one word and changed r7."""
    cpu = mini_sim.CPU()
    cpu.mem.write(AT, LOOP + encoded(cpu, '[r3++=4] = r1'))
    cpu.R[1], cpu.R[3], cpu.R[4], cpu.R[7], cpu.pc = 0x11223344, 0x01C60000, 3, 0x30, AT
    cpu.step()
    assert cpu.mem.read(0x01C60000, 16) == bytes.fromhex('44332211') * 3 + bytes(4)
    assert (cpu.R[7], cpu.R[3], cpu.R[4], cpu.pc) == (0x30, 0x01C6000C, 0, AT + 4)


def test_slots_and_settings_do_not_meet():
    slots = [library.ir_range(k) for k in range(library.IR_SLOTS)]
    assert slots[0][0] == 0xEF000 and slots[7] == (0xFD000, library.SETTINGS) and library.SETTINGS == 0xFE000
    assert all(slots[k][1] == slots[k + 1][0] for k in range(7))
    assert library.IR_SAMPLES * 2 + 40 <= 2 * library.SECTOR and library.IR_LAST * 2 + 40 <= library.SECTOR
