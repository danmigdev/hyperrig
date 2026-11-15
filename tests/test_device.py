"""Exercise host MIDI workflows with a simulated transport, not a real pedal."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hyperrig.device import ReadOnlyMini
from hyperrig.mini import Frame


class SimulatedMidi:
    def __init__(self, name=b"TANK MINI_004", wrong_echo=False, unstable=False):
        self.name, self.wrong_echo, self.unstable = name, wrong_echo, unstable
        preset = b"\x46\0" + bytes(range(6)) + bytes(84)
        self.bank = preset * 21 + b"PATCHEND\0\0"
        self.sent = []
        self.bank_reads = 0
        self.input, self.output = self.Input(self), self.Output(self)

    def MidiIn(self):
        return self.input

    def MidiOut(self):
        return self.output

    class Input:
        def __init__(self, bus):
            self.bus, self.closed = bus, False

        def get_ports(self):
            return ["Simulated input"]

        def ignore_types(self, **kwargs):
            pass

        def set_callback(self, callback):
            self.callback = callback

        def open_port(self, index):
            pass

        def close_port(self):
            self.closed = True

    class Output:
        def __init__(self, bus):
            self.bus, self.closed = bus, False

        def get_ports(self):
            return ["Simulated output"]

        def open_port(self, index):
            pass

        def close_port(self):
            self.closed = True

        def send_message(self, wire):
            frame = Frame.decode(bytes(wire))
            self.bus.sent.append(frame)
            if frame.command == 0x11:
                reply = Frame(0x11, self.bus.name + bytes(14))
            elif frame.command == 0x23:
                address = int.from_bytes(frame.body[1:5], "little")
                length = int.from_bytes(frame.body[5:8], "little")
                if address == 0:
                    self.bus.bank_reads += 1
                bank = self.bus.bank
                if self.bus.unstable and self.bus.bank_reads > 1:
                    bank = b"\x47" + bank[1:]
                echo = bytes(8) if self.bus.wrong_echo else frame.body
                reply = Frame(0x23, echo + bank[address:address + length])
            else:
                raise AssertionError("host sent an unexpected command")
            self.bus.input.callback((list(reply.encode()), 0.0), None)


class ReadOnlyDeviceTests(unittest.TestCase):
    def test_preset_backup_uses_two_bounded_reads(self):
        api = SimulatedMidi()
        with tempfile.TemporaryDirectory() as folder, patch("hyperrig.device._rtmidi", return_value=api):
            destination = Path(folder) / "backup"
            with ReadOnlyMini(0, 0) as device:
                info = device.backup(destination)
            self.assertEqual((destination / "presets.bin").read_bytes(), api.bank)
            self.assertEqual(len(info["presets"]), 21)
            self.assertEqual(info["equal_reads"], 2)
            self.assertEqual(api.bank_reads, 2)
            self.assertEqual([f.command for f in api.sent], [0x11] + [0x23] * 32)
            for frame in api.sent[1:]:
                self.assertEqual(frame.body[0], 4)
                self.assertLessEqual(int.from_bytes(frame.body[5:8], "little"), 128)
        self.assertTrue(api.input.closed and api.output.closed)

    def test_wrong_model_is_closed_before_reads(self):
        api = SimulatedMidi(name=b"TANK-G_001")
        with patch("hyperrig.device._rtmidi", return_value=api):
            with self.assertRaisesRegex(ValueError, "not a Tank Mini"):
                with ReadOnlyMini(0, 0):
                    self.fail("wrong device was accepted")
        self.assertEqual(len(api.sent), 1)
        self.assertTrue(api.input.closed and api.output.closed)

    def test_wrong_read_address_is_rejected(self):
        api = SimulatedMidi(wrong_echo=True)
        with patch("hyperrig.device._rtmidi", return_value=api), ReadOnlyMini(0, 0) as device:
            with self.assertRaisesRegex(ValueError, "address/length"):
                device.read("presets")

    def test_changing_bank_does_not_create_a_backup(self):
        api = SimulatedMidi(unstable=True)
        with tempfile.TemporaryDirectory() as folder, patch("hyperrig.device._rtmidi", return_value=api):
            destination = Path(folder) / "backup"
            with ReadOnlyMini(0, 0) as device:
                with self.assertRaisesRegex(ValueError, "changed between reads"):
                    device.backup(destination)
            self.assertFalse(destination.exists())

    def test_write_command_never_reaches_transport(self):
        api = SimulatedMidi()
        with patch("hyperrig.device._rtmidi", return_value=api), ReadOnlyMini(0, 0) as device:
            with self.assertRaises(ValueError):
                device.exchange(Frame(0x21))
        self.assertEqual(len(api.sent), 1)


if __name__ == "__main__":
    unittest.main()
