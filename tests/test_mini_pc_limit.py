import copy
import json
import unittest

from hyperrig.jieli import crc16, sfc, unpack_app
from firmware.mini.pc_limit_port import patches as p
from tools import audit_mini_pc_limit as audit
from tools.audit_mini_ultrarig_port import repack_header


class PcLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=audit.G.read_bytes();cls.raw=audit.IMAGE.read_bytes()
        cls.plain,cls.entries,cls.files=unpack_app(cls.raw)
        cls.end=p.ENTRY+len(cls.files['app.bin'])
        cls.proof=json.loads(audit.PROOF.read_bytes())
        cls.sdk=audit.SDK.read_text(encoding='utf-8')

    def patched_image(self, end=None, extra=None):
        end=self.end if end is None else end
        patch,=p.pc_limit_patches(self.g,end)
        plain=bytearray(self.plain);off=p.PATCH_ADDRESS-p.BASE
        plain[off:off+6]=patch.after
        if extra: extra(plain)
        entry=next(e for e in self.entries if e.name=='app.bin')
        plain[0x20:0x40]=repack_header(plain[0x20:0x40],data_crc=crc16(plain[entry.offset:entry.offset+entry.size]))
        # Root directory covers all retained app/config data, including headers.
        # Use the decoded root directory entry rather than a guessed alignment.
        from hyperrig.jieli import jlfs_entry
        root=jlfs_entry(bytes(plain[:32]),0)
        plain[:32]=repack_header(plain[:32],data_crc=crc16(plain[32:root.size]))
        cipher_end=(root.size+31)&~31
        return sfc(bytes(plain[:cipher_end]))+bytes(plain[cipher_end:])

    def test_literal_inventory_and_copy_sources(self):
        items=p.consumer_inventory(self.g)
        self.assertEqual([x['patch'] for x in items],[False,False,True])

    def test_patch_is_one_six_byte_instruction(self):
        patch,=p.pc_limit_patches(self.g,self.end)
        self.assertEqual(patch.address,0x0200067e)
        self.assertEqual(patch.after.hex(),'c1fff2740702')
        self.assertEqual(len(patch.after),len(patch.before))

    def test_cpu0_skips_shared_limits(self):
        self.assertEqual(p.simulate_limit_setup(self.plain,0)['PC_limits'],{})

    def test_cpu1_decodes_all_four_old_limits(self):
        result=p.simulate_limit_setup(self.plain,1)
        self.assertEqual(result['PC_limits'],dict(zip(map(str,p.LIMIT_REGISTERS),
                (p.ORIGINAL_END,p.ENTRY,0x01c1f088,0x01c00000))))

    def test_actual_crash_matches_pc_limit_not_codec_nack(self):
        result=audit.diagnose(self.plain,self.proof,self.sdk)
        self.assertEqual(result['SDK_cause'],'c0_pc_limit_err_r')
        self.assertFalse(result['codec_GPIO_call_reached_in_this_trace'])

    def test_different_crash_rejected(self):
        proof=copy.deepcopy(self.proof)
        row=next(x for x in proof['guard']['commands'] if x['line']=='CRASH')
        row['lines'][0]=row['lines'][0].replace('dbg=0x1000','dbg=0x80000')
        with self.assertRaises(ValueError):audit.diagnose(self.plain,proof,self.sdk)

    def test_stale_installed_image_fails_candidate_gate(self):
        with self.assertRaisesRegex(ValueError,'patch absent'):
            p.verify_candidate(self.raw,executable_end=self.end,g_plain=self.g)

    def test_candidate_has_one_changed_mmio_limit(self):
        result=p.verify_candidate(self.patched_image(),executable_end=self.end,g_plain=self.g)
        self.assertEqual(result['decoded_setup'][1]['PC_limits'][str(0x01eee380)],self.end)
        self.assertFalse(result['new_image_hardware_tested'])

    def test_end_must_match_actual_app_including_guard(self):
        raw=self.patched_image(self.end-2)
        with self.assertRaisesRegex(ValueError,'actual final'):
            p.verify_candidate(raw,executable_end=self.end-2,g_plain=self.g)

    def test_changed_copy_source_fails(self):
        def change(plain):plain[p.COPY_SITES[0]-p.BASE+2]^=1
        with self.assertRaisesRegex(ValueError,'RAM copy'):
            p.verify_candidate(self.patched_image(extra=change),executable_end=self.end,g_plain=self.g)

    def test_changed_debug_enable_fails(self):
        def change(plain):plain[0x6f4]^=1
        with self.assertRaisesRegex(ValueError,'other debug'):
            p.verify_candidate(self.patched_image(extra=change),executable_end=self.end,g_plain=self.g)

    def test_broad_odd_or_noninteger_limit_rejected(self):
        for end in (True,0,p.ORIGINAL_END,p.APPEND_START,p.MAX_END+2,self.end+1,float(self.end)):
            with self.subTest(end=end),self.assertRaises(ValueError):p.pc_limit_patches(self.g,end)

    def test_original_preimage_and_cpu_selection_rejected(self):
        g=bytearray(self.g);g[0x680]^=1
        with self.assertRaises(ValueError):p.pc_limit_patches(bytes(g),self.end)
        for cpu in (-1,2,True):
            with self.assertRaises(ValueError):p.simulate_limit_setup(self.plain,cpu)

    def test_report_retains_physical_limits(self):
        result=audit.audit()
        self.assertFalse(result['new_image_emitted'])
        self.assertFalse(result['audio_verified'])
        self.assertEqual(result['only_changed_register'],0x01eee380)


if __name__=='__main__':unittest.main()
