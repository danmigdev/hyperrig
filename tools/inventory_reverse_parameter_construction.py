"""Audit the parameter-to-constructor integration without adding function entries.

Retain inventory14, both frozen parent corpora and every earlier code/data rule.
The new empty-function report joins existing bodies at three original call sites.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
from pathlib import Path
from inventory_reverse import ROOT, address, hex_address, local, sha
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_integrations import configured_evidence, REQUIRED_OPTIONS
from inventory_reverse_models import MODEL_REPORT, MODEL_SHA
from inventory_reverse_lifecycle import (LifecycleInventory, IR_REPORT, STORAGE_REPORT,
    PRESERVED_REPORTS as INVENTORY13_REPORTS)

ADAPTER = 'tools/inventory_reverse_parameter_construction.py'
REPORT = 'build/reverse-effect-parameter-construction-02/verification.json'
REPORT_SHA = '5221f339f3dffbac52b461cc9531c2c39eff8109e2a95a168959e53fc8127427'
MANIFEST_SHA = 'bc6ddb5fbdfd52bd281009edeee0184a3595dc669f700fa0ddd7e88cb5312d19'
OWNERSHIP_REPORT = 'build/reverse-effect-resource-ownership-03/verification.json'
OWNERSHIP_SHA = 'b876adaa7a7dbd23108f8d943058e9fd39d12a9a6d77d088ffded8473f2806fd'
PRESERVED_REPORTS = (*INVENTORY13_REPORTS, STORAGE_REPORT, IR_REPORT)
DIRECT_JOINS = {0x0202f37c: 0x0202cf62, 0x0202f970: 0x0202cf62, 0x0202f7ba: 0x0202cd32}


def span(item):
    return address(item['start']), address(item['end_exclusive'])


def static_identity(item):
    return (*span(item), item['sha256'])


def construction_evidence(report, ownership, models, raw, decode, regions, data_ranges,
                          direct_joins=DIRECT_JOINS):
    """Bind the complete merged corpus and its smaller named joined domain."""
    evidence = configured_evidence(report, raw, decode, regions, data_ranges)
    expected_bodies = {**ownership['functions'],
        **{'construction_'+name: item for name, item in models['functions'].items()}}
    bodies = report['joined_bodies']
    if set(bodies) != set(expected_bodies):
        raise ValueError('parameter construction must retain every named parent body')
    joined_pcs = set()
    for name, item in bodies.items():
        prior = expected_bodies[name]
        if span(item) != span(prior) or item['sha256'] != prior['bytes_sha256']:
            raise ValueError('parameter construction changed a prior whole-body declaration')
        pcs = {pc for pc, _, _ in decode(*span(item))}
        if joined_pcs & pcs:
            raise ValueError('parameter construction named bodies overlap')
        joined_pcs.update(pcs)

    expected_loaded = {address(pc) for pc in ownership['bound_instruction_windows']}
    for item in models['loaded_instruction_windows']:
        if sha(raw(*span(item))) != item['sha256']:
            raise ValueError('parent model loaded span changed')
        expected_loaded.update(pc for pc, _, _ in decode(*span(item)))
    loaded = {address(pc) for pc in report['bound_instruction_windows']}
    if loaded != expected_loaded:
        raise ValueError('parameter construction loaded set is not the exact two-parent union')
    coverage = report['instruction_coverage']
    gaps = {address(pc) for pc in coverage['unvisited_all']}
    joined_gaps = [address(pc) for pc in coverage['unvisited_joined']]
    expected = {'joined_decoded': len(joined_pcs), 'joined_visited': len(joined_pcs-gaps)}
    if (not joined_pcs <= loaded or len(joined_gaps) != len(set(joined_gaps))
        or set(joined_gaps) != joined_pcs & gaps
        or any(type(coverage.get(k)) is not int or coverage[k] != v for k, v in expected.items())):
        raise ValueError('parameter construction joined coverage differs from exact parent bodies')

    expected_static = dict(ownership['static_data'])
    for name, item in models['loaded_static_data'].items():
        same = [prior for prior in expected_static.values() if span(prior) == span(item)]
        if same:
            if any(static_identity(prior) != static_identity(item) for prior in same):
                raise ValueError('parent static bindings disagree')
        else:
            key = 'construction_'+name
            if key in expected_static: raise ValueError('parent static role names collide')
            expected_static[key] = item
    static = report['static_data']
    if (set(static) != set(expected_static)
        or any(static_identity(item) != static_identity(expected_static[name]) for name, item in static.items())):
        raise ValueError('parameter construction changed the exact inherited static roles')

    observed = {}
    for item in report['direct_construction_sites']:
        pc, target, calls = address(item['site']), address(item['target']), item['calls']
        decoded = decode(pc, address(report['bound_instruction_windows'][hex(pc)]['end_exclusive']))
        if len(decoded) != 1 or decoded[0][0] != pc:
            raise ValueError('constructor join is not one complete original instruction')
        _, size, text = decoded[0]
        match = re.fullmatch(r'call (-?\d+)', text)
        if (pc in observed or pc in gaps or target in gaps or direct_joins.get(pc) != target or match is None
            or pc+size+int(match[1]) != target or type(calls) is not int or calls <= 0
            or not any(a == target and parent['kind'] == 'function_region' for (a, _), parent in regions.items())):
            raise ValueError('constructor join target, identity or execution witness changed')
        observed[pc] = target
    if observed != direct_joins:
        raise ValueError('parameter construction must observe every exact direct join')
    distinct_static = {static_identity(item) for item in static.values()}
    evidence.update(joined_whole_bodies=len(bodies), **expected,
        unvisited_joined_instructions=len(joined_gaps), exact_two_parent_instruction_union=True,
        static_role_bindings=len(static), distinct_static_bindings=len(distinct_static),
        exact_inherited_static_roles=True,
        direct_sites=[{'site': hex_address(pc), 'target': hex_address(target)} for pc, target in sorted(observed.items())])
    return evidence


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 56 or len(set(PRESERVED_REPORTS)) != 56:
        raise ValueError('inventory14 must contain 56 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('parameter construction inventory omitted or duplicated prior evidence')


class ParameterConstructionInventory(LifecycleInventory):
    def __init__(self, *required, parameter_construction_report, **options):
        selected = local(parameter_construction_report).relative_to(ROOT).as_posix()
        if selected != REPORT: raise ValueError('inventory requires frozen parameter-construction02')
        if REPORT in [local(p).relative_to(ROOT).as_posix() for p in options.get('additional_reports', ())]:
            raise ValueError('parameter construction report is already explicitly selected')
        self.construction_join = None
        super().__init__(*required, **options)

    def reports(self):
        omitted = super().reports()
        raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen parameter construction report changed')
        report = json.loads(raw_report)
        parents = []
        for name, expected in ((OWNERSHIP_REPORT, OWNERSHIP_SHA), (MODEL_REPORT, MODEL_SHA)):
            original = self.read(name)
            if sha(original) != expected: raise ValueError('frozen constructor integration parent changed')
            parents.append(json.loads(original))
        self.audit_sources(report['source_sha256']); self.audit_manifest(REPORT, MANIFEST_SHA)
        self.construction_join = construction_evidence(report, *parents,
            self.raw, self.decode, self.regions, self.data_ranges)
        self.modules.append({'module': local(REPORT).parent.name, 'report': REPORT,
            'report_sha256': sha(raw_report), 'declared_regions': 0, 'integration_only': True,
            'source_hashes_checked': len(report['source_sha256']), 'scope_limits': report['limitations'],
            'instruction_coverage': coverage_summary(report),
            'reported_region_coverage': self.construction_join['reused_bodies'],
            'reported_coverage_notes': {'empty_function_declaration_preserved': True,
                'loaded_windows_equal_exact_two_parent_union': True,
                'joined_and_loaded_instruction_gaps_remain_separate': True,
                'arbitrary_constructor_guard_prefix_equivalence_not_claimed': True},
            'integration_evidence': self.construction_join})
        return [name for name in omitted if name != REPORT]

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=13, parameter_construction_inventory_adapter=ADAPTER,
            parameter_construction_evidence=self.construction_join)
        report['audits'].update(inventory14_all_fifty_six_reports_retained=True,
            parameter_construction_empty_function_schema_preserved=True,
            parameter_construction_joined_bodies_and_loaded_parent_union_authenticated=True,
            parameter_construction_direct_join_sites_independently_decoded=True,
            parameter_construction_static_bindings_preserve_exact_parent_roles=True)
        report['scope_policy'].extend([
            'parameter construction adds no function or data exclusion; named joined bodies and the full loaded set retain their separate coverage gaps',
            'all three original direct constructor sites are authenticated; equal numeric platform callback tokens do not become recovered calls',
            'parent static role duplicates remain explicit and do not enlarge prior data exclusions',
            'constructor API, mapping and numerical guards remain C-only checks unless a specific original execution-prefix observation is supplied'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject corpus, body, coverage, static-role and direct-site drift."""
    from inventory_reverse import REFERENCE_SHA
    checks = 0
    code = bytes(range(16)); data = b'abcdWXYZ'
    def raw(a, b): return (data[a-0x2000:b-0x2000] if a >= 0x2000 else code[a-0x1000:b-0x1000])
    def decode(a, b):
        result = []
        while a < b:
            size = 4 if a == 0x1000 else 2
            result.append((a, size, 'call 0' if a == 0x1000 else 'rts')); a += size
        return result
    def binding(a, b): return {'start': a, 'end_exclusive': b, 'sha256': sha(raw(a, b))}
    def body(a, b): return {'start': a, 'end_exclusive': b, 'bytes_sha256': sha(raw(a, b))}
    ownership = {'functions': {'caller': body(0x1000, 0x1004)},
        'bound_instruction_windows': {'0x1000': binding(0x1000, 0x1004)},
        'static_data': {'first': binding(0x2000, 0x2004)}}
    models = {'functions': {'callee': body(0x1004, 0x1008)},
        'loaded_instruction_windows': [binding(0x1004, 0x100a)],
        'loaded_static_data': {'same': binding(0x2000, 0x2004), 'second': binding(0x2004, 0x2008)}}
    regions = {(a, b): {'kind': 'function_region', 'sha256': sha(raw(a, b))}
        for a, b in ((0x1000, 0x1004), (0x1004, 0x1008), (0x1008, 0x100a))}
    valid = {'result': 'pass', 'original_image_sha256': REFERENCE_SHA, 'integration_only': True,
        'new_original_functions': 0, 'functions': {}, 'new_static_data_ranges': [],
        'joined_bodies': {'caller': {**binding(0x1000, 0x1004), 'decoded': 1, 'visited': 1, 'unvisited': []},
            'construction_callee': {**binding(0x1004, 0x1008), 'decoded': 2, 'visited': 1, 'unvisited': [0x1006]}},
        'instruction_coverage': {'new_decoded': 0, 'new_visited': 0, 'unvisited_new': [],
            'joined_decoded': 3, 'joined_visited': 2, 'unvisited_joined': [0x1006],
            'all_decoded': 4, 'all_visited': 2, 'unvisited_all': [0x1006, 0x1008]},
        'static_data': {'first': binding(0x2000, 0x2004), 'construction_second': binding(0x2004, 0x2008)},
        'bound_instruction_windows': {hex(pc): binding(pc, pc+size) for pc, size, _ in decode(0x1000, 0x100a)},
        'direct_construction_sites': [{'site': 0x1000, 'target': 0x1004, 'calls': 1}]}
    def run(report=valid, parent=ownership, model=models, parents=regions):
        return construction_evidence(report, parent, model, raw, decode, parents,
            [(0x2000, 0x2004, 'first'), (0x2004, 0x2008, 'second')], {0x1000: 0x1004})
    def rejected(function, *args, **options):
        nonlocal checks
        try: function(*args, **options)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid parameter construction evidence accepted')
    assert run()['joined_whole_bodies'] == 2; checks += 1
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'new_original_functions', 1), ((), 'functions', {'invented': {}}),
        (('instruction_coverage',), 'joined_decoded', 4), (('instruction_coverage',), 'joined_visited', 3),
        (('instruction_coverage',), 'unvisited_joined', [0x1008]),
        (('instruction_coverage',), 'unvisited_joined', [0x1006, 0x1006]),
        (('joined_bodies', 'caller'), 'end_exclusive', 0x1002),
        (('joined_bodies', 'caller'), 'sha256', '0'*64),
        (('static_data', 'first'), 'end_exclusive', 0x2002),
        (('direct_construction_sites', 0), 'target', 0x1008),
        (('direct_construction_sites', 0), 'calls', 0),
        (('direct_construction_sites', 0), 'calls', True),
        ((), 'direct_construction_sites', [])]:
        changed = copy.deepcopy(valid); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(run, changed)
    for key, item in (('joined_bodies', 'caller'), ('static_data', 'first'), ('bound_instruction_windows', '0x1008')):
        changed = copy.deepcopy(valid); del changed[key][item]; rejected(run, changed)
    changed = copy.deepcopy(valid); changed['direct_construction_sites'] *= 2; rejected(run, changed)
    for pc, name in ((0x1000, 'caller'), (0x1004, 'construction_callee')):
        changed = copy.deepcopy(valid); coverage = changed['instruction_coverage']
        coverage['unvisited_all'].append(pc); coverage['all_visited'] -= 1
        coverage['unvisited_joined'].append(pc); coverage['joined_visited'] -= 1
        changed['joined_bodies'][name]['unvisited'].append(pc)
        changed['joined_bodies'][name]['visited'] -= 1
        rejected(run, changed)
    changed = copy.deepcopy(models); changed['loaded_instruction_windows'] = [binding(0x1004, 0x1008)]
    rejected(run, model=changed)
    changed = copy.deepcopy(models); changed['loaded_static_data']['same']['sha256'] = '0'*64
    rejected(run, model=changed)
    changed = copy.deepcopy(ownership); changed['functions']['caller'] = body(0x1000, 0x1002)
    rejected(run, parent=changed)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 56,
        'new_functions': 0, 'new_data_exclusions': 0, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    for name in ('configured-signal-report', 'model-report', 'ir-numerical-report', 'parameter-construction-report'):
        parser.add_argument('--'+name)
    parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true'); args = parser.parse_args()
    required = tuple(getattr(args, name.replace('-', '_')) for name in REQUIRED_OPTIONS)
    extra = {name: getattr(args, name) for name in ('configured_signal_report', 'model_report',
        'ir_numerical_report', 'parameter_construction_report')}
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report or any(extra.values()):
            parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required) or not all(extra.values()):
        parser.error('choose --output or --check and provide every required report')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a fresh directory under build/')
    report = ParameterConstructionInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'parameter-construction-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'parameter_construction_evidence': {k: v for k, v in report['parameter_construction_evidence'].items()
            if k != 'reused_bodies'}}, indent=2))


if __name__ == '__main__': main()
