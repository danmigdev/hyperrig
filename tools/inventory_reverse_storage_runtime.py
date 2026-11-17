"""Audit storage runtime joins without adding functions or data exclusions.

Keep every inventory18 report. Bind the exact preparation/control/coordination
union, canonical instruction windows, inherited CPU records and private-state
evidence without borrowing execution coverage from the separate parent corpora.
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
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_integrations import REQUIRED_OPTIONS
from inventory_reverse_parameter_construction import span, static_identity
from inventory_reverse_lifecycle import STORAGE_REPORT, STORAGE_SHA
from inventory_reverse_storage_control import REPORT as CONTROL_REPORT, REPORT_SHA as CONTROL_SHA
from inventory_reverse_storage_coordination import (REPORT as COORDINATION_REPORT,
    REPORT_SHA as COORDINATION_SHA, CPU_SITES)
from inventory_reverse_sample_processing import (SampleProcessingInventory,
    REPORT as SAMPLE_REPORT, PRESERVED_REPORTS as INVENTORY17_REPORTS)

ADAPTER = 'tools/inventory_reverse_storage_runtime.py'
MODEL = 'tools/storage_runtime_machine.py'
REPORT = 'build/reverse-storage-runtime-01/verification.json'
REPORT_SHA = 'dc170cdf97207efa912e242a03f712ccc7cfd5ceafd9fda22283bfb6524b5454'
MANIFEST_SHA = '03ae57ab91eeb21583cd47b668677305b4832e2fd08c5bf559ce4a451d593b16'
PRESERVED_REPORTS = (*INVENTORY17_REPORTS, SAMPLE_REPORT)
PARENT_REPORTS = {'preparation': (STORAGE_REPORT, STORAGE_SHA),
    'control': (CONTROL_REPORT, CONTROL_SHA),
    'coordination': (COORDINATION_REPORT, COORDINATION_SHA)}
PARENT_SOURCES = {
    'firmware/src/hyperrig_preset_storage_preparation.c':
        '553d68066bc3337883cb02025c139dcdedc59f4649c60dba98e0e2629b8257cf',
    'firmware/src/hyperrig_storage_control.c':
        '7a7fdf7fcfb6bb4af30101694f0dd4a5dfd613661c9a097e59f3aeba0b026238',
    'firmware/src/hyperrig_storage_coordination.c':
        '8b38e68971db73c27c54eae0fbfe6daf6fef59c1c335c9780d0f713cf0db5aa3',
}
JOINS = {
    0x02002876: (0x02002810, 3), 0x02002dc2: (0x02002772, 0),
    0x02002dc6: (0x02002bcc, 0), 0x02002dd2: (0x02002786, 1),
    0x02002de4: (0x02002b80, 3), 0x02002df2: (0x02002786, 1),
    0x02002f36: (0x02002772, 0), 0x02002f3a: (0x02002bcc, 0),
    0x02002f40: (0x02002786, 1), 0x02002f74: (0x02002ef2, 4),
    0x02002fa2: (0x02002786, 1), 0x02002dcc: (0x02002d06, 1),
    0x02002dee: (0x02002d70, 3), 0x02002e02: (0x02002d06, 1),
    0x02002e12: (0x02002920, 0), 0x02002f9a: (0x02002d70, 3),
    0x020034bc: (0x02002d10, 3), 0x0200795c: (0x02002d10, 3),
}


def keyed(values, label):
    result = {}
    for key, value in values.items():
        pc = address(key)
        if pc in result: raise ValueError(label+' has duplicate address identities')
        result[pc] = value
    return result


def pc_set(values, allowed, label):
    pcs = [address(value) for value in values]
    if len(pcs) != len(set(pcs)) or not set(pcs) <= allowed:
        raise ValueError(label+' contains duplicate or noncanonical instruction starts')
    return set(pcs)


def services(values):
    result = {}
    for pc, item in keyed(values, 'storage service registry').items():
        if type(item['arity']) is not int or not 0 <= item['arity'] <= 12:
            raise ValueError('storage service arity is not an original argument count')
        result[pc] = address(item['target']), item['arity']
    return result


def registry_evidence(report, constants, parents):
    if (report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA
        or report.get('functions') != {} or report.get('new_data_exclusions') != []
        or type(report.get('new_original_functions')) is not int or report['new_original_functions'] != 0):
        raise ValueError('storage runtime must retain empty new-function and data declarations')
    if constants.get('REGIONS') != {} or constants.get('JOINS') != JOINS or constants.get('PARENTS') != PARENT_SOURCES:
        raise ValueError('storage runtime model registry or frozen derivative parents changed')
    expected = {}
    for key, parent in parents.items():
        for name, item in parent['functions'].items(): expected[key+'_'+name] = item
    for name, item in parents['preparation']['reused_functions'].items(): expected['reused_'+name] = item
    bodies = report['reused_functions']
    if set(bodies) != set(expected) or len(bodies) != 75:
        raise ValueError('storage runtime must retain all 75 exact named parent bodies')
    for name, item in bodies.items():
        prior = expected[name]
        if span(item) != span(prior) or item['bytes_sha256'] != prior['bytes_sha256']:
            raise ValueError('storage runtime whole-body identity differs from its parent')
    return expected


def runtime_evidence(report, constants, parents, raw, decode, regions, data_ranges, isa):
    registry_evidence(report, constants, parents)
    bodies = report['reused_functions']; canonical, by_body = {}, {}
    for name, item in bodies.items():
        a, b = span(item); parent = regions.get((a, b)); body = decode(a, b)
        if (parent is None or parent['kind'] != 'function_region'
            or parent['sha256'] != item['bytes_sha256'] or sha(raw(a, b)) != item['bytes_sha256']
            or type(item['bytes']) is not int or item['bytes'] != b-a
            or type(item['instructions']) is not int or item['instructions'] != len(body)):
            raise ValueError('storage runtime body bytes, geometry or instruction count changed')
        pcs = {pc for pc, _, _ in body}
        if pcs & canonical.keys(): raise ValueError('storage runtime parent bodies overlap')
        by_body[name] = pcs
        canonical.update({pc: (size, text) for pc, size, text in body})
    loaded = keyed(report['loaded_instruction_windows'], 'storage loaded windows')
    if set(loaded) != set(canonical):
        raise ValueError('storage loaded windows are not the exact complete-parent union')
    for pc, item in loaded.items():
        size, _ = canonical[pc]
        if type(item['bytes']) is not int or item['bytes'] != size or sha(raw(pc, pc+size)) != item['sha256']:
            raise ValueError('storage loaded window is not one exact canonical instruction')
    visited = pc_set(report['visited'], canonical.keys(), 'storage visited PCs')
    missing = set(canonical)-visited; coverage = report['instruction_coverage']
    counts = {'new_decoded': 0, 'new_visited': 0, 'joined_decoded': len(canonical),
        'joined_visited': len(visited), 'all_decoded': len(canonical), 'all_visited': len(visited)}
    if (any(type(coverage[k]) is not int or coverage[k] != value for k, value in counts.items())
        or coverage['unvisited_new'] != []
        or pc_set(coverage['unvisited_all'], canonical.keys(), 'storage loaded gaps') != missing
        or pc_set(coverage['unvisited_joined'], canonical.keys(), 'storage joined gaps') != missing):
        raise ValueError('storage runtime coverage differs from exact loaded and visited sets')
    gap_instructions = keyed(report['gap_instructions'], 'storage gap instructions')
    if set(gap_instructions) != missing or any(text.removesuffix('  #') != canonical[pc][1]
            for pc, text in gap_instructions.items()):
        raise ValueError('storage gap instruction text differs from original complete-body decoding')
    expected_gap_functions = {name for name, pcs in by_body.items() if pcs & missing}
    if set(report['gap_functions']) != expected_gap_functions:
        raise ValueError('storage per-function gap registry changed')
    per_function = {}
    for name, item in bodies.items():
        pcs = by_body[name]; absent = pcs & missing; count = item['visited_instructions']
        if type(count) is not int or count != len(pcs & visited):
            raise ValueError('storage per-function visited count changed')
        if absent and pc_set(report['gap_functions'][name]['unvisited'], pcs, 'storage function gaps') != absent:
            raise ValueError('storage per-function gaps contradict the canonical observed set')
        per_function[name] = {'decoded': len(pcs), 'visited': count, 'unvisited': len(absent), 'reused': True}
    parent_services = {}
    for parent in parents.values():
        for pc, item in services(parent['service_sites']).items():
            if pc in parent_services and parent_services[pc] != item:
                raise ValueError('storage parent service ABIs disagree')
            parent_services[pc] = item
    for pc, item in JOINS.items():
        if parent_services.get(pc) != item:
            raise ValueError('storage join differs from its original caller ABI')
    external = {pc: item for pc, item in parent_services.items() if pc not in JOINS}
    if services(report['service_sites']) != external or len(external) != 35:
        raise ValueError('storage runtime changed its exact remaining platform-site registry')
    entries = {span(item)[0] for item in bodies.values()}; decoded_external = {}
    for pc, (size, text) in canonical.items():
        if not text.startswith('call '): continue
        match = re.fullmatch(r'call (-?\d+)', text)
        if match is None: raise ValueError('unreviewed indirect call in storage closure')
        target = pc+size+int(match[1])
        if target not in entries:
            if pc not in external or external[pc][0] != target:
                raise ValueError('storage original call escapes its declared closure')
            decoded_external[pc] = external[pc]
    if decoded_external != external:
        raise ValueError('storage external registry includes a noncanonical call site')
    joins = keyed(report['direct_joins'], 'storage direct joins')
    if services(report['direct_joins']) != JOINS:
        raise ValueError('storage runtime changed the eighteen exact direct joins')
    for pc, (target, _) in JOINS.items():
        size, text = canonical[pc]; calls = joins[pc]['calls']
        if (text != f'call {target-pc-size}' or target not in entries
            or pc not in visited or target not in visited or type(calls) is not int or calls <= 0):
            raise ValueError('storage join lacks an executed original call and complete callee entry')
    prior_static = parents['control']['branch_tables']; static = report['bound_static_data']
    if set(static) != set(prior_static): raise ValueError('storage runtime changed inherited static roles')
    for name, item in static.items():
        a, b = span(item)
        if (static_identity(item) != static_identity(prior_static[name]) or sha(raw(a, b)) != item['sha256']
            or sum(x == a and y == b for x, y, _ in data_ranges) != 1):
            raise ValueError('storage inherited table bytes or data classification changed')
    for parent_name, key in (('control', 'auxiliary_reset_witness'), ('coordination', 'auxiliary_initial_state')):
        item, prior = report[key], parents[parent_name][key]; a, b = span(item)
        if (static_identity(item) != static_identity(prior) or sha(raw(a, b)) != item['sha256']
            or any(a < y and x < b for x, y, _ in data_ranges)):
            raise ValueError('storage auxiliary code or mutable state changed classification')
    cpu = keyed(report['cpu_primary_evidence'], 'storage CPU records')
    previous_cpu = keyed(parents['coordination']['cpu_primary_evidence']['records'], 'parent CPU records')
    if set(cpu) != set(CPU_SITES) or cpu != previous_cpu:
        raise ValueError('storage CPU evidence differs from its exact pinned parent records')
    for pc, (identifier, text, digest) in CPU_SITES.items():
        size, decoded = canonical[pc]; found = codec.decode(isa, raw(pc, pc+size), 0)
        if found is None: raise ValueError('storage CPU observation is undecoded')
        instruction, fields, width = found
        record = {'id': instruction.id, 'decoded': codec.format(instruction, fields),
            'summary': instruction.summary, 'notes': instruction.notes,
            'status': instruction.status, 'sources': instruction.sources}
        if (width != size or decoded != text or instruction.id != identifier or record != cpu[pc]
            or sha(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()) != digest):
            raise ValueError('storage CPU instruction or primary ISA record changed')
    derivation = report['derivation']
    if (derivation['parents'] != PARENT_SOURCES or type(derivation['checked_complete_derivatives']) is not int
        or derivation['checked_complete_derivatives'] != 2 or derivation['unchanged_coordination_source'] is not True
        or any(report['source_sha256'].get(name) != digest for name, digest in PARENT_SOURCES.items())):
        raise ValueError('storage checked source-derivative ancestry changed')
    return {'new_functions': 0, 'new_data_exclusions': 0, 'reused_whole_functions': len(bodies),
        **counts, 'unvisited_loaded': len(missing), 'direct_join_sites': len(JOINS),
        'remaining_platform_sites': len(external), 'remaining_platform_targets': len({t for t, _ in external.values()}),
        'inherited_static_spans': len(static), 'inherited_static_bytes': sum(b-a for a, b in map(span, static.values())),
        'inherited_CPU_records': len(cpu), 'auxiliary_reset_and_mutable_IRQ_bytes': 30,
        'checked_source_derivatives': 2, 'private_knowledge_and_finite_work_guards_are_portable': True,
        'per_function': per_function}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 60 or len(set(PRESERVED_REPORTS)) != 60:
        raise ValueError('inventory18 must contain 60 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('storage runtime inventory omitted or duplicated prior evidence')


class StorageRuntimeInventory(SampleProcessingInventory):
    def __init__(self, *required, storage_runtime_report, additional_reports=(), **options):
        if local(storage_runtime_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen storage-runtime01')
        additions = [local(p).relative_to(ROOT).as_posix() for p in additional_reports]
        if REPORT in additions: raise ValueError('storage runtime report is already explicitly selected')
        self.runtime_storage = None
        super().__init__(*required, additional_reports=additions, **options)

    def reports(self):
        omitted = super().reports(); raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen storage runtime report changed')
        report = json.loads(raw_report); self.audit_sources(report['source_sha256'])
        self.audit_manifest(REPORT, MANIFEST_SHA)
        parents = {}
        for name, (path, digest) in PARENT_REPORTS.items():
            data = self.read(path)
            if sha(data) != digest: raise ValueError('frozen storage runtime parent report changed')
            parents[name] = json.loads(data)
        constants = declared_constants(self.read(MODEL).decode('utf-8'))
        self.runtime_storage = runtime_evidence(report, constants, parents, self.raw, self.decode,
            self.regions, self.data_ranges, self.instructions)
        self.modules.append({'module': local(REPORT).parent.name, 'report': REPORT,
            'report_sha256': sha(raw_report), 'declared_regions': 0, 'integration_only': True,
            'source_hashes_checked': len(report['source_sha256']), 'scope_limits': report['limitations'],
            'instruction_coverage': coverage_summary(report),
            'reported_region_coverage': self.runtime_storage['per_function'],
            'reported_coverage_notes': {'empty_function_declaration_preserved': True,
                'loaded_windows_equal_the_exact_seventy_five_parent_body_union': True,
                'all_eighteen_direct_join_sites_and_callee_entries_executed': True,
                'inherited_execution_counts_are_not_borrowed': True,
                'finite_work_and_private_knowledge_guards_remain_portable': True},
            'storage_runtime_evidence': self.runtime_storage})
        return [name for name in omitted if name != REPORT]

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=17, storage_runtime_inventory_adapter=ADAPTER,
            storage_runtime_evidence=self.runtime_storage)
        report['audits'].update(inventory18_all_sixty_reports_retained=True,
            storage_runtime_empty_new_function_and_data_declarations_preserved=True,
            storage_runtime_exact_parent_union_and_canonical_coverage_bound=True,
            storage_runtime_eighteen_direct_joins_and_remaining_platform_ABIs_bound=True,
            storage_runtime_inherited_tables_CPU_records_and_auxiliary_roles_preserved=True,
            storage_runtime_checked_derivative_ancestry_bound=True)
        report['scope_policy'].extend([
            'storage runtime joins 75 existing complete bodies at eighteen original call sites; it adds no function, candidate or data exclusion',
            'its 2283 loaded instructions are the exact parent union, with 1701 visited and all 582 gaps recorded independently of earlier execution coverage',
            '35 remaining platform call sites retain their original ABIs; five existing tables and five CPU/ISA records retain their prior classification and provenance',
            'active private payload leases belong only to internal driver accesses; actual completed stores establish initialized bytes while callback views remain public-only',
            'unavailable private payload, finite work and API failures retain portable status; reported native read success does not invent initialized data',
            'shared service/event allowances and specific matched prefixes do not prove arbitrary work-prefix equivalence, physical flash durability or hardware scheduling'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject contradictory parent unions, code windows, joins and classifications."""
    packed, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(packed) != REFERENCE_SHA or unpack_app(packed)[2]['app.bin'] != app:
        raise ValueError('self-check original image changed')
    inv = object.__new__(Inventory); inv.app = app; inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    prior = json.loads(local('build/reverse-inventory-18/inventory.json').read_bytes())
    inv.data_ranges = [(address(r['start']), address(r['end_exclusive']), r['kind']) for r in prior['known_data_ranges']]
    decode = functools.cache(inv.decode); regions = {span(item): item for item in prior['reconstructed_regions']}
    data = local(REPORT).read_bytes()
    if sha(data) != REPORT_SHA: raise ValueError('self-check frozen storage runtime report changed')
    report = json.loads(data); constants = declared_constants(local(MODEL).read_text())
    parents = {name: json.loads(local(path).read_bytes()) for name, (path, _) in PARENT_REPORTS.items()}
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid storage runtime evidence accepted')
    def audit(item, bindings=regions, ranges=inv.data_ranges):
        return runtime_evidence(item, constants, parents, inv.raw, decode, bindings, ranges, inv.instructions)
    assert audit(report)['all_visited'] == 1701; checks += 1
    for name in report['reused_functions']:
        for key, value in [('start', 0), ('bytes_sha256', '0'*64), ('bytes', True),
                ('instructions', 0), ('visited_instructions', -1)]:
            changed = copy.deepcopy(report); changed['reused_functions'][name][key] = value; rejected(audit, changed)
    pc = next(iter(report['loaded_instruction_windows'])); gap = next(iter(report['gap_functions']))
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
        ((), 'functions', {'invented': {}}), ((), 'new_original_functions', False),
        ((), 'new_data_exclusions', [0x01c1fc54]),
        ((), 'visited', report['visited']+[report['visited'][0]]),
        (('instruction_coverage',), 'all_visited', True),
        (('instruction_coverage',), 'joined_decoded', 0),
        (('instruction_coverage',), 'unvisited_joined', []),
        (('instruction_coverage',), 'unvisited_new', [0x020031d4]),
        (('loaded_instruction_windows', pc), 'bytes', 1),
        (('loaded_instruction_windows', pc), 'sha256', '0'*64),
        (('gap_functions', gap), 'unvisited', []),
        ((), 'gap_instructions', {}), ((), 'gap_functions', {}),
        (('bound_static_data', 'control200'), 'end_exclusive', 0x02002a34),
        (('auxiliary_reset_witness',), 'sha256', '0'*64),
        (('auxiliary_initial_state',), 'end_exclusive', 0x01c1fc60),
        (('derivation',), 'checked_complete_derivatives', True),
        (('derivation',), 'unchanged_coordination_source', False)]:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(audit, changed)
    for key in ('loaded_instruction_windows', 'gap_instructions', 'service_sites', 'direct_joins', 'cpu_primary_evidence'):
        changed = copy.deepcopy(report); pc = next(iter(changed[key])); changed[key][str(address(pc))] = changed[key][pc]
        rejected(audit, changed)
    for key in report['direct_joins']:
        for field, value in [('target', '0x02000000'), ('arity', True), ('calls', 0)]:
            changed = copy.deepcopy(report); changed['direct_joins'][key][field] = value; rejected(audit, changed)
    for key in report['service_sites']:
        changed = copy.deepcopy(report); changed['service_sites'][key]['arity'] += 1; rejected(audit, changed)
    for key in report['cpu_primary_evidence']:
        changed = copy.deepcopy(report); changed['cpu_primary_evidence'][key]['notes'] = 'changed'; rejected(audit, changed)
    # Keep counters and per-function gap records mutually consistent while
    # removing a claimed joined callee entry: the positive call count cannot
    # then serve as execution evidence.
    changed = copy.deepcopy(report); target = JOINS[0x02002dc2][0]; text = None
    changed['visited'] = [pc for pc in changed['visited'] if address(pc) != target]
    for key in ('all_visited', 'joined_visited'): changed['instruction_coverage'][key] -= 1
    for key in ('unvisited_all', 'unvisited_joined'): changed['instruction_coverage'][key].append(hex(target))
    for name, item in changed['reused_functions'].items():
        if span(item)[0] == target:
            item['visited_instructions'] -= 1; text = decode(*span(item))[0][2]
            changed['gap_functions'].setdefault(name, {'unvisited': []})['unvisited'].append(hex(target))
    assert text is not None; changed['gap_instructions'][hex(target)] = text; rejected(audit, changed)
    for key in ('auxiliary_reset_witness', 'auxiliary_initial_state'):
        a, b = span(report[key]); rejected(audit, report, regions, [*inv.data_ranges, (a, b, 'invalid_exclusion')])
    for key in ('REGIONS', 'JOINS', 'PARENTS'):
        changed = dict(constants); changed[key] = {'invented': 0}
        rejected(registry_evidence, report, changed, parents)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 60,
        'new_functions': 0, 'new_data_exclusions': 0, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report',
        'storage_coordination_report', 'sample_processing_report', 'storage_runtime_report')
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
    report = StorageRuntimeInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'storage-runtime-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'storage_runtime_evidence': {k: v for k, v in report['storage_runtime_evidence'].items()
            if k != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
