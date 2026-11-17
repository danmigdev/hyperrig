"""Audit the offline storage-platform closure while retaining inventory20.

Bind whole bodies, original call sites, exact instruction windows and primary
CPU records. Mutable mailbox bytes are auxiliary evidence, never code/data
exclusions. Interrupt activation and MMIO/lock completion remain fixtures.
"""
from __future__ import annotations
import argparse
import copy
import functools
import json
import re
from pathlib import Path

from inventory_reverse import (Inventory, ROOT, REFERENCE, REFERENCE_SHA, APP,
    address, hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_effects import declared_constants
from inventory_reverse_integrations import REQUIRED_OPTIONS
from inventory_reverse_parameter_construction import span, static_identity
from inventory_reverse_storage_runtime import keyed, pc_set
from inventory_reverse_effect_setup import (EffectSetupInventory,
    REPORT as SETUP_REPORT, PRESERVED_REPORTS as INVENTORY19_REPORTS)

ADAPTER = 'tools/inventory_reverse_storage_platform.py'
MODEL = 'tools/storage_platform_machine.py'
REPORT = 'build/reverse-storage-platform-02/verification.json'
REPORT_SHA = '82bb5477eff5ce088e14ab9d13463fc11033a34725f011700b4c56264c33136b'
MANIFEST_SHA = 'c20b96bf5512cdddc74be7ebf88351609ebb9188159c6a149748aee6403a7087'
PRESERVED_REPORTS = (*INVENTORY19_REPORTS, SETUP_REPORT)
REGIONS = {
    'gate_disable': (0x02000558, 0x02000564), 'gate_enable': (0x02000564, 0x02000570),
    'register': (0x020005ac, 0x02000604), 'peer_stop': (0x01c010e4, 0x01c01108),
    'enter': (0x01c01108, 0x01c011c2), 'peer_resume': (0x01c011c2, 0x01c011da),
    'leave': (0x01c011da, 0x01c01234), 'interrupt': (0x01c041dc, 0x01c04256),
    'clock': (0x01c04862, 0x01c0486c),
}
REUSED = {'irq_enter': (0x01c00e2e, 0x01c00e46), 'irq_leave': (0x01c00e46, 0x01c00e62)}
DIRECT_SITES = {
    0x020005d0: 0x02000558, 0x02000600: 0x02000564, 0x01c0112e: 0x01c00e2e,
    0x01c0117c: 0x01c010e4, 0x01c01188: 0x01c00e2e, 0x01c01208: 0x01c011c2,
    0x01c0122c: 0x01c00e46, 0x01c041f4: 0x01c00e2e, 0x01c0424a: 0x01c00e46,
}
INDIRECT_SITES = {0x01c04230: 1, 0x01c04248: 1}
CPU_SITES = {
    0x02000558: ('mov.r_sr', 'r0 = icfg', '96c39792fc117678a252a3bbdb0965b6fca1cc46f3ec9531dc996ec86df9f831'),
    0x0200055e: ('mov.sr_r', 'icfg = r0', '8948fcb2999e71b7151303e34ccf1eee146fdf3b68cfe36a56f6160b7e6c90b2'),
    0x01c01150: ('mov.r_sr', 'r2 = cnum', '5c4f83609cb9b2b891a97d08988aa3b4d10aaf4a360e7fa287d905e7e2f82abf'),
    0x01c011a2: ('lockset', 'lockset', '398eef4f8687d73b1c0b5a1016f6705ce8d27414cd30a6a7a4ced119a6dbe236'),
    0x01c011c2: ('if.ne.ri.s12', 'if (r0 != 0) {', '84cdd167cef234fb73ddffdb1fad7e6e97f1ea6d09eb0da3dcfc2f9e203b66a5'),
    0x01c0122a: ('lockclr', 'lockclr', 'ba742d566bcd5641fa6a6ec08be54f0e29e6c089d0f9bde7ddb85b80b54a3a68'),
    0x01c041dc: ('push.srl', '[--sp] = {psr, rets, reti}', '9bf1c736d8843c44c13c44774381dfed3fe35952b0480f89cb98896588e44638'),
    0x01c041de: ('push.rmask', '[--sp] = {r4-r0}', 'db0e62b92425325e40866fd2bf89d1958d00c9c2c89be8b1aa2c0fc24fd762a6'),
    0x01c0424e: ('pop.rmask', '{r4-r0} = [sp++]', 'b09b0f282aaa3dd705e969cccd6a3314210da105201ae678915c27ef2349450b'),
    0x01c04252: ('pop.srl', '{psr, rets, reti} = [sp++]', '6d82692ede6b632f707ddab144f932edf785a66e9b0d58262c18586845abb73a'),
    0x01c04254: ('rti', 'rti', '60b30bb88c378ca30c6c9ac72312b0840171c70490b5da28d0a6f788cde824ee'),
    0x01c00e2e: ('cli', 'cli', '6e7ec874c2902d32ad705a7b05ffc762bf45d9bf802d428ec530732caa437412'),
    0x01c00e5e: ('sti', 'sti', '864f15571e33e214e973e089ef6071d325403f5da9d0d39eac8f0c5dfed1cd6c'),
}
INITIAL = (0x01c1fc40, 0x01c1fc54,
    'de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90')
INITIAL_ROLE = 'mutable initialized mailbox and lock depths, not immutable data'
MMIO = ((0x00010704, 0x00010708), (0x01eee000, 0x01eee00c),
    (0x01eef100, 0x01eef180), (0x01eef1a0, 0x01eef1a8), (0x01eef300, 0x01eef380))
MINI = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'


def registry_evidence(report, constants):
    if (report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA
        or type(report.get('new_original_functions')) is not int or report['new_original_functions'] != 9
        or report.get('new_data_exclusions') != []):
        raise ValueError('platform requires nine new bodies and no data exclusion for the pinned image')
    for key, expected in (('functions', REGIONS), ('reused_functions', REUSED)):
        if {name: span(item) for name, item in report[key].items()} != expected:
            raise ValueError('platform whole-body registry changed')
    for key, expected in (('REGIONS', REGIONS), ('REUSED', REUSED), ('DIRECT_SITES', DIRECT_SITES),
            ('INDIRECT_SITES', INDIRECT_SITES), ('INITIAL_MAILBOX', INITIAL), ('MMIO', MMIO),
            ('ISA_SITES', {pc: item[0] for pc, item in CPU_SITES.items()}),
            ('ISA_RECORD_SHA256', {hex(pc): item[2] for pc, item in CPU_SITES.items()})):
        if constants.get(key) != expected: raise ValueError('platform model declaration changed: '+key)
    if any(report.get(key) is not False for key in ('hardware_test', 'device_access', 'audio_test', 'firmware_changed')):
        raise ValueError('platform offline evidence cannot become a hardware or firmware-change claim')
    if report['mini_binding'] != {'sha256': MINI, 'complete_regions': 11, 'instructions': 217, 'auxiliary_mutable_bytes': 20}:
        raise ValueError('platform reviewed MINI binding changed')


def runtime_evidence(report, constants, raw, decode, regions, data_ranges, isa):
    registry_evidence(report, constants)
    canonical, new_pcs, per_function = {}, set(), {}
    for key in ('functions', 'reused_functions'):
        for name, item in report[key].items():
            a, b = span(item); parent = regions.get((a, b)); body = decode(a, b)
            if (parent is None or parent['kind'] != 'function_region'
                or parent['sha256'] != item['bytes_sha256'] or sha(raw(a, b)) != item['bytes_sha256']
                or type(item['bytes']) is not int or item['bytes'] != b-a
                or type(item['instructions']) is not int or item['instructions'] != len(body)
                or type(item['visited_instructions']) is not int or item['visited_instructions'] != len(body)):
                raise ValueError('platform body bytes, parent, whole extent or coverage changed')
            pcs = {pc for pc, _, _ in body}
            if pcs & canonical.keys(): raise ValueError('platform body declarations overlap')
            if any(a < y and x < b for x, y, _ in data_ranges):
                raise ValueError('platform executable body overlaps a data exclusion')
            canonical.update({pc: (size, text) for pc, size, text in body})
            if key == 'functions': new_pcs.update(pcs)
            per_function[name] = {'decoded': len(pcs), 'visited': len(pcs), 'unvisited': 0,
                'reused': key == 'reused_functions'}
    coverage = report['instruction_coverage']
    expected = {'new_decoded': 200, 'new_visited': 200, 'all_decoded': 217, 'all_visited': 217}
    if (len(new_pcs) != 200 or len(canonical) != 217
        or any(type(coverage[k]) is not int or coverage[k] != v for k, v in expected.items())
        or coverage['unvisited_new'] != [] or coverage['unvisited_all'] != [] or report['gap_instructions'] != {}):
        raise ValueError('platform coverage differs from the canonical complete closure')
    visited = pc_set(report['visited'], set(canonical), 'platform visited PCs')
    if visited != canonical.keys(): raise ValueError('platform coverage omits a canonical instruction')
    windows = keyed(report['loaded_instruction_windows'], 'platform instruction windows')
    if windows.keys() != canonical.keys(): raise ValueError('platform loaded window set differs from complete bodies')
    for pc, item in windows.items():
        size, _ = canonical[pc]
        if type(item['bytes']) is not int or item['bytes'] != size or sha(raw(pc, pc+size)) != item['sha256']:
            raise ValueError('platform loaded window is not one exact original instruction')
    direct, indirect = {}, {}
    for pc, (size, text) in canonical.items():
        if match := re.fullmatch(r'call (-?\d+)', text): direct[pc] = pc+size+int(match[1])
        elif text.startswith('call '):
            if text != 'call r1': raise ValueError('platform original indirect register changed')
            indirect[pc] = 1
    if direct != DIRECT_SITES or indirect != INDIRECT_SITES:
        raise ValueError('platform original direct or indirect site registry changed')
    recorded = keyed(report['direct_sites'], 'platform direct sites')
    if recorded.keys() != direct.keys(): raise ValueError('platform reported direct call set changed')
    entries = {a for a, _ in (*REGIONS.values(), *REUSED.values())}
    for pc, target in direct.items():
        item = recorded[pc]
        if address(item['target']) != target or item['visited'] is not True or pc not in visited or target not in visited or target not in entries:
            raise ValueError('platform direct call or complete callee entry is not authenticated and visited')
    recorded = keyed(report['indirect_sites'], 'platform indirect sites')
    if recorded.keys() != indirect.keys(): raise ValueError('platform reported indirect call set changed')
    for pc, arity in indirect.items():
        item = recorded[pc]
        if type(item['arity']) is not int or item['arity'] != arity or item['visited'] is not True or pc not in visited:
            raise ValueError('platform external indirect site lost its one-word ABI or execution evidence')
    records = keyed(report['cpu_primary_evidence'], 'platform primary ISA records')
    if records.keys() != CPU_SITES.keys(): raise ValueError('platform primary ISA evidence set changed')
    for pc, (identifier, text, digest) in CPU_SITES.items():
        size, decoded_text = canonical[pc]
        found = codec.decode(isa, raw(pc, pc+size), 0)
        if found is None: raise ValueError('undecoded platform CPU observation')
        instruction, fields, decoded_size = found
        original = {'id': instruction.id, 'decoded': codec.format(instruction, fields),
            'summary': instruction.summary, 'notes': instruction.notes,
            'status': instruction.status, 'sources': instruction.sources}
        canonical_hash = sha(json.dumps(original, sort_keys=True, separators=(',', ':')).encode())
        if (decoded_size != size or decoded_text != text or instruction.id != identifier
            or original['decoded'] != text or canonical_hash != digest or records[pc] != original):
            raise ValueError('platform CPU instruction or local primary record changed')
    witness = report['auxiliary_initial_state']; a, b, digest = INITIAL
    if (static_identity(witness) != INITIAL or witness.get('classification') != INITIAL_ROLE
        or raw(a, b) != bytes(20) or sha(raw(a, b)) != digest
        or any(a < y and x < b for x, y, _ in data_ranges)):
        raise ValueError('platform mutable mailbox witness changed or became a data exclusion')
    return {'new_whole_functions': 9, 'reused_whole_functions': 2, **expected,
        'canonical_instruction_windows': len(windows), 'direct_internal_sites': len(direct),
        'indirect_external_sites': {hex_address(pc): arity for pc, arity in indirect.items()},
        'CPU_primary_records': len(records), 'CPU_observations_are_synthetic': True,
        'separate_interrupt_activation_is_supplied': True,
        'interrupt_delivery_or_lock_scheduling_proven': False,
        'auxiliary_mutable_initial_state': witness, 'new_data_exclusions': 0,
        'per_function': per_function}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 62 or len(set(PRESERVED_REPORTS)) != 62:
        raise ValueError('inventory20 must retain exactly 62 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('platform inventory omitted or duplicated earlier report evidence')


class StoragePlatformInventory(EffectSetupInventory):
    def __init__(self, *required, storage_platform_report, additional_reports=(), **options):
        if local(storage_platform_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen storage-platform02')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if REPORT in additions: raise ValueError('platform report is already explicitly selected')
        self.platform_runtime = None
        super().__init__(*required, additional_reports=[*additions, REPORT], **options)

    def reports(self):
        omitted = super().reports(); self.audit_manifest(REPORT, MANIFEST_SHA)
        raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen platform report changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report['source_sha256'].get(MODEL) != sha(source): raise ValueError('platform model source changed')
        constants = declared_constants(source.decode('utf-8'))
        self.platform_runtime = runtime_evidence(report, constants, self.raw, self.decode,
            self.regions, self.data_ranges, self.instructions)
        module = next(item for item in self.modules if item['report'] == REPORT)
        module.update(reported_region_coverage=self.platform_runtime['per_function'],
            storage_platform_runtime_evidence=self.platform_runtime)
        return omitted

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=19, storage_platform_inventory_adapter=ADAPTER,
            storage_platform_runtime_evidence=self.platform_runtime)
        report['audits'].update(inventory20_all_sixty_two_reports_retained=True,
            platform_complete_new_and_reused_bodies_and_canonical_windows_bound=True,
            platform_direct_calls_and_reused_entries_independently_decoded_and_visited=True,
            platform_indirect_sites_retain_external_one_word_ABI=True,
            platform_primary_ISA_records_independently_decoded=True,
            platform_mailbox_initial_state_remains_auxiliary_mutable=True,
            platform_adds_no_data_exclusions=True)
        report['scope_policy'].extend([
            'storage platform adds nine complete bodies and reuses two existing IRQ helpers without duplicate function entries',
            'all 217 canonical instruction windows, nine direct sites, two indirect one-word ABIs and thirteen primary CPU records are authenticated',
            'the twenty initialized mailbox/lock-depth bytes remain auxiliary mutable state and add no data exclusion',
            'the ISR executes a separate supplied context and explicit native RTI; interrupt delivery, lock completion and MMIO values remain synthetic fixtures',
            'all inventory20 policies remain, including the exact eight-byte setup prefix supersession and the remaining unclassified two-byte tail',
            'offline platform evidence does not establish hardware scheduling, inter-core fairness, storage durability or whole-firmware execution'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject changed evidence without deriving an inventory or rerunning firmware."""
    packed, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(packed) != REFERENCE_SHA or unpack_app(packed)[2]['app.bin'] != app:
        raise ValueError('self-check original image changed')
    prior = json.loads(local('build/reverse-inventory-20/inventory.json').read_bytes())
    if set(prior['selected_reports']) != set(PRESERVED_REPORTS):
        raise ValueError('self-check inventory20 report set changed')
    inv = object.__new__(Inventory); inv.app = app; inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    inv.data_ranges = [(address(item['start']), address(item['end_exclusive']), item['kind'])
        for item in prior['known_data_ranges']]
    raw_report = local(REPORT).read_bytes()
    if sha(raw_report) != REPORT_SHA or sha(local(REPORT).with_name('build-manifest.json').read_bytes()) != MANIFEST_SHA:
        raise ValueError('self-check frozen platform report/manifest changed')
    report = json.loads(raw_report); model = local(MODEL).read_bytes()
    if sha(model) != report['source_sha256'][MODEL]: raise ValueError('self-check platform model changed')
    constants = declared_constants(model.decode())
    regions = {span(item): item for item in prior['reconstructed_regions']}
    for item in report['functions'].values():
        if span(item) in regions: raise ValueError('platform new body was already counted')
        regions[span(item)] = {'kind': 'function_region', 'sha256': item['bytes_sha256']}
    decode = functools.lru_cache(None)(inv.decode); raw = functools.lru_cache(None)(inv.raw)
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError, IndexError): checks += 1; return
        raise AssertionError('invalid platform evidence accepted')
    def audit(item): return runtime_evidence(item, constants, raw, decode, regions, inv.data_ranges, inv.instructions)
    registry_evidence(report, constants); checks += 1
    assert audit(report)['all_visited'] == 217; checks += 1
    for key in ('functions', 'reused_functions'):
        for name in report[key]:
            for field, value in [('start', 0), ('end_exclusive', 0), ('bytes', True),
                    ('bytes_sha256', '0'*64), ('instructions', 0), ('visited_instructions', False)]:
                changed = copy.deepcopy(report); changed[key][name][field] = value; rejected(audit, changed)
    paths = [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64), ((), 'new_original_functions', True),
        ((), 'new_original_functions', 11), ((), 'new_data_exclusions', [INITIAL[:2]]),
        ((), 'visited', report['visited'][:-1]), ((), 'visited', report['visited']+[report['visited'][0]]),
        ((), 'visited', ['0x02000559', *report['visited'][1:]]), ((), 'gap_instructions', {'0x02000558': 'missing'}),
        (('instruction_coverage',), 'new_visited', 199), (('instruction_coverage',), 'all_decoded', True),
        (('instruction_coverage',), 'all_visited', 216), (('instruction_coverage',), 'unvisited_new', [0x02000558]),
        (('instruction_coverage',), 'unvisited_all', [0x01c00e2e]), ((), 'hardware_test', True),
        ((), 'device_access', True), ((), 'audio_test', True), ((), 'firmware_changed', True),
        (('mini_binding',), 'sha256', '0'*64), (('mini_binding',), 'auxiliary_mutable_bytes', 24),
        (('auxiliary_initial_state',), 'start', INITIAL[0]-4),
        (('auxiliary_initial_state',), 'end_exclusive', INITIAL[1]+4),
        (('auxiliary_initial_state',), 'sha256', '0'*64),
        (('auxiliary_initial_state',), 'classification', 'immutable table'),
        ((), 'direct_sites', {}), ((), 'indirect_sites', {}), ((), 'cpu_primary_evidence', {}),
        ((), 'loaded_instruction_windows', {}),
    ]
    for path, key, value in paths:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(audit, changed)
    for pc in report['loaded_instruction_windows']:
        changed = copy.deepcopy(report); changed['loaded_instruction_windows'][pc]['sha256'] = '0'*64; rejected(audit, changed)
    key = next(iter(report['loaded_instruction_windows']))
    for width in (0, True, report['loaded_instruction_windows'][key]['bytes']+2):
        changed = copy.deepcopy(report); changed['loaded_instruction_windows'][key]['bytes'] = width; rejected(audit, changed)
    for field in ('loaded_instruction_windows', 'direct_sites', 'indirect_sites', 'cpu_primary_evidence'):
        changed = copy.deepcopy(report); key = next(iter(changed[field])); changed[field][str(address(key))] = changed[field][key]
        rejected(audit, changed)
    for pc in DIRECT_SITES:
        for field, value in [('target', '0x02000000'), ('visited', False), ('visited', 1)]:
            changed = copy.deepcopy(report); changed['direct_sites'][hex(pc)][field] = value; rejected(audit, changed)
    for pc in INDIRECT_SITES:
        for field, value in [('arity', True), ('arity', 0), ('arity', 2), ('visited', False), ('visited', 1)]:
            changed = copy.deepcopy(report); changed['indirect_sites'][hex(pc)][field] = value; rejected(audit, changed)
    for pc in CPU_SITES:
        for field in ('id', 'decoded', 'notes', 'summary', 'status', 'sources'):
            changed = copy.deepcopy(report); changed['cpu_primary_evidence'][hex(pc)][field] = 'altered'; rejected(audit, changed)
    for bounds in (*REGIONS.values(), *REUSED.values()):
        changed = copy.deepcopy(regions); changed.pop(bounds)
        rejected(runtime_evidence, report, constants, raw, decode, changed, inv.data_ranges, inv.instructions)
        changed = copy.deepcopy(regions); changed[bounds]['kind'] = 'fragment'
        rejected(runtime_evidence, report, constants, raw, decode, changed, inv.data_ranges, inv.instructions)
    for key in ('REGIONS', 'REUSED', 'DIRECT_SITES', 'INDIRECT_SITES', 'INITIAL_MAILBOX', 'MMIO', 'ISA_SITES', 'ISA_RECORD_SHA256'):
        changed = copy.deepcopy(constants); changed[key] = {}; rejected(registry_evidence, report, changed)
    for start, end in (INITIAL[:2], REGIONS['register']):
        rejected(runtime_evidence, report, constants, raw, decode, regions,
            [*inv.data_ranges, (start, end, 'invented_platform_data')], inv.instructions)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 62,
        'new_whole_functions': 9, 'new_data_exclusions': 0, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report', 'storage_coordination_report',
        'sample_processing_report', 'storage_runtime_report', 'effect_setup_report', 'storage_platform_report')
    for name in names: parser.add_argument('--'+name.replace('_', '-'))
    parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true'); args = parser.parse_args()
    required = tuple(getattr(args, name.replace('-', '_')) for name in REQUIRED_OPTIONS)
    extra = {name: getattr(args, name) for name in names}
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report or any(extra.values()):
            parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required) or not all(extra.values()):
        parser.error('choose --output or --check and provide every required report')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a fresh directory under build/')
    report = StoragePlatformInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'storage-platform-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'storage_platform_runtime_evidence': {k: v for k, v in report['storage_platform_runtime_evidence'].items()
            if k != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
