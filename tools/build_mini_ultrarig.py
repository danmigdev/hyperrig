"""Compose the complete original UltraRig G application for MINI, offline.

Every original-byte change is enumerated and invertible. The appended board
shim is compiled separately, followed by the mandatory entry recovery guard.
This tool also derives the MINI editor against
the exact image hash; it never connects to or writes a device.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_mini_ultrarig_port import (G_PATH, MINI_PATH, compose_candidate, pinned_inputs)
from tools.audit_mini_panel_port import panel_patches
from tools.audit_mini_boot_contract import boot_patches
from tools.build_mini_app import build as build_editor
from firmware.mini.audio_port.patches import audio_patches, verify_control_flow
from firmware.mini.audio_port.verify import inspect as inspect_audio
from tools.build_mini_entry_recovery_v2 import (APPEND_ORIGIN, build as build_recovery,
    patches as recovery_patches, bind_append)


def sha(data): return hashlib.sha256(data).hexdigest()
def require(condition, message):
    if not condition: raise ValueError(message)
def read_json(path): return json.loads(path.read_text(encoding='utf-8'))
def relative(path): return path.resolve().relative_to(ROOT).as_posix()
def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def build(output: Path, audio_manifest: Path):
    output = output.resolve()
    require(output.is_relative_to(ROOT / 'build'), 'output must stay inside build/')
    audio = read_json(audio_manifest)
    for name, expected in audio['source_sha256'].items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT) and sha(path.read_bytes()) == expected, f'audio source differs: {name}')
    elf = (ROOT / audio['elf']['path']).read_bytes()
    require(sha(elf) == audio['elf']['sha256'], 'audio ELF differs from manifest')
    payload, inspected = inspect_audio(elf, 0x02076aac, 0x0207de81)
    require(sha(payload) == audio['payload']['sha256'] and
            payload == (ROOT / audio['payload']['path']).read_bytes(), 'audio payload differs')
    require(inspected['symbols'] == audio['elf']['symbols'], 'audio entry symbols differ')
    g_raw, mini = (ROOT / G_PATH).read_bytes(), (ROOT / MINI_PATH).read_bytes()
    g_plain, *_ = pinned_inputs(g_raw, mini)
    # The allocator derives this location from the actual audio bytes. Keep
    # word alignment explicit so a future shim cannot leave a stale branch.
    require(len(payload) % 2 == 0, 'audio code must end on an instruction boundary')
    alignment_padding = b'\0' * ((-len(payload)) & 3)  # pi32v2 nop halfwords
    preceding_append = payload + alignment_padding
    recovery_address = APPEND_ORIGIN + len(preceding_append)
    recovery = build_recovery(recovery_address)
    recovery_payload = (ROOT / recovery['component']['file']).read_bytes()
    appended = bind_append(g_plain, preceding_append, recovery_payload, recovery)
    require(recovery['policy']['requires_initial_DIR_inputs'] is False and
            recovery['component']['BSS_bytes'] == recovery['component']['initialized_RAM_bytes'] == 0,
            'application recovery policy or RAM contract differs')
    groups = {'panel': tuple(panel_patches(g_plain)), 'boot': tuple(boot_patches(g_plain)),
              'audio': tuple(audio_patches(g_plain, inspected['symbols'])),
              'recovery': tuple(recovery_patches(g_plain, recovery_address))}
    require(len(groups['recovery']) == 1 and
            [p.record() for p in groups['recovery']] == recovery['patches'], 'mandatory recovery hook differs')
    require(verify_control_flow(groups['audio'], inspected['symbols']) == 42, 'audio hook flow differs')
    patches = tuple(p for group in groups.values() for p in group)
    image, composition = compose_candidate(g_raw, mini, additional_patches=patches, append_code=appended)
    # Run the independent formatter twice to catch inadvertent retained state.
    second, repeated = compose_candidate(g_raw, mini, additional_patches=patches, append_code=appended)
    require(second == image and repeated == composition, 'composition is not deterministic')
    require(composition['stock_mini_application_bytes_used'] == 0, 'stock application graft is outside the agreed goal')
    require(composition['crc_and_layout_valid'] and
            composition['original_application_recovered_exactly_by_reversing_patches'], 'image provenance/CRC validation')

    output.mkdir(parents=True, exist_ok=True)
    image_path = output / 'hyperrig-mini.app-area.bin'
    image_path.write_bytes(image)
    recovery_manifest_path = output / 'entry-recovery-manifest.json'
    write_json(recovery_manifest_path, recovery)
    recovery_binding = {
        'version': 2, 'mandatory': True, 'manifest': relative(recovery_manifest_path),
        'manifest_sha256': sha(recovery_manifest_path.read_bytes()),
        'address': recovery_address, 'end_exclusive': recovery['component']['end_exclusive'],
        'payload_bytes': len(recovery_payload), 'payload_sha256': sha(recovery_payload),
        'preceding_audio_bytes': len(payload), 'alignment_padding_bytes': len(alignment_padding),
        'actual_preceding_payload_validated': True, 'requires_initial_DIR_inputs': False,
        'cold_entry_verified_on_mini': False, 'valid_image_hang_recovery_verified': False,
        'damaged_header_entry_or_guard_covered': False,
        'physical_key_and_reset_qualification': 'Separate HYK1 evidence; not inferred as a full application boot.',
    }
    gates = ['Full application has not booted on the physical MINI.',
             'Codec preconditions, nominal 48kHz timing and analog audio remain to be qualified.',
             'The application entry guard has not run on cold boot; physical HYK1 key/reset qualification is separate.',
             'A damaged application header, entry or guard is outside the footswitch guard coverage.',
             'Preset read/write through the adapted application has not been demonstrated.',
             'Physical LED and knob mapping remains incomplete.']
    firmware_manifest = {
        'project': 'HyperRig', 'target': 'tank-mini', 'architecture': 'standalone-ultrarig-port',
        'firmware_version': 'tankm_fw M5.71 rel ble', 'image_path': relative(image_path),
        'image_sha256': sha(image), 'image_kind': 'MINI application area, not complete NOR or FWSC',
        'capabilities': {'identity': True, 'read': True, 'write': False, 'panel': False},
        'hardware_verified': False, 'flashable': False, 'remaining_gates': gates,
        'original_application': {'path': G_PATH, 'sha256': sha(g_raw), 'model': 'UltraRig G alpha11 v2 M5.71'},
        'stock_MINI_application_used': False,
        'SPL_and_unit_partitions_included': False,
        'audio_shim': {'manifest': relative(audio_manifest), 'sha256': sha(audio_manifest.read_bytes()),
                       'codec_script': audio['codec_script']},
        'entry_recovery': recovery_binding,
    }
    manifest_path = output / 'firmware-manifest.json'
    write_json(manifest_path, firmware_manifest)
    app_report = build_editor(output / 'app', manifest_path, output / 'editor-report.json')
    profile = app_report['profile']
    require(profile['image_sha256'] == sha(image) and profile['capabilities']['read'] and
            not profile['capabilities']['write'] and not profile['hardware_verified'], 'editor capability binding differs')
    paths = sorted(set(['tools/build_mini_ultrarig.py', 'tools/audit_mini_ultrarig_port.py',
             'tools/audit_mini_panel_port.py', 'tools/audit_mini_boot_contract.py',
             'tools/build_mini_app.py', 'app/mini/board-profile.json',
             'app/mini/mini-profile.js', 'app/mini/mini-ui.js', *recovery['source_sha256']]))
    report = {'project': 'HyperRig', 'target': 'tank-mini', 'kind': 'integrated offline candidate',
        'architecture': 'standalone-ultrarig-port', 'goal': 'docs/HYPERRIG_GOAL.md',
        'composition': composition, 'patch_groups': {name: [p.name for p in group] for name, group in groups.items()},
        'source_sha256': {name: sha((ROOT / name).read_bytes()) for name in paths},
        'audio_manifest': relative(audio_manifest), 'audio_manifest_sha256': sha(audio_manifest.read_bytes()),
        'entry_recovery': recovery_binding,
        'editor_report': relative(output / 'editor-report.json'),
        'firmware_manifest': relative(manifest_path), 'firmware_manifest_sha256': sha(manifest_path.read_bytes()),
        'editor': relative(output / 'app/web/tankmini.html'),
        'editor_sha256': sha((output / 'app/web/tankmini.html').read_bytes()),
        'read_capability_enabled_for_target_identity': True, 'write_capability_enabled': False,
        'boot_verified_on_mini': False, 'audio_verified_on_mini': False,
        'flashable': False, 'device_access_performed': False, 'remaining_gates': gates}
    write_json(output / 'integration-report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/hyperrig-mini-integrated')
    parser.add_argument('--audio-manifest', type=Path, default=ROOT / 'build/mini-audio-port/manifest.json')
    parser.add_argument('--report', type=Path, default=ROOT / 'research/mini-integrated-port.json')
    args = parser.parse_args()
    report = build(args.output, args.audio_manifest)
    report_path = args.report.resolve()
    require(report_path.is_relative_to(ROOT), 'report must stay in workspace')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(report_path, report)
    print(json.dumps({'image': report['firmware_manifest'], 'image_sha256': report['composition']['sha256'],
                      'bytes': report['composition']['bytes'], 'patches': len(report['composition']['patches']),
                      'appended_bytes': report['composition']['appended_code']['bytes'],
                      'editor': report['editor'], 'flashable': False}))


if __name__ == '__main__': main()
