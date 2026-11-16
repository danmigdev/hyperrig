"""Offline update-policy tests. The synthetic target is never a firmware build."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import plan_mini_pc_limit_upgrade as upgrade


class UpgradePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = (upgrade.ROOT/upgrade.BACKUP_PATH).read_bytes()
        cls.parent = (upgrade.ROOT/upgrade.revision.BASELINE_IMAGE).read_bytes()
        target = bytearray(cls.parent)
        target[0x120] ^= 1  # Intentionally synthetic; only the planner policy is under test.
        cls.target = bytes(target)

    def current(self):
        value = bytearray(self.stock)
        value[upgrade.APP_START:upgrade.APP_END] = self.parent
        for offset in (0x82020, 0xBE020, 0xBF020):
            value[offset] ^= 0x55  # Legitimate runtime partition differences must survive.
        return bytes(value)

    def prepare(self, data=None, *, target=None, claimed_hash=None):
        raw = self.current() if data is None else data
        candidate = self.target if target is None else target
        with tempfile.TemporaryDirectory(dir=upgrade.ROOT/'build') as directory:
            path = Path(directory)/'fresh-fixture.bin'
            path.write_bytes(raw)
            with patch.object(upgrade, 'checked_target', return_value=(candidate,
                    {'path': 'OFFLINE_FIXTURE', 'sha256': upgrade.sha(candidate)},
                    {'offline_fixture_not_build_validation': True})):
                return upgrade.prepare_upgrade(path,
                    expected_full_sha256=claimed_hash or upgrade.sha(raw),
                    expected_target_sha256=upgrade.sha(candidate))

    def test_runtime_partitions_preserved_and_only_header_sector_changed(self):
        plan = self.prepare()
        self.assertEqual(plan.installation.sector_order, (0x4000,))
        self.assertEqual(plan.installation.preimage, self.parent)
        self.assertEqual(plan.expected_full_readback()[0x82000:], self.current()[0x82000:])
        record = json.loads(plan.plan_bytes)
        changed = {r['name'] for r in record['preserved_regions'] if r['differs_from_stock_backup']}
        self.assertEqual(changed, {'VM', 'BTIF', 'USR'})
        self.assertEqual(record['page_order'][-1], 0x4000)
        self.assertTrue(upgrade.validate_completed_full(plan, plan.expected_full_readback())['application_verified'])

    def test_wrong_unit_parent_or_claimed_hash_rejected(self):
        for offset in (0x40, 0xFF020, 0x4820):
            with self.subTest(offset=offset):
                raw = bytearray(self.current()); raw[offset] ^= 1
                with self.assertRaises(ValueError): self.prepare(bytes(raw))
        with self.assertRaises(ValueError): self.prepare(claimed_hash='0'*64)

    def test_second_sector_or_already_identical_target_rejected(self):
        wrong = bytearray(self.target); wrong[4096+7] ^= 1
        with self.assertRaises(ValueError): self.prepare(target=bytes(wrong))
        with self.assertRaises(ValueError): self.prepare(target=self.parent)

    def test_final_read_must_preserve_runtime_state_not_restore_stock(self):
        plan = self.prepare()
        wrong = bytearray(plan.expected_full_readback())
        wrong[0x82000:] = self.stock[0x82000:]
        with self.assertRaises(ValueError): upgrade.validate_completed_full(plan, bytes(wrong))
        wrong = bytearray(plan.expected_full_readback()); wrong[0x4680] ^= 1
        with self.assertRaises(ValueError): upgrade.validate_completed_full(plan, bytes(wrong))
        with self.assertRaises(ValueError): replace(plan, full_preimage=plan.full_preimage[:-1])


if __name__ == '__main__':
    unittest.main()
