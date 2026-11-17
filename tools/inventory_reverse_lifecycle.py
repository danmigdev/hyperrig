"""Audit storage preparation and the IR lifecycle/numerical integration.

Preserve inventory13 and its exact code/data policies. Storage adds eleven
whole bodies; the IR report has an intentionally empty new-function schema.
Authenticate its reused bodies without inserting synthetic function entries.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from inventory_reverse import ROOT, REFERENCE_SHA, address, hex_address, local, sha
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_integrations import configured_evidence, REQUIRED_OPTIONS
from inventory_reverse_models import (ModelsInventory, MODEL_REPORT,
    PRESERVED_REPORTS as INVENTORY12_REPORTS)

ADAPTER = 'tools/inventory_reverse_lifecycle.py'
IR_REPORT = 'build/reverse-ir-effect-numerical-02/verification.json'
IR_SHA = '3b032c2821356276b29771b825e72ea74aabefd045fd46b61a8aae264728aeb3'
IR_MANIFEST_SHA = '0f26a47a2abecfd1a9f85ad21ec38fb4c46c8471acdb19094057d2b7d53e71d4'
STORAGE_REPORT = 'build/reverse-preset-storage-preparation-02/verification.json'
STORAGE_SHA = '50e4c3d0d19e2911ee629718489f395674a4e2e5d6695063a86ab21b571f8860'
STORAGE_MANIFEST_SHA = 'ebde7c602e271ccce2657fc18a770489f05caf2ab3b9f56c027a7c0cd9d3772a'
PRESERVED_REPORTS = (*INVENTORY12_REPORTS, MODEL_REPORT)
RESAMPLING = {'start': 0x0203be2c, 'end_exclusive': 0x0203be50,
    'sha256': '5e4544bfe9c57a8a3dc7f9db243232a0362dca09497be8503c418e379879165c'}


def passing_original(report):
    if report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA:
        raise ValueError('lifecycle evidence must pass against the pinned original')


def ir_evidence(report, raw, decode, regions, data_ranges):
    """Adapt only metadata names; no reconstructed region is added."""
    passing_original(report)
    if report.get('integration_only') is not True or report.get('functions') != {}:
        raise ValueError('IR numerical integration must retain its empty new-function schema')
    if report.get('new_original_functions', 0) != 0 or report.get('new_static_data_ranges', []) != []:
        raise ValueError('IR numerical integration cannot claim new functions or data')
    reused = report.get('reused_functions')
    if not isinstance(reused, dict) or not reused:
        raise ValueError('IR numerical integration lacks complete reused bodies')
    joined, declared_pcs = {}, set()
    for name, item in reused.items():
        start, end = address(item['start']), address(item['end_exclusive'])
        pcs = {pc for pc, _, _ in decode(start, end)}
        if declared_pcs & pcs:
            raise ValueError('IR numerical reused declarations overlap')
        declared_pcs.update(pcs)
        joined[name] = {'start': start, 'end_exclusive': end, 'sha256': item['bytes_sha256'],
            'decoded': item['instructions'], 'visited': item['visited'], 'unvisited': item['unvisited']}
    static = report.get('static_data', {})
    if (set(static) != {'resampling_taps'}
        or {key: address(value) if key != 'sha256' else value
            for key, value in static['resampling_taps'].items()} != RESAMPLING):
        raise ValueError('IR numerical integration changed its sole reused table binding')
    if sum((a, b) == (RESAMPLING['start'], RESAMPLING['end_exclusive']) for a, b, _ in data_ranges) != 1:
        raise ValueError('IR resampling must retain one exact prior data exclusion')
    # The frozen report calls these reused_functions and uses bytes_sha256 /
    # instructions. The shared validator calls them joined_bodies and uses
    # sha256 / decoded. This view is never passed to the region loader.
    view = dict(report, new_original_functions=0, new_static_data_ranges=[], joined_bodies=joined)
    evidence = configured_evidence(view, raw, decode, regions, data_ranges)
    loaded_pcs = {address(pc) for pc in report['bound_instruction_windows']}
    if loaded_pcs != declared_pcs:
        raise ValueError('IR numerical windows differ from the exact reused-body closure')
    evidence.update(reused_whole_bodies=len(reused), empty_function_declaration_preserved=True,
        metadata_adapter='reused_functions -> joined_bodies, bytes_sha256 -> sha256, instructions -> decoded; in memory only')
    return evidence


def storage_evidence(report, raw, decode, regions):
    """Check both new and reused storage regions and every declared gap."""
    passing_original(report)
    if report.get('new_data_exclusions') != []:
        raise ValueError('storage preparation cannot add data exclusions')
    new, reused = report.get('functions'), report.get('reused_functions')
    if not isinstance(new, dict) or not new or not isinstance(reused, dict) or not reused or set(new) & set(reused):
        raise ValueError('storage preparation requires distinct new and reused declarations')
    all_pcs, new_pcs, per_body = set(), set(), {}
    for name, item in {**new, **reused}.items():
        start, end = address(item['start']), address(item['end_exclusive'])
        prior = regions.get((start, end))
        if (prior is None or prior['kind'] != 'function_region'
            or prior['sha256'] != item['bytes_sha256'] or sha(raw(start, end)) != item['bytes_sha256']):
            raise ValueError('storage body is not an exact loaded whole function')
        pcs = {pc for pc, _, _ in decode(start, end)}
        if not pcs or all_pcs & pcs:
            raise ValueError('storage body declarations are empty or overlapping')
        if name in new:
            if item.get('bytes') != end-start or type(item.get('instructions')) is not int or item['instructions'] != len(pcs):
                raise ValueError('new storage body byte/instruction extent changed')
            new_pcs.update(pcs)
        all_pcs.update(pcs); per_body[name] = pcs
    coverage = report.get('instruction_coverage', {})
    missing = {}
    for key, allowed in (('unvisited_new', new_pcs), ('unvisited_all', all_pcs)):
        values = [address(pc) for pc in coverage[key]]
        if len(values) != len(set(values)) or not set(values) <= allowed:
            raise ValueError('storage gap lies outside its declared instruction domain')
        missing[key] = set(values)
    if missing['unvisited_new'] != missing['unvisited_all'] & new_pcs:
        raise ValueError('storage new and loaded gap sets disagree')
    expected = {'new_decoded': len(new_pcs), 'new_visited': len(new_pcs-missing['unvisited_new']),
        'all_decoded': len(all_pcs), 'all_visited': len(all_pcs-missing['unvisited_all'])}
    if any(type(coverage.get(key)) is not int or coverage[key] != value for key, value in expected.items()):
        raise ValueError('storage aggregate coverage differs from complete original bodies')
    return {'new_functions': len(new), 'reused_functions': len(reused), **expected,
        'new_data_exclusions': 0, 'new_gaps': len(missing['unvisited_new']),
        'inherited_gaps': len(missing['unvisited_all']-new_pcs),
        'per_function': {name: {'decoded': len(pcs), 'visited': len(pcs-missing['unvisited_all']),
            'unvisited': len(pcs & missing['unvisited_all'])} for name, pcs in per_body.items()}}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 54 or len(set(PRESERVED_REPORTS)) != 54:
        raise ValueError('inventory13 must contain 54 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, STORAGE_REPORT, IR_REPORT} <= set(selected):
        raise ValueError('lifecycle inventory omitted or duplicated prior evidence')


class LifecycleInventory(ModelsInventory):
    def __init__(self, *required, configured_signal_report, model_report,
                 ir_numerical_report, additional_reports=()):
        self.ir_numerical_report = local(ir_numerical_report).relative_to(ROOT).as_posix()
        if self.ir_numerical_report != IR_REPORT:
            raise ValueError('lifecycle inventory requires frozen IR numerical02')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if self.ir_numerical_report in additions:
            raise ValueError('IR numerical report is already explicitly selected')
        if additions.count(STORAGE_REPORT) != 1:
            raise ValueError('lifecycle inventory requires storage preparation02 exactly once')
        self.ir_evidence, self.storage_evidence = None, None
        super().__init__(*required, configured_signal_report=configured_signal_report,
            model_report=model_report, additional_reports=additions)

    def audit_manifest(self, report_name, expected):
        path = local(report_name)
        name = (path.parent/'build-manifest.json').relative_to(ROOT).as_posix()
        raw_manifest = self.read(name)
        if sha(raw_manifest) != expected: raise ValueError('frozen lifecycle manifest changed')
        for filename, digest in json.loads(raw_manifest)['files'].items():
            if Path(filename).name != filename:
                raise ValueError('lifecycle artifact must be a direct manifest sibling')
            artifact = (path.parent/filename).relative_to(ROOT).as_posix()
            if sha(self.read(artifact)) != digest:
                raise ValueError('lifecycle artifact differs from its completed manifest')
            self.audited_artifacts.add(artifact)

    def reports(self):
        omitted = super().reports()
        raw_storage = self.read(STORAGE_REPORT)
        if sha(raw_storage) != STORAGE_SHA: raise ValueError('frozen storage report changed')
        storage = json.loads(raw_storage)
        self.audit_manifest(STORAGE_REPORT, STORAGE_MANIFEST_SHA)
        self.storage_evidence = storage_evidence(storage, self.raw, self.decode, self.regions)
        module = next(item for item in self.modules if item['report'] == STORAGE_REPORT)
        module.update(reused_region_evidence=self.storage_evidence,
            reported_region_coverage=self.storage_evidence['per_function'],
            reported_coverage_notes={'classified_new_gaps': storage['gap_classification'],
                'all_reused_storage_bodies_and_instruction_gaps_independently_bound': True})
        raw_ir = self.read(IR_REPORT)
        if sha(raw_ir) != IR_SHA: raise ValueError('frozen IR numerical report changed')
        report = json.loads(raw_ir)
        self.audit_sources(report['source_sha256']); self.audit_manifest(IR_REPORT, IR_MANIFEST_SHA)
        self.ir_evidence = ir_evidence(report, self.raw, self.decode, self.regions, self.data_ranges)
        self.modules.append({'module': local(IR_REPORT).parent.name, 'report': IR_REPORT,
            'report_sha256': sha(raw_ir), 'declared_regions': 0, 'integration_only': True,
            'source_hashes_checked': len(report['source_sha256']), 'scope_limits': report['limitations'],
            'instruction_coverage': coverage_summary(report),
            'reported_region_coverage': self.ir_evidence['reused_bodies'],
            'reported_coverage_notes': {'empty_function_declaration_preserved': True,
                'loaded_windows_equal_the_exact_reused_function_closure': True,
                'no_native_guard_prefix_claim_added': True},
            'integration_evidence': self.ir_evidence})
        return [name for name in omitted if name != IR_REPORT]

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=12, lifecycle_inventory_adapter=ADAPTER,
            storage_preparation_evidence=self.storage_evidence, ir_numerical_evidence=self.ir_evidence)
        report['audits'].update(inventory13_all_fifty_four_reports_retained=True,
            storage_new_and_reused_whole_bodies_and_coverage_independently_bound=True,
            ir_numerical_empty_function_schema_preserved=True,
            ir_numerical_reused_bodies_and_canonical_windows_match_exactly=True,
            lifecycle_reports_add_no_data_exclusions=True)
        report['scope_policy'].extend([
            'storage preparation adds eleven complete bodies; ten existing helpers and every new/reused instruction gap are independently bound without duplicate function counts',
            'IR numerical integration declares no new functions; an in-memory metadata-name adapter authenticates all 35 existing bodies and their exact canonical instruction closure',
            'the existing 36-byte IR resampling table retains its prior data exclusion; neither new report adds data classification',
            'storage and IR comparisons preserve their stated mapping, callback and finite-work domains; C-only guards do not become native returns or hardware/durability claims'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject altered body identity, canonical windows, coverage and retention."""
    checks = 0
    code = b'\0\0\x80\0\x80\0\x80\0'
    table_bytes = local('analysis/firmware/m571_g_app/app.bin').read_bytes()[
        RESAMPLING['start']-0x02000120:RESAMPLING['end_exclusive']-0x02000120]
    if sha(table_bytes) != RESAMPLING['sha256']: raise ValueError('self-check resampling bytes changed')
    def raw(a, b):
        return table_bytes[a-RESAMPLING['start']:b-RESAMPLING['start']] if a >= RESAMPLING['start'] else code[a-0x1000:b-0x1000]
    def decode(a, b):
        result = []
        while a < b:
            size = 4 if a == 0x1000 else 2
            result.append((a, size, 'wide' if size == 4 else 'rts')); a += size
        return result
    parents = {(a, b): {'kind': 'function_region', 'sha256': sha(raw(a, b))}
        for a, b in ((0x1000, 0x1004), (0x1004, 0x1008))}
    known = [(RESAMPLING['start'], RESAMPLING['end_exclusive'], 'existing_ir_table')]
    valid = {'result': 'pass', 'original_image_sha256': REFERENCE_SHA, 'integration_only': True,
        'functions': {}, 'reused_functions': {
            'first': {'start': 0x1000, 'end_exclusive': 0x1004, 'bytes_sha256': sha(raw(0x1000, 0x1004)),
                'instructions': 1, 'visited': 1, 'unvisited': []},
            'second': {'start': 0x1004, 'end_exclusive': 0x1008, 'bytes_sha256': sha(raw(0x1004, 0x1008)),
                'instructions': 2, 'visited': 1, 'unvisited': [0x1006]}},
        'static_data': {'resampling_taps': dict(RESAMPLING)},
        'instruction_coverage': {'new_decoded': 0, 'new_visited': 0, 'unvisited_new': [],
            'all_decoded': 3, 'all_visited': 2, 'unvisited_all': [0x1006]},
        'bound_instruction_windows': {hex(pc): {'start': pc, 'end_exclusive': pc+size,
            'sha256': sha(raw(pc, pc+size))} for pc, size, _ in decode(0x1000, 0x1008)}}
    def ir(report=valid, regions=parents, data=known): return ir_evidence(report, raw, decode, regions, data)
    def rejected(function, *args, **kwargs):
        nonlocal checks
        try: function(*args, **kwargs)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid lifecycle evidence accepted')
    assert ir()['new_functions'] == 0; checks += 1
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64), ((), 'integration_only', False),
        ((), 'functions', {'invented': {}}), ((), 'new_original_functions', 1),
        ((), 'new_static_data_ranges', [0x2000]), ((), 'reused_functions', {}),
        (('reused_functions', 'first'), 'end_exclusive', 0x1002),
        (('reused_functions', 'first'), 'bytes_sha256', '0'*64),
        (('reused_functions', 'first'), 'instructions', 2),
        (('reused_functions', 'second'), 'visited', 2),
        (('reused_functions', 'second'), 'unvisited', [0x1004]),
        (('static_data', 'resampling_taps'), 'end_exclusive', RESAMPLING['end_exclusive']+2),
        (('static_data', 'resampling_taps'), 'sha256', '0'*64),
        (('instruction_coverage',), 'new_decoded', 1), (('instruction_coverage',), 'all_visited', 3),
        (('instruction_coverage',), 'unvisited_all', [0x1006, 0x1006])]:
        changed = copy.deepcopy(valid); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(ir, changed)
    changed = copy.deepcopy(valid); del changed['reused_functions']['second']; rejected(ir, changed)
    changed = copy.deepcopy(valid); changed['reused_functions']['duplicate'] = changed['reused_functions']['first']
    rejected(ir, changed)
    changed = copy.deepcopy(valid)
    changed['bound_instruction_windows']['0x1000'] = {'start': 0x1002, 'end_exclusive': 0x1004,
        'sha256': sha(raw(0x1002, 0x1004))}
    rejected(ir, changed)
    altered = copy.deepcopy(parents); altered[(0x1000, 0x1004)]['kind'] = 'parser_fragment'
    rejected(ir, regions=altered); rejected(ir, regions={}); rejected(ir, data=[]); rejected(ir, data=known+known)

    storage = {'result': 'pass', 'original_image_sha256': REFERENCE_SHA, 'new_data_exclusions': [],
        'functions': {'first': {'start': 0x1000, 'end_exclusive': 0x1004, 'bytes': 4,
            'bytes_sha256': sha(raw(0x1000, 0x1004)), 'instructions': 1}},
        'reused_functions': {'second': {'start': 0x1004, 'end_exclusive': 0x1008,
            'bytes_sha256': sha(raw(0x1004, 0x1008))}},
        'instruction_coverage': {'new_decoded': 1, 'new_visited': 0, 'unvisited_new': [0x1000],
            'all_decoded': 3, 'all_visited': 2, 'unvisited_all': [0x1000]}}
    def storage_check(report=storage, regions=parents): return storage_evidence(report, raw, decode, regions)
    assert storage_check()['inherited_gaps'] == 0; checks += 1
    for path, key, value in [
        ((), 'new_data_exclusions', [0x2000]), ((), 'functions', {}), ((), 'reused_functions', {}),
        (('functions', 'first'), 'bytes', 2), (('functions', 'first'), 'instructions', 2),
        (('functions', 'first'), 'bytes_sha256', '0'*64),
        (('reused_functions', 'second'), 'end_exclusive', 0x1006),
        (('instruction_coverage',), 'new_decoded', 2), (('instruction_coverage',), 'new_visited', 1),
        (('instruction_coverage',), 'all_decoded', 4), (('instruction_coverage',), 'all_visited', 3),
        (('instruction_coverage',), 'unvisited_new', [0x1002]),
        (('instruction_coverage',), 'unvisited_all', [0x1006]),
        (('instruction_coverage',), 'unvisited_all', [0x1000, 0x1000])]:
        changed = copy.deepcopy(storage); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(storage_check, changed)
    rejected(storage_check, regions={}); rejected(storage_check, regions=altered)
    changed = copy.deepcopy(storage); changed['reused_functions']['first'] = changed['functions']['first']
    rejected(storage_check, changed)
    selected = [*PRESERVED_REPORTS, STORAGE_REPORT, IR_REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[IR_REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 54,
        'new_data_exclusions': 0, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    parser.add_argument('--configured-signal-report'); parser.add_argument('--model-report')
    parser.add_argument('--ir-numerical-report'); parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true'); args = parser.parse_args()
    required = tuple(getattr(args, name.replace('-', '_')) for name in REQUIRED_OPTIONS)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report or args.configured_signal_report or args.model_report or args.ir_numerical_report:
            parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required) or not args.configured_signal_report or not args.model_report or not args.ir_numerical_report:
        parser.error('choose --output or --check and provide every required report')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a fresh directory under build/')
    report = LifecycleInventory(*required, configured_signal_report=args.configured_signal_report,
        model_report=args.model_report, ir_numerical_report=args.ir_numerical_report,
        additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'lifecycle-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'storage_preparation_evidence': {k: v for k, v in report['storage_preparation_evidence'].items() if k != 'per_function'},
        'ir_numerical_evidence': {k: v for k, v in report['ir_numerical_evidence'].items() if k != 'reused_bodies'}}, indent=2))


if __name__ == '__main__': main()
