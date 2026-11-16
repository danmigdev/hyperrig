"""Hand-calculated checks of the original control instructions; no device access."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class ControlInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from control_machine import ControlsProgram
        cls.program = ControlsProgram()

    def initial(self, mapping=(0, 1, 2, 3)):
        globals_, state = bytearray(270), bytearray(1860)
        globals_[116:120] = bytes(mapping)
        state[74] = 1
        return globals_, state, 0

    def edge(self, memory, physical, pressed, a=0, b=0):
        return self.program.execute(*memory, physical, pressed, a, b)

    def events(self, result):
        return [(logical, event) for logical, event, _ in result["calls"]]

    def test_missing_mapping_records_raw_state_without_an_action(self):
        original = self.initial((4, 3, 1, 0))
        result = self.edge(original, 2, 1)
        expected = bytearray(original[1])
        expected[1569] = 1
        self.assertEqual(result["memory"], (bytes(original[0]), bytes(expected), 0))
        self.assertEqual(self.events(result), [])

    def test_duplicate_mapping_uses_last_logical_slot(self):
        result = self.edge(self.initial((1, 1, 1, 1)), 1, 1, 123, 456)
        self.assertEqual(self.events(result), [(3, 0)])
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 1828 + 3 * 4)[0], 123)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 1844 + 3 * 4)[0], 456)

    def test_disabled_actions_still_record_edges_and_ignore_duplicates(self):
        globals_, state, owner = self.initial()
        state[74] = 0
        result = self.edge((globals_, state, owner), 0, 1)
        self.assertEqual(self.events(result), [])
        state = bytearray(result["memory"][1])
        state[74] = 1
        duplicate = self.edge((globals_, state, owner), 0, 1)
        self.assertEqual(duplicate["writes"], [])
        self.assertEqual(self.events(duplicate), [])

    def test_immediate_press_suppresses_exactly_the_release(self):
        result = self.edge(self.initial(), 0, 1)
        self.assertEqual(self.events(result), [(0, 0)])
        self.assertEqual(result["memory"][1][960], 1)
        released = self.edge(result["memory"], 0, 0)
        self.assertEqual(self.events(released), [])
        self.assertEqual(released["memory"][1][960], 0)

    def test_deferred_primary_action_fires_on_release(self):
        globals_, state, owner = self.initial()
        globals_[239] = 7
        pressed = self.edge((globals_, state, owner), 0, 1)
        self.assertEqual(self.events(pressed), [])
        self.assertEqual(self.events(self.edge(pressed["memory"], 0, 0)), [(0, 0)])

    def test_second_edge_keeps_first_stamps_and_emits_event_two(self):
        globals_, state, owner = self.initial()
        globals_[242] = 8
        first = self.edge((globals_, state, owner), 0, 1, 123, 456)
        waiting = self.edge(first["memory"], 0, 0)
        self.assertEqual(waiting["memory"][1][964], 1)
        self.assertEqual(self.events(waiting), [])
        second = self.edge(waiting["memory"], 0, 1, 987, 999)
        self.assertEqual(struct.unpack_from("<I", second["memory"][1], 1828)[0], 123)
        self.assertEqual(struct.unpack_from("<I", second["memory"][1], 1844)[0], 456)
        result = self.edge(second["memory"], 0, 0)
        self.assertEqual(self.events(result), [(0, 2)])
        self.assertEqual(result["memory"][1][964], 0)

    def test_repeat_window_wraps_and_keeps_its_owner(self):
        globals_, state, _ = self.initial()
        struct.pack_into("<I", state, 1508, 0)
        state[964] = 1
        result = self.edge((globals_, state, 1), 0, 1, 33, 0xFFFFFFFE)
        self.assertEqual(self.events(result), [(0, 1)])
        self.assertEqual(result["memory"][2], 1)
        self.assertEqual(struct.unpack_from("<I", result["memory"][1], 1508)[0], 2498)
        self.assertEqual(result["memory"][1][932], 1)
        self.assertEqual(result["memory"][1][960], 1)
        self.assertEqual(result["memory"][1][964], 0)

    def test_equal_deadline_expires_the_repeat_window(self):
        globals_, state, _ = self.initial()
        struct.pack_into("<I", state, 1508, 100)
        result = self.edge((globals_, state, 1), 0, 1, 0, 100)
        self.assertEqual(self.events(result), [(0, 0)])
        self.assertEqual(result["memory"][2], 0)

    def test_immediate_policy_action_and_mask_precedence(self):
        globals_, state, owner = self.initial()
        for action1, action2, mask, expected in ((0, 0, 0, 1), (7, 0, 0, 0), (7, 0, 4, 1), (7, 8, 4, 0)):
            globals_[239 + 18], globals_[242 + 18], globals_[11] = action1, action2, mask
            result = self.program.execute(globals_, state, owner, 2, 0, immediate=True)
            self.assertEqual(result["result"], expected)
            self.assertEqual(result["writes"], [])

    def test_bad_domain_and_uninitialized_reads_fail(self):
        with self.assertRaisesRegex(ValueError, "domain"):
            self.edge(self.initial(), 5, 1)
        with self.assertRaisesRegex(ValueError, "domain"):
            self.edge(self.initial(), 0, 2)
        from control_machine import ControlMachine, STATE
        machine = ControlMachine(self.program, *self.initial(), 0, 1, 0, 0, immediate=False)
        del machine.memory[STATE + 1567]
        with self.assertRaisesRegex(ValueError, "uninitialized"):
            machine.run()


if __name__ == "__main__":
    unittest.main()
