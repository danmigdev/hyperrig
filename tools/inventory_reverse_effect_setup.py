"""Audit original effect setup, exact table extents and source integration.

Retain inventory19 and all frozen evidence. Decode whole bodies before binding
instruction windows; distinguish fixed-input gaps and raw helper reads from
executed coverage and classified tables.
"""
from __future__ import annotations
import argparse
import copy
import functools
import json
import re
import struct
from pathlib import Path

from inventory_reverse import (Inventory, ROOT, REFERENCE, REFERENCE_SHA, APP,
    address, hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_effects import declared_constants
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_integrations import REQUIRED_OPTIONS
from inventory_reverse_models import UNCLASSIFIED as MODEL_UNCLASSIFIED
from inventory_reverse_parameter_construction import (span, static_identity,
    REPORT as PARAMETER_REPORT, REPORT_SHA as PARAMETER_SHA)
from inventory_reverse_lifecycle import IR_REPORT, IR_SHA
from inventory_reverse_storage_runtime import (StorageRuntimeInventory, keyed, pc_set,
    REPORT as STORAGE_RUNTIME_REPORT, PRESERVED_REPORTS as INVENTORY18_REPORTS)

ADAPTER = 'tools/inventory_reverse_effect_setup.py'
MODEL = 'tools/effect_setup_machine.py'
REPORT = 'build/reverse-effect-setup-03/verification.json'
REPORT_SHA = 'bde014640f2abc55e46f453408103010dcb10f95fe0d78dd09574fbaa3ce22e9'
MANIFEST_SHA = 'f991cc25f80efef64b824a2bcc322242e1fd699458eb7aa7c06860e9cf4f6840'
PRESERVED_REPORTS = (*INVENTORY18_REPORTS, STORAGE_RUNTIME_REPORT)
PARENT_REPORTS = {'parameters': (PARAMETER_REPORT, PARAMETER_SHA),
    'ir': (IR_REPORT, IR_SHA)}
# Exact extents reviewed against the complete original bodies. These are not
# inferred from adjacent labels, candidate addresses or individual windows.

REGIONS = {'create': (0x202e710, 0x202ea90),
 'create_disabled': (0x202ea90, 0x202eabc),
 'tempo': (0x202f46c, 0x202f4e8),
 'demand': (0x202def2, 0x202df04),
 'allocate': (0x202e4c2, 0x202e710),
 'refresh29': (0x202e328, 0x202e346),
 'initialize29': (0x202dfe4, 0x202e328),
 'refresh30': (0x202e3ce, 0x202e3f6),
 'initialize30': (0x202e346, 0x202e3ce),
 'pool_claim': (0x202e3f6, 0x202e432),
 'pool_attach': (0x202e432, 0x202e4c2),
 'demand_by_type': (0x202a00a, 0x202a076),
 'partition_sizes': (0x202a1be, 0x202a226),
 'partition_pack': (0x202a250, 0x202a2a4),
 'object_count': (0x2029c22, 0x2029c3e),
 'object_segment': (0x2029ed4, 0x2029f8e),
 'segment_bytes': (0x2029f8e, 0x2029f98),
 'object_total': (0x2029f98, 0x2029fc8),
 'object_extra': (0x2029e3c, 0x2029e54),
 'buffer_selector': (0x1c065a4, 0x1c065b4),
 'layout29': (0x1c05f1c, 0x1c05ff2),
 'saturating_double': (0x202df9a, 0x202dfb6),
 'phase_pair': (0x202dfb6, 0x202dfe4),
 'route_insert': (0x202ddfc, 0x202de50),
 'base_cost': (0x202a664, 0x202a680),
 'insertion_cost': (0x202a5de, 0x202a664),
 'neighbor_group': (0x202a50a, 0x202a5de),
 'default_mode': (0x1c05d92, 0x1c05dcc),
 'has_mode': (0x1c05d78, 0x1c05d92),
 'mode_cost': (0x1c05dcc, 0x1c05e14),
 'next_mode': (0x1c06088, 0x1c06098),
 'pool_full': (0x1c06038, 0x1c0604e),
 'stereo_extra_cost': (0x1c06098, 0x1c060e6),
 'group_eligible': (0x1c0604e, 0x1c0606e),
 'group_fixed': (0x1c0606e, 0x1c06088),
 'total_cost': (0x2028de8, 0x2028e46),
 'slot_cost': (0x2028cb2, 0x2028cf8),
 'route_cost': (0x2028cf8, 0x2028d8a),
 'branch_cost': (0x2028c0c, 0x2028c5c),
 'filter_cost': (0x2028db0, 0x2028de8),
 'filter_enabled': (0x2028d8a, 0x2028db0),
 'estimate_slot': (0x1c05d02, 0x1c05d40),
 'type_cost': (0x202930e, 0x202936c),
 'ir_partition_cost': (0x1c05d4a, 0x1c05d6a),
 'ir_fallback_cost': (0x1c05d6a, 0x1c05d78)}

PARAMETER_JOINS = {0x202f338: 0x202e328, 0x202f412: 0x2028cb2, 0x202f44a: 0x2028de8, 0x202fda0: 0x2028cb2, 0x202fe48: 0x2028de8}

CREATION_JOINS = {0x202e9ae: 0x202cf62, 0x202e9d4: 0x202cf62, 0x202e92a: 0x202983a, 0x202f4ba: 0x202f07e, 0x202f4cc: 0x202f07e}

TABLES = {'stereo_branches': (0x1c060a6, 0x1c060c9, '5dc4cf8f1d20dd94c81c4f1d7c37e6c1724444715d5988a1bc6eb106fc85d2dc'),
 'stereo_alignment': (0x1c060c9, 0x1c060ca, '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'),
 'group_flags': (0x203b940, 0x203b97c, '0b99fb255d9a4849be3201a9dc5321737f11f3bef6514cb8643cf0ac58a835ea'),
 'object1_short_lengths': (0x203b4ae,
                           0x203b4b6,
                           'e5bfb2fb92a6c54c409f00b095799f42bf140499df4bfb528789bef3acfcec17')}

CONSUMERS = {'stereo_extra_cost': (0x1c06098,
                       0x1c060e6,
                       '86608b5571d3471e22c4333d6ac5005ba91700f389023f46fae8badadee2f4c0',
                       14),
 'group_fixed': (0x1c0606e, 0x1c06088, '1b27d2030c92424e5601f082dfe27f34d6cbb447f36f9d96c4cdce8604fd0ae3', 8),
 'object_mode': (0x1c05ed6, 0x1c05eec, '7575f62133bed654a212d5c5b01f16d01f19bcaf7c955eaffaf2aae4f0830b87', 9),
 'object_count': (0x2029c22, 0x2029c3e, 'f545c39a0a16b9ac3afc03dfdfe151475c98c12414d5c68167d1f2136920b7e3', 10),
 'object_segment': (0x2029ed4,
                    0x2029f8e,
                    'e2749514102b19a46bae8f26a070423ada1a5d796d250f1d1fb016b64ed37d33',
                    65),
 'partition_sizes': (0x202a1be,
                     0x202a226,
                     'f79ba63b780c8d6bb85597379d7fe297e006810495e3bb49a541de9a783052d3',
                     36),
 'object_total': (0x2029f98, 0x2029fc8, 'ef8ebd4d9c2e9a29c563f6ebeccd66c54405f2f1cd1deea6d52f83bca4715b5a', 20),
 'segment_bytes': (0x2029f8e, 0x2029f98, '705afc47d2ddbef568efa651745a5fccc1c53613c051d810def85d36eec1e4d9', 5)}

TABLE_CONSUMERS = {'stereo_branches': ('stereo_extra_cost',),
 'stereo_alignment': ('stereo_extra_cost',),
 'group_flags': ('group_fixed',),
 'object1_short_lengths': ('object_mode',
                           'object_count',
                           'object_segment',
                           'partition_sizes',
                           'object_total',
                           'segment_bytes')}

PROOF_SITES = {'stereo_branches': ((0x1c06098, 'r1 = r0 + -5'),
                     (0x1c0609c, 'if (r1 > 34) goto 60'),
                     (0x1c060a0, 'r0 = 2400'),
                     (0x1c060a4, 'tbb [r1]')),
 'stereo_alignment': ((0x1c060a4, 'tbb [r1]'), (0x1c060ca, 'r0 = 1400')),
 'group_flags': ((0x1c0606e, 'if (r1 != 1) goto 18'),
                 (0x1c06072, 'r0 += -9'),
                 (0x1c06074, 'if (r0 <= 14) {'),
                 (0x1c06078, 'r1 = 33798464'),
                 (0x1c0607e, 'r0 = [r1+r0<<2]')),
 'object1_short_lengths': ((0x1c05ed6, 'r1 = r0'),
                           (0x1c05edc, 'if (r1 != 34) {'),
                           (0x1c05ee0, 'r2 = 0'),
                           (0x1c05ee4, 'if (r1 != 33) {'),
                           (0x1c05ee8, 'r0 = r2'),
                           (0x2029c22, '[--sp] = rets'),
                           (0x2029c24, 'call -4341076'),
                           (0x2029c2c, 'if (r0 != 1) {'),
                           (0x2029c34, 'if (r0 != 2) {'),
                           (0x2029f0a, 'if (r3 == 8) goto 90'),
                           (0x2029f0e, 'if (r0 != 1) goto 32'),
                           (0x2029f12, 'ifs (r3 <= 3) goto 90'),
                           (0x2029f16, 'ifs (r3 <= 7) goto 104'),
                           (0x2029f1a, 'r1 = r3 + -9'),
                           (0x2029f1e, 'r0 = 3'),
                           (0x2029f20, 'if (r3 != 12) {'),
                           (0x2029f24, 'r0 = r1'),
                           (0x2029f26, 'r1 = 33797294'),
                           (0x2029f2c, 'r0 = h[r1+r0<<1] (u)'),
                           (0x202a1f4, 'call -1494'),
                           (0x202a1fe, 'r7 = 0'),
                           (0x202a202, 'call -632'),
                           (0x202a20a, 'r7 = r7 + 1'),
                           (0x202a20c, 'if (r8 != r7) goto -16'),
                           (0x2029fa6, 'call -904'),
                           (0x2029fb4, 'r6 = 0'),
                           (0x2029fba, 'call -46'),
                           (0x2029fbe, 'r6 = r6 + 1'),
                           (0x2029fc2, 'if (r5 != r6) goto -16'),
                           (0x2029f90, 'call -190'))}

EXTRA_REUSED = {'convert_effect': (0x0202a452, 0x0202a50a),
    'neighbors': (0x0202de8c, 0x0202def2)}
INDIRECT_SITES = dict.fromkeys((0x0202e798, 0x0202e810, 0x0202e834, 0x0202e94a,
    0x0202e9ee, 0x0202ea1e, 0x0202ea4e, 0x0202ea84), 3)
INDIRECT_SITES.update({0x0202e616: 0, 0x0202e6c4: 0, 0x0202e70c: 1})
RAW_TAIL = (0x0203b4b6, 0x0203b4b8,
    '96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7')
SINE_PAIRS_SHA = '0109e6171e613d6ac1e25ef6ed7d794cd870d2a39b8cb2bf8e4ddcd7e67dca2e'
DERIVATIVE_PARENT = 'firmware/src/hyperrig_effect_parameter_construction.c'
DERIVATIVE_SHA = 'b337edb670dc6585e331eaf9c1550bc03ce3f1367f34c8ef297fd3cf36c73033'


def registry_evidence(report, constants, parents):
    if (report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA
        or constants.get('REGIONS') != REGIONS
        or constants.get('STATIC') != {name: value[:2] for name, value in TABLES.items()}
        or constants.get('AUXILIARY_STATIC') != {'raw_object1_index13': RAW_TAIL[:2]}
        or constants.get('PARAMETER_JOINS') != PARAMETER_JOINS
        or constants.get('CREATION_JOINS') != CREATION_JOINS):
        raise ValueError('setup report, exact new registry or join declarations changed')
    if set(report['functions']) != set(REGIONS):
        raise ValueError('setup must declare all 45 reviewed new complete bodies')
    for name, bounds in REGIONS.items():
        if span(report['functions'][name]) != bounds:
            raise ValueError('setup new function endpoint differs from reviewed registry')
    expected = {'parameter_'+name: span(item) for name, item in parents['parameters']['joined_bodies'].items()}
    expected.update({'ir_'+name: span(item) for name, item in parents['ir']['reused_functions'].items()})
    expected.update(EXTRA_REUSED)
    if len(expected) != 144 or {name: span(item) for name, item in report['reused_functions'].items()} != expected:
        raise ValueError('setup reused registry differs from exact named parents and two helpers')
    return expected


def with_setup_ranges(previous):
    ranges = [*previous, *((a, b, 'setup_'+name) for name, (a, b, _) in TABLES.items())]
    for i, (a, b, _) in enumerate(ranges):
        if a >= b or any(a < y and x < b for x, y, _ in ranges[i+1:]):
            raise ValueError('setup data exclusions overlap or have invalid bounds')
    # Later consumer evidence supersedes exactly eight bytes of inventory13's
    # unread prefix. Its two-byte tail and every other unknown span stay unknown.
    for a, b in (RAW_TAIL[:2], *MODEL_UNCLASSIFIED[1:]):
        if any(a < y and x < b for x, y, _ in ranges):
            raise ValueError('setup classified an unauthenticated surrounding span')
    return ranges


def table_evidence(report, raw, decode, isa):
    proofs = report['new_table_proofs']
    if set(proofs) != set(TABLES): raise ValueError('setup table proof set changed')
    bodies, canonical, parallel_seconds = {}, {}, set()
    for name, (a, b, digest, count) in CONSUMERS.items():
        if sha(raw(a, b)) != digest: raise ValueError('setup complete consumer bytes changed')
        decoded = decode(a, b)
        if len(decoded) != count: raise ValueError('setup complete consumer instruction count changed')
        bodies[name] = dict(start=hex_address(a), end_exclusive=hex_address(b),
            sha256=digest, decoded_instructions=count)
        for pc, size, text in decoded:
            prior = canonical.setdefault(pc, (size, text))
            if prior != (size, text): raise ValueError('setup consumer decoding disagrees')
            instruction, fields, found_size = codec.decode(isa, raw(a, b), pc-a)
            if found_size != size: raise ValueError('setup consumer packet size changed')
            if codec.format(instruction, fields).endswith('  #'): parallel_seconds.add(pc+size)
    tables = {}
    for name, expected in TABLES.items():
        item = proofs[name]; a, b, digest = expected
        if static_identity(item) != expected or sha(raw(a, b)) != digest:
            raise ValueError('setup table bytes or exact extent changed')
        if set(item['consumers']) != set(TABLE_CONSUMERS[name]):
            raise ValueError('setup table lacks its complete consumer and caller set')
        for consumer, body in item['consumers'].items():
            start, end, body_sha, count = CONSUMERS[consumer]
            if (span(body) != (start, end) or body['bytes_sha256'] != body_sha
                or type(body['instructions']) is not int or body['instructions'] != count):
                raise ValueError('setup table consumer is not the reviewed complete body')
        sites = item['decoded_sites']
        if [(address(site['address']), site['text'].removesuffix('  #')) for site in sites] != list(PROOF_SITES[name]):
            raise ValueError('setup decoded index proof sites changed')
        for site in sites:
            pc = address(site['address']); size, text = canonical[pc]
            if text != site['text'].removesuffix('  #') or sha(raw(pc, pc+size)) != site['bytes_sha256']:
                raise ValueError('setup proof site does not match whole-consumer decoding')
        tables[name] = dict(start=hex_address(a), end_exclusive=hex_address(b),
            sha256=digest, bytes=b-a, kind='setup_'+name, complete_consumers=list(item['consumers']),
            proof_sites=[hex_address(address(site['address'])) for site in sites])
    targets = [0x01c060a6+2*value for value in raw(0x01c060a6, 0x01c060c9)]
    if (len(targets) != 35 or raw(0x01c060c9, 0x01c060ca) != b'\0'
        or any(pc not in canonical or pc in parallel_seconds or not 0x01c060ca <= pc < 0x01c060e6 for pc in targets)):
        raise ValueError('setup branch table does not target canonical consumer packet starts')
    # These constants and loop guards supplement the report's use-site list.
    extra = {0x01c05ed8: 'r0 = 1', 0x01c05eda: 'r2 = 1', 0x01c05ee2: 'r2 = r2 << 1',
        0x02029c2a: 'r2 = 13', 0x0202a1fa: 'ifs (r0 < 1) goto 20',
        0x02029faa: 'r5 = r0', 0x02029fac: 'ifs (r5 >= 1) goto 4'}
    if any(canonical[pc][1] != text for pc, text in extra.items()):
        raise ValueError('setup original mode/count and loop bounds changed')
    tables['stereo_branches'].update(entries=35, entry_width=1, targets=list(map(hex_address, targets)))
    tables['group_flags'].update(entries=15, entry_width=4)
    tables['object1_short_lengths'].update(entries=4, entry_width=2,
        ordinary_caller_indices=[9, 10, 11, 12], raw_helper_has_no_count_guard=True)
    return {'tables': tables, 'complete_consumers': bodies,
        'additional_decoded_bound_sites': list(map(hex_address, extra)),
        'raw_helper_tail_remains_unclassified': True}


def fixed_gap_evidence(report, canonical, raw):
    coverage = report['instruction_coverage']
    if pc_set(coverage['unvisited_new'], set(canonical), 'setup new gaps') != {0x0202e3b6}:
        raise ValueError('setup fixed-input gap changed')
    classification = keyed(report['missing_classification'], 'setup gap classification')
    if set(classification) != {0x0202e3b6} or classification[0x0202e3b6]['kind'] != 'fixed-input unreachable':
        raise ValueError('setup unvisited instruction lacks its fixed-input classification')
    if sha(raw(0x0202e346, 0x0202e3ce)) != 'da34685940ae5b7990f5639a807d8791705607508813599c5a0b31c59eb46c72':
        raise ValueError('setup fixed-loop initializer changed')
    expected = {0x0202e378: 'r4 = 0', 0x0202e37a: 'r10 = r1 + 0x3F000000',
        0x0202e37e: 'r11 = 1078530011', 0x0202e384: 'r12 = r1 + 0x3B000000',
        0x0202e392: 'r5 = r1 + 0x3F800000', 0x0202e396: 'r0 = utof(r4)',
        0x0202e39a: 'r0 = r0 + r10 (f)', 0x0202e39e: 'r0 = r0 * r11 (f)',
        0x0202e3a2: 'r0 = r0 * r12 (f)', 0x0202e3a6: 'call -23860',
        0x0202e3aa: 'r1 = r0 * r14 (f)', 0x0202e3b2: 'iff (r0 >= r5) {',
        0x0202e3b6: 'r1 = r13', 0x0202e3be: 'r4 = r4 + 1',
        0x0202e3c0: 'if (r4 != 256) goto -46'}
    if any(canonical[pc][1] != text for pc, text in expected.items()):
        raise ValueError('setup fixed sine-input sequence or saturation guard changed')
    item = report['type30_fixed_sine_observations']; pairs = item['pairs']
    if (item['pc'] != 0x0202e3aa or item['index_register'] != 'r4' or item['value_register'] != 'r0'
        or len(pairs) != 256 or [pair[0] for pair in pairs] != list(range(256))
        or any(len(pair) != 2 or any(type(word) is not int for word in pair)
               or not 0 <= pair[1] < 0x3f800000 for pair in pairs)
        or item['sha256'] != SINE_PAIRS_SHA
        or sha(b''.join(struct.pack('<2I', *pair) for pair in pairs)) != SINE_PAIRS_SHA):
        raise ValueError('setup fixed-input original sine observations changed')
    return {'unexecuted': hex_address(0x0202e3b6), 'fixed_inputs': 256,
        'observation_sha256': SINE_PAIRS_SHA, 'maximum_result_word': hex_address(max(v for _, v in pairs)),
        'independently_replayed_with_frozen_pure_sine_model': True,
        'mapped_input_or_callback_dependence': False, 'hardware_floating_point_validation': False}


def corpus_evidence(report, constants, parents, raw, decode, regions, data_ranges):
    reused = registry_evidence(report, constants, parents)
    canonical, body_pcs = {}, {}
    for bounds, item in regions.items():
        if item['kind'] != 'function_region': continue
        decoded = decode(*bounds); body_pcs[bounds] = {pc for pc, _, _ in decoded}
        for pc, size, text in decoded:
            if pc in canonical: raise ValueError('setup canonical whole bodies overlap')
            canonical[pc] = size, text
    new = set().union(*(body_pcs[bounds] for bounds in REGIONS.values()))
    expected = set(new)
    for parent in parents.values(): expected.update(address(pc) for pc in parent['bound_instruction_windows'])
    for bounds in EXTRA_REUSED.values(): expected.update(body_pcs[bounds])
    loaded = set()
    for pc, item in keyed(report['bound_instruction_windows'], 'setup loaded windows').items():
        a, b = span(item)
        if (pc != a or pc not in canonical or canonical[pc][0] != b-a
            or sha(raw(a, b)) != item['sha256']):
            raise ValueError('setup loaded window is not an exact canonical whole-body instruction')
        loaded.add(pc)
    if loaded != expected: raise ValueError('setup loaded windows differ from the exact parent/new union')
    joined = set().union(*(body_pcs[bounds] for bounds in (*REGIONS.values(), *reused.values())))
    coverage = report['instruction_coverage']; gaps = {}; counts = {}
    for name, domain in (('new', new), ('joined', joined), ('all', loaded)):
        gaps[name] = pc_set(coverage['unvisited_'+name], domain, 'setup '+name+' gaps')
        counts[name+'_decoded'] = len(domain); counts[name+'_visited'] = len(domain-gaps[name])
    if (gaps['new'] != new & gaps['all'] or gaps['joined'] != joined & gaps['all']
        or any(type(coverage[key]) is not int or coverage[key] != value for key, value in counts.items())):
        raise ValueError('setup aggregate counts disagree with canonical instruction gaps')
    per_function = {}
    for group in ('functions', 'reused_functions'):
        for name, item in report[group].items():
            bounds = span(item); parent = regions.get(bounds); pcs = body_pcs.get(bounds, set())
            if (parent is None or parent['kind'] != 'function_region' or not pcs <= loaded
                or parent['sha256'] != item['bytes_sha256'] or sha(raw(*bounds)) != item['bytes_sha256']
                or type(item['instructions']) is not int or item['instructions'] != len(pcs)
                or type(item['visited']) is not int or item['visited'] != len(pcs-gaps['all'])
                or pc_set(item['unvisited'], pcs, 'setup body gaps') != pcs & gaps['all']):
                raise ValueError('setup named function bytes, whole bounds or coverage changed')
            per_function[name] = dict(decoded=len(pcs), visited=len(pcs-gaps['all']),
                unvisited=len(pcs & gaps['all']), reused=group == 'reused_functions')
    direct = {}
    for item in report['direct_setup_sites']:
        pc, target = address(item['site']), address(item['target'])
        if pc in direct or type(item['calls']) is not int or item['calls'] <= 0:
            raise ValueError('setup direct join is duplicated or has no executed calls')
        direct[pc] = target
    if direct != PARAMETER_JOINS | CREATION_JOINS: raise ValueError('setup direct join set changed')
    for pc, target in direct.items():
        size, text = canonical[pc]
        if (text != f'call {target-pc-size}' or pc not in loaded-gaps['all']
            or target not in loaded-gaps['all'] or not any(a == target for a, _ in body_pcs)):
            raise ValueError('setup direct join or complete callee entry was not executed')
    indirect = {pc for pc in new if canonical[pc][1].startswith('call ')
        and re.fullmatch(r'call (-?\d+)', canonical[pc][1]) is None}
    if indirect != set(INDIRECT_SITES): raise ValueError('setup original indirect call-site set changed')
    observed = set()
    for item in report['external_call_sites']:
        pc = address(item['pc'])
        if pc not in indirect: continue
        if (type(item['argument_words']) is not int or item['argument_words'] != INDIRECT_SITES[pc]
            or type(item['calls']) is not int or item['calls'] <= 0 or pc in gaps['all']):
            raise ValueError('setup original callback ABI or external call evidence changed')
        observed.add(pc)
    if observed != indirect: raise ValueError('setup callback site lacks executed external evidence')
    inherited = dict(parents['parameters']['static_data'])
    inherited.update({'setup_'+name: item for name, item in parents['ir']['static_data'].items()})
    expected_static = {name: static_identity(item) for name, item in inherited.items()}
    expected_static.update({'setup_'+name: value for name, value in TABLES.items()})
    expected_static['setup_raw_object1_index13'] = RAW_TAIL
    if {name: static_identity(item) for name, item in report['static_data'].items()} != expected_static:
        raise ValueError('setup static roles differ from exact parents, tables and raw tail')
    for name, (a, b, digest) in expected_static.items():
        if sha(raw(a, b)) != digest: raise ValueError('setup static bytes changed')
        overlaps = [(x, y, kind) for x, y, kind in data_ranges if a < y and x < b]
        if name == 'setup_raw_object1_index13':
            if overlaps: raise ValueError('setup raw segment tail became a data exclusion')
        elif not any(x <= a < b <= y for x, y, _ in overlaps):
            raise ValueError('setup inherited or newly proven table lost its data role')
    auxiliary = report['auxiliary_raw_read_bindings']
    if (set(auxiliary) != {'raw_object1_index13'} or static_identity(auxiliary['raw_object1_index13']) != RAW_TAIL
        or auxiliary['raw_object1_index13'].get('inventory_data_exclusion') is not False):
        raise ValueError('setup raw above-count witness changed its auxiliary role')
    derivative = report['derivative_provenance']
    expected_derivative = {'parent': DERIVATIVE_PARENT, 'parent_sha256': DERIVATIVE_SHA,
        'derived': 'firmware/src/hyperrig_effect_setup_parameters.c',
        'direct_sites': [{'site': f'0x{pc:08x}', 'target': f'0x{target:08x}'} for pc, target in PARAMETER_JOINS.items()],
        'permitted_changes': ['public prefix/header', 'one borrowed bridge', 'five exact direct calls'],
        'prior_numerical_resource_ownership_sources_unchanged': True}
    if derivative != expected_derivative or report['source_sha256'].get(DERIVATIVE_PARENT) != DERIVATIVE_SHA:
        raise ValueError('setup checked parameter derivative ancestry changed')
    return {'new_whole_functions': len(REGIONS), 'named_reused_whole_functions': len(reused),
        **counts, 'new_gaps': len(gaps['new']), 'joined_gaps': len(gaps['joined']),
        'loaded_gaps': len(gaps['all']), 'direct_join_sites': len(direct),
        'new_indirect_call_sites': len(indirect), 'inherited_static_roles': len(inherited),
        'new_data_spans': len(TABLES), 'new_data_bytes': sum(b-a for a, b, _ in TABLES.values()),
        'auxiliary_raw_tail_bytes': 2, 'per_function': per_function,
        'fixed_input_gap': fixed_gap_evidence(report, canonical, raw)}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 61 or len(set(PRESERVED_REPORTS)) != 61:
        raise ValueError('inventory19 must retain exactly 61 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('setup inventory omitted or duplicated earlier report evidence')


class EffectSetupInventory(StorageRuntimeInventory):
    def __init__(self, *required, effect_setup_report, additional_reports=(), **options):
        if local(effect_setup_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen effect-setup03')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if REPORT in additions: raise ValueError('setup report is already explicitly selected')
        self.setup_tables, self.setup_corpus = None, None
        # The older generic reader assumes a joined corpus is identical to its
        # new-function declaration. Add this mixed new/reused report explicitly.
        super().__init__(*required, additional_reports=additions, **options)

    def add_known_data(self):
        super().add_known_data(); raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen setup report changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report['source_sha256'].get(MODEL) != sha(source): raise ValueError('setup model source changed')
        self.setup_parents = {}
        for name, (path, digest) in PARENT_REPORTS.items():
            data = self.read(path)
            if sha(data) != digest: raise ValueError('frozen setup parent report changed')
            self.setup_parents[name] = json.loads(data)
        self.setup_constants = declared_constants(source.decode('utf-8'))
        registry_evidence(report, self.setup_constants, self.setup_parents)
        self.data_ranges = with_setup_ranges(self.data_ranges)
        self.setup_tables = table_evidence(report, self.raw, self.decode, self.instructions)

    def reports(self):
        omitted = super().reports(); self.audit_manifest(REPORT, MANIFEST_SHA)
        raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen setup report changed')
        report = json.loads(raw_report); self.audit_sources(report['source_sha256'])
        for name, item in report['functions'].items():
            self.add_region(local(REPORT).parent.name, name, item['start'], item['end_exclusive'], item['bytes_sha256'])
        self.setup_corpus = corpus_evidence(report, self.setup_constants, self.setup_parents,
            self.raw, self.decode, self.regions, self.data_ranges)
        coverage = report['instruction_coverage']
        self.modules.append({'module': local(REPORT).parent.name, 'report': REPORT,
            'report_sha256': sha(raw_report), 'declared_regions': len(REGIONS),
            'source_hashes_checked': len(report['source_sha256']), 'scope_limits': report['limitations'],
            'instruction_coverage': coverage_summary(report),
            'reported_region_coverage': {name: self.setup_corpus['per_function'][name] for name in REGIONS},
            'reported_coverage_notes': {'classified_new_gaps': report['missing_classification'],
                'new_joined_and_loaded_domains_remain_distinct': True,
                'inherited_execution_counts_are_not_borrowed': True,
                'all_ten_direct_join_sites_and_callee_entries_executed': True},
            'joined_region_coverage': {'decoded': coverage['joined_decoded'], 'visited': coverage['joined_visited'],
                'unvisited': self.setup_corpus['joined_gaps'],
                'unvisited_addresses': list(map(hex_address, coverage['unvisited_joined'])),
                'note': 'The joined domain includes 45 new bodies and 144 named reused roles; only the new bodies add functions.'},
            'effect_setup_evidence': self.setup_corpus})
        return [name for name in omitted if name != REPORT]

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        old_key = 'model_unused_table_prefixes_suffixes_and_alignment_left_unclassified'
        if report['audits'].pop(old_key) is not True: raise ValueError('prior model classification policy changed')
        report.update(schema=18, effect_setup_inventory_adapter=ADAPTER,
            effect_setup_tables=self.setup_tables, effect_setup_evidence=self.setup_corpus,
            data_classification_supersession={'prior_snapshot': 'reverse-inventory-13',
                'prior_audit_key': old_key, 'prior_audit_result': True,
                'previous_unknown_span': [hex_address(v) for v in MODEL_UNCLASSIFIED[0]],
                'new_proven_span': [hex_address(v) for v in TABLES['object1_short_lengths'][:2]],
                'remaining_unknown_tail': [hex_address(v) for v in RAW_TAIL[:2]],
                'prior_reports_and_adapters_unchanged': True})
        report['audits'].update(inventory19_all_sixty_one_reports_retained=True,
            setup_complete_bodies_and_exact_loaded_parent_union_authenticated=True,
            setup_table_consumers_and_original_index_bounds_independently_decoded=True,
            setup_branch_targets_are_canonical_packet_starts=True,
            setup_exact_eight_byte_prefix_has_new_consumer_evidence=True,
            setup_surrounding_unclassified_bytes_remain_unclassified=True,
            setup_direct_join_sites_and_callee_entries_executed=True,
            setup_callback_ABIs_and_external_site_identity_preserved=True,
            setup_fixed_input_gap_and_separate_coverage_domains_bound=True,
            setup_checked_parameter_derivative_ancestry_bound=True)
        report['scope_policy'].extend([
            'setup adds 45 complete bodies; its 144 named reused bodies and larger loaded corpus add no duplicate functions',
            'four proven data spans total 104 bytes: 35 branch bytes, one alignment byte, fifteen words and four halfwords',
            'new complete consumer evidence supersedes exactly eight bytes of the inventory13 unknown prefix; the remaining two bytes stay auxiliary and unclassified',
            'raw object-segment indices are not bounded by the normal caller count; outside-count reads do not enlarge a proven table',
            'all ten direct joins execute their original callees; eleven new indirect sites retain external callback identity and their original argument counts',
            'one fixed-input saturation instruction remains unexecuted; every joined and loaded gap is retained without borrowing parent execution counts',
            'finite mapping/work limits, allocation fixtures and MMIO outputs do not establish hardware DSP, physical audio or whole-firmware execution'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    prior = json.loads(local('build/reverse-inventory-19/inventory.json').read_bytes())
    report = json.loads(local(REPORT).read_bytes())
    parents = {name: json.loads(local(path).read_bytes()) for name, (path, _) in PARENT_REPORTS.items()}
    constants = declared_constants(local(MODEL).read_text())
    inv = object.__new__(Inventory); inv.app = local(APP).read_bytes(); inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    previous_ranges = [(address(item['start']), address(item['end_exclusive']), item['kind'])
        for item in prior['known_data_ranges']]
    inv.data_ranges = with_setup_ranges(previous_ranges)
    regions = {span(item): item for item in prior['reconstructed_regions']}
    for item in report['functions'].values():
        assert span(item) not in regions
        regions[span(item)] = {'kind': 'function_region', 'sha256': item['bytes_sha256']}
    decode = functools.lru_cache(None)(inv.decode); raw = functools.lru_cache(None)(inv.raw)
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError, IndexError, struct.error): checks += 1; return
        raise AssertionError('invalid setup evidence accepted')
    def audit(item):
        return corpus_evidence(item, constants, parents, raw, decode, regions, inv.data_ranges)
    def tables(item): return table_evidence(item, raw, decode, inv.instructions)
    result = audit(report)
    assert (result['new_decoded'], result['new_visited'], result['joined_decoded'], result['joined_visited'],
        result['all_decoded'], result['all_visited']) == (1759, 1758, 9761, 8164, 22289, 8518)
    assert len(tables(report)['complete_consumers']) == 8; checks += 2
    for group in ('functions', 'reused_functions'):
        for name in report[group]:
            changed = copy.deepcopy(report); changed[group][name]['bytes_sha256'] = '0'*64
            rejected(audit, changed)
    paths = [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
        ((), 'functions', {}), ((), 'reused_functions', {}),
        (('functions', 'create'), 'end_exclusive', 0x0202ea8e),
        (('functions', 'create'), 'instructions', True),
        (('functions', 'create'), 'visited', -1),
        (('functions', 'create'), 'unvisited', [0x0202e710]),
        (('instruction_coverage',), 'new_decoded', 1758),
        (('instruction_coverage',), 'new_visited', True),
        (('instruction_coverage',), 'unvisited_new', []),
        (('instruction_coverage',), 'joined_visited', 0),
        (('instruction_coverage',), 'unvisited_joined', []),
        (('instruction_coverage',), 'unvisited_all', []),
        ((), 'missing_classification', {}),
        (('type30_fixed_sine_observations',), 'pc', 0x0202e3ae),
        (('type30_fixed_sine_observations',), 'pairs', [[i, 0] for i in range(256)]),
        (('type30_fixed_sine_observations',), 'sha256', '0'*64),
        ((), 'static_data', {}), ((), 'auxiliary_raw_read_bindings', {}),
        (('auxiliary_raw_read_bindings', 'raw_object1_index13'), 'inventory_data_exclusion', True),
        (('derivative_provenance',), 'parent_sha256', '0'*64),
        (('derivative_provenance',), 'prior_numerical_resource_ownership_sources_unchanged', False),
    ]
    for path, key, value in paths:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(audit, changed)
    pc = next(iter(report['bound_instruction_windows']))
    for key, value in [('start', address(pc)+2), ('end_exclusive', address(pc)+1), ('sha256', '0'*64)]:
        changed = copy.deepcopy(report); changed['bound_instruction_windows'][pc][key] = value
        rejected(audit, changed)
    changed = copy.deepcopy(report)
    changed['bound_instruction_windows'][str(address(pc))] = changed['bound_instruction_windows'][pc]
    rejected(audit, changed)
    for i in range(len(report['direct_setup_sites'])):
        for key, value in [('calls', 0), ('target', 0x02000000)]:
            changed = copy.deepcopy(report); changed['direct_setup_sites'][i][key] = value
            rejected(audit, changed)
    for name in TABLES:
        for key, value in [('start', TABLES[name][0]+1), ('end_exclusive', TABLES[name][1]+1), ('sha256', '0'*64),
                ('consumers', {}), ('decoded_sites', [])]:
            changed = copy.deepcopy(report); changed['new_table_proofs'][name][key] = value
            rejected(tables, changed)
        for i in range(len(report['new_table_proofs'][name]['decoded_sites'])):
            changed = copy.deepcopy(report)
            changed['new_table_proofs'][name]['decoded_sites'][i]['text'] = 'rts'
            rejected(tables, changed)
    for name in ('REGIONS', 'STATIC', 'AUXILIARY_STATIC', 'PARAMETER_JOINS', 'CREATION_JOINS'):
        changed = dict(constants); changed[name] = {}
        rejected(registry_evidence, report, changed, parents)
    rejected(with_setup_ranges, [*previous_ranges, (RAW_TAIL[0], RAW_TAIL[1], 'invented')])
    rejected(with_setup_ranges, inv.data_ranges)
    for start, end in MODEL_UNCLASSIFIED[1:]:
        rejected(with_setup_ranges, [*previous_ranges, (start, end, 'invented')])
    # A positive call counter cannot substitute for executed callee entry.
    # Keep every aggregate and per-body gap consistent while removing entry.
    changed = copy.deepcopy(report); target = 0x0202cf62
    for label in ('joined', 'all'):
        changed['instruction_coverage'][label+'_visited'] -= 1
        changed['instruction_coverage']['unvisited_'+label].append(target)
    for group in ('functions', 'reused_functions'):
        for item in changed[group].values():
            if span(item)[0] <= target < span(item)[1]:
                item['visited'] -= 1; item['unvisited'].append(target)
    rejected(audit, changed)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [value for value in selected if value != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 61,
        'new_whole_functions': 45, 'new_data_spans': 4, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report',
        'storage_coordination_report', 'sample_processing_report', 'storage_runtime_report', 'effect_setup_report')
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
    report = EffectSetupInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'effect-setup-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'effect_setup_evidence': {key: value for key, value in report['effect_setup_evidence'].items()
            if key != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
