"""Hand-calculated checks for control instruction semantics and call boundaries."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class ControlActionInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from control_action_machine import ControlActionProgram
        cls.program = ControlActionProgram()

    def initial(self):
        globals_, state = bytearray(272), bytearray(1860)
        globals_[116:120] = bytes(range(4))
        state[74] = 1
        return globals_, state, 0

    def calls(self, result):
        return [call[:2] for call in result["calls"]]

    def test_table_bytes_are_data_and_all_ten_targets_are_decoded(self):
        from control_action_machine import TABLE_START, TABLE_END
        self.assertEqual(bytes(self.program.table), bytes((5, 9, 22, 26, 30, 35, 40, 45, 61, 69)))
        self.assertFalse(any(at in self.program.code for at in range(TABLE_START, TABLE_END)))
        self.assertEqual([TABLE_START + 2 * entry for entry in self.program.table],
                         [0x2014A86, 0x2014A8E, 0x2014AA8, 0x2014AB0, 0x2014AB8,
                          0x2014AC2, 0x2014ACC, 0x2014AD6, 0x2014AF6, 0x2014B06])

    def test_no_action_still_records_wrapped_clock_and_slot_stamps(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 24, 0xFFFFFFFF)
        struct.pack_into("<I", memory[1], 1840, 123)
        struct.pack_into("<I", memory[1], 1856, 456)
        memory[0][270] = 17
        result = self.program.execute(*memory, "action", 3, 2)
        expected = bytearray(memory[1])
        struct.pack_into("<II", expected, 968, 123, 456)
        struct.pack_into("<I", expected, 1824, 0xFFFFFFF6)
        struct.pack_into("<I", expected, 812, 0xFFFFFFF6)
        expected[927] = 1
        self.assertEqual(result["memory"], (bytes(memory[0]), bytes(expected), 0))
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 3, (17 << 16) | 2))])

    def test_last_action_tail_drives_preset_then_optional_scene(self):
        memory = self.initial()
        memory[0][269:272] = bytes((2, 255, 3))
        result = self.program.execute(*memory, "action", 3, 2,
                                      boundary=lambda service, *_: int(service == 0x200CF88))
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 3, 0xFF0202)),
            (0x200CF88, (255, 0, 0)), (0x200CA7E, (255, 0, 0)), (0x2014366, (3, 0, 0))])

    def test_parallel_hold_packet_sets_flag_before_dispatch(self):
        memory = self.initial()
        memory[0][239] = 9
        memory[1][1567] = 1
        memory[1][964] = 1
        struct.pack_into("<H", memory[1], 1608, 999)
        result = self.program.execute(*memory, "tick", 1)
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 0, 0x901))])
        self.assertEqual(result["memory"][1][52], 1)
        at_call = result["calls"][0][2][1]
        self.assertEqual((at_call[932], at_call[964]), (1, 0))
        self.assertEqual(struct.unpack_from("<H", at_call, 1608)[0], 1000)
        self.assertIn(0x2014BAC, result["visited"])
        self.assertIn(0x2014BB0, result["visited"])

    def test_delayed_event_waits_until_301_and_clears_pending_first(self):
        memory = self.initial()
        memory[0][236] = 9
        memory[1][964] = 1
        struct.pack_into("<H", memory[1], 1616, 299)
        waiting = self.program.execute(*memory, "tick", 1)
        self.assertEqual(waiting["calls"], [])
        result = self.program.execute(*waiting["memory"], "tick", 1)
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 0, 0x900))])
        self.assertEqual(result["calls"][0][2][1][964], 0)

    def test_unsigned_timer_addition_wraps_before_cap(self):
        for initial, delta, expected in ((59999, 2, 60000), (65535, 0, 60000),
                                         (65535, 0xFFFF0001, 0), (1, 0xFFFFFFFF, 0)):
            memory = self.initial()
            memory[1][1567] = 1
            struct.pack_into("<H", memory[1], 1608, initial)
            result = self.program.execute(*memory, "tick", delta)
            self.assertEqual(struct.unpack_from("<H", result["memory"][1], 1608)[0], expected)
            self.assertEqual(result["calls"], [])

    def test_tap_hold_arms_repeat_without_calling_tap_handler(self):
        memory = self.initial()
        memory[0][239] = 7
        struct.pack_into("<I", memory[0], 24, 100)
        struct.pack_into("<H", memory[1], 1608, 1000)
        struct.pack_into("<I", memory[1], 1844, 876)
        result = self.program.execute(*memory, "action", 0, 1)
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 0, 0x701))])
        self.assertEqual(result["memory"][2], 1)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 1508)[0], 3500)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 928)[0], 876)

    def test_tap_with_zero_hold_counter_forwards_both_stamps(self):
        memory = self.initial()
        memory[0][239] = 7
        struct.pack_into("<I", memory[1], 1828, 123)
        struct.pack_into("<I", memory[1], 1844, 456)
        result = self.program.execute(*memory, "action", 0, 1)
        self.assertEqual(self.calls(result)[1:], [(0x200A4B2, (123, 456, 0))])
        self.assertEqual(result["memory"][2], 0)

    def test_invalid_effect_uses_exclusive_then_else_diagnostic(self):
        for auxiliary, code in ((3, 779), (255, 768)):
            memory = self.initial()
            memory[0][236:239] = bytes((8, 11, auxiliary))
            result = self.program.execute(*memory, "action", 0, 0,
                boundary=lambda service, *_: 0xFFFFFFFF if service == 0x201499C else 0)
            self.assertEqual(self.calls(result)[1:], [(0x201499C, (236, 0, 0)),
                                                      (0x2002D10, (10, code, auxiliary))])

    def test_scene_step_accumulator_preserves_wraparound(self):
        for action, initial, expected in ((5, 0xFFFFFFFF, 0), (5, 0x7FFFFFFF, 0x80000000),
                                          (6, 0, 0xFFFFFFFF)):
            memory = self.initial()
            memory[0][236] = action
            struct.pack_into("<I", memory[1], 956, initial)
            result = self.program.execute(*memory, "action", 0, 0)
            self.assertEqual(struct.unpack_from("<I", result["memory"][1], 956)[0], expected)
            self.assertEqual(len(result["calls"]), 1)

    def test_duplicate_physical_map_advances_all_four_logical_timers(self):
        memory = self.initial()
        memory[0][116:120] = bytes(4)
        memory[1][1567] = 1
        for logical in range(4):
            memory[0][239 + logical * 9] = 9
        result = self.program.execute(*memory, "tick", 1000)
        self.assertEqual(self.calls(result), [(0x2002D10, (9, logical, 0x901)) for logical in range(4)])
        self.assertEqual(result["memory"][1][932:936], bytes((1, 1, 1, 1)))
        self.assertEqual(result["memory"][1][52], 0)

    def test_disabled_tick_is_an_explicit_external_boundary(self):
        memory = self.initial()
        memory[1][74] = 0
        result = self.program.execute(*memory, "tick", 123)
        self.assertEqual(self.calls(result), [(0x20146AE, (123, 0, 0))])
        self.assertEqual(result["writes"], [])

    def test_notify_mutation_precedes_clock_and_action_type_reload(self):
        from control_action_machine import GLOBAL
        memory = self.initial()
        memory[0][236] = 1
        def notify(service, args, machine):
            self.assertEqual(service, 0x2002D10)
            machine.write(GLOBAL + 24, 42, 4)
            machine.write(GLOBAL + 236, 9, 1)
            return 0
        result = self.program.execute(*memory, "action", 0, 0, boundary=notify)
        self.assertEqual(result["memory"][1][52], 1)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 812)[0], 420)
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 0, 256))])

    def test_invalid_domains_and_escape_fail(self):
        for operation, args in (("action", (4, 0)), ("action", (0, 3)), ("tick", (-1,))):
            with self.assertRaisesRegex(ValueError, "domain"):
                self.program.execute(*self.initial(), operation, *args)
        memory = self.initial()
        from control_action_machine import ControlActionMachine
        machine = ControlActionMachine(self.program, *memory, "tick", (1,), None)
        machine.pc = 0x2014BB0
        with self.assertRaisesRegex(ValueError, "second half"):
            machine.run()
        machine.pc = 0x2014A7C
        with self.assertRaisesRegex(ValueError, "escaped"):
            machine.run()


if __name__ == "__main__":
    unittest.main()
