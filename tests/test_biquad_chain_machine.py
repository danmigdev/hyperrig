"""Independent expectations for section ownership, chain order and clock behavior."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())
sys.path.insert(0, str(ROOT / "tools"))


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class BiquadChainInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from biquad_chain_machine import BiquadChainProgram
        from verify_biquad_chain import baseline, Clock
        cls.program, cls.initial, cls.clock = BiquadChainProgram(), staticmethod(baseline), Clock

    def run_original(self, memory=None, samples=(1, -2, 3), *, operation="process", section=0,
                     script=((100, ()), (500, ()))):
        return self.program.execute(memory or self.initial(), list(samples), operation, section, self.clock(script).call)

    def enabled(self, clock=True):
        memory = self.initial()
        memory[1][40] = 1
        struct.pack_into("<I", memory[2], 0, int(clock))
        return memory

    def test_update_copies_only_coefficients_and_flags(self):
        memory = self.initial()
        memory[0][:] = bytes(range(220))
        memory[1][:] = bytes([0xA5] * 220)
        memory[5][:] = bytes([255] * 5)
        result = self.run_original(memory, operation="update", section=3)
        expected = bytearray(memory[1])
        expected[132:152] = memory[0][132:152]
        expected[172:174] = memory[0][172:174]
        self.assertEqual(result["memory"][1], expected)
        self.assertEqual(result["memory"][5], b"\xff\xff\xff\0\xff")
        self.assertEqual(result["memory"][0], memory[0])
        self.assertEqual(result["samples"], [1, -2, 3])

    def test_direct_update_does_not_require_pending(self):
        memory = self.initial()
        result = self.run_original(memory, operation="update", section=0)
        self.assertEqual(result["memory"][1][:20], memory[0][:20])
        self.assertEqual(result["memory"][1][20:40], memory[1][20:40])

    def test_all_disabled_preserves_activity_and_counters(self):
        memory = self.initial()
        struct.pack_into("<I", memory[2], 0, 1)
        result = self.run_original(memory)
        self.assertEqual(result["memory"], tuple(bytes(v) for v in memory))
        self.assertEqual(result["calls"], [])
        self.assertEqual(result["kernel_calls"], [])

    def test_pending_enable_retains_live_history(self):
        memory = self.initial()
        struct.pack_into("<5i", memory[0], 0, 0, 1 << 28, 0, 0, 0)
        struct.pack_into("<i", memory[1], 20, 123)
        memory[0][40] = memory[5][0] = 1
        result = self.run_original(memory, samples=[7])
        self.assertEqual(result["samples"], [123])
        self.assertEqual(result["memory"][5][0], 0)

    def test_pending_disable_skips_audio_and_clock(self):
        memory = self.enabled()
        memory[5][0] = 1
        result = self.run_original(memory)
        self.assertEqual(result["samples"], [1, -2, 3])
        self.assertEqual(result["calls"], [])
        self.assertEqual(result["memory"][6], memory[6])
        self.assertEqual(result["memory"][1][20:40], memory[1][20:40])

    def test_sections_run_in_order_with_original_saturation(self):
        memory = self.initial()
        struct.pack_into("<i", memory[1], 0, 1 << 29)
        struct.pack_into("<i", memory[1], 44, 1 << 27)
        memory[1][40] = memory[1][84] = 1
        result = self.run_original(memory, samples=[2147483647])
        self.assertEqual(result["samples"], [1073741824])
        self.assertEqual(result["kernel_calls"], [("rounded", 0, 1), ("rounded", 1, 1)])

    def test_nonboolean_flags_select_residue_kernel(self):
        memory = self.initial()
        memory[1][40:42] = b"\xff\xff"
        struct.pack_into("<i", memory[1], 0, 1 << 27)
        struct.pack_into("<I", memory[1], 36, 0)
        result = self.run_original(memory, samples=[1, 1, 1, 1])
        self.assertEqual(result["samples"], [0, 1, 0, 1])
        self.assertEqual(result["kernel_calls"], [("residual", 0, 4)])

    def test_zero_frames_still_apply_updates_and_time(self):
        memory = self.enabled()
        result = self.run_original(memory, samples=[])
        self.assertEqual(len(result["calls"]), 2)
        self.assertEqual(result["kernel_calls"], [])
        self.assertEqual(result["memory"][1], memory[1])
        self.assertEqual(result["memory"][6], b"\0")
        self.assertEqual(struct.unpack("<I", result["memory"][3])[0], 175)

    def test_average_moves_quarter_toward_current_delta(self):
        for previous, elapsed, expected in ((0, 101, 101), (100, 101, 100), (100, 104, 101),
                                             (100, 99, 100), (100, 96, 99), (100, 100, 100)):
            memory = self.enabled()
            struct.pack_into("<I", memory[3], 0, previous)
            result = self.run_original(memory, samples=[], script=((0, ()), (elapsed, ())))
            self.assertEqual(struct.unpack("<I", result["memory"][3])[0], expected)

    def test_pending_update_resets_average_filter(self):
        memory = self.enabled()
        memory[0][40] = memory[5][0] = 1
        result = self.run_original(memory, samples=[])
        self.assertEqual(struct.unpack("<I", result["memory"][3])[0], 400)

    def test_clock_difference_and_total_wrap(self):
        memory = self.enabled()
        result = self.run_original(memory, samples=[], script=((0xFFFFFFF0, ()), (0x20, ())))
        self.assertEqual(struct.unpack("<I", result["memory"][4])[0], 0x20)
        self.assertEqual(struct.unpack("<I", result["memory"][3])[0], 87)

    def test_first_clock_can_remove_second_clock(self):
        memory = self.enabled()
        result = self.run_original(memory, script=((100, ((0x01C34198, 0, 4),)),))
        self.assertEqual(len(result["calls"]), 1)
        self.assertEqual(result["memory"][3:5], tuple(bytes(v) for v in memory[3:5]))

    def test_second_clock_uses_new_token(self):
        memory = self.enabled()
        result = self.run_original(memory, script=((100, ((0x01C34198, 0x87654321, 4),)), (500, ())))
        self.assertEqual([event[0] for event in result["calls"]], [1, 0x87654321])

    def test_first_clock_changes_are_seen_by_audio(self):
        memory = self.enabled()
        result = self.run_original(memory, script=((100, ((0x31000000, 1000, 4),
                                                          (0x01C33320, 1 << 27, 4))), (500, ())))
        self.assertEqual(result["samples"], [500, -1, 2])

    def test_counters_are_read_after_second_clock(self):
        memory = self.enabled()
        result = self.run_original(memory, samples=[], script=((100, ()), (500, (
            (0x01C32DC8, 1000, 4), (0x01C34470, 7, 4)))))
        self.assertEqual(struct.unpack("<I", result["memory"][3])[0], 850)
        self.assertEqual(struct.unpack("<I", result["memory"][4])[0], 407)

    def test_pending_set_during_clock_waits_until_next_call(self):
        memory = self.enabled()
        result = self.run_original(memory, samples=[], script=((100, ((0x01C32E54, 1, 1),)), (500, ())))
        self.assertEqual(result["memory"][5][0], 1)
        self.assertEqual(struct.unpack("<I", result["memory"][3])[0], 175)

    def test_all_sections_select_both_kernels(self):
        for variant in (0, 1):
            memory = self.initial()
            for i in range(5):
                memory[1][44*i+40:44*i+42] = bytes((1, variant))
            result = self.run_original(memory)
            self.assertEqual(result["kernel_calls"], [("residual" if variant else "rounded", i, 3) for i in range(5)])

    def test_domain_and_public_memory_guards(self):
        from biquad_chain_machine import BiquadChainMachine
        for samples, operation, section in (([0]*129, "process", 0), ([1 << 31], "process", 0),
                                            ([], "update", 5), ([], "update", -1)):
            with self.assertRaises(ValueError):
                self.program.execute(self.initial(), samples, operation, section)
        machine = BiquadChainMachine(self.program, self.initial(), [0], "process", 0, None)
        with self.assertRaises(ValueError):
            machine.write(0x01C33240, 1, 4)
        with self.assertRaises(ValueError):
            machine.read(0x31000004, 4)
        with self.assertRaises(ValueError):
            machine.mutate(0x30000FFC, 1, 4)


if __name__ == "__main__":
    unittest.main()
