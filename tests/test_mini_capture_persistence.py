"""Offline protocol/audit tests. No transport or browser is constructed."""
import base64
import copy
import hashlib
from pathlib import Path
import unittest
import zlib

from tools import mini_capture_persistence as cap

ROOT = Path(__file__).resolve().parents[1]


class CapturePersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blob = (ROOT/'analysis/firmware/m571_g_app/embedded-0.a2l').read_bytes()

    def initial(self, *, rows=(), current=-1):
        return {'MODEL': [cap.MODEL_LINE], 'CLIST': [*rows, f'CLIST end current={current} slots=15']}

    def fixture(self, *, initial=None):
        initial = initial or self.initial()
        plan = cap.plan_capture(initial, self.blob)
        slot = plan['slot']
        rows = initial['CLIST'][:-1]
        if plan['request']:
            rows = [*rows, f"CAP {slot} 4892 'A2' trim=0.0"]
            rows.sort(key=lambda line: int(line.split()[1]))
        answers = self.initial(rows=rows, current=slot)
        if plan['request']:
            answers[plan['request']] = [f"CSAVE ok {slot} 'A2' 4892 B"]
        answers[plan['header_request']] = [f"CREAD {slot} len=4892 crc=2144df1c id=77ac505b aux=0 fs=0 name='A2'"]
        for off, command in zip(range(0, len(self.blob), 96), plan['chunk_requests']):
            part = self.blob[off:off+96]
            answers[command] = [f'CREAD {slot} {off} {len(part)} {zlib.crc32(part):08x} '+base64.b64encode(part).decode()]
        return plan, answers

    def test_pristine_default_and_complete_roundtrip(self):
        plan, answers = self.fixture()
        self.assertEqual(plan['request'], 'CSAVE 0 A2')
        self.assertEqual(len(plan['chunk_requests']), 51)
        self.assertEqual(plan['chunk_requests'][-1], 'CREAD 0 4800')
        result = cap.verify_capture(plan, answers, self.blob)
        self.assertTrue(result['verified'])
        self.assertEqual(result['capture_sha256'], cap.A2_SHA256)
        self.assertEqual(result['chunk_count'], 51)
        self.assertFalse(result['hardware_execution_attested'])
        self.assertFalse(result['power_cycle_retention_proven'])
        self.assertFalse(result['audio_quality_proven'])

    def test_first_free_slot_preserves_existing_metadata(self):
        initial = self.initial(rows=("CAP 0 600 'Existing' trim=-1.5 in=-12.0", "CAP 3 100 'Other' trim=0.0 amx"))
        plan, answers = self.fixture(initial=initial)
        self.assertEqual(plan['slot'], 1)
        self.assertEqual(plan['request'], 'CSAVE 1 A2')
        self.assertTrue(cap.verify_capture(plan, answers, self.blob)['preexisting_inventory_metadata_unchanged'])
        answers['CLIST'][0] = answers['CLIST'][0].replace('Existing', 'Replaced')
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'library'):
            cap.verify_capture(plan, answers, self.blob)

    def test_existing_active_pristine_slot_is_read_only(self):
        initial = self.initial(rows=("CAP 4 4892 'A2' trim=0.0",), current=4)
        plan, answers = self.fixture(initial=initial)
        self.assertIsNone(plan['request'])
        self.assertFalse(any(command.startswith('CSAVE') for command in answers))
        result = cap.verify_capture(plan, answers, self.blob)
        self.assertIsNone(result['csave_ack'])
        self.assertEqual(result['current_capture'], 4)

    def test_full_library_does_not_overwrite(self):
        rows = [f"CAP {n} 10 'Existing{n}' trim=0.0" for n in range(15)]
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'no free'):
            cap.plan_capture(self.initial(rows=rows), self.blob)

    def test_model_trim_name_shape_or_engine_changes_stop_before_plan(self):
        for value in (cap.MODEL_LINE.replace("'A2'", "'Other'"),
                      cap.MODEL_LINE.replace('trim=0.0', 'trim=0.5'),
                      cap.MODEL_LINE.replace('layers=23', 'layers=24'),
                      cap.MODEL_LINE.replace('engine=A2L', 'engine=AM4')):
            with self.subTest(value=value), self.assertRaises(cap.CapturePersistenceError):
                cap.plan_capture({**self.initial(), 'MODEL': [value]}, self.blob)

    def test_invalid_incomplete_or_duplicate_clist(self):
        invalid = ([], ["CAP 0 4892 'A2' trim=0.0"],
                   ['CLIST end current=-1 slots=16'], ['CLIST end current=0 slots=15'],
                   ["CAP 1 10 'A' trim=0", "CAP 1 10 'A' trim=0", 'CLIST end current=-1 slots=15'],
                   ["CAP 2 10 'A' trim=0", "CAP 1 10 'B' trim=0", 'CLIST end current=-1 slots=15'],
                   ['CLIST end current=-1 slots=15', 'CLIST end current=-1 slots=15'],
                   ['ERR CLIST pair', 'CLIST end current=-1 slots=15'])
        for lines in invalid:
            with self.subTest(lines=lines), self.assertRaises(cap.CapturePersistenceError):
                cap.parse_clist(lines)

    def test_other_current_capture_is_not_overwritten(self):
        for row in ("CAP 4 4892 'Other' trim=0.0", "CAP 4 4892 'A2' trim=0.5",
                    "CAP 4 4892 'A2' trim=0.0 in=-12.0", "CAP 4 4892 'A2' trim=0.0 amx"):
            with self.subTest(row=row), self.assertRaises(cap.CapturePersistenceError):
                cap.plan_capture(self.initial(rows=(row,), current=4), self.blob)

    def test_changed_blob_is_rejected_even_with_valid_crc_residue(self):
        changed = bytearray(self.blob)
        changed[100] ^= 1
        changed[-4:] = zlib.crc32(changed[:-4]).to_bytes(4, 'little')
        self.assertEqual(zlib.crc32(changed), cap.A2_CRC32)
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'SHA256'):
            cap.validate_blob(bytes(changed))

    def test_wrong_or_multiple_csave_ack(self):
        for lines in (["CSAVE ok 1 'A2' 4892 B"], ["CSAVE ok 0 'A2' 4891 B"],
                      ['ERR CSAVE'], ["CSAVE ok 0 'A2' 4892 B"]*2):
            plan, answers = self.fixture(); answers[plan['request']] = lines
            with self.subTest(lines=lines), self.assertRaises(cap.CapturePersistenceError):
                cap.verify_capture(plan, answers, self.blob)

    def test_missing_extra_or_size_argument_command(self):
        plan, answers = self.fixture()
        for action in ('missing', 'extra', 'count'):
            altered = copy.deepcopy(answers)
            if action == 'missing': del altered['CREAD 0 96']
            if action == 'extra': altered['CLOAD 0'] = ['CLOAD ok 0 audio=2']
            if action == 'count': altered['CREAD 0 0 96'] = altered.pop('CREAD 0 0')
            with self.subTest(action=action), self.assertRaisesRegex(cap.CapturePersistenceError, 'commands'):
                cap.verify_capture(plan, altered, self.blob)

    def test_header_metadata_all_fields_bound(self):
        plan, answers = self.fixture()
        head = answers['CREAD 0'][0]
        for old, new in (('CREAD 0', 'CREAD 1'), ('len=4892','len=4891'),
                         ('crc=2144df1c', 'crc=2144df1d'), ('id=77ac505b', 'id=77ac505c'),
                         ('aux=0','aux=1'), ('fs=0','fs=48000'), ("name='A2'", "name='Other'")):
            altered = copy.deepcopy(answers); altered['CREAD 0'] = [head.replace(old, new)]
            with self.subTest(field=old), self.assertRaises(cap.CapturePersistenceError):
                cap.verify_capture(plan, altered, self.blob)

    def test_chunk_order_offset_crc_and_length(self):
        plan, answers = self.fixture()
        first = answers['CREAD 0 0'][0]
        fields = first.split()
        corruptions = [answers['CREAD 0 96'][0], first.replace('CREAD 0 0 ', 'CREAD 1 0 ')]
        bad = fields.copy(); bad[3] = '95'; corruptions.append(' '.join(bad))
        bad = fields.copy(); bad[4] = '00000000'; corruptions.append(' '.join(bad))
        bad = fields.copy(); bad[5] = bad[5][:-1]; corruptions.append(' '.join(bad))
        for value in corruptions:
            altered = copy.deepcopy(answers); altered['CREAD 0 0'] = [value]
            with self.subTest(value=value[:60]), self.assertRaises(cap.CapturePersistenceError):
                cap.verify_capture(plan, altered, self.blob)

    def test_chunk_valid_crc_wrong_bytes_still_rejected(self):
        plan, answers = self.fixture()
        part = bytearray(self.blob[:96]); part[40] ^= 1; part = bytes(part)
        answers['CREAD 0 0'] = [f'CREAD 0 0 96 {zlib.crc32(part):08x} '+base64.b64encode(part).decode()]
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'bytes differ'):
            cap.verify_capture(plan, answers, self.blob)

    def test_noncanonical_base64_unused_pad_bits_rejected(self):
        plan, answers = self.fixture()
        fields = answers['CREAD 0 4800'][0].split()
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        b64 = fields[5]; self.assertTrue(b64.endswith('='))
        index = alphabet.index(b64[-2]); self.assertEqual(index & 3, 0)
        fields[5] = b64[:-2]+alphabet[index+1]+'='
        self.assertEqual(base64.b64decode(fields[5]), self.blob[4800:])
        answers['CREAD 0 4800'] = [' '.join(fields)]
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'noncanonical'):
            cap.verify_capture(plan, answers, self.blob)

    def test_plan_and_observation_changes_are_rejected(self):
        for field, value in (('slot', 1), ('request', 'CSAVE 0 Other'), ('retries', 1)):
            plan, answers = self.fixture(); plan[field] = value
            with self.subTest(field=field), self.assertRaises(cap.CapturePersistenceError):
                cap.verify_capture(plan, answers, self.blob)
        plan, answers = self.fixture(); answers['MODEL'] = [cap.MODEL_LINE.replace('trim=0.0','trim=1.0')]
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'MODEL changed'):
            cap.verify_capture(plan, answers, self.blob)

    def test_input_objects_are_not_mutated(self):
        plan, answers = self.fixture()
        before_plan, before_answers = copy.deepcopy(plan), copy.deepcopy(answers)
        result = cap.verify_capture(plan, answers, self.blob)
        result['command_responses']['MODEL'].append('bad')
        self.assertEqual(plan, before_plan); self.assertEqual(answers, before_answers)

    def test_original_binary_and_frozen_v3_byte_audit(self):
        from hyperrig.jieli import unpack_app
        plain = (ROOT/'analysis/firmware/m571_g_app/app_area.dec.bin').read_bytes()
        raw = (ROOT/'build/hyperrig-mini-audio-v3/hyperrig-mini.app-area.bin').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c')
        candidate = unpack_app(raw)[0]
        editor = (ROOT/'artifacts/alpha11/v2/UltraRig-alpha11-v2-win/web/tankg.html').read_text('utf-8')
        result = cap.audit_default(plain, candidate, editor, self.blob)
        self.assertTrue(result['csave_accepts_current_minus_one'])
        self.assertFalse(result['hardware_executed'])
        changed = bytearray(candidate); changed[0xC29C] ^= 1
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'csave_validate_copy'):
            cap.audit_default(plain, bytes(changed), editor, self.blob)
        with self.assertRaisesRegex(cap.CapturePersistenceError, 'anchors'):
            cap.audit_default(plain, candidate, editor.replace('await send(`${c} ${slot}`, pre, 3000)', 'bad'), self.blob)


if __name__ == '__main__':
    unittest.main()
