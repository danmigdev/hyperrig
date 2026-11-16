"""Prepare the single-sector v2 -> v3 update from a retained fresh NOR read.

Offline only. The installed application must be exact v2. Runtime VM/USR/BTIF
bytes are preserved from the fresh read, rather than reset to the stock backup.
The existing bounded writer and its validation are reused unchanged.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import install_mini_app as installer
from tools import build_mini_ultrarig_v3 as revision
from tools.restore_mini_stock import BACKUP_PATH, BACKUP_SHA, canonical, retained_file

APP_START, APP_END, CAPACITY = 0x4000, 0x82000, 0x100000
OLD_SHA = revision.BASELINE_SHA
NEW_DIR = ROOT/'build/hyperrig-mini-audio-v3'
sha, require = installer.sha, installer.require


def checked_target(expected_sha256):
    """Recompose the exact reviewed PC-limit change; never build/write files."""
    baseline = revision.load_baseline()
    expected, _, validation = revision.compose_revision(
        baseline, (ROOT/revision.G_PATH).read_bytes(), (ROOT/revision.MINI_PATH).read_bytes())
    target, target_ref = retained_file(NEW_DIR/'hyperrig-mini.app-area.bin')
    require(target == expected and sha(target) == expected_sha256,
            'target differs from the exact PC-limit-only v3 derivation')
    require([item['physical_address'] for item in validation['changed_sectors_vs_v2']] == [APP_START],
            'only the application header sector may change')
    return target, target_ref, validation


@dataclass(frozen=True)
class UpgradePlan:
    installation: installer.Installation
    full_preimage: bytes
    plan_bytes: bytes

    def __post_init__(self):
        spec = self.installation
        require(type(self.full_preimage) is bytes and len(self.full_preimage) == CAPACITY,
                'complete immutable fresh NOR required')
        require(isinstance(spec, installer.Installation) and spec.purpose == 'install-candidate'
                and spec.sector_order == (APP_START,) and sha(spec.preimage) == OLD_SHA
                and spec.preimage == self.full_preimage[APP_START:APP_END]
                and spec.fresh_full_read_sha256 == sha(self.full_preimage)
                and spec.backup_sha256 == BACKUP_SHA, 'upgrade input provenance differs')
        require(type(self.plan_bytes) is bytes and spec.plan_sha256 == sha(self.plan_bytes),
                'immutable plan hash differs')
        plan = json.loads(self.plan_bytes)
        require(canonical(plan) == self.plan_bytes and plan.get('kind') == 'mini-v2-v3-pc-limit-upgrade'
                and plan.get('target_app_sha256') == sha(spec.candidate)
                and plan.get('preimage_app_sha256') == OLD_SHA
                and plan.get('fresh_full_read', {}).get('sha256') == sha(self.full_preimage)
                and plan.get('sector_order') == [APP_START]
                and plan.get('physical_write_allowlist') == [APP_START, APP_END]
                and plan.get('expected_full_readback_sha256') == sha(self.expected_full_readback()),
                'upgrade plan content differs')

    def expected_full_readback(self):
        return self.full_preimage[:APP_START] + self.installation.candidate + self.full_preimage[APP_END:]

    def retain_plan(self, path):
        path = Path(path).resolve()
        require(path.is_relative_to(ROOT) and path.parent.is_dir(), 'new workspace plan path required')
        with path.open('xb') as stream:
            stream.write(self.plan_bytes)
            stream.flush()
            import os
            os.fsync(stream.fileno())
        return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(self.plan_bytes)}


def prepare_upgrade(fresh_dump_path, *, expected_full_sha256, expected_target_sha256,
                    stock_backup_path=ROOT/BACKUP_PATH, slot=0x01C20000):
    current, current_ref = retained_file(fresh_dump_path)
    stock, stock_ref = retained_file(stock_backup_path)
    require(len(current) == len(stock) == CAPACITY and sha(current) == expected_full_sha256,
            'fresh full NOR extent or reviewed hash differs')
    require(sha(stock) == BACKUP_SHA, 'same-unit stock backup differs')
    require(current[:APP_START] == stock[:APP_START] and current[0xFF000:] == stock[0xFF000:],
            'SPL or unit keymac differs from the retained unit backup')
    require(sha(current[APP_START:APP_END]) == OLD_SHA,
            'fresh current application is not the fully installed v2 image')
    target, target_ref, validation = checked_target(expected_target_sha256)
    base = installer.prepare_installation(slot=slot)
    require(base.backup_sha256 == BACKUP_SHA and sha(base.candidate) == OLD_SHA,
            'frozen operational writer provenance differs')
    old = current[APP_START:APP_END]
    changed = [a for a in range(APP_START, APP_END, 4096)
               if old[a-APP_START:a-APP_START+4096] != target[a-APP_START:a-APP_START+4096]]
    require(changed == [APP_START], 'upgrade must change exactly sector0x4000')
    preserved = []
    for name, lo, hi in (('SPL', 0, APP_START), ('VM', APP_END, 0xBE000),
                         ('BTIF', 0xBE000, 0xBF000), ('USR', 0xBF000, 0xFF000),
                         ('keymac', 0xFF000, CAPACITY)):
        preserved.append({'name': name, 'start': lo, 'end_exclusive': hi,
                          'current_sha256': sha(current[lo:hi]),
                          'differs_from_stock_backup': current[lo:hi] != stock[lo:hi],
                          'preserve_current_bytes': True})
    plan = {'schema': 1, 'kind': 'mini-v2-v3-pc-limit-upgrade', 'target': 'tank-mini',
            'fresh_full_read': current_ref, 'same_unit_stock_backup': stock_ref,
            'candidate': target_ref, 'preimage_app_sha256': OLD_SHA,
            'target_app_sha256': sha(target), 'physical_write_allowlist': [APP_START, APP_END],
            'sector_order': changed, 'header_sector_last': True, 'header_page_last': True,
            'preimage_sector_sha256': sha(old[:4096]), 'target_sector_sha256': sha(target[:4096]),
            'preimage_sector_crc32': installer.crc(old[:4096]), 'target_sector_crc32': installer.crc(target[:4096]),
            'page_order': installer.builder.page_order(APP_START), 'PC_limit_validation': validation,
            'preserved_regions': preserved,
            'expected_full_readback_sha256': sha(current[:APP_START]+target+current[APP_END:]),
            'writer': base.summary(), 'previous_session_tokens_or_bitmap_reused': False,
            'power_loss_atomicity_proven': False, 'automatic_retry': False,
            'automatic_reset': False, 'device_io': False,
            'post_operation': 'Remain in ROM until complete independent NOR comparison and reviewed boot.'}
    raw = canonical(plan)
    spec = replace(base, candidate=target, preimage=old, sector_order=(APP_START,),
                   plan_sha256=sha(raw), fresh_full_read_sha256=sha(current))
    return UpgradePlan(spec, current, raw)


def validate_completed_full(plan, readback):
    require(isinstance(plan, UpgradePlan) and type(readback) is bytes and len(readback) == CAPACITY,
            'verified upgrade plan and full immutable NOR readback required')
    require(readback == plan.expected_full_readback(),
            'full NOR differs from candidate application or preserved current unit data')
    return {'application_verified': True, 'candidate_sha256': sha(plan.installation.candidate),
            'full_NOR_sha256': sha(readback), 'external_regions_unchanged_from_fresh_read': True,
            'external_regions_restored_to_stock': False, 'boot_attempted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-dump', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--target-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.fresh_dump is None:
        require(not any((args.sha256, args.target_sha256, args.output)), 'fresh dump required')
        print(json.dumps({'device_io': False, 'writes': False, 'requires_fresh_current_app': OLD_SHA}))
        return
    require(args.sha256 and args.target_sha256 and args.output, 'explicit hashes and a new plan path required')
    plan = prepare_upgrade(args.fresh_dump, expected_full_sha256=args.sha256,
                           expected_target_sha256=args.target_sha256)
    print(json.dumps({'device_io': False, 'plan': plan.retain_plan(args.output),
                      'installation': plan.installation.summary()}))


if __name__ == '__main__':
    main()
