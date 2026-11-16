"""Hand-calculated selection checks, separate from the C differential harness."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = ((ROOT / "analysis/firmware/m571_g_app/app.bin").is_file() and
             (ROOT / "upstream/pi32v2-isa/pi32v2isa").is_dir())


@unittest.skipUnless(AVAILABLE, "bootstrap and analyze the pinned firmware first")
class SelectionInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tools"))
        from selection_machine import SelectionProgram
        cls.program = SelectionProgram()

    def initial(self):
        globals_, state = bytearray(272), bytearray(1860)
        globals_[116:120] = bytes(range(4))
        state[74] = 1
        return globals_, state, 0, bytearray((1, 1, 1, 1)), bytearray(2), bytearray(20), bytearray(48)

    def calls(self, result):
        return [call[:2] for call in result["calls"]]

    def test_preset_wrap_and_no_current_fallback(self):
        for current, step, expected in ((31, 1, 0), (0, 0xFFFFFFFF, 31),
                                        (0xFFFFFFFF, 1, 0), (0xFFFFFFFF, 0xFFFFFFFF, 31)):
            memory = self.initial()
            struct.pack_into("<I", memory[0], 92, current)
            result = self.program.execute(*memory, "preset_step", step,
                boundary=lambda service, *_: int(service == 0x200CF88))
            self.assertEqual(self.calls(result), [(0x200CF88, (expected, 0, 0)), (0x200CA7E, (expected, 0, 0))])

    def test_preset_empty_search_visits_exactly_32_candidates(self):
        result = self.program.execute(*self.initial(), "preset_step", 1)
        self.assertEqual(self.calls(result), [(0x200CF88, (slot, 0, 0)) for slot in (*range(1, 32), 0)])
        self.assertEqual(result["writes"], [])

    def test_preset_skips_missing_and_failed_loads(self):
        def boundary(service, args, machine):
            if service == 0x200CF88:
                return int(args[0] != 2)
            return int(args[0] == 1)
        result = self.program.execute(*self.initial(), "preset_step", 1, boundary=boundary)
        self.assertEqual(self.calls(result), [(0x200CF88, (1, 0, 0)), (0x200CA7E, (1, 0, 0)),
            (0x200CF88, (2, 0, 0)), (0x200CF88, (3, 0, 0)), (0x200CA7E, (3, 0, 0))])

    def test_wrapped_signed_remainder_is_not_python_floor_remainder(self):
        memory = self.initial()
        struct.pack_into("<I", memory[0], 92, 0x7FFFFFFF)
        result = self.program.execute(*memory, "preset_step", 0)
        self.assertEqual(self.calls(result)[0], (0x200CF88, (0xFFFFFFFF, 0, 0)))
        self.assertEqual([call[1][0] for call in result["calls"][1:]], [31] * 31)

    def test_abs_signed_minimum_saturates_as_in_pinned_hardware_results(self):
        from selection_machine import SelectionMachine
        machine = SelectionMachine(self.program, *self.initial(), "scene_flush", (), None)
        machine.pc = 0x020148D8
        machine.regs["r1"] = 0x80000000
        machine.step()
        self.assertEqual(machine.regs["r8"], 0x7FFFFFFF)

    def test_scene_pending_clears_before_the_first_service_call(self):
        memory = self.initial()
        struct.pack_into("<I", memory[1], 956, 1)
        result = self.program.execute(*memory, "scene_flush")
        self.assertEqual(self.calls(result), [(0x1C04862, (0, 0, 0)), (0x200A1D6, (1, 0, 0)),
                                             (0x200A228, (0, 0, 0)), (0x2002D10, (8, 1, 0))])
        self.assertEqual(result["calls"][0][2][1][956:960], bytes(4))

    def test_scene_zero_and_empty_requests_apply_nothing(self):
        for pending in (0, 1, 0xFFFFFFFF, 0x80000000):
            memory = self.initial()
            memory[3][:] = bytes(4)
            struct.pack_into("<I", memory[1], 956, pending)
            result = self.program.execute(*memory, "scene_flush")
            self.assertEqual(result["calls"], [])
            self.assertEqual(result["memory"][1][956:960], bytes(4))

    def test_scene_skips_inactive_and_counts_enabled_scenes(self):
        for step, expected in ((1, 2), (2, 0), (3, 2), (0xFFFFFFFF, 2), (0xFFFFFFFE, 0)):
            memory = self.initial()
            memory[3][:] = bytes((1, 0, 1, 0))
            struct.pack_into("<I", memory[1], 956, step)
            result = self.program.execute(*memory, "scene_flush")
            self.assertEqual(self.calls(result)[1], (0x200A1D6, (expected, 0, 0)))

    def test_scene_no_current_uses_directional_start(self):
        for step, expected in ((1, 0), (0xFFFFFFFF, 3)):
            memory = self.initial()
            struct.pack_into("<I", memory[0], 88, 0xFFFFFFFF)
            struct.pack_into("<I", memory[1], 956, step)
            result = self.program.execute(*memory, "scene_flush")
            self.assertEqual(self.calls(result)[1], (0x200A1D6, (expected, 0, 0)))

    def test_direct_scene_rejects_unavailable_and_out_of_range(self):
        memory = self.initial()
        memory[3][2] = 0
        for scene in (2, 4, 0xFFFFFFFF):
            result = self.program.execute(*memory, "scene", scene)
            self.assertEqual(result["calls"], [])
            self.assertEqual(result["writes"], [])

    def test_scene_report_receives_apply_result_and_preserved_clock(self):
        def boundary(service, *_):
            return {0x1C04862: 77, 0x200A1D6: 13, 0x200A228: 0x1234}.get(service, 0)
        result = self.program.execute(*self.initial(), "scene", 3, boundary=boundary)
        self.assertEqual(self.calls(result)[2:], [(0x200A228, (13, 77, 0)), (0x2002D10, (8, 3, 0x1234))])

    def test_scene_report_suppression_is_reread_after_apply(self):
        from selection_machine import STATE
        for initial, after in ((0, 1), (1, 0)):
            memory = self.initial()
            memory[1][740] = initial
            def boundary(service, args, machine):
                if service == 0x200A1D6:
                    machine.write(STATE + 740, after, 1)
                return 0
            result = self.program.execute(*memory, "scene", 0, boundary=boundary)
            self.assertEqual(len(result["calls"]), 2 if after else 4)

    def effects(self):
        memory = self.initial()
        memory[4][:] = bytes((2, 2))
        memory[5][0:2], memory[5][10:12] = bytes((0, 1)), bytes((2, 3))
        for index, kind in enumerate((5, 7, 5, 5)):
            memory[6][3 * index:3 * index + 3] = bytes((kind, 1, 1))
        return memory

    def test_effect_occurrences_span_both_chains(self):
        for occurrence, expected in ((0, 0), (1, 2), (2, 3), (3, 0xFFFFFFFF)):
            memory = self.effects()
            memory[0][236:239] = bytes((8, 5, occurrence))
            result = self.program.execute(*memory, "resolve", 236)
            self.assertEqual(result["result"], expected)
            self.assertEqual(result["calls"], [])
            self.assertEqual(result["memory"], tuple(bytes(x) if isinstance(x, bytearray) else x for x in memory))

    def test_absolute_binding_preserves_absent_and_invalid_ids(self):
        for identifier in (0, 255):
            memory = self.effects()
            memory[5][0] = identifier
            memory[6][2] = 0
            memory[0][236:239] = bytes((8, 0, 255))
            result = self.program.execute(*memory, "resolve", 236)
            self.assertEqual(result["result"], identifier)

    def test_missing_headers_do_not_match_a_type(self):
        memory = self.effects()
        memory[6][2] = 0
        memory[0][236:239] = bytes((8, 5, 0))
        result = self.program.execute(*memory, "resolve", 236)
        self.assertEqual(result["result"], 2)

    def test_type_zero_and_non_effect_records_do_not_resolve(self):
        for kind, argument in ((8, 0), (0, 5), (9, 5), (255, 5)):
            memory = self.effects()
            memory[0][236:239] = bytes((kind, argument, 0))
            result = self.program.execute(*memory, "resolve", 236)
            self.assertEqual(result["result"], 0xFFFFFFFF)

    def test_two_full_chains_are_truncated_at_sixteen(self):
        for position, expected in ((15, 15), (16, 0xFFFFFFFF)):
            memory = self.effects()
            memory[4][:] = bytes((10, 10))
            memory[5][:] = bytes(range(20))
            memory[0][269:272] = bytes((8, position, 255))
            result = self.program.execute(*memory, "resolve", 269)
            self.assertEqual(result["result"], expected)

    def test_effect_toggle_uses_original_header_and_resolved_slot(self):
        memory = self.effects()
        memory[0][236:239] = bytes((8, 5, 1))
        result = self.program.execute(*memory, "action", 0, 0)
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 0, 0x50800)), (0x200D060, (2, 0, 0))])

    def test_missing_effect_emits_diagnostic_without_a_set(self):
        memory = self.effects()
        memory[0][236:239] = bytes((8, 5, 3))
        result = self.program.execute(*memory, "action", 0, 0)
        self.assertEqual(self.calls(result)[1:], [(0x2002D10, (10, 773, 3))])

    def test_edge_reaches_preset_search_without_dispatcher_stub(self):
        memory = self.initial()
        memory[0][236] = 3
        result = self.program.execute(*memory, "edge", 0, 1, 100, 200,
            boundary=lambda service, *_: int(service == 0x200CF88))
        self.assertEqual(self.calls(result), [(0x2002D10, (9, 0, 0x300)),
                                             (0x200CF88, (1, 0, 0)), (0x200CA7E, (1, 0, 0))])

    def test_invalid_domain_and_uninitialized_stack_reads_fail(self):
        memory = self.initial()
        memory[4][0] = 11
        with self.assertRaisesRegex(ValueError, "domain"):
            self.program.execute(*memory, "resolve", 236)
        from selection_machine import SelectionMachine
        machine = SelectionMachine(self.program, *self.initial(), "resolve", (236,), None)
        machine.regs["sp"] -= 16
        with self.assertRaisesRegex(ValueError, "uninitialized"):
            machine.read(machine.regs["sp"], 1)


if __name__ == "__main__":
    unittest.main()
