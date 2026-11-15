import unittest

from hyperrig.mini import Frame, Preset, decode_table, read_request, validate_readonly


class CapturedProtocolTests(unittest.TestCase):
    """Vectors from tankmini-linux's hardware captures, not our encoder."""

    def test_identity_request_matches_capture(self):
        self.assertEqual(Frame(0x11).encode(), bytes.fromhex("f0 00 32 45 00 00 00 40 7f 00 f7"))

    def test_identity_response_capture(self):
        raw = bytes.fromhex("f0 00 32 45 58 01 00 00 2a 41 1c 2d 02 52 29 12 27 49 3e 41 01 43 06 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 20 24 f7")
        frame = Frame.decode(raw)
        self.assertEqual(frame.command, 0x11)
        self.assertEqual(frame.body, b"TANK MINI_004" + bytes(14))
        self.assertEqual(frame.encode(), raw)

    def test_corrupt_reply_rejected(self):
        raw = bytearray(bytes.fromhex("f0 00 32 45 00 00 00 40 7f 00 f7"))
        raw[-3] ^= 1
        with self.assertRaises(ValueError):
            Frame.decode(raw)

    def test_read_requests_are_bounded(self):
        validate_readonly(read_request("presets", 1932, 10))
        with self.assertRaises(ValueError):
            read_request("presets", 1932, 11)
        for frame in (Frame(0x21), Frame(0x22), Frame(0x23, b"\0" * 8)):
            with self.assertRaises(ValueError):
                validate_readonly(frame)

    def test_invalid_preset_bank_rejected(self):
        with self.assertRaises(ValueError):
            decode_table(bytes(1942))
        with self.assertRaises(ValueError):
            Preset.decode(bytes(92))


if __name__ == "__main__":
    unittest.main()
