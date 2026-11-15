"""Real branch encodings: catch target drift for mixed instruction lengths."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT / "upstream/pi32v2-isa/pi32v2isa").exists(), "bootstrap ISA dependency first")
class BranchAddressTests(unittest.TestCase):
    def test_real_firmware_branches_use_instruction_end(self):
        from tools.disassemble import relative_target, codec, table
        instructions = table.load()
        cases = [
            # UltraRig G reset; Mini timer-registration call; Mini scan loop exit.
            (0x02000120, "14 94", 0x0200018A),
            (0x020060B4, "bf ea 79 ff", 0x02005FAA),
            (0x0200A0A0, "20 ff 40 4b 1a 00", 0x0200A0DA),
        ]
        for pc, raw, expected in cases:
            with self.subTest(pc=hex(pc)):
                instruction, fields, size = codec.decode(instructions, bytes.fromhex(raw), 0)
                self.assertEqual(relative_target(pc, size, codec.format(instruction, fields)), expected)


if __name__ == "__main__":
    unittest.main()
