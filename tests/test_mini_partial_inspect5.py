"""Post-stop confirmation: two exact RAM echo states, no hardware access."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'analysis/hardware'), str(ROOT / 'tools')]
spec = importlib.util.spec_from_file_location('mini_partial_inspect5',
    ROOT / 'analysis/hardware/read_mini_partial_install5.py')
inspect = importlib.util.module_from_spec(spec); spec.loader.exec_module(inspect)
from tests.test_mini_app_writer_protocol import encoded_record, changed_record

TAG = 3953063795


def prior_record():
    return encoded_record({4:1,8:inspect.A,12:TAG,16:4,20:0,24:3,28:15,
        32:0x4F000,36:0x4F600,40:0x2ACA209C,44:0x27BB81FE,
        48:0xEEB7C4D2,52:0xEEB7C4D2,56:0xEB6014,60:0,64:2,
        68:41,72:3,76:38,80:623104,84:462,88:260,92:1,96:0x3F,
        100:1,104:0,108:1,112:52,116:1})


def alternatives():
    return inspect.echo_state_alternatives(prior_record(), build_tag=TAG)


class FakeWriter:
    def __init__(self, raw=None, *, bad_identity=False, fail=None):
        self.raw = prior_record() if raw is None else raw
        self.bad_identity, self.fail, self.commands = bad_identity, fail, []

    def exchange(self, cdb, data_out=None, read_length=0):
        op = int.from_bytes(cdb[:2], 'big'); self.commands.append(op)
        assert data_out is None and cdb[2:] == b'\xff' * 14
        if op == self.fail: raise TimeoutError('mock command failure')
        if op == 0xFC78:
            assert read_length == 16
            return b'\xfc\x78' + (b'BAD!' if self.bad_identity else b'HYW1') + b'\1\1' + struct.pack('>II', inspect.A, 32768)
        if op == 0xFD88:
            assert read_length == 128
            return self.raw
        raise AssertionError('inspection emitted an unexpected command')


class Inspect5Tests(unittest.TestCase):
    def test_wire_fixture_matches_last_physical_audit(self):
        self.assertEqual(inspect.sha(prior_record()), '767978da4ff19004a4021b0a97a19122d309ce0fa92c6b9c18a3b0da7a78930e')
        self.assertEqual(alternatives()[1], changed_record(prior_record(),104,1))

    def test_both_exact_states_accepted_without_echo_retry_or_NOR_command(self):
        for echoed, raw in enumerate(alternatives()):
            fake, retained = FakeWriter(raw), []
            result = inspect.confirm_writer(fake, alternatives(), build_tag=TAG, retain=retained.append)
            self.assertEqual(fake.commands, [0xFC78,0xFD88])
            self.assertEqual(retained, [raw])
            self.assertEqual(result['echoed'], echoed)
            self.assertEqual(result['stack_observed_bytes'], 52)
            self.assertEqual(result['read_bytes'], 623104)
            self.assertEqual(result['program_attempts'], 38)

    def test_every_other_field_change_rejected_even_with_correct_envelope_crc(self):
        for echoed, base in enumerate(alternatives()):
            for offset in range(4,120,4):
                if offset == 104: continue
                value = struct.unpack_from('<I',base,offset)[0] ^ 1
                fake = FakeWriter(changed_record(base,offset,value)); retained=[]
                with self.subTest(echoed=echoed, offset=offset), self.assertRaises(ValueError):
                    inspect.confirm_writer(fake, alternatives(), build_tag=TAG, retain=retained.append)
                self.assertEqual(fake.commands,[0xFC78,0xFD88])
                self.assertEqual(len(retained),1)

    def test_echo_mark_must_be_boolean_and_stack_growth_is_not_allowed(self):
        for offset,value in ((104,2),(112,56),(112,112),(112,48)):
            fake=FakeWriter(changed_record(prior_record(),offset,value))
            with self.subTest(offset=offset,value=value), self.assertRaises(ValueError):
                inspect.confirm_writer(fake, alternatives(), build_tag=TAG, retain=lambda _:None)

    def test_expected_witness_cannot_whitelist_an_extra_field(self):
        altered=changed_record(alternatives()[1],80,623360)
        fake=FakeWriter(altered)
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake,(prior_record(),altered),build_tag=TAG,retain=lambda _:None)
        self.assertEqual(fake.commands,[])

    def test_invalid_old_stage_guard_busy_or_stack_rejected_before_identity(self):
        for offset,value in ((16,3),(20,7),(60,1),(60,2),(60,4),(64,0x40),
                             (92,0),(100,0),(104,1),(108,0),(112,56)):
            with self.subTest(offset=offset,value=value), self.assertRaises(ValueError):
                inspect.echo_state_alternatives(changed_record(prior_record(),offset,value),build_tag=TAG)

    def test_identity_failure_never_reads_audit_or_loads_reader(self):
        fake=FakeWriter(bad_identity=True)
        with self.assertRaises(ValueError):
            inspect.confirm_writer(fake,alternatives(),build_tag=TAG,retain=lambda _:None)
        self.assertEqual(fake.commands,[0xFC78])

    def test_transport_or_evidence_failure_never_retries(self):
        for fail in (0xFC78,0xFD88):
            fake=FakeWriter(fail=fail)
            with self.subTest(fail=fail), self.assertRaises(TimeoutError):
                inspect.confirm_writer(fake,alternatives(),build_tag=TAG,retain=lambda _:None)
            self.assertEqual(fake.commands.count(fail),1)
        fake=FakeWriter()
        def blocked(_): raise OSError('raw evidence could not be saved')
        with self.assertRaises(OSError):
            inspect.confirm_writer(fake,alternatives(),build_tag=TAG,retain=blocked)
        self.assertEqual(fake.commands,[0xFC78,0xFD88])


if __name__ == '__main__': unittest.main()
