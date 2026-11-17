"""Focused original-instruction witnesses for newly recovered sample engines."""
from pathlib import Path
import hashlib
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from effect_sample_processing_machine import (EffectSampleProcessingProgram, REGIONS,
    DIRECT_SITES, MAPPED, ARENA, SAMPLES, MASK32)
from verify_effect_sample_processing import baseline, setword, initialize, EFFECTS, check_derivative


def word(memory, address, width=4):
    for (base, n), data in zip(MAPPED, memory):
        if base <= address <= address+width <= base+n:
            return int.from_bytes(data[address-base:address-base+width], 'little')
    raise AssertionError('test address not mapped')


class OriginalSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.program = EffectSampleProcessingProgram()

    def run_machine(self, name, args, memory=None):
        return self.program.execute(baseline() if memory is None else memory, name, args)

    def test_whole_registry_and_exact_direct_sites(self):
        self.assertEqual(1324, len(self.program.sample_code))
        self.assertEqual(4082, sum(b-a for a, b in REGIONS.values()))
        self.assertEqual(10, len(DIRECT_SITES))
        self.assertEqual(9, check_derivative()['textual_replacements'])

    def test_two_weight_blocks_are_exact_reversed_original_words(self):
        raw = self.program.data['correlation_weights']
        self.assertEqual('1e8b8aa3482ac62ae54fcaf6b4dd11b104b34129c7308ad7cae9114f4e9c7cd8', hashlib.sha256(raw).hexdigest())
        values = [int.from_bytes(raw[i:i+4], 'little') for i in range(0, len(raw), 4)]
        self.assertEqual(40, len(values)); self.assertEqual(values[:20], list(reversed(values[20:])))

    def test_zero_count_cascade_still_captures_tail_and_publishes_history(self):
        memory = baseline(); setword(memory, SAMPLES, 0x2468ace0); setword(memory, ARENA, 0x13579bdf)
        result = self.run_machine('cascade', (SAMPLES+4, 0, ARENA+256, 5, ARENA, ARENA+512, 0, 0, 0), memory)
        self.assertEqual(0x2468ace0, word(result['memory'], ARENA))
        self.assertEqual(0x13579bdf, word(result['memory'], ARENA+4))

    def test_q28_coefficients_stay_cached_after_output_overwrites_them(self):
        memory = baseline()
        for off in range(0, 32, 4): setword(memory, SAMPLES+off, 0)
        setword(memory, SAMPLES, 1 << 27); setword(memory, SAMPLES+20, 1 << 26)
        for off in range(0, 16, 4): setword(memory, ARENA+off, 0)
        result = self.run_machine('cascade', (SAMPLES, 8, SAMPLES, 5, ARENA, ARENA+256, 1, 1, 0), memory)
        self.assertEqual(1 << 26, word(result['memory'], SAMPLES))
        self.assertEqual(1 << 25, word(result['memory'], SAMPLES+20))

    def test_q28_history_is_published_after_future_input_reads(self):
        memory = baseline()
        for i, value in enumerate((1 << 28, 0, 0, 0, 0)): setword(memory, ARENA+4*i, value)
        inputs = (11, 22, 33, 44, 55, 66, 77, 88)
        for i, value in enumerate(inputs): setword(memory, SAMPLES+4*i, value)
        result = self.run_machine('cascade', (SAMPLES, 8, ARENA, 5, SAMPLES+8, ARENA+256, 1, 1, 0), memory)
        self.assertEqual(77, word(result['memory'], SAMPLES+24))
        self.assertEqual(88, word(result['memory'], SAMPLES+28))
        self.assertEqual((88, 77, 88, 77), tuple(word(result['memory'], SAMPLES+8+4*i) for i in range(4)))

    def test_mixer_zero_count_does_not_dereference_sources(self):
        memory = baseline()
        result = self.run_machine('mixer', (0xdead0000, 0xbad00000, 0, 0, 0, 0, 0, 0), memory)
        self.assertEqual(tuple(map(bytes, memory)), result['memory'])

    def test_width_zero_preserves_original_output_store_order(self):
        machine = self.program.machine(baseline(), 'width', (0, 1, ARENA, ARENA+4)); writes = []
        old_write = machine.write
        def write(address, value, size):
            if address in (ARENA, ARENA+4): writes.append((address, value, size))
            old_write(address, value, size)
        machine.write = write
        while machine.step(): pass
        self.assertEqual([(ARENA+4, 0, 4), (ARENA, 0, 4)], writes)

    def test_hex_subtraction_preserves_carry_for_wide_float_normalization(self):
        machine = self.program.machine(baseline(), 'transition', (EFFECTS,))
        machine.pc = 0x01c0b6c2; machine.regs.update(r12=0x80000000, r13=0, r3=0)
        machine.carry = 0
        self.assertTrue(machine.step()); self.assertEqual(1, machine.carry)
        self.assertTrue(machine.step()); self.assertEqual(1, machine.carry)
        self.assertTrue(machine.step()); self.assertEqual(2, machine.value('r0')&2)

    def test_raw_updater_high_index_reads_exact_adjacent_rom_and_wraps_byte(self):
        memory = baseline(); setword(memory, EFFECTS+84, ARENA+8192)
        setword(memory, EFFECTS+407, 255, 1); setword(memory, EFFECTS+396, 17)
        result = self.run_machine('update', (EFFECTS,), memory)
        self.assertEqual(0, word(result['memory'], EFFECTS+407, 1))
        self.assertEqual({(0x0203b7e0+255*80+4*i, 4) for i in range(20)}, result['rom_reads'])

    def test_update_parallel_packet_keeps_twenty_samples_and_raw_mode(self):
        memory = baseline(); setword(memory, EFFECTS+84, ARENA+8192)
        setword(memory, EFFECTS+407, 1, 1); setword(memory, EFFECTS+409, 255, 1)
        machine = self.program.machine(memory, 'update', (EFFECTS,))
        for _ in range(200):
            if machine.pc == 0x01c0be30: break
            self.assertTrue(machine.step())
        else: self.fail('original updater did not reach its correlation call')
        descriptor = machine.value('r0')
        self.assertEqual(20, machine.read(descriptor+16, 4))
        self.assertEqual(255, machine.read(descriptor+20, 4))

    def test_indirect_clock_collision_does_not_enter_loaded_sample_code(self):
        events = []
        def boundary(target, args, _memory): events.append((target, args)); return 123
        machine = self.program.machine(baseline(), 'stage', (0, SAMPLES, 128), boundary)
        machine.pc = 0x01c10824; machine.set('r0', REGIONS['cascade'][0])
        self.assertTrue(machine.single_step())
        self.assertEqual([(REGIONS['cascade'][0], ())], events)
        self.assertEqual(0x01c10826, machine.pc); self.assertEqual(123, machine.value('r0'))
        self.assertEqual([], machine.real_calls)

    def test_odd_correlation_walk_does_not_invent_an_early_return(self):
        memory = baseline()
        for i, value in enumerate((ARENA+8192, ARENA+4096, 0, 1, 3, 0)): setword(memory, ARENA+4*i, value)
        machine = self.program.machine(memory, 'correlation', (ARENA,)); machine.writes = []
        for _ in range(600): self.assertTrue(machine.step())
        self.assertFalse(any(ARENA+24 <= address < ARENA+56 for address, _, _ in machine.writes))
        self.assertNotEqual(0, machine.value('sp'))

    def test_zero_block_ring_walk_performs_samples_before_budget_observation(self):
        memory = baseline()
        for i, value in enumerate((SAMPLES, ARENA+8192, 0, 0, 123, 1 << 20, 1 << 22, 65536,
            65536, 65536, 0, 0, 0, 0, 0, 1 << 30, 65536)):
            setword(memory, ARENA+4*i, value)
        machine = self.program.machine(memory, 'ring', (ARENA,)); machine.writes = []
        for _ in range(600): self.assertTrue(machine.step())
        self.assertTrue(any(SAMPLES <= address < SAMPLES+128 for address, _, _ in machine.writes))
        self.assertNotEqual(tuple(map(bytes, memory)), machine.snapshot())

    def test_actual_type25_builder_has_no_scripted_numerical_service(self):
        memory = baseline(); initialize(memory, EFFECTS, 25)
        result = self.program.prepare(memory, EFFECTS)
        self.assertEqual([], result['calls'])
        self.assertIn(0x0202b87e, result['internal_calls'])
        self.assertGreater(word(result['memory'], EFFECTS+316), 0)

    def test_zero_candidate_nonfinite_conversion_exits_at_original_phase_gate(self):
        for period in (0, 1, MASK32):
            memory = baseline()
            for i, value in enumerate((0, 1 << 30, 0, 1 << 30)):
                setword(memory, EFFECTS+364+8*i, value, 8)
            for off, value in ((308, period), (328, 0), (332, 0), (292, 1), (300, 0), (296, 0x13579bdf)):
                setword(memory, EFFECTS+off, value)
            result = self.run_machine('transition', (EFFECTS,), memory)
            self.assertIn(0x01c0b9d2, result['visited']); self.assertIn(0x01c0b9da, result['visited'])
            self.assertNotIn(0x01c0b9f4, result['visited'])
            self.assertEqual(0x13579bdf, word(result['memory'], EFFECTS+296))


if __name__ == '__main__': unittest.main()
