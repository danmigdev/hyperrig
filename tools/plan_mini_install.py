"""Prepare an exact application-sector replacement/rollback plan, offline.

No transport, flash command, uploader, elevation or device operation exists
here. A validated layout is not a proven hardware installation or recovery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_mini_ultrarig_port import (MINI_START, MINI_END, MINI_SIZE,
    MINI_PARTITIONS, BACKUP_PATH, BACKUP_SHA, validate_map)
from hyperrig.jieli import unpack_app

SECTOR = 4096

def sha(data): return hashlib.sha256(data).hexdigest()
def require(condition, message):
    if not condition: raise ValueError(message)


def prepare(manifest_path: Path, backup_path: Path, output: Path):
    spec = json.loads(manifest_path.read_text(encoding='utf-8'))
    require(spec.get('target') == 'tank-mini' and spec.get('architecture') == 'standalone-ultrarig-port',
            'only the complete UltraRig-derived MINI application is in scope')
    require(spec.get('stock_MINI_application_used') is False, 'manifest must exclude a stock application graft')
    image_path = (ROOT / spec['image_path']).resolve()
    require(image_path.is_relative_to(ROOT), 'candidate path outside workspace')
    image = image_path.read_bytes()
    require(len(image) == MINI_SIZE and sha(image) == spec['image_sha256'], 'candidate image hash/extent differs')
    plain, entries, files = unpack_app(image)
    validate_map(entries, MINI_PARTITIONS)
    require(b'tankm_fw M5.71 rel ble\0' in files['app.bin'] and b'HyperRig auth\0' in files['app.bin'],
            'candidate identity is not the adapted MINI firmware')
    backup = backup_path.read_bytes()
    require(len(backup) == 0x100000 and sha(backup) == BACKUP_SHA, 'expected the verified full backup of this MINI')
    original = backup[MINI_START:MINI_END]
    _, original_entries, _ = unpack_app(original)
    validate_map(original_entries, MINI_PARTITIONS)
    sectors = []
    for address in range(MINI_START, MINI_END, SECTOR):
        offset = address - MINI_START
        old, new = original[offset:offset+SECTOR], image[offset:offset+SECTOR]
        require(len(old) == len(new) == SECTOR, 'partial NOR sector')
        sectors.append({'physical_address': address, 'bytes': SECTOR,
                        'backup_sha256': sha(old), 'candidate_sha256': sha(new), 'differs': old != new})
    # This is a review ordering only. It is not asserted to make flash updates
    # atomic, and no sector is ever erased or programmed by this tool.
    ordered = [s['physical_address'] for s in sectors if s['differs'] and s['physical_address'] != MINI_START]
    if sectors[0]['differs']: ordered.append(MINI_START)
    require(len(set(ordered)) == len(ordered) and all(MINI_START <= a <= MINI_END-SECTOR for a in ordered),
            'write plan outside application partition')
    preserved = [
        ('factory_SPL_and_boot_configuration', 0, MINI_START),
        ('MINI_VM_complete_including_factory_staged_updater', MINI_END, 0xbe000),
        ('BTIF', 0xbe000, 0xbf000), ('USR', 0xbf000, 0xff000), ('key_mac', 0xff000, 0x100000)]
    composed = backup[:MINI_START] + image + backup[MINI_END:]
    for _, start, end in preserved:
        require(composed[start:end] == backup[start:end], 'preserved partition changed')
    require(composed[0xb7000:0xbd000] == backup[0xb7000:0xbd000], 'factory OTA area changed')
    output = output.resolve()
    require(output.is_relative_to(ROOT / 'build'), 'generated plan must stay under build/')
    output.mkdir(parents=True, exist_ok=True)
    rollback = output / 'stock-mini-app-area.bin'
    rollback.write_bytes(original)
    report = {'project': 'HyperRig', 'target': 'tank-mini', 'offline_only': True,
        'device_access_performed': False, 'write_commands_emitted': False, 'execution_ready': False,
        'candidate': {'path': spec['image_path'], 'sha256': sha(image), 'bytes': len(image)},
        'unit_backup': {'path': backup_path.resolve().relative_to(ROOT).as_posix(), 'sha256': sha(backup),
                        'bytes': len(backup), 'fresh_read_immediately_before_install_required': True},
        'rollback': {'path': rollback.relative_to(ROOT).as_posix(), 'sha256': sha(original), 'bytes': len(original)},
        'physical_write_allowlist': [MINI_START, MINI_END], 'sector_bytes': SECTOR,
        'sectors': sectors, 'changed_sectors': len(ordered), 'proposed_sector_order': ordered,
        'application_header_sector_last': True, 'power_loss_atomicity_proven': False,
        'preserved_regions': [{'name': name, 'range': [start, end], 'sha256': sha(backup[start:end])}
                              for name, start, end in preserved],
        'factory_OTA_preserved': True, 'hypothetical_full_image_sha256': sha(composed),
        'hypothetical_full_image_written_to_disk': False,
        'preconditions_not_satisfied_by_this_plan': [
            'Independent recovery trigger demonstrated on this MINI, including valid-image startup failure.',
            'Codec/board adaptations reviewed and current candidate explicitly qualified for first boot.',
            'Fresh device read agrees with the accepted preimage or differences have been reviewed.',
            'Bounded writer reviewed for this exact NOR and application-sector allowlist.',
            'Every programmed sector and final whole application verified by readback; exact rollback available.'],
        'source_sha256': sha(Path(__file__).read_bytes())}
    (output / 'install-plan.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware-manifest', type=Path, required=True)
    parser.add_argument('--backup', type=Path, default=ROOT / BACKUP_PATH)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/mini-install-plan')
    args = parser.parse_args()
    report = prepare(args.firmware_manifest, args.backup, args.output)
    print(json.dumps({k: report[k] for k in ('offline_only', 'execution_ready', 'changed_sectors',
                                           'physical_write_allowlist', 'factory_OTA_preserved', 'rollback')}))


if __name__ == '__main__': main()
