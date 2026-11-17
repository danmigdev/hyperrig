"""Audit sample engines, their direct joins and the bounded correlation table.

Retain all inventory17 evidence. Authenticate loaded instruction windows against
complete original bodies; auxiliary raw-index reads never enlarge the table.
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
from inventory_reverse_integrations import REQUIRED_OPTIONS, AUXILIARY
from inventory_reverse_models import MODEL_REPORT, MODEL_SHA
from inventory_reverse_parameter_construction import span, static_identity
from inventory_reverse_storage_coordination import (StorageCoordinationInventory,
    REPORT as COORDINATION_REPORT, PRESERVED_REPORTS as INVENTORY16_REPORTS)

ADAPTER = 'tools/inventory_reverse_sample_processing.py'
MODEL = 'tools/effect_sample_processing_machine.py'
VERIFIER = 'tools/verify_effect_sample_processing.py'
REPORT = 'build/reverse-effect-sample-processing-01/verification.json'
REPORT_SHA = 'ee7486a6df065262f121e9c05527dc7ab237af64f7af290af959a02aaac3afa3'
MANIFEST_SHA = '6bb7c58f5a9a2519d7ae7a32810f54990eee57841e38b920c2be558b49711ef2'
PROCESSING_REPORT = 'build/reverse-effect-processing-02/verification.json'
AUDIO_REPORT = 'build/reverse-audio-task-03/verification.json'
PRESERVED_REPORTS = (*INVENTORY16_REPORTS, COORDINATION_REPORT)
REGIONS = {
    'cascade': (0x01c08b3e, 0x01c08c76), 'transition': (0x01c0b5d6, 0x01c0ba14),
    'mixer': (0x01c0ba14, 0x01c0bbce), 'width': (0x01c0bbce, 0x01c0bd8c),
    'update': (0x01c0bd8c, 0x01c0be92), 'ring': (0x01c18f90, 0x01c19448),
    'correlation': (0x01c19448, 0x01c1958e),
}
JOINED = {
    'constructor': (0x0202cf62, 0x0202ddfc), 'type25_builder': (0x0202b87e, 0x0202ba56),
    'dispatch': (0x01c0deb6, 0x01c0f678), 'individual': (0x01c0f678, 0x01c10446),
    'grouped': (0x01c10446, 0x01c10818), 'stage': (0x01c10e06, 0x01c11b00),
    'task': (0x01c01e5e, 0x01c02dbc), 'q28': (0x01c15dec, 0x01c15fdc),
    'q28_residual': (0x01c15fdc, 0x01c16222),
}
DIRECT_SITES = {
    0x01c0e6a2: 0x01c08b3e, 0x01c0e706: 0x01c08b3e,
    0x01c0f2e2: 0x01c18f90, 0x01c0f37c: 0x01c18f90,
    0x01c0f3ae: 0x01c0b5d6, 0x01c0f45c: 0x01c0ba14,
    0x01c0f4f4: 0x01c0ba14, 0x01c0f480: 0x01c0bbce,
    0x01c0f492: 0x01c0bbce, 0x01c0f630: 0x01c0bd8c,
}
INTERNAL_SITES = {0x01c08c22: 0x01c15fdc, 0x01c08c38: 0x01c15dec,
    0x01c0be30: 0x01c19448}
GAP_GROUPS = (
    (0x01c0b718, 0x01c0b71c, 0x01c0b71e, 0x01c0b720, 0x01c0b724, 0x01c0b726),
    (0x01c0b800, 0x01c0b804, 0x01c0b806, 0x01c0b808, 0x01c0b80a,
        0x01c0b80c, 0x01c0b812, 0x01c0b814),
    (0x01c0b8ea, 0x01c0b8ee, 0x01c0b8f0, 0x01c0b8f4),
    (0x01c0b744,), (0x01c0ba0c,),
)
WEIGHTS = (0x0203b7e0, 0x0203b880,
    '1e8b8aa3482ac62ae54fcaf6b4dd11b104b34129c7308ad7cae9114f4e9c7cd8')
RAW_READS = (
    (0x0203b880, 0x0203b8d0, '575987f39344e07899cc9073cdb0daeec6ababae671e8310d2c4c2ff82d60aa8'),
    (0x02040790, 0x020407e0, '50922a29723112510046defa49a2e55704bf2a6b5393a3e02cf46baa2d38023a'),
)
# Raw index 2 reads part of an already classified selector table. Retain that
# earlier role; the updater witness adds no classification of its own. Index
# 255 has no prior data classification.
RAW_PRIOR_DATA = {(0x0203b880, 0x0203b8d0):
    [(0x0203b880, 0x0203b8d4, 'effect_support_selector')],
    (0x02040790, 0x020407e0): []}
# Bind the field provenance, unsigned caller limit, descriptor construction and
# both pair loops. The two marked packets store the pre-update register value.
TABLE_SITES = {
    0x01c0dec8: (2, 'r15_r14 = r1_r0  #'),
    0x01c0e08e: (4, 'r6 = r14 + 84'),
    0x01c0e56c: (4, 'r0 = [r6++=204]'),
    0x01c0e590: (4, 'r0 = r6 + 117  #'),
    0x01c0e596: (2, '[sp+96] = r0'),
    0x01c0f22c: (2, '[sp+64] = r14'),
    0x01c0f60c: (2, 'r12 = [sp+64]'),
    0x01c0f610: (2, 'r9 = [sp+96]'),
    0x01c0f626: (4, 'r0 = b[r9+2] (u)'),
    0x01c0f62a: (4, 'if (r0 > 1) goto 10'),
    0x01c0f62e: (2, 'r0 = r12'),
    0x01c0f630: (4, 'call -14504'),
    0x01c0bd90: (4, 'r8 = r0 + 404'),
    0x01c0bd94: (4, 'r12 = b[r8+3] (u)'),
    0x01c0bdf8: (4, 'r0 = r12 * 0x50  #'),
    0x01c0bdfc: (2, '[sp] = r6'),
    0x01c0bdfe: (6, 'r1 = 33798112'),
    0x01c0be04: (2, 'r0 = r0 + r1'),
    0x01c0be0a: (2, '[sp+4] = r0'),
    0x01c0be1c: (2, 'r0 = 20'),
    0x01c0be1e: (2, 'r0 = r4.b0 (u)  #'),
    0x01c0be20: (2, '[sp+16] = r0'),
    0x01c0be22: (4, 'r0 = r2 + 1648  #'),
    0x01c0be26: (2, '[sp+20] = r0'),
    0x01c0be2e: (2, 'r0 = sp + 0'),
    0x01c0be30: (6, 'call 54802'),
    0x01c19450: (2, 'r7 = [r0+4]'),
    0x01c19456: (2, 'r2 = [r0+16]'),
    0x01c19462: (2, '[sp+4] = r2'),
    0x01c19474: (2, 'r3 = [r7+0]'),
    0x01c194a2: (2, 'r7 = r7 + 4'),
    0x01c194ae: (2, 'r3 = [r7+0]'),
    0x01c194dc: (2, 'r7 = r7 + 4'),
    0x01c194e2: (2, 'r0 = [sp+4]'),
    0x01c194e4: (2, 'r0 += -2'),
    0x01c194e6: (2, '[sp+4] = r0'),
    0x01c194e8: (2, 'if (r0 != 0) goto -124'),
    0x01c194f2: (2, 'r3 = [r7+0]'),
    0x01c19520: (2, 'r7 = r7 + 4'),
    0x01c1952c: (2, 'r3 = [r7+0]'),
    0x01c1955a: (2, 'r7 = r7 + 4'),
    0x01c19560: (2, 'r0 = [sp+4]'),
    0x01c19562: (2, 'r0 += -2'),
    0x01c19564: (2, '[sp+4] = r0'),
    0x01c19566: (2, 'if (r0 != 0) goto -124'),
}


def registry_evidence(report, constants):
    if (report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA
        or type(report.get('new_original_functions')) is not int or report['new_original_functions'] != 7
        or type(report.get('scripted_new_sample_replacements')) is not int
        or report['scripted_new_sample_replacements'] != 0):
        raise ValueError('sample processing requires seven passing pinned-image bodies without replacements')
    for key, expected in (('functions', REGIONS), ('joined_bodies', JOINED)):
        if {name: span(item) for name, item in report[key].items()} != expected:
            raise ValueError('sample whole-body registry changed')
    if constants.get('REGIONS') != REGIONS or constants.get('DIRECT_SITES') != DIRECT_SITES:
        raise ValueError('sample model body or direct-join registry changed')


def table_evidence(report, raw, decode, isa):
    item = report['static_data']['correlation_weights']
    if static_identity(item) != WEIGHTS or sha(raw(*WEIGHTS[:2])) != WEIGHTS[2]:
        raise ValueError('sample correlation weights differ from exactly two twenty-word blocks')
    decoded, consumers = {}, {}
    for name, key, count in (('dispatch', 'joined_bodies', 1992),
            ('update', 'functions', 94), ('correlation', 'functions', 122)):
        item = report[key][name]; a, b = (JOINED if key == 'joined_bodies' else REGIONS)[name]
        body = decode(a, b)
        if span(item) != (a, b) or sha(raw(a, b)) != item['sha256'] or len(body) != count:
            raise ValueError('sample table consumer bytes or complete extent changed')
        decoded.update({pc: (size, text) for pc, size, text in body})
        consumers[name] = {'start': hex_address(a), 'end_exclusive': hex_address(b),
            'sha256': item['sha256'], 'decoded': len(body)}
    for pc, (size, text) in TABLE_SITES.items():
        if decoded.get(pc) != (size, text.removesuffix('  #')):
            raise ValueError('sample table proof is not a canonical consumer instruction')
        found = codec.decode(isa, raw(pc, pc+size), 0)
        if found is None or found[2] != size or codec.format(found[0], found[1]) != text:
            raise ValueError(f'sample table address, index, count or packet proof changed at {pc:#x}')
    return {'start': hex_address(WEIGHTS[0]), 'end_exclusive': hex_address(WEIGHTS[1]),
        'sha256': WEIGHTS[2], 'bytes': 160, 'blocks': 2, 'words_per_block': 20,
        'consumers': consumers, 'decoded_proof_sites': len(TABLE_SITES),
        'raw_updater_index_is_full_byte': True, 'bounded_by_dispatcher': True,
        'proof_sites': [hex_address(pc) for pc in sorted(TABLE_SITES)]}


def with_sample_range(ranges):
    a, b = WEIGHTS[:2]
    if any(a < y and x < b for x, y, _ in ranges):
        raise ValueError('sample weights overlap a prior data classification')
    return [*ranges, (a, b, 'sample_correlation_weights')]


def pc_set(values, allowed, label):
    pcs = [address(value) for value in values]
    if len(pcs) != len(set(pcs)) or not set(pcs) <= allowed:
        raise ValueError(label+' contains duplicate or noncanonical PCs')
    return set(pcs)


def runtime_evidence(report, parents, raw, decode, regions, data_ranges, invariant_gaps):
    registry_evidence(report, {'REGIONS': REGIONS, 'DIRECT_SITES': DIRECT_SITES})
    # Decode each complete parent once. Never establish instruction boundaries
    # by decoding a claimed window in isolation.
    canonical, body_pcs = {}, {}
    for bounds, parent in regions.items():
        if parent['kind'] != 'function_region': continue
        body = decode(*bounds); body_pcs[bounds] = {pc for pc, _, _ in body}
        for pc, size, text in body:
            if pc in canonical: raise ValueError('sample canonical parent bodies overlap')
            canonical[pc] = (size, text)
    new = set().union(*(body_pcs[b] for b in REGIONS.values()))
    expected = set(new)
    for parent in (parents['processing'], parents['audio']):
        expected.update(address(pc) for pc in parent['bound_instruction_windows'])
    for item in parents['models']['loaded_instruction_windows']:
        a, b = span(item)
        if sha(raw(a, b)) != item['sha256']:
            raise ValueError('sample inherited model window changed')
        pcs = {pc for pc in canonical if a <= pc < b}
        if not pcs or min(pcs) != a or max(pcs)+canonical[max(pcs)][0] != b:
            raise ValueError('sample model window cuts a canonical instruction')
        expected.update(pcs)
    loaded = set()
    for key, item in report['bound_instruction_windows'].items():
        a, b = span(item)
        if (address(key) != a or a in loaded or a not in canonical
            or canonical[a][0] != b-a or sha(raw(a, b)) != item['sha256']):
            raise ValueError('sample loaded window is not an exact canonical instruction')
        loaded.add(a)
    if loaded != expected:
        raise ValueError('sample loaded instructions differ from the exact parent/new-body union')
    coverage = report['instruction_coverage']
    gaps = pc_set(coverage['unvisited_all'], loaded, 'sample loaded gaps')
    new_gaps = pc_set(coverage['unvisited_new'], new, 'sample new gaps')
    counts = {'new_decoded': len(new), 'new_visited': len(new-new_gaps),
        'all_decoded': len(loaded), 'all_visited': len(loaded-gaps)}
    if new_gaps != new & gaps or any(type(coverage[k]) is not int or coverage[k] != v for k, v in counts.items()):
        raise ValueError('sample coverage differs from canonical loaded/new sets')
    grouped = coverage['unvisited_by_entry_invariant']
    if ({reason: tuple(pcs) for reason, pcs in grouped.items()}
            != {reason: tuple(pcs) for reason, pcs in invariant_gaps.items()}
        or coverage['unclassified_unvisited'] != []
        or {tuple(sorted(group)) for group in grouped.values()} != set(GAP_GROUPS)
        or sum(map(len, grouped.values())) != 20
        or set().union(*(set(group) for group in grouped.values())) != new_gaps):
        raise ValueError('sample twenty original invariant gaps changed')
    declared = {}
    for key in ('functions', 'joined_bodies'):
        for name, item in report[key].items():
            a, b = span(item); parent = regions.get((a, b)); pcs = body_pcs.get((a, b), set())
            absent = pc_set(item['unvisited'], pcs, 'sample per-body gaps')
            field = 'instructions' if key == 'functions' else 'decoded'
            if (parent is None or parent['kind'] != 'function_region'
                or parent['sha256'] != item['sha256'] or sha(raw(a, b)) != item['sha256']
                or not pcs <= loaded or type(item[field]) is not int or item[field] != len(pcs)
                or type(item['visited']) is not int or item['visited'] != len(pcs-gaps)
                or absent != pcs & gaps):
                raise ValueError('sample complete-body bytes or coverage changed')
            declared[name] = {'decoded': len(pcs), 'visited': len(pcs-gaps),
                'unvisited': len(absent), 'reused': key == 'joined_bodies'}
    sites = {}
    for key, item in report['direct_dispatcher_joins'].items():
        pc, target = address(key), address(item['target'])
        if pc in sites or item['visited'] is not True: raise ValueError('sample join is duplicated or unvisited')
        sites[pc] = target
    if sites != DIRECT_SITES: raise ValueError('sample direct-join set changed')
    observed_internal = {}
    for pc in new:
        size, text = canonical[pc]
        if text.startswith('call '):
            match = re.fullmatch(r'call (-?\d+)', text)
            if match is None: raise ValueError('unreviewed indirect call in sample numerical body')
            observed_internal[pc] = pc+size+int(match[1])
    if observed_internal != INTERNAL_SITES: raise ValueError('sample numerical callee closure changed')
    for pc, target in (DIRECT_SITES | INTERNAL_SITES).items():
        size, text = canonical[pc]
        if (text != f'call {target-pc-size}' or pc in gaps or target in gaps
            or target not in loaded or not any(a == target for a, _ in body_pcs)):
            raise ValueError('sample direct join is not an executed original call and complete callee')
    inherited = dict(parents['processing']['static_data'])
    for name, item in parents['models']['loaded_static_data'].items():
        if name in inherited and static_identity(inherited[name]) != static_identity(item):
            raise ValueError('sample inherited static roles disagree')
        inherited[name] = item
    static = report['static_data']
    if set(static) != {*inherited, 'correlation_weights'}:
        raise ValueError('sample static role set differs from both exact parents and weights')
    auxiliary_roles = []
    for name, item in static.items():
        a, b = span(item)
        if sha(raw(a, b)) != item['sha256']:
            raise ValueError('sample static bytes differ from original')
        if name in inherited and static_identity(item) != static_identity(inherited[name]):
            raise ValueError('sample inherited static role changed')
        if name == 'correlation_weights' and static_identity(item) != WEIGHTS:
            raise ValueError('sample weight-table extent changed')
        if not any(x <= a < b <= y for x, y, _ in data_ranges):
            if name not in AUXILIARY or static_identity(item) != static_identity(AUXILIARY[name]):
                raise ValueError('sample auxiliary role lacks exact prior evidence')
            auxiliary_roles.append(name)
    auxiliary = report['auxiliary_raw_updater_rom_reads']
    if tuple(map(static_identity, auxiliary)) != RAW_READS:
        raise ValueError('sample raw updater ROM witnesses changed or enlarged')
    for a, b, digest in RAW_READS:
        overlaps = sorted((x, y, name) for x, y, name in data_ranges if a < y and x < b)
        if sha(raw(a, b)) != digest or overlaps != RAW_PRIOR_DATA[(a, b)]:
            raise ValueError('sample raw updater witnesses changed prior data classifications')
    derivative = report['caller_derivative']
    if derivative != {'frozen_sha256': 'f4e475acc0f797673740ac0428811d3b83129b4356878606484c1b54c81421b2',
            'native_direct_sites': 10, 'textual_replacements': 9, 'result': 'pass'}:
        raise ValueError('sample checked caller derivative changed')
    return {'new_whole_functions': 7, 'named_reused_whole_functions': 9, **counts,
        'unvisited_new': len(new_gaps), 'unvisited_loaded': len(gaps),
        'direct_dispatcher_joins': len(DIRECT_SITES), 'internal_numerical_calls': len(INTERNAL_SITES),
        'exact_parent_and_new_instruction_union': True, 'inherited_static_roles': len(inherited),
        'prior_auxiliary_roles': sorted(auxiliary_roles), 'raw_updater_auxiliary_windows': 2,
        'raw_updater_auxiliary_bytes': 160, 'raw_index2_retains_prior_selector_role': True,
        'raw_index255_remains_unclassified': True, 'new_data_exclusions': 1,
        'new_data_bytes': 160, 'per_function': declared}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 59 or len(set(PRESERVED_REPORTS)) != 59:
        raise ValueError('inventory17 must contain 59 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('sample inventory omitted or duplicated prior evidence')


class SampleProcessingInventory(StorageCoordinationInventory):
    def __init__(self, *required, sample_processing_report, additional_reports=(), **options):
        if local(sample_processing_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen sample-processing01')
        additions = [local(p).relative_to(ROOT).as_posix() for p in additional_reports]
        if REPORT in additions: raise ValueError('sample processing report is already selected')
        self.sample_table, self.sample_runtime = None, None
        super().__init__(*required, additional_reports=[*additions, REPORT], **options)

    def add_known_data(self):
        super().add_known_data(); raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen sample report changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report['source_sha256'].get(MODEL) != sha(source): raise ValueError('sample model source changed')
        registry_evidence(report, declared_constants(source.decode('utf-8')))
        self.sample_table = table_evidence(report, self.raw, self.decode, self.instructions)
        self.data_ranges = with_sample_range(self.data_ranges)

    def reports(self):
        omitted = super().reports(); self.audit_manifest(REPORT, MANIFEST_SHA)
        report = json.loads(self.read(REPORT))
        parents = {name: json.loads(self.read(path)) for name, path in
            (('processing', PROCESSING_REPORT), ('models', MODEL_REPORT), ('audio', AUDIO_REPORT))}
        if sha(self.read(MODEL_REPORT)) != MODEL_SHA: raise ValueError('sample model parent changed')
        invariant_gaps = declared_constants(self.read(VERIFIER).decode('utf-8'))['INVARIANT_GAPS']
        self.sample_runtime = runtime_evidence(report, parents, self.raw, self.decode,
            self.regions, self.data_ranges, invariant_gaps)
        module = next(item for item in self.modules if item['report'] == REPORT)
        module.update(reported_region_coverage={name: self.sample_runtime['per_function'][name] for name in REGIONS},
            sample_processing_runtime_evidence=self.sample_runtime)
        return omitted

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=16, sample_processing_inventory_adapter=ADAPTER,
            sample_processing_table=self.sample_table, sample_processing_runtime_evidence=self.sample_runtime)
        report['audits'].update(inventory17_all_fifty_nine_reports_retained=True,
            sample_complete_bodies_and_canonical_loaded_instruction_union_bound=True,
            sample_direct_joins_and_numerical_callee_closure_independently_decoded=True,
            sample_correlation_table_has_exact_caller_and_pair_loop_bounds=True,
            sample_raw_updater_ROM_reads_remain_auxiliary_not_data_exclusions=True,
            sample_twenty_invariant_gaps_remain_unexecuted=True)
        report['scope_policy'].extend([
            'sample processing adds seven complete bodies; ten direct dispatcher joins and three internal numerical calls execute original callees',
            'the 22919 loaded instructions are the exact union of the frozen processing, construction and audio corpora plus seven new bodies; 18450 remain unvisited in this corpus',
            'only two twenty-word correlation blocks add a data exclusion; separate raw-index reads at indices 2 and 255 authenticate bytes without enlarging that table',
            'twenty transition instructions remain unexecuted under documented full-entry invariants, including the pinned floating conversion semantics',
            'constructor preparation is a separate invocation with retained public state, not proof of a recovered scheduling/allocation edge',
            'raw count, mapping and finite work guards retain their stated domains; controlled platform services do not establish physical audio or hardware timing'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject altered coverage, call joins, boundaries and data classification."""
    packed, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(packed) != REFERENCE_SHA or unpack_app(packed)[2]['app.bin'] != app:
        raise ValueError('self-check original image changed')
    inv = object.__new__(Inventory); inv.app = app; inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    prior = json.loads(local('build/reverse-inventory-17/inventory.json').read_bytes())
    inv.data_ranges = with_sample_range([(address(r['start']), address(r['end_exclusive']), r['kind'])
        for r in prior['known_data_ranges']])
    decode = functools.cache(inv.decode)
    raw_report = local(REPORT).read_bytes()
    if sha(raw_report) != REPORT_SHA: raise ValueError('self-check frozen sample report changed')
    report = json.loads(raw_report); constants = declared_constants(local(MODEL).read_text())
    gaps = declared_constants(local(VERIFIER).read_text())['INVARIANT_GAPS']
    parents = {name: json.loads(local(path).read_bytes()) for name, path in
        (('processing', PROCESSING_REPORT), ('models', MODEL_REPORT), ('audio', AUDIO_REPORT))}
    regions = {span(item): item for item in prior['reconstructed_regions']}
    regions.update({span(item): {'kind': 'function_region', 'sha256': item['sha256']}
        for item in report['functions'].values()})
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid sample evidence accepted')
    def audit(item, bindings=regions, ranges=inv.data_ranges):
        return runtime_evidence(item, parents, inv.raw, decode, bindings, ranges, gaps)
    registry_evidence(report, constants); checks += 1
    assert table_evidence(report, inv.raw, decode, inv.instructions)['bytes'] == 160; checks += 1
    assert audit(report)['new_visited'] == 1304; checks += 1
    for key in ('functions', 'joined_bodies'):
        for name in report[key]:
            count = 'instructions' if key == 'functions' else 'decoded'
            for field, value in [('start', 0), ('sha256', '0'*64), (count, True), ('visited', -1)]:
                changed = copy.deepcopy(report); changed[key][name][field] = value; rejected(audit, changed)
    pc = next(iter(report['bound_instruction_windows']))
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'new_original_functions', True),
        ((), 'original_image_sha256', '0'*64), ((), 'scripted_new_sample_replacements', 1),
        (('instruction_coverage',), 'new_visited', 1324),
        (('instruction_coverage',), 'all_visited', True),
        (('instruction_coverage',), 'unvisited_all', report['instruction_coverage']['unvisited_all']+[REGIONS['cascade'][0]+1]),
        (('instruction_coverage',), 'unvisited_new', []),
        (('instruction_coverage',), 'unclassified_unvisited', [0x01c0b718]),
        (('instruction_coverage',), 'unvisited_by_entry_invariant', {}),
        (('bound_instruction_windows', pc), 'end_exclusive', 0),
        (('bound_instruction_windows', pc), 'sha256', '0'*64),
        (('caller_derivative',), 'native_direct_sites', 9),
        (('static_data', 'correlation_weights'), 'end_exclusive', WEIGHTS[1]+80),
        (('static_data', 'costs'), 'start', 0),
        ((), 'auxiliary_raw_updater_rom_reads', report['auxiliary_raw_updater_rom_reads'][:1])]:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(audit, changed)
    changed = copy.deepcopy(report); changed['bound_instruction_windows'][str(address(pc))] = changed['bound_instruction_windows'][pc]
    rejected(audit, changed)
    changed = copy.deepcopy(report); changed['instruction_coverage']['unvisited_all'].append(changed['instruction_coverage']['unvisited_all'][0])
    rejected(audit, changed)
    for pc in DIRECT_SITES:
        for field, value in [('target', REGIONS['ring'][0]+2), ('visited', False)]:
            changed = copy.deepcopy(report); changed['direct_dispatcher_joins'][hex(pc)][field] = value; rejected(audit, changed)
    for name in ('reset_configuration', 'task_registration'):
        # The inherited auxiliary classification is separately audited by the
        # prior adapter; adding an auxiliary raw updater range is rejected here.
        assert name in audit(report)['prior_auxiliary_roles']; checks += 1
    for a, b, _ in RAW_READS:
        rejected(audit, report, regions, [*inv.data_ranges, (a, b, 'invalid_raw_table')])
    for name in ('REGIONS', 'DIRECT_SITES'):
        changed = dict(constants); changed[name] = {}; rejected(registry_evidence, report, changed)
    for a, b in (WEIGHTS[:2], (WEIGHTS[0]-2, WEIGHTS[0]+2), (WEIGHTS[1]-2, WEIGHTS[1]+2)):
        rejected(with_sample_range, [(a, b, 'overlap')])
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 59,
        'new_data_exclusions': 1, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report',
        'storage_coordination_report', 'sample_processing_report')
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
    report = SampleProcessingInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'sample-processing-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'sample_processing_runtime_evidence': {k: v for k, v in report['sample_processing_runtime_evidence'].items()
            if k != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
