"""Build revision3 offline: retain v2 audio/entry bytes and extend its PC window.

The exact previously installed application is reproduced before adding the
single PC-limit immediate patch. No frozen v2 file is rebuilt or overwritten.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.jieli import unpack_app
from tools.audit_mini_ultrarig_port import (
    BinaryPatch, G_PATH, MINI_PATH, IDENTITY_PATCHES, VM_PATCH,
    FLASH_BASE, ENTRY, MINI_START, compose_candidate, pinned_inputs,
)
from tools.build_mini_app import build as build_editor

BASELINE = 'build/hyperrig-mini-audio-v2'
BASELINE_IMAGE = BASELINE+'/hyperrig-mini.app-area.bin'
BASELINE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
BASELINE_PINS = {
    BASELINE_IMAGE: BASELINE_SHA,
    BASELINE+'/integration-report.json': '2090029ce50b7610f140d0eb8aa63684311f24baa5915fd43d9bb68b7a9acb81',
    BASELINE+'/firmware-manifest.json': 'f119ab571a6cb04c8ca72513b5d18d614e079e756d209ce5794fbaeb4fe77d12',
    BASELINE+'/entry-recovery-manifest.json': '7477a0a10ae9ad7c5459432535873eb05105dc9b1065c76a1eb6f1c7cd4ca729',
    'build/mini-audio-port-v2/manifest.json': 'cbf4fb5a2f14aa0319983d62e4c787f5886a546eecaa4fa214af240359afeeda',
}
EDITOR_PINS = {
    'tools/build_mini_app.py': '529e9be717919c52659249d1732ba7e1c7916cfd35ba94562f59104c4f7f8176',
    'app/mini/board-profile.json': '1d2dff1f2e541e36191ee3e7cef1f2fcb6d65b2757331be2477a016978a11058',
    'app/mini/mini-profile.js': '237d6db737a23a24b91417c47d08c40b69f30556197b6de5e3ffb08d3cd04e23',
    'app/mini/mini-ui.js': 'b54aa4258391102ed66b06aeab21aa0936466d51c9e56afbaffb990837046007',
}
PHYSICAL_PROOF = {'path': 'build/mini-desktop-real-03/connected-proof.json',
                  'sha256': '96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_checked(name, expected):
    path = (ROOT/name).resolve()
    require(path.is_relative_to(ROOT), 'input leaves the workspace')
    raw = path.read_bytes()
    require(sha(raw) == expected, 'pinned input changed: '+name)
    return raw


def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')


def load_baseline():
    raw = {name: read_checked(name, expected) for name, expected in BASELINE_PINS.items()}
    integrated = json.loads(raw[BASELINE+'/integration-report.json'])
    manifest = json.loads(raw[BASELINE+'/firmware-manifest.json'])
    audio = json.loads(raw['build/mini-audio-port-v2/manifest.json'])
    recovery = json.loads(raw[BASELINE+'/entry-recovery-manifest.json'])
    pins = dict(BASELINE_PINS)
    # These are frozen target components. Do not run either component builder.
    for item in (audio, recovery):
        for name, expected in item['source_sha256'].items():
            read_checked(name, expected); pins[name] = expected
    audio_bytes = read_checked(audio['payload']['path'], audio['payload']['sha256'])
    read_checked(audio['elf']['path'], audio['elf']['sha256'])
    component = recovery['component']
    guard_bytes = read_checked(component['file'], component['payload_sha256'])
    read_checked(component['elf'], component['elf_sha256'])
    for name, expected in ((audio['payload']['path'], audio['payload']['sha256']),
                           (audio['elf']['path'], audio['elf']['sha256']),
                           (component['file'], component['payload_sha256']),
                           (component['elf'], component['elf_sha256'])):
        pins[name] = expected
    return {'image': raw[BASELINE_IMAGE], 'integration': integrated, 'manifest': manifest,
            'audio': audio, 'recovery': recovery, 'audio_bytes': audio_bytes,
            'guard_bytes': guard_bytes, 'pins': pins}


def compose_revision(baseline, g_raw, mini_raw):
    from firmware.mini.pc_limit_port.patches import pc_limit_patches, verify_candidate
    require(sha(baseline['image']) == BASELINE_SHA, 'baseline application is not installed revision2')
    gp, _, gf, *_ = pinned_inputs(g_raw, mini_raw)
    old_plain, old_entries, old_files = unpack_app(baseline['image'])
    old_record = baseline['integration']['composition']
    rows = old_record['patches']
    builtins = tuple(IDENTITY_PATCHES)+(VM_PATCH,)
    require(rows[:len(builtins)] == [p.record() for p in builtins], 'baseline builtin patch table changed')
    extra = tuple(BinaryPatch(p['name'], p['cpu_address'], bytes.fromhex(p['before_hex']),
                              bytes.fromhex(p['after_hex']), p['rationale']) for p in rows[len(builtins):])
    require([p.record() for p in extra] == rows[len(builtins):], 'baseline patch record bounds differ')
    original_size = len(gf['app.bin'])
    append = old_files['app.bin'][original_size:]
    append_address = ENTRY+original_size
    audio, recovery = baseline['audio'], baseline['recovery']
    component = recovery['component']
    audio_bytes, guard_bytes = baseline['audio_bytes'], baseline['guard_bytes']
    require(sha(audio_bytes) == audio['payload']['sha256'] and len(audio_bytes) == audio['payload']['bytes'],
            'audio payload differs from its frozen manifest')
    require(sha(guard_bytes) == component['payload_sha256'] and len(guard_bytes) == component['payload_bytes'],
            'entry guard payload differs from its frozen manifest')
    padding = b'\0' * ((-len(audio_bytes)) & 3)
    require(audio['payload']['base'] == append_address and
            component['address'] == append_address+len(audio_bytes)+len(padding),
            'frozen component addresses do not match actual append')
    require(append == audio_bytes+padding+guard_bytes, 'v2 append differs from audio plus entry guard')
    executable_end = append_address+len(append)
    require(executable_end == component['address']+len(guard_bytes) == component['end_exclusive'],
            'entry guard end differs from actual executable payload')
    require(executable_end == FLASH_BASE+old_record['cfg_tool_area_offset'], 'cfg starts inside executable append')
    rebuilt, previous = compose_candidate(g_raw, mini_raw, additional_patches=extra, append_code=append)
    require(rebuilt == baseline['image'] and previous == old_record,
            'cannot reproduce the exact installed v2 bytes and patch audit')
    patches = tuple(pc_limit_patches(gp, executable_end))
    require(len(patches) == 1 and patches[0].address == 0x0200067E and len(patches[0].before) == 6,
            'revision3 must add only the PC-limit li32 instruction')
    image, composition = compose_candidate(g_raw, mini_raw, additional_patches=extra+patches, append_code=append)
    pc_setup = verify_candidate(image, executable_end=executable_end, g_plain=gp)
    plain, entries, files = unpack_app(image)
    require(len(files['app.bin']) == len(old_files['app.bin']), 'revision3 changed application extent')
    require(files['app.bin'][original_size:] == append, 'revision3 changed the frozen append bytes')
    require(files['cfg_tool.bin'] == old_files['cfg_tool.bin'], 'revision3 changed cfg_tool')
    require([e.to_dict() for e in entries[2:]] == [e.to_dict() for e in old_entries[2:]],
            'revision3 changed cfg placement or partition geometry')
    restored = bytearray(files['app.bin'])
    allowed = set()
    for patch in patches:
        start = patch.address-ENTRY
        require(restored[start:start+len(patch.after)] == patch.after, 'PC patch output mismatch')
        restored[start:start+len(patch.before)] = patch.before
        allowed.update(range(start, start+len(patch.before)))
    changed = [i for i, (a, b) in enumerate(zip(old_files['app.bin'], files['app.bin'])) if a != b]
    require(changed and set(changed) <= allowed and bytes(restored) == old_files['app.bin'],
            'an undeclared application byte changed from v2')
    # The reset-copy constants share the old flash-end value. They are data
    # source addresses and MUST NOT be changed by the execution-window patch.
    for start in (0x1B8, 0x1DC):
        require(plain[start:start+6] == old_plain[start:start+6], 'RAM copy source was altered')
    require(composition['original_application_recovered_exactly_by_reversing_patches'] and
            composition['crc_and_layout_valid'], 'original-source inverse/CRC audit failed')
    sectors = []
    for offset in range(0, len(image), 4096):
        before, after = baseline['image'][offset:offset+4096], image[offset:offset+4096]
        if before != after:
            sectors.append({'physical_address': MINI_START+offset, 'bytes': len(after),
                            'before_sha256': sha(before), 'after_sha256': sha(after),
                            'changed_bytes': sum(a != b for a, b in zip(before, after))})
    require([s['physical_address'] for s in sectors] == [0x4000],
            'PC immediate and JLFS checksums must change only application sector0x4000')
    validation = {'baseline_reproduced_byte_exactly': True,
                  'baseline_image_sha256': BASELINE_SHA, 'new_PC_patches': [p.record() for p in patches],
                  'executable_end_from_actual_guard': executable_end,
                  'PC_limit_old_upper': 0x02056780, 'PC_limit_new_upper': executable_end,
                  'PC_limit_flash_lower_unchanged': 0x02000120,
                  'PC_limit_RAM_unchanged': [0x01C00000, 0x01C1F088],
                  'PC_limit_setup': pc_setup,
                  'original_RAM_copy_source_unchanged': 0x02056780,
                  'audio_payload_byte_identical': True, 'entry_guard_payload_byte_identical': True,
                  'audio_payload_sha256': sha(audio_bytes), 'entry_guard_payload_sha256': sha(guard_bytes),
                  'append_bytes': len(append), 'append_sha256': sha(append),
                  'only_declared_PC_instruction_changes_application': True,
                  'changed_application_CPU_bytes': [ENTRY+i for i in changed],
                  'inverse_PC_patch_recovers_v2_application_exactly': True,
                  'inverse_all_patches_recovers_original_G_exactly': True,
                  'JLFS_CRC_SFC_roundtrip_passed': True, 'cfg_and_partition_geometry_unchanged': True,
                  'changed_sectors_vs_v2': sectors, 'hardware_verified': False}
    return image, composition, validation


def build(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'build') and not output.exists(),
            'use a new output directory under build; frozen artifacts cannot be overwritten')
    baseline = load_baseline()
    for name, expected in EDITOR_PINS.items():
        read_checked(name, expected)
    g_raw, mini_raw = (ROOT/G_PATH).read_bytes(), (ROOT/MINI_PATH).read_bytes()
    image, composition, validation = compose_revision(baseline, g_raw, mini_raw)
    output.mkdir(parents=True)
    image_path = output/'hyperrig-mini.app-area.bin'
    image_path.write_bytes(image)
    guard_manifest = output/'entry-recovery-manifest.json'
    guard_manifest.write_bytes(read_checked(BASELINE+'/entry-recovery-manifest.json',
                                          BASELINE_PINS[BASELINE+'/entry-recovery-manifest.json']))
    recovery_binding = copy.deepcopy(baseline['manifest']['entry_recovery'])
    recovery_binding['manifest'] = relative(guard_manifest)
    recovery_binding['manifest_sha256'] = sha(guard_manifest.read_bytes())
    gates = [
        'Revision3 has not been executed on the physical MINI; its PC-window correction needs a new boot observation.',
        'Revision2 reached the real editor in safe mode after a CPU0 PC-limit exception at the audio shim; this is not an audio pass.',
        'Codec timing, DMA/sample rate and audible input/output still need physical qualification.',
        'Held-footswitch application recovery and cold-power boot remain untested.',
        'Preset edit/save/reload and Android BLE remain separate physical qualifications.',
        'Physical LED and knob mapping is incomplete.',
    ]
    manifest = copy.deepcopy(baseline['manifest'])
    manifest.update(revision=3, image_path=relative(image_path), image_sha256=sha(image),
                    hardware_verified=False, flashable=False, remaining_gates=gates,
                    entry_recovery=recovery_binding,
                    command_capabilities={}, family_capabilities={},
                    PC_limit_correction=validation,
                    previous_revision={'image_sha256': BASELINE_SHA, 'physical_editor_proof': PHYSICAL_PROOF,
                                       'exception': 'CPU0 DBG_MSG0x1000 PC-limit; RETI0x02076AAE',
                                       'hardware_observation_applies_to_revision3': False})
    for name in ('command_validation', 'family_validation', 'write_validation'):
        manifest.pop(name, None)
    manifest['capabilities'] = {'identity': True, 'read': True, 'write': False, 'panel': False}
    manifest_path = output/'firmware-manifest.json'
    write_json(manifest_path, manifest)
    app_report = build_editor(output/'app', manifest_path, output/'editor-report.json')
    profile = app_report['profile']
    require(profile['image_sha256'] == sha(image) and profile['capabilities']['read'] and
            not profile['capabilities']['write'] and not profile['capabilities']['panel'] and
            not profile['hardware_verified'] and not profile['command_capabilities'] and
            not profile['family_capabilities'], 'new editor capability/hash binding differs')
    sources = {**EDITOR_PINS, 'tools/build_mini_ultrarig_v3.py': sha(Path(__file__).read_bytes())}
    for name in ('tools/audit_mini_ultrarig_port.py', 'hyperrig/jieli.py',
                 'firmware/mini/pc_limit_port/patches.py'):
        sources[name] = sha((ROOT/name).read_bytes())
    groups = copy.deepcopy(baseline['integration']['patch_groups'])
    groups['PC_limit'] = [p['name'] for p in validation['new_PC_patches']]
    report = {'project': 'HyperRig', 'target': 'tank-mini', 'revision': 3,
              'kind': 'offline PC-window correction with frozen v2 audio and entry guard',
              'architecture': 'standalone-ultrarig-port', 'composition': composition,
              'patch_groups': groups, 'validation': validation, 'source_sha256': sources,
              'frozen_component_pins': baseline['pins'],
              'audio_manifest': baseline['integration']['audio_manifest'],
              'audio_manifest_sha256': baseline['integration']['audio_manifest_sha256'],
              'entry_recovery': recovery_binding, 'previous_revision_physical_proof': PHYSICAL_PROOF,
              'firmware_manifest': relative(manifest_path), 'firmware_manifest_sha256': sha(manifest_path.read_bytes()),
              'editor_report': relative(output/'editor-report.json'),
              'editor': relative(output/'app/web/tankmini.html'),
              'editor_sha256': sha((output/'app/web/tankmini.html').read_bytes()),
              'boot_verified_on_mini': False, 'audio_verified_on_mini': False,
              'read_capability_enabled_for_target_identity': True, 'write_capability_enabled': False,
              'flashable': False, 'device_access_performed': False, 'remaining_gates': gates}
    write_json(output/'integration-report.json', report)
    # Re-read retained artifacts after the build; none of the builders above may
    # overwrite the installed v2 work product or its compiled components.
    for name, expected in baseline['pins'].items():
        read_checked(name, expected)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/hyperrig-mini-audio-v3')
    args = parser.parse_args(argv)
    report = build(args.output)
    print(json.dumps({'image': report['firmware_manifest'], 'image_sha256': report['composition']['sha256'],
                      'app_bytes': report['composition']['app_bytes'],
                      'PC_limit_upper': report['validation']['PC_limit_new_upper'],
                      'changed_sectors_vs_v2': report['validation']['changed_sectors_vs_v2'],
                      'audio_and_guard_unchanged': True, 'hardware_verified': False}, indent=2))


if __name__ == '__main__':
    main()
