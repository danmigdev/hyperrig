"""Verify local originals and catalogue editable/recovered material offline."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

def item(path, expected=None):
    path = Path(path)
    data = (ROOT / path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError(f'original differs from pinned hash: {path}')
    return {'path': path.as_posix(), 'bytes': len(data), 'sha256': digest,
            'compared_with_pinned_original': expected is not None}


def main():
    inputs = json.loads((ROOT / 'research/input-manifest.json').read_text(encoding='utf-8'))
    originals = []
    for asset in inputs['release']['assets']:
        originals.append(dict(item(Path('artifacts/alpha11') / asset['name'], asset['sha256']),
                              url=asset['url'], kind='original release package'))
    for firmware in inputs['firmware_images']:
        originals.append(dict(item(firmware['path'], firmware['sha256']), kind='original firmware image'))
    recovered = []
    for directory, patterns, status in (
        ('recovered/ultrarig-original', ('web/*.html', 'web/*.js', '*.md'), 'original shipped HTML/JavaScript and licences'),
        ('recovered/android', ('assets/public/*.html', 'assets/public/*.js', 'assets/*.json'), 'original APK assets'),
        ('recovered/installer', ('*.marshal', '*.dis.txt', '*.constants.json'), 'Python bytecode/disassembly, not original Python source'),
        ('recovered/ghidra', ('tank-g-*/decompiled.c', 'tank-b-*/decompiled.c', 'tank-g-*/functions.tsv', 'tank-b-*/functions.tsv'),
         'inferred decompiler output, not a compilable firmware project')):
        for pattern in patterns:
            for path in sorted((ROOT / directory).glob(pattern)):
                recovered.append(dict(item(path.relative_to(ROOT)), status=status))
    if not originals or len([r for r in recovered if r['path'].endswith('decompiled.c')]) != 4:
        raise ValueError('expected original G/B packages and all four firmware decompilations')
    report = {'project': 'HyperRig', 'release': inputs['release']['tag'], 'originals': originals,
        'recovered': recovered, 'originals_modified': False, 'network_access_performed': False,
        'complete_original_firmware_C_sources_recovered': False,
        'complete_original_installer_Python_sources_recovered': False,
        'editable_components': [
            {'component': 'MINI integral firmware port', 'paths': ['firmware/mini/audio_port',
                'tools/audit_mini_panel_port.py', 'tools/audit_mini_boot_contract.py', 'tools/audit_mini_ultrarig_port.py'],
             'build': 'python -B -X utf8 firmware/mini/audio_port/verify.py; python -B -X utf8 tools/build_mini_ultrarig.py',
             'status': 'Original binary application with explicit invertible patches and compiled board shim'},
            {'component': 'Native A2 DSP reconstruction', 'paths': ['firmware/src', 'firmware/include'],
             'build': 'python tools/build_native.py',
             'status': 'Compilable reconstructed three-channel int32 path; other firmware remains binary'},
            {'component': 'MINI editor', 'paths': ['app/mini', 'tools/build_mini_app.py'],
             'build': 'python tools/build_mini_app.py',
             'status': 'Full shipped original editor with explicit MINI source overlays'},
            {'component': 'G/B Windows packages and Android copy', 'paths': ['hyperrig/branding.py', 'tools/rebrand.py'],
             'build': 'python tools/rebrand.py --android',
             'status': 'Rebuilt binary/source packages; these are distinct from MINI hardware support'}],
        'provenance_and_licences': 'docs/PROVENIENZA.md',
        'scope': 'Verified local copies and explicit edit routes; not proof of complete reverse engineering or MINI boot.'}
    (ROOT / 'research/local-source-inventory.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'originals_verified': len(originals), 'recovered_files_catalogued': len(recovered),
                      'complete_original_firmware_C_sources_recovered': False}))


if __name__ == '__main__': main()
