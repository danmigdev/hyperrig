"""Post-stop writer confirmation uses fake RAM replies only."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'analysis/hardware'), str(ROOT / 'tools')]
spec = importlib.util.spec_from_file_location('mini_partial_inspect4',
    ROOT / 'analysis/hardware/read_mini_partial_install4.py')
inspect = importlib.util.module_from_spec(spec);spec.loader.exec_module(inspect)
from tests.test_mini_app_writer_protocol import encoded_record, changed_record

TAG = 3953063795


def expected_record():
    return encoded_record({4:1,8:inspect.A,12:TAG,16:3,20:0,24:71,28:22,
        32:0x4D000,36:0x4D900,48:0xAF70A76D,52:0xAF70A76D,56:0xEB6014,
        60:0,64:2,68:1201,72:71,76:1130,80:3411456,84:12885,88:260,
        92:1,96:0x3FF,100:0,104:0,108:1,112:112,116:1})


class FakeWriter:
    def __init__(self, raw=None, *, bad_identity=False, fail=None):
        self.raw = expected_record() if raw is None else raw
        self.bad_identity, self.fail, self.commands = bad_identity, fail, []

    def exchange(self, cdb, data_out=None, read_length=0):
        op = int.from_bytes(cdb[:2], 'big');self.commands.append(op)
        assert data_out is None and cdb[2:] == b'\xff' * 14
        if op == self.fail: raise TimeoutError('mock command failure')
        if op == 0xFC78:
            assert read_length == 16
            return b'\xfc\x78' + (b'BAD!' if self.bad_identity else b'HYW1') + b'\1\1' + struct.pack('>II', inspect.A, 32768)
        if op == 0xFD88:
            assert read_length == 128
            return self.raw
        raise AssertionError('inspection emitted an unexpected command')


class Inspect4Tests(unittest.TestCase):
    def test_only_identity_and_fresh_audit_then_exact_acknowledged_read_state(self):
        fake = FakeWriter();retained=[]
        result = inspect.confirm_writer(fake, expected_record(), build_tag=TAG, retain=retained.append)
        self.assertEqual(fake.commands, [0xFC78,0xFD88])
        self.assertEqual(retained, [expected_record()])
        self.assertEqual(result['read_bytes'], 3411456)
        self.assertEqual(result['program_attempts'], 1130)

    def test_stale_audit_before_completed_read_is_not_accepted(self):
        fake = FakeWriter(changed_record(expected_record(),80,3411200));retained=[]
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake, expected_record(), build_tag=TAG, retain=retained.append)
        self.assertEqual(len(retained), 1)
        self.assertEqual(fake.commands, [0xFC78,0xFD88])

    def test_changed_counts_sequence_CRC_stack_or_guards_rejected(self):
        for offset, value in ((24,72),(28,23),(52,1),(68,1202),(72,72),(76,1131),
                              (80,3411712),(84,12886),(92,0),(96,0x7FF),(108,0),(112,108),(116,0)):
            fake = FakeWriter(changed_record(expected_record(),offset,value))
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                inspect.confirm_writer(fake, expected_record(), build_tag=TAG, retain=lambda _:None)
            self.assertEqual(fake.commands, [0xFC78,0xFD88])

    def test_busy_write_enabled_and_protection_rejected_even_if_expected_tampered(self):
        for offset, value in ((60,1),(60,2),(60,4),(64,0x40)):
            raw = changed_record(expected_record(),offset,value);fake=FakeWriter(raw)
            with self.subTest(offset=offset,value=value), self.assertRaises(ValueError):
                inspect.confirm_writer(fake, raw, build_tag=TAG, retain=lambda _:None)

    def test_identity_failure_does_not_sample_or_change_state(self):
        fake=FakeWriter(bad_identity=True)
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake, expected_record(), build_tag=TAG, retain=lambda _:None)
        self.assertEqual(fake.commands, [0xFC78])

    def test_transport_and_disk_failures_never_retry(self):
        for fail in (0xFC78,0xFD88):
            fake=FakeWriter(fail=fail)
            with self.subTest(fail=fail), self.assertRaises(TimeoutError):
                inspect.confirm_writer(fake, expected_record(), build_tag=TAG, retain=lambda _:None)
            self.assertEqual(fake.commands.count(fail),1)
        fake=FakeWriter()
        def blocked(_): raise OSError('raw evidence could not be saved')
        with self.assertRaises(OSError): inspect.confirm_writer(fake, expected_record(), build_tag=TAG, retain=blocked)
        self.assertEqual(fake.commands,[0xFC78,0xFD88])


if __name__ == '__main__': unittest.main()
