"""Audit integration-only evidence without inventing reconstructed regions.

Keep inventory11's fifty reports, source and data policies unchanged. The
configured-signal report deliberately declares no new functions; authenticate
its reused bodies and loaded instruction windows against the existing regions.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from inventory_reverse import ROOT, REFERENCE_SHA, address, hex_address, local, sha
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_construction import (ConstructionInventory, CONSTRUCTION_REPORT,
    PRESERVED_REPORTS as INVENTORY10_REPORTS)

ADAPTER = 'tools/inventory_reverse_integrations.py'
CONFIGURED_REPORT = 'build/reverse-effect-configured-signal-02/verification.json'
CONFIGURED_SHA = '064cb4a86f6e764e5408ee13f1461678034f0f08a0d3464b2ddad7876fdd47a8'
CONFIGURED_MANIFEST_SHA = 'a48dd61894d50840ad3d7d7bbd1e4944e4c8b9c1379900b13075ed4217ef2e3e'
AUDIO_REPORT = 'build/reverse-audio-task-03/verification.json'
# Earlier audio evidence binds these auxiliary bytes without declaring them
# reconstructed functions or new data exclusions. In particular registration
# is a code witness, not a table to remove from candidate decoding.
AUXILIARY = {
    'reset_configuration': {'start': 0x01c1f7f0, 'end_exclusive': 0x01c1f818,
        'sha256': 'ca25495ca89ac22d109f1bf553d967fc88013889c9b6e17419d3299b93535bb6',
        'kind': 'initial RAM configuration bytes'},
    'task_registration': {'start': 0x02005250, 'end_exclusive': 0x0200525e,
        'sha256': 'd3d962f59dd433f43cc30a07e1e191279fd12a30f6f37ce16829b8cb814a2ec5',
        'kind': 'task registration instruction witness'},
}
PRESERVED_REPORTS = (*INVENTORY10_REPORTS, CONSTRUCTION_REPORT,
    'build/reverse-effect-signal-01/verification.json',
    'build/reverse-effect-parameter-lifecycle-02/verification.json',
    'build/reverse-effect-ownership-01/verification.json')
REQUIRED_OPTIONS = ('parser-report', 'processing-report', 'ir-report', 'application-report',
    'ir-processing-report', 'audio-report', 'stage-report', 'resampling-report',
    'enable-report', 'support-report', 'effect-processing-report', 'parameters-report',
    'resources-report', 'construction-report')


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 50 or len(set(PRESERVED_REPORTS)) != 50:
        raise ValueError('inventory11 must contain fifty distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, CONFIGURED_REPORT} <= set(selected):
        raise ValueError('integration inventory omitted or duplicated preserved evidence')


def configured_evidence(report, raw, decode, regions, data_ranges, auxiliary=None):
    """Validate empty new declarations and independently bound reused coverage."""
    if (report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA
        or report.get('integration_only') is not True or report.get('new_original_functions') != 0
        or report.get('functions') != {} or report.get('new_static_data_ranges') != []):
        raise ValueError('configured signal must declare integration only, with no new bodies or data')
    coverage = report.get('instruction_coverage', {})
    if any(coverage.get(key) != value for key, value in
           (('new_decoded', 0), ('new_visited', 0), ('unvisited_new', []))):
        raise ValueError('integration report must not claim new decoded instructions')
    windows = report.get('bound_instruction_windows')
    if not isinstance(windows, dict) or not windows:
        raise ValueError('integration report lacks original instruction windows')
    canonical = {}
    for (start, end), parent in regions.items():
        if parent['kind'] != 'function_region':continue
        for pc, size, _ in decode(start, end):
            if pc in canonical and canonical[pc] != size:
                raise ValueError('prior function decodings disagree')
            canonical[pc] = size
    loaded, spans = set(), []
    for key, item in windows.items():
        start, end = address(item['start']), address(item['end_exclusive'])
        if address(key) != start or start in loaded or end <= start:
            raise ValueError('integration instruction key, duplicate or bounds')
        if canonical.get(start) != end-start:
            raise ValueError('loaded integration window is not a canonical prior function instruction')
        if sha(raw(start, end)) != item['sha256']:
            raise ValueError('integration instruction bytes differ from the pinned image')
        decoded = decode(start, end)
        if len(decoded) != 1 or decoded[0][:2] != (start, end-start):
            raise ValueError('integration window is not one complete decoded instruction')
        loaded.add(start); spans.append((start, end))
    spans.sort()
    if any(b > c for (_, b), (c, _) in zip(spans, spans[1:])):
        raise ValueError('integration instruction windows overlap')
    missing = [address(pc) for pc in coverage.get('unvisited_all', [])]
    visited = coverage.get('all_visited')
    if (coverage.get('all_decoded') != len(loaded) or type(visited) is not int
        or not 0 <= visited <= len(loaded) or len(missing) != len(set(missing))
        or not set(missing) <= loaded or len(missing) != len(loaded)-visited):
        raise ValueError('integration loaded coverage differs from its exact instruction set')
    missing = set(missing)
    bodies = report.get('joined_bodies')
    if not isinstance(bodies, dict) or not bodies:
        raise ValueError('integration report lacks named reused bodies')
    declared = {}
    for name, body in bodies.items():
        start, end = address(body['start']), address(body['end_exclusive'])
        parent = regions.get((start, end))
        if (parent is None or parent['kind'] != 'function_region'
            or parent['sha256'] != body['sha256'] or sha(raw(start, end)) != body['sha256']):
            raise ValueError('joined body is not an exact previously reconstructed function')
        pcs = {pc for pc, _, _ in decode(start, end)}
        absent = [address(pc) for pc in body.get('unvisited', [])]
        if (not pcs <= loaded or body.get('decoded') != len(pcs)
            or body.get('visited') != len(pcs-missing) or len(absent) != len(set(absent))
            or set(absent) != pcs & missing):
            raise ValueError('joined body coverage differs from loaded instruction observations')
        declared[name] = {'start': hex_address(start), 'end_exclusive': hex_address(end),
            'decoded': len(pcs), 'visited': len(pcs-missing), 'unvisited': len(absent)}
    static = report.get('static_data')
    if not isinstance(static, dict) or not static:
        raise ValueError('integration report lacks its reused table bindings')
    auxiliary = auxiliary or {}; ancillary = []
    for name, item in static.items():
        start, end = address(item['start']), address(item['end_exclusive'])
        if end <= start or sha(raw(start, end)) != item['sha256']:
            raise ValueError('integration static bytes do not match the pinned image')
        if not any(a <= start < end <= b for a, b, _ in data_ranges):
            prior = auxiliary.get(name)
            if prior is None or any(item[key] != prior[key] for key in ('start', 'end_exclusive', 'sha256')):
                raise ValueError('integration auxiliary bytes lack matching prior evidence')
            ancillary.append({'name': name, **prior})
    return {'loaded_instructions': len(loaded), 'visited_loaded_instructions': visited,
        'unvisited_loaded_instructions': len(missing), 'reused_static_spans': len(static),
        'previously_excluded_data_spans': len(static)-len(ancillary), 'prior_auxiliary_spans': ancillary,
        'reused_bodies': declared, 'new_functions': 0, 'new_data_exclusions': 0}


class IntegrationsInventory(ConstructionInventory):
    def __init__(self, *required, configured_signal_report, additional_reports=()):
        self.configured_report = local(configured_signal_report).relative_to(ROOT).as_posix()
        if self.configured_report != CONFIGURED_REPORT:
            raise ValueError('integration adapter requires frozen configured-signal02')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if self.configured_report in additions:
            raise ValueError('configured-signal report is already selected explicitly')
        super().__init__(*required, additions)
        self.configured_bindings = None

    def reports(self):
        omitted = super().reports()
        path = local(self.configured_report); raw_report = self.read(self.configured_report)
        if sha(raw_report) != CONFIGURED_SHA:
            raise ValueError('frozen configured-signal report digest changed')
        report = json.loads(raw_report)
        prior_audio = json.loads(self.read(AUDIO_REPORT))
        for name, expected in AUXILIARY.items():
            if prior_audio['bound_static_data'].get(name) != {k:v for k,v in expected.items() if k != 'kind'}:
                raise ValueError('prior audio auxiliary binding changed')
        self.configured_bindings = configured_evidence(report, self.raw, self.decode,
            self.regions, self.data_ranges, AUXILIARY)
        self.audit_sources(report['source_sha256'])
        manifest_path = (path.parent/'build-manifest.json').relative_to(ROOT).as_posix()
        raw_manifest = self.read(manifest_path)
        if sha(raw_manifest) != CONFIGURED_MANIFEST_SHA:
            raise ValueError('frozen configured-signal manifest digest changed')
        manifest = json.loads(raw_manifest)
        for name, digest in manifest['files'].items():
            if Path(name).name != name:
                raise ValueError('integration artifact name must identify a direct manifest sibling')
            artifact = (path.parent/name).relative_to(ROOT).as_posix()
            if sha(self.read(artifact)) != digest:
                raise ValueError('integration artifact differs from its completed manifest')
            self.audited_artifacts.add(artifact)
        self.modules.append({'module': path.parent.name, 'report': self.configured_report,
            'report_sha256': sha(raw_report), 'declared_regions': 0, 'integration_only': True,
            'source_hashes_checked': len(report['source_sha256']), 'scope_limits': report['limitations'],
            'instruction_coverage': coverage_summary(report),
            'reported_region_coverage': self.configured_bindings['reused_bodies'],
            'reported_coverage_notes': {'new_function_declarations_are_empty': True,
                'loaded_windows_are_bound_to_existing_functions': True,
                'loaded_coverage_is_not_a_whole_firmware_measure': True},
            'integration_evidence': self.configured_bindings})
        return [name for name in omitted if name != self.configured_report]

    def run(self):
        report = super().run()
        require_preserved_reports(report['selected_reports'])
        self.read(ADAPTER)
        report.update(schema=10, integration_inventory_adapter=ADAPTER,
            configured_signal_evidence=self.configured_bindings)
        report['audits'].update(inventory11_all_fifty_reports_retained=True,
            configured_signal_empty_function_declaration_preserved=True,
            configured_signal_loaded_windows_belong_to_existing_function_regions=True,
            configured_signal_reused_bodies_and_loaded_coverage_independently_bound=True,
            configured_signal_static_bytes_match_prior_evidence=True,
            configured_signal_auxiliary_bytes_are_not_promoted_to_functions_or_data_exclusions=True)
        report['scope_policy'].extend([
            'configured-signal02 declares no new functions: its exact reused bodies, loaded instruction windows and execution gaps are authenticated without adding regions or candidates',
            'integration-only evidence retains its original report and manifest bytes; no synthetic function declaration is inserted to satisfy an older loader schema',
            'thirty configured-signal static spans match existing data exclusions; the reset configuration and task-registration witness retain their prior audio-report bindings without any new code/data classification',
            'source construction and signal processing are separate synchronous invocations on retained public bytes, not a newly discovered native call edge or scheduler proof'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject altered integration claims using a minimal independently decoded map."""
    checks = 0
    code = {0x1000: b'\x80\x00', 0x1002: b'\x80\x00'}; data = b'\x01\x02'
    def raw(a, b):
        return data[a-0x2000:b-0x2000] if a >= 0x2000 else b''.join(code[p] for p in range(a, b, 2))
    def decode(a, b):return [(pc, 2, 'rts') for pc in range(a, b, 2)]
    regions = {(0x1000, 0x1004): {'kind': 'function_region', 'sha256': sha(raw(0x1000, 0x1004))}}
    known = [(0x2000, 0x2002, 'existing_data')]
    valid = {'result': 'pass', 'original_image_sha256': REFERENCE_SHA, 'integration_only': True,
        'new_original_functions': 0, 'functions': {}, 'new_static_data_ranges': [],
        'instruction_coverage': {'new_decoded': 0, 'new_visited': 0, 'unvisited_new': [],
            'all_decoded': 2, 'all_visited': 1, 'unvisited_all': [0x1002]},
        'bound_instruction_windows': {hex(pc): {'start': pc, 'end_exclusive': pc+2, 'sha256': sha(v)} for pc, v in code.items()},
        'joined_bodies': {'whole': {'start': 0x1000, 'end_exclusive': 0x1004,
            'sha256': regions[(0x1000, 0x1004)]['sha256'], 'decoded': 2, 'visited': 1, 'unvisited': [0x1002]}},
        'static_data': {'table': {'start': 0x2000, 'end_exclusive': 0x2002, 'sha256': sha(data)}}}
    def rejected(report=valid, parents=regions, ranges=known, decoder=decode, reader=raw, auxiliary=None):
        nonlocal checks
        try:configured_evidence(report, reader, decoder, parents, ranges, auxiliary)
        except (ValueError, KeyError, TypeError):checks += 1; return
        raise AssertionError('invalid integration evidence accepted')
    evidence = configured_evidence(valid, raw, decode, regions, known)
    assert evidence['new_functions'] == evidence['new_data_exclusions'] == 0; checks += 1
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
        ((), 'integration_only', False), ((), 'new_original_functions', 1),
        ((), 'functions', {'fake': {}}), ((), 'new_static_data_ranges', [0x2002]),
        ((), 'bound_instruction_windows', {}), ((), 'joined_bodies', {}), ((), 'static_data', {}),
        (('instruction_coverage',), 'new_decoded', 2), (('instruction_coverage',), 'new_visited', 1),
        (('instruction_coverage',), 'unvisited_new', [0x1002]),
        (('instruction_coverage',), 'all_decoded', 3), (('instruction_coverage',), 'all_visited', 3),
        (('instruction_coverage',), 'unvisited_all', [0x1002, 0x1002]),
        (('instruction_coverage',), 'unvisited_all', [0x2000]),
        (('bound_instruction_windows', '0x1000'), 'start', 0x1002),
        (('bound_instruction_windows', '0x1000'), 'end_exclusive', 0x1004),
        (('bound_instruction_windows', '0x1000'), 'sha256', '0'*64),
        (('joined_bodies', 'whole'), 'end_exclusive', 0x1002),
        (('joined_bodies', 'whole'), 'sha256', '0'*64),
        (('joined_bodies', 'whole'), 'decoded', 3), (('joined_bodies', 'whole'), 'visited', 2),
        (('joined_bodies', 'whole'), 'unvisited', [0x1000]),
        (('static_data', 'table'), 'sha256', '0'*64),
        (('static_data', 'table'), 'end_exclusive', 0x2003)]:
        bad = copy.deepcopy(valid); node = bad
        for part in path:node = node[part]
        node[key] = value; rejected(bad)
    rejected(parents={}); rejected(ranges=[]); rejected(decoder=lambda a,b: [])
    altered = copy.deepcopy(regions); altered[(0x1000, 0x1004)]['kind'] = 'command_fragment'; rejected(parents=altered)
    # A valid instruction decoded at an interior byte cannot create a new
    # canonical start in an otherwise reconstructed parent.
    extra = copy.deepcopy(valid); extra['instruction_coverage'].update(all_decoded=3, all_visited=2)
    extra['bound_instruction_windows']['0x1102'] = {'start':0x1102, 'end_exclusive':0x1104, 'sha256':sha(b'\x80\x00')}
    parents = dict(regions); parents[(0x1100, 0x1104)] = {'kind':'function_region', 'sha256':sha(b'\0\0\x80\x00')}
    def extra_raw(a,b):return b'\0\0\x80\x00'[a-0x1100:b-0x1100] if 0x1100<=a<b<=0x1104 else raw(a,b)
    def extra_decode(a,b):return [(0x1100,4,'whole packet')] if a==0x1100 else decode(a,b)
    rejected(extra, parents=parents, decoder=extra_decode, reader=extra_raw)
    parents[(0x1100, 0x1104)]['kind'] = 'command_fragment'
    rejected(extra, parents=parents, reader=extra_raw)
    aux = {'table': {**valid['static_data']['table'], 'kind':'prior auxiliary witness'}}
    assert configured_evidence(valid, raw, decode, regions, [], aux)['new_data_exclusions'] == 0; checks += 1
    changed = copy.deepcopy(aux); changed['table']['sha256'] = '0'*64; rejected(ranges=[], auxiliary=changed)
    changed = copy.deepcopy(aux); changed['table']['end_exclusive'] += 1; rejected(ranges=[], auxiliary=changed)
    selected = [*PRESERVED_REPORTS, CONFIGURED_REPORT]; require_preserved_reports(selected); checks += 1
    for omitted in selected:
        try:require_preserved_reports([name for name in selected if name != omitted])
        except ValueError:checks += 1
        else:raise AssertionError('omitted historical evidence accepted')
    try:require_preserved_reports(selected+[CONFIGURED_REPORT])
    except ValueError:checks += 1
    else:raise AssertionError('duplicated evidence accepted')
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 50,
        'new_function_regions': 0, 'new_data_exclusions': 0, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS:parser.add_argument('--'+name)
    parser.add_argument('--configured-signal-report'); parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true'); args = parser.parse_args()
    required = tuple(getattr(args, name.replace('-', '_')) for name in REQUIRED_OPTIONS)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report or args.configured_signal_report:
            parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required) or not args.configured_signal_report:
        parser.error('choose --output or --check and provide every required report')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a fresh directory under build/')
    report = IntegrationsInventory(*required, configured_signal_report=args.configured_signal_report,
        additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'integration-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'configured_signal_evidence': report['configured_signal_evidence']}, indent=2))


if __name__ == '__main__':main()
