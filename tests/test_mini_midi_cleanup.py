"""MIDI cleanup failure coverage without opening a hardware port."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from hyperrig.device import ReadOnlyMini


class MidiCleanupTests(unittest.TestCase):
    def test_output_is_closed_even_when_input_cleanup_fails(self):
        device = ReadOnlyMini(0, 1)
        device.midi_in = SimpleNamespace(close_port=Mock(side_effect=SystemError("input detached")))
        device.midi_out = SimpleNamespace(close_port=Mock())
        with self.assertRaisesRegex(SystemError, "input detached"):
            device.__exit__(None, None, None)
        device.midi_out.close_port.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
