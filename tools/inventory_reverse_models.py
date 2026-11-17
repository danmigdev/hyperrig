"""Audit model-builder functions and exact original table extents.

Preserve all inventory12 evidence. Bind complete consumers, decoded use sites
and immutable record fields before excluding new data from candidate scans.
Original reports, snapshots and earlier inventory adapters remain unchanged.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from inventory_reverse import (ROOT, REFERENCE, REFERENCE_SHA, APP, address,
    hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_resources import declared_constants
from inventory_reverse_integrations import (IntegrationsInventory, CONFIGURED_REPORT,
    REQUIRED_OPTIONS, PRESERVED_REPORTS as INVENTORY11_REPORTS)

ADAPTER = 'tools/inventory_reverse_models.py'
MODEL = 'tools/effect_model_construction_machine.py'
MODEL_REPORT = 'build/reverse-effect-model-construction-03/verification.json'
MODEL_SHA = 'f36d4654d4517242cc988490fa921ac894140314ca450c36a4cbad2dd64b9c03'
MODEL_MANIFEST_SHA = '810d7b415de78ad895a4973dd276907bfc8e3b2f5db9919fdffb8f5ade66d1d9'
PRESERVED_REPORTS = (*INVENTORY11_REPORTS, CONFIGURED_REPORT,
    'build/reverse-effect-resource-ownership-03/verification.json',
    'build/reverse-ir-effect-lifecycle-01/verification.json')

# Unread index-zero entries, unused record tails and alignment stay unknown.
UNCLASSIFIED = ((0x0203b4ae, 0x0203b4b8), (0x0203b74c, 0x0203b75c),
    (0x0203b764, 0x0203b768), (0x0203bdf8, 0x0203bdfc), (0x0203be28, 0x0203be29))

CONSUMERS = {
    'build16_to23': {'bounds': (0x0202b838, 0x0202b87e), 'instructions': 22,
        'sha256': '93180b35df21ef19722f5bc401e1c511bcd76462ba3f510bac9773352767f38a'},
    'object_mode2': {'bounds': (0x0202c5a2, 0x0202c836), 'instructions': 181,
        'sha256': 'd519a57a6243c41b8c1a9cc47065d787ee5067b8e55375d9507378bacac6be37'},
    'object_record': {'bounds': (0x01c06004, 0x01c06028), 'instructions': 12,
        'sha256': '5d62bb531623a7fbb54e05809aec0daf3a2d5f5beca18e525930741bace62fc0'},
    'build19': {'bounds': (0x0202ae22, 0x0202af48), 'instructions': 89,
        'sha256': '52a31823bc958fab29506a5bd35650e366b20305e36e6e06cf266fc4ed88f549'},
    'tone_setup': {'bounds': (0x0202b484, 0x0202b5ac), 'instructions': 101,
        'sha256': 'd25b447fba649e72e9760c8853bf111327d3447e494e42d3da54dceaf1cc8cb5'},
    'object_mode1': {'bounds': (0x0202c248, 0x0202c5a2), 'instructions': 252,
        'sha256': '938c4bf46a871856ffbb52f261a081d3901e9a33907313f4307756f11aa0b279'},
    'object_feedback': {'bounds': (0x0202c11c, 0x0202c1e2), 'instructions': 50,
        'sha256': '1a473ee7d47c035fe826607f8ba538e98e34fd9a27768962a86497e9856ffdc3'},
    'object_mode0': {'bounds': (0x0202c836, 0x0202cc9c), 'instructions': 324,
        'sha256': '3ecf1be69937900f73697e583f783e8d3da5392fae3111693f2b587097a15ba4'},
    'object_length': {'bounds': (0x02029e98, 0x02029ec8), 'instructions': 11,
        'sha256': 'f7a9f62368ed120b517b23f24e891d611f4d9bd9e885e9ce10b30993fb2b1fb3'},
    'build39': {'bounds': (0x0202a872, 0x0202ab98), 'instructions': 217,
        'sha256': '51104143400e0a416f1437f0db113ceee8be7457850340ee2ee330bbfa9620bb'},
    'build21': {'bounds': (0x0202b616, 0x0202b69e), 'instructions': 35,
        'sha256': 'b7b7abe5ce7a8469fdc4df4e18f76a62645e51a5818e9ed48cff4e1b6ee79e22'},
    'build22': {'bounds': (0x0202b69e, 0x0202b762), 'instructions': 49,
        'sha256': '485ed453ce2f3e59c65ea6b7829ae291fd58b2a504edcccfb8b0f845c9bb77bf'},
    'build23': {'bounds': (0x0202b762, 0x0202b838), 'instructions': 57,
        'sha256': 'ef1115c9a78bdc22bd9f0ef14853c4f26649ae9766d25c7bd64eb97d7a5673b9'},
}

# Primary spans and exact byte hashes. All sixteen are new exclusions.
TABLES = {
    'model_branches': {'bounds': (0x0202b846, 0x0202b84e),
        'sha256': '50dfa976443d2c3d488ddc99aa53d4312573a3f9dfacd257b0004eea89c5b100', 'consumer': 'build16_to23'},
    'object2_lengths': {'bounds': (0x0203b4a8, 0x0203b4ae),
        'sha256': 'bb24a17787ab6fa5628d482b3918ba5f9899c258bb7c107e7ff7721933c82b85', 'consumer': 'object_mode2'},
    'object_records': {'bounds': (0x0203b4b8, 0x0203b608),
        'sha256': '4e59f7d1f5e9fcb9f8cda862a9617972d7a6d13f195d09123822dbbb042b2cca', 'consumer': 'object_record'},
    'type19_records': {'bounds': (0x0203b674, 0x0203b6bc),
        'sha256': '5d35c5210a07dd4193a841acc2c0a12218a472fc012ff354e44164346b3e7cbb', 'consumer': 'build19'},
    'tone_records': {'bounds': (0x0203b6bc, 0x0203b710),
        'sha256': 'e2b897cd35db3aed3fca0151902f7a0b7c486333201214da60e26c6794bdba1c', 'consumer': 'tone_setup'},
    'object1_routes': {'bounds': (0x0203b710, 0x0203b718),
        'sha256': 'd0db9eadbe003260388923f0c8a32b9e41cbe08ce2fae46a9d47d918f4a9ec5c', 'consumer': 'object_mode1'},
    'feedback_levels': {'bounds': (0x0203b718, 0x0203b72c),
        'sha256': 'b5b267b7fa03f95eb0446c6752bf84aa57d88ec542945d79876e89a36f644da6', 'consumer': 'object_feedback'},
    'object0_lengths2': {'bounds': (0x0203b72c, 0x0203b74c),
        'sha256': 'd67bc471c40f22ed38f94ebb5b70e61fb2ef12dc5172206c7ed07a53e282ff03', 'consumer': 'object_mode0'},
    'object0_feedback2': {'bounds': (0x0203b75c, 0x0203b764),
        'sha256': '53b2b012f868a6146fe4bb29dcc7df3f03d0bbd3757f2325ee696bb3dd17a97b', 'consumer': 'object_mode0'},
    'object1_lengths': {'bounds': (0x0203bdc8, 0x0203bdd8),
        'sha256': 'e9e35d59acbb7ee1f83555d0e28d8994a5081a1ff0cc6767a328d24c6b7e0ff6', 'consumer': 'object_length'},
    'type39_times': {'bounds': (0x0203bdd8, 0x0203bde8),
        'sha256': 'e6368da1e5faac64cf73f0be7bbb70b84ec3538739d9422832de30460af0cac8', 'consumer': 'build39'},
    'object1_lengths8': {'bounds': (0x0203bde8, 0x0203bdf8),
        'sha256': '27b07ed386d8e131884205b9a5ba001013d7df51f9dc8a12db83df3265ce51bc', 'consumer': 'object_mode1'},
    'object2_feedback1_to3': {'bounds': (0x0203bdfc, 0x0203be08),
        'sha256': '6d77b10f40970f841e90d261e31ecabdfd59d85558270ae1a1b26ce2a467e5e6', 'consumer': 'object_mode2'},
    'object0_lengths1': {'bounds': (0x0203be08, 0x0203be18),
        'sha256': '2b6f391cec626b5b589d8fa66787f5890d28a61384eed5b8183c1f0cd4582cd9', 'consumer': 'object_mode0'},
    'object31_levels': {'bounds': (0x0203be18, 0x0203be28),
        'sha256': '8fc5a2a33470aa1573ee569af3f998dd3edb34539222b2e9725412158b58d3d3', 'consumer': 'object_mode0'},
    'object2_counts1_to3': {'bounds': (0x0203be29, 0x0203be2c),
        'sha256': '43a119bd5fbd984d67329818a7457099fe1a3a94527360738b8d3b6ca101b409', 'consumer': 'object_mode2'},
}

# Index initialization, bounds, strides, field loads and actual callers.
PROOF_SITES = {
    'build16_to23': (
        (0x0202b83a, 2, 'r1 = b[r0+0] (u)'),
        (0x0202b83c, 2, 'r1 += -16'),
        (0x0202b83e, 4, 'if (r1 <= 7) goto 2'),
        (0x0202b844, 2, 'tbb [r1]'),
    ),
    'object_mode2': (
        (0x0202c616, 4, 'ifs (r5 >= 3) {'),
        (0x0202c61a, 2, 'r2 = 3'),
        (0x0202c61e, 4, 'ifs (r5 >= 1) {'),
        (0x0202c622, 2, 'r3 = r2'),
        (0x0202c624, 6, 'r2 = 33799720'),
        (0x0202c62c, 4, 'r2 = b[r3+r2] (u)'),
        (0x0202c69e, 6, 'r0 = 33797288'),
        (0x0202c6a4, 4, 'r0 = h[r0+r11<<1] (u)'),
        (0x0202c6f4, 4, 'if (r11 != 3) goto -90'),
        (0x0202c75c, 6, 'r1 = 33799672'),
        (0x0202c768, 4, 'r1 = [r1+r5<<2]'),
    ),
    'object_record': (
        (0x01c06004, 4, 'if (r0 == 31) goto 16'),
        (0x01c06008, 2, 'r1 = 1'),
        (0x01c0600a, 4, 'if (r0 == 32) goto 12'),
        (0x01c0600e, 2, 'r1 = 3'),
        (0x01c06010, 4, 'if (r0 != 35) {'),
        (0x01c06014, 2, 'r1 = 0'),
        (0x01c06018, 2, 'r1 = 2'),
        (0x01c0601a, 4, 'r0 = r1 * 0x54'),
        (0x01c0601e, 6, 'r1 = 33797304'),
        (0x01c06024, 2, 'r0 = r0 + r1'),
    ),
    'build19': (
        (0x0202ae2c, 2, 'r0 = h[r5+14] (u)'),
        (0x0202ae2e, 4, 'if (r0 != 1) {'),
        (0x0202ae32, 2, 'r0 = 0'),
        (0x0202ae34, 4, 'r0 = r0 * 0x24'),
        (0x0202ae38, 6, 'r1 = 33797748'),
        (0x0202ae3e, 2, 'r6 = r0 + r1'),
        (0x0202aef8, 2, 'r1 = [r6+32]'),
    ),
    'tone_setup': (
        (0x0202b4a0, 4, 'r0 = r1 * 0x1C'),
        (0x0202b4a4, 6, 'r2 = 33797820'),
        (0x0202b4c6, 2, 'r2 = r2 + r0'),
    ),
    'object_mode1': (
        (0x0202c2b4, 2, 'r0 = r3'),
        (0x0202c2b6, 4, 'call -9250'),
        (0x0202c2dc, 4, 'if (r3 != 8) goto -44'),
        (0x0202c454, 6, 'r11 = 33799656'),
        (0x0202c466, 6, 'r3 = 33797904'),
        (0x0202c476, 4, 'r0 = h[r11+r15<<1] (u)'),
        (0x0202c494, 4, 'r4 = b[r15+r3] (u)'),
        (0x0202c4ac, 4, 'if (r15 != 8) goto -58'),
    ),
    'object_feedback': (
        (0x0202c136, 4, 'iff (r3 u< r6) {'),
        (0x0202c13c, 2, 'r5 = r4 << 2'),
        (0x0202c13e, 6, 'r6 = 33797912'),
        (0x0202c144, 4, 'r6 = [++r5=r6]'),
        (0x0202c148, 2, 'r5 = [r5+4]'),
    ),
    'object_mode0': (
        (0x0202c842, 6, 'call -4352068'),
        (0x0202c848, 2, 'r12 = r0'),
        (0x0202c850, 4, 'r1 = b[r12+55] (u)'),
        (0x0202c8a8, 4, 'r0 = r12 + 52'),
        (0x0202c8b0, 2, '[sp+16] = r0'),
        (0x0202c8b2, 4, 'r9 = b[r0+5] (u)'),
        (0x0202c8d0, 4, 'r4 = h[++r7=r0] (u)'),
        (0x0202c8fa, 2, 'r1 = h[r7+16] (u)'),
        (0x0202c9f8, 2, 'r8 = [sp+16]'),
        (0x0202ca94, 4, 'r0 = r8 + 24'),
        (0x0202ca98, 2, 'r1 = 0'),
        (0x0202caa4, 4, 'r4 = h[r0+r1<<1] (u)'),
        (0x0202cac2, 4, 'if (r1 != 4) goto -34'),
        (0x0202caea, 4, 'r1 = b[r8+6] (u)'),
        (0x0202caf6, 2, 'if (r1 == 0) goto 242'),
        (0x0202caf8, 4, 'if (r1 != 1) {'),
        (0x0202cafc, 6, 'r11 = 33797932'),
        (0x0202cb02, 6, 'r11 = 33799688'),
        (0x0202cb54, 2, 'r5 = r1 << 3'),
        (0x0202cb5c, 4, 'r2 = h[r11+r7<<1] (u)'),
        (0x0202cb84, 4, 'ifs (r7 < r5) goto -44'),
        (0x0202cb8c, 6, 'r7 = 33797980'),
        (0x0202cba6, 2, 'r0 = [r7+0]'),
        (0x0202cbe0, 2, 'r7 = r7 + 4'),
        (0x0202cbe6, 4, 'ifs (r3 < r1) goto -74'),
        (0x0202cbf6, 4, 'r0 = h[r3+76] (s)'),
        (0x0202cbfc, 4, 'ifs (r0 >= 3) {'),
        (0x0202cc00, 2, 'r1 = 3'),
        (0x0202cc04, 4, 'r4 = r9 + 0x3480000'),
        (0x0202cc08, 4, 'ifs (r0 >= 0) {'),
        (0x0202cc0c, 2, 'r2 = r1'),
        (0x0202cc0e, 6, 'r0 = 33799704'),
        (0x0202cc14, 4, 'r0 = [r0+r2<<2]'),
    ),
    'object_length': (
        (0x02029e98, 6, 'r1 = 33799624'),
        (0x02029e9e, 4, 'r0 = h[r1+r0<<1] (u)'),
    ),
    'build39': (
        (0x0202a902, 6, 'r6 = 33799640'),
        (0x0202a918, 2, 'r0 = [r6++=4]'),
        (0x0202a93e, 2, 'r7 = r7 + 1'),
        (0x0202a940, 4, 'if (r7 != 4) goto -44'),
    ),
    'build21': (
        (0x0202b666, 2, 'r1 = 0'),
        (0x0202b668, 2, 'call -190'),
    ),
    'build22': (
        (0x0202b73a, 2, 'r1 = 1'),
        (0x0202b73e, 4, 'call -406'),
    ),
    'build23': (
        (0x0202b814, 2, 'r1 = 2'),
        (0x0202b816, 4, 'call -622'),
    ),
}


def check_declarations(constants):
    expected = {name: spec['bounds'] for name, spec in TABLES.items()}
    if constants.get('STATIC') != expected:
        raise ValueError('model static registry differs from the sixteen reviewed spans')
    if constants.get('TABLES') != {'model_branches': TABLES['model_branches']['bounds']}:
        raise ValueError('model embedded-table declaration changed')
    regions = constants.get('REGIONS', {})
    if len(regions) != 49:
        raise ValueError('model registry must declare exactly 49 new whole bodies')
    for name, spec in CONSUMERS.items():
        if regions.get(name) != spec['bounds']:
            raise ValueError('model complete consumer declaration changed')


def with_model_ranges(previous):
    spans = [*previous, *((*spec['bounds'], 'model_'+name) for name, spec in TABLES.items())]
    for i, (start, end, _) in enumerate(spans):
        if start >= end or any(start < b and a < end for a, b, _ in spans[i+1:]):
            raise ValueError('model data overlaps another exclusion')
    for a, b in UNCLASSIFIED:
        if any(a < end and start < b for start, end, _ in spans):
            raise ValueError('unread table prefixes, suffixes or alignment were classified as data')
    return spans


def normalized_model_report(report):
    if (report.get('result') != 'pass' or report.get('original_sha256') != REFERENCE_SHA
        or report.get('original_image_sha256', REFERENCE_SHA) != REFERENCE_SHA):
        raise ValueError('model report is not passing evidence for the pinned original')
    return dict(report, original_image_sha256=REFERENCE_SHA)


def decode_consumer(name, raw, isa):
    spec = CONSUMERS[name]; start, end = spec['bounds']
    if len(raw) != end-start or sha(raw) != spec['sha256']:
        raise ValueError('model complete consumer bytes differ')
    embedded = TABLES['model_branches']['bounds']
    decoded, seconds, cursor = [], set(), 0
    while cursor < len(raw):
        pc = start+cursor
        if embedded[0] <= pc < embedded[1]:
            if pc != embedded[0] or embedded[1] > end:
                raise ValueError('model consumer cuts through embedded data')
            cursor = embedded[1]-start; continue
        found = codec.decode(isa, raw, cursor)
        if found is None: raise ValueError('undecoded model consumer instruction')
        instruction, fields, size = found
        if pc+size > end or pc < embedded[1] and embedded[0] < pc+size:
            raise ValueError('model instruction crosses a function or table boundary')
        text = codec.format(instruction, fields)
        decoded.append((pc, size, text.removesuffix('  #')))
        if text.endswith('  #'): seconds.add(pc+size)
        cursor += size
    if len(decoded) != spec['instructions'] or not seconds <= {pc for pc, _, _ in decoded}:
        raise ValueError('model consumer instruction count or packet layout changed')
    if not all(site in decoded for site in PROOF_SITES[name]):
        raise ValueError('model table address, index, field or caller proof changed')
    return decoded, seconds


def branch_targets(raw, decoded, seconds):
    start, end = TABLES['model_branches']['bounds']
    a, b = CONSUMERS['build16_to23']['bounds']
    if len(raw) != 8 or len(raw) != end-start:
        raise ValueError('model dispatch must contain exactly eight byte entries')
    pcs = {pc for pc, _, _ in decoded}
    if any(start <= pc < end for pc in pcs):
        raise ValueError('model dispatch bytes were decoded as instructions')
    targets = [start+2*v for v in raw]
    if any(not a <= target < b or target not in pcs or target in seconds for target in targets):
        raise ValueError('model dispatch target is not a complete consumer packet start')
    return targets


def table_evidence(report, raw, isa):
    normalized_model_report(report)
    if set(report.get('static_data', {})) != set(TABLES):
        raise ValueError('model report changed the exact sixteen static declarations')
    consumers, decodings, seconds = {}, {}, {}
    for name, spec in CONSUMERS.items():
        item = report['functions'][name]
        if ((address(item['start']), address(item['end_exclusive'])) != spec['bounds']
            or item.get('bytes_sha256') != spec['sha256']
            or item.get('instructions') != spec['instructions'] or item.get('new') is not True):
            raise ValueError('model report lacks an exact complete table consumer')
        decoded, parallel = decode_consumer(name, raw(*spec['bounds']), isa)
        decodings[name], seconds[name] = decoded, parallel
        consumers[name] = {'start': hex_address(spec['bounds'][0]),
            'end_exclusive': hex_address(spec['bounds'][1]), 'sha256': spec['sha256'],
            'decoded_instructions': len(decoded),
            'instruction_sites': [{'address': hex_address(pc), 'size': size, 'instruction': text}
                                  for pc, size, text in PROOF_SITES[name]]}
    tables = {}
    for name, spec in TABLES.items():
        item = report['static_data'][name]; start, end = spec['bounds']; data = raw(start, end)
        if ((address(item['start']), address(item['end_exclusive'])) != spec['bounds']
            or item.get('sha256') != spec['sha256'] or sha(data) != spec['sha256']):
            raise ValueError('model table range or exact byte hash changed')
        tables[name] = {'start': hex_address(start), 'end_exclusive': hex_address(end),
            'bytes': end-start, 'sha256': spec['sha256'], 'kind': 'model_'+name,
            'consumer': spec['consumer'], 'new_exclusion': True}
    start, end = TABLES['object_records']['bounds']
    groups = list(raw(start, end)[58::84])
    if groups != [0, 2, 0, 0] or report.get('immutable_record_groups') != groups:
        raise ValueError('model object group fields differ from the pinned four records')
    tables['object_records'].update(record_width=84, records=4, group_field_offset=58,
        immutable_groups=groups, field_consumer='object_mode0')
    tables['object0_lengths2'].update(elements=16, element_width=2,
        group_count_bound=2, elements_per_group=8)
    tables['object0_feedback2'].update(elements=2, element_width=4, group_count_bound=2)
    tables['object0_lengths1'].update(elements=8, element_width=2,
        statically_identified_consumer=True, dynamically_reachable_with_pinned_records=False)
    tables['tone_records'].update(record_width=28, records=3,
        selector_callers=['build21', 'build22', 'build23'])
    tables['object1_lengths'].update(elements=8, element_width=2, index_caller='object_mode1')
    data = raw(*TABLES['model_branches']['bounds'])
    targets = branch_targets(data, decodings['build16_to23'], seconds['build16_to23'])
    tables['model_branches'].update(entries=8, entry_width=1, padding_bytes=0,
        targets=list(map(hex_address, targets)), targets_are_packet_starts=True)
    return {'tables': tables, 'complete_consumers': consumers}


def corpus_evidence(report, raw, decode, regions, data_ranges, declared_new):
    """Authenticate all canonical function instructions before reading windows."""
    normalized_model_report(report)
    functions = report.get('functions')
    if not isinstance(functions, dict) or not functions:
        raise ValueError('model report requires complete function declarations')
    canonical, new_pcs, function_pcs, new_names = {}, set(), {}, set()
    for name, item in functions.items():
        start, end = address(item['start']), address(item['end_exclusive'])
        if end <= start or sha(raw(start, end)) != item['bytes_sha256']:
            raise ValueError('model function bytes or bounds changed')
        if item.get('new') is True:
            if (start, end) in regions or declared_new.get(name) != (start, end):
                raise ValueError('new model function is prior evidence or differs from its registry')
            new_names.add(name)
        elif item.get('new') is False:
            prior = regions.get((start, end))
            if prior is None or prior['kind'] != 'function_region' or prior['sha256'] != item['bytes_sha256']:
                raise ValueError('reused model function is not an exact prior whole body')
        else: raise ValueError('model function needs an explicit new/reused boolean')
        instructions = decode(start, end)
        if (type(item.get('instructions')) is not int or item['instructions'] != len(instructions)
            or type(item.get('visited')) is not int or not 0 <= item['visited'] <= len(instructions)):
            raise ValueError('model per-function coverage differs from canonical decoding')
        pcs = set()
        for pc, size, text in instructions:
            if pc in canonical: raise ValueError('model function declarations overlap')
            canonical[pc] = (size, text); pcs.add(pc)
        function_pcs[name] = pcs
        if item['new']: new_pcs.update(pcs)
    if new_names != set(declared_new):
        raise ValueError('model report omitted or invented a new registry entry')
    windows = report.get('loaded_instruction_windows')
    if not isinstance(windows, list) or not windows:
        raise ValueError('model report lacks loaded instruction windows')
    loaded, spans = set(), []
    for item in windows:
        start, end = address(item['start']), address(item['end_exclusive'])
        if end <= start or sha(raw(start, end)) != item['sha256']:
            raise ValueError('model loaded window bytes or bounds changed')
        for pc, size, text in decode(start, end):
            if pc in loaded or canonical.get(pc) != (size, text):
                raise ValueError('model window is not a unique canonical function instruction')
            loaded.add(pc)
        spans.append((start, end))
    spans.sort()
    if any(b > c for (_, b), (c, _) in zip(spans, spans[1:])) or loaded != set(canonical):
        raise ValueError('model windows overlap or differ from the complete function corpus')
    coverage = report['instruction_coverage']; gaps = {}
    for key, domain in (('unvisited_new', new_pcs), ('unvisited_inherited', loaded-new_pcs)):
        values = list(map(address, coverage[key])); gaps[key] = set(values)
        if len(values) != len(set(values)) or not set(values) <= domain:
            raise ValueError('model execution gap lies outside its new/reused instruction domain')
    absent = gaps['unvisited_new'] | gaps['unvisited_inherited']
    expected = {'new_decoded': len(new_pcs), 'new_visited': len(new_pcs-absent),
        'all_decoded': len(loaded), 'all_visited': len(loaded-absent)}
    if any(type(coverage.get(key)) is not int or coverage[key] != value for key, value in expected.items()):
        raise ValueError('model aggregate coverage disagrees with canonical instruction gaps')
    per_function = {}
    for name, pcs in function_pcs.items():
        if functions[name]['visited'] != len(pcs-absent):
            raise ValueError('model body visitation differs from its declared gaps')
        per_function[name] = {'decoded': len(pcs), 'visited': len(pcs-absent), 'unvisited': len(pcs & absent)}
    static = report.get('loaded_static_data')
    if not isinstance(static, dict) or not static: raise ValueError('model loaded static bindings are absent')
    for item in static.values():
        start, end = address(item['start']), address(item['end_exclusive'])
        if (end <= start or sha(raw(start, end)) != item['sha256']
            or not any(a <= start < end <= b for a, b, _ in data_ranges)):
            raise ValueError('model loaded data lacks exact original and classified range bindings')
    return {'new_functions': len(new_names), 'reused_functions': len(functions)-len(new_names),
        **expected, 'new_gaps': len(gaps['unvisited_new']), 'inherited_gaps': len(gaps['unvisited_inherited']),
        'per_function': per_function, 'static_spans': len(static)}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 53 or len(set(PRESERVED_REPORTS)) != 53:
        raise ValueError('inventory12 must contain exactly 53 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, MODEL_REPORT} <= set(selected):
        raise ValueError('model inventory omitted or duplicated prior evidence')


class ModelsInventory(IntegrationsInventory):
    def __init__(self, *required, configured_signal_report, model_report, additional_reports=()):
        self.model_report = local(model_report).relative_to(ROOT).as_posix()
        if self.model_report != MODEL_REPORT: raise ValueError('model adapter requires frozen construction03')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if self.model_report in additions: raise ValueError('model report is already explicitly selected')
        self.model_tables, self.model_corpus = {}, None
        super().__init__(*required, configured_signal_report=configured_signal_report,
            additional_reports=additions)

    def add_known_data(self):
        super().add_known_data()
        raw_report = self.read(self.model_report)
        if sha(raw_report) != MODEL_SHA: raise ValueError('frozen model report digest changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report.get('source_sha256', {}).get(MODEL) != sha(source):
            raise ValueError('model registry differs from the passing report source')
        constants = declared_constants(source.decode('utf-8')); check_declarations(constants)
        self.model_new = constants['REGIONS']
        self.data_ranges = with_model_ranges(self.data_ranges)
        self.model_tables = table_evidence(report, self.raw, self.instructions)
        for name, spec in CONSUMERS.items():
            decoded, _ = decode_consumer(name, self.raw(*spec['bounds']), self.instructions)
            if self.decode(*spec['bounds']) != decoded:
                raise ValueError('inventory and independent model consumer decoding disagree')

    def reports(self):
        omitted = super().reports(); path = local(self.model_report)
        raw_report = self.read(self.model_report)
        if sha(raw_report) != MODEL_SHA: raise ValueError('frozen model report digest changed')
        report = normalized_model_report(json.loads(raw_report))
        self.audit_sources(report['source_sha256'])
        manifest_path = (path.parent/'build-manifest.json').relative_to(ROOT).as_posix()
        raw_manifest = self.read(manifest_path)
        if sha(raw_manifest) != MODEL_MANIFEST_SHA: raise ValueError('frozen model manifest digest changed')
        for name, digest in json.loads(raw_manifest)['files'].items():
            if Path(name).name != name: raise ValueError('model artifact must be a direct manifest sibling')
            artifact = (path.parent/name).relative_to(ROOT).as_posix()
            if sha(self.read(artifact)) != digest: raise ValueError('model artifact differs from its completed manifest')
            self.audited_artifacts.add(artifact)
        self.model_corpus = corpus_evidence(report, self.raw, self.decode, self.regions,
            self.data_ranges, self.model_new)
        for name, item in report['functions'].items():
            self.add_region(path.parent.name, name, item['start'], item['end_exclusive'], item['bytes_sha256'])
        self.modules.append({'module': path.parent.name, 'report': self.model_report,
            'report_sha256': sha(raw_report), 'declared_regions': len(report['functions']),
            'source_hashes_checked': len(report['source_sha256']),
            'instruction_coverage': coverage_summary(report),
            'reported_region_coverage': self.model_corpus['per_function'],
            'reported_coverage_notes': {'classified_new_gaps': report['missing_classification'],
                'new_and_reused_instruction_gaps_preserved': True,
                'loaded_windows_are_not_additional_reconstructed_regions': True},
            'scope_limits': ['All six former constructor numerical services execute recovered arithmetic.',
                'Five new instruction gaps retain their original report classifications; no whole-firmware or hardware execution is claimed.',
                'Finite map, exponential, generator and table-index domains are stated in the module source and documentation.'],
            'original_hash_field_adapter': 'original_sha256 -> original_image_sha256 in memory only'})
        return [name for name in omitted if name != self.model_report]

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=11, model_inventory_adapter=ADAPTER, model_data_tables=self.model_tables,
            model_instruction_evidence=self.model_corpus,
            model_data_exclusion_summary={'new_spans': 16, 'new_bytes': 669,
                'new_embedded_spans': 1, 'new_embedded_bytes': 8, 'branch_entries': 8,
                'padding_bytes': 0, 'new_external_spans': 15, 'new_external_bytes': 661,
                'complete_consumers': 13, 'decoded_proof_sites': sum(map(len, PROOF_SITES.values())),
                'report': self.model_report})
        report['audits'].update(inventory12_all_fifty_three_reports_retained=True,
            model_tables_exact_declarations_bytes_and_complete_consumers_verified=True,
            model_index_bounds_strides_fields_and_callers_independently_decoded=True,
            model_immutable_record_groups_bound_to_original_bytes=True,
            model_unused_table_prefixes_suffixes_and_alignment_left_unclassified=True,
            model_branch_targets_are_canonical_packet_starts=True,
            model_loaded_windows_and_new_reused_coverage_bound_to_complete_functions=True,
            model_original_hash_schema_adapted_without_changing_evidence=True)
        report['scope_policy'].extend([
            'sixteen model table spans total 669 bytes: eight embedded dispatch bytes and 661 external bytes; no surrounding alignment or unread suffix is classified by adjacency',
            'immutable object record group fields are 0,2,0,0, limiting the reached non-single tables to sixteen halfwords and two float words; their twenty unread suffix bytes stay unclassified',
            'the separate groups==1 table is statically bound to an original consumer but remains unreachable under the pinned immutable records; it is not dynamically validated',
            'all new and reused model bodies are decoded canonically before authenticating merged loaded windows; five new and every inherited instruction gap remain explicit',
            'model evidence adds only its 49 complete new bodies; numerical integration, lookup data and merged windows add no synthetic functions or firmware-completion percentage'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject altered code/data evidence without generating an inventory."""
    original, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(original) != REFERENCE_SHA or unpack_app(original)[2]['app.bin'] != app:
        raise ValueError('model self-check requires the pinned original application')
    inventory = object.__new__(ModelsInventory)
    inventory.app = app; inventory.instructions = table.load()
    inventory.flash_start, inventory.flash_end = 0x02000120, 0x02000120+len(app)
    inventory.ram_source, inventory.ram_size = 0x02056780, 0x2030c
    inventory.ram_start, inventory.ram_end = 0x01c00000, 0x01c2030c
    inventory.data_ranges = with_model_ranges([])
    constants = declared_constants(local(MODEL).read_text(encoding='utf-8'))
    check_declarations(constants); checks = 1
    def rejected(function, *args, **kwargs):
        nonlocal checks
        try: function(*args, **kwargs)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid model inventory evidence accepted')
    report_bytes = local(MODEL_REPORT).read_bytes()
    if sha(report_bytes) != MODEL_SHA: raise ValueError('model self-check report digest changed')
    valid = json.loads(report_bytes)
    evidence = table_evidence(valid, inventory.raw, inventory.instructions); checks += 1
    assert sum(value['bytes'] for value in evidence['tables'].values()) == 669; checks += 1
    for name, spec in TABLES.items():
        changed = copy.deepcopy(constants); changed['STATIC'][name] = (0, 1)
        rejected(check_declarations, changed)
        for key, value in (('start', 0), ('end_exclusive', spec['bounds'][1]+1), ('sha256', '0'*64)):
            changed = copy.deepcopy(valid); changed['static_data'][name][key] = value
            rejected(table_evidence, changed, inventory.raw, inventory.instructions)
        a, b = spec['bounds']; previous = [(a+1, b, 'conflict')]
        before = list(previous); rejected(with_model_ranges, previous)
        assert previous == before; checks += 1
        inventory.data_ranges = [(a, b, 'single_model_table')]
        for pc, wanted in ((a-1, 'flash_outside_known_data'), (a, 'single_model_table'),
            (b-1, 'single_model_table'), (b, 'flash_outside_known_data')):
            assert inventory.classification(pc) == wanted; checks += 1
    for name, spec in CONSUMERS.items():
        changed = copy.deepcopy(constants); changed['REGIONS'][name] = (0, 1)
        rejected(check_declarations, changed)
        for key, value in (('bytes_sha256', '0'*64), ('end_exclusive', spec['bounds'][1]-2),
            ('instructions', spec['instructions']+1), ('new', False)):
            changed = copy.deepcopy(valid); changed['functions'][name][key] = value
            rejected(table_evidence, changed, inventory.raw, inventory.instructions)
        raw = inventory.raw(*spec['bounds'])
        rejected(decode_consumer, name, raw[:-1], inventory.instructions)
        rejected(decode_consumer, name, bytes([raw[0]^1])+raw[1:], inventory.instructions)
    changed = copy.deepcopy(constants); changed['STATIC']['invented'] = (0, 1)
    rejected(check_declarations, changed)
    changed = copy.deepcopy(constants); changed['TABLES']['model_branches'] = (0, 1)
    rejected(check_declarations, changed)
    changed = copy.deepcopy(constants); changed['REGIONS']['invented'] = (0, 1)
    rejected(check_declarations, changed)
    changed = copy.deepcopy(valid); changed['immutable_record_groups'] = [0, 3, 0, 0]
    rejected(table_evidence, changed, inventory.raw, inventory.instructions)
    inventory.data_ranges = with_model_ranges([])
    for a, b in UNCLASSIFIED:
        for pc in range(a, b):
            assert inventory.classification(pc) == 'flash_outside_known_data'; checks += 1
        rejected(with_model_ranges, [(a, b, 'invented_data')])
    raw = inventory.raw(*TABLES['model_branches']['bounds'])
    decoded, seconds = decode_consumer('build16_to23', inventory.raw(*CONSUMERS['build16_to23']['bounds']), inventory.instructions)
    targets = branch_targets(raw, decoded, seconds); checks += 1
    for target in set(targets):
        rejected(branch_targets, raw, decoded, seconds | {target})
        rejected(branch_targets, raw, [item for item in decoded if item[0] != target], seconds)
    for changed in (raw[:-1], raw+b'\0', b'\0'+raw[1:], b'\xff'+raw[1:]):
        rejected(branch_targets, changed, decoded, seconds)
    rejected(branch_targets, raw, decoded+[(TABLES['model_branches']['bounds'][0], 2, 'not code')], seconds)
    selected = [*PRESERVED_REPORTS, MODEL_REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[MODEL_REPORT])
    adapted = normalized_model_report(valid)
    assert 'original_image_sha256' not in valid and adapted['original_image_sha256'] == REFERENCE_SHA; checks += 1
    rejected(normalized_model_report, {'result': 'pass', 'original_image_sha256': REFERENCE_SHA})

    # An independently decoded minimal corpus isolates canonical boundaries,
    # reused-parent identity and new/reused coverage classification.
    code = b'\0\0\x80\0\x80\0\x80\0'; data = b'\x01\x02'
    def raw_span(a, b): return data[a-0x2000:b-0x2000] if a >= 0x2000 else code[a-0x1000:b-0x1000]
    def decode_span(a, b):
        items = []
        while a < b:
            size = 4 if a == 0x1000 else 2
            items.append((a, size, 'wide' if size == 4 else 'rts')); a += size
        return items
    prior = {(0x1004, 0x1008): {'kind': 'function_region', 'sha256': sha(raw_span(0x1004, 0x1008))}}
    new = {'new': (0x1000, 0x1004)}; known = [(0x2000, 0x2002, 'prior_data')]
    sample = {'result': 'pass', 'original_sha256': REFERENCE_SHA,
        'functions': {'new': {'start': 0x1000, 'end_exclusive': 0x1004,
            'bytes_sha256': sha(raw_span(0x1000, 0x1004)), 'instructions': 1, 'visited': 1, 'new': True},
            'old': {'start': 0x1004, 'end_exclusive': 0x1008,
            'bytes_sha256': prior[(0x1004, 0x1008)]['sha256'], 'instructions': 2, 'visited': 1, 'new': False}},
        'loaded_instruction_windows': [{'start': 0x1000, 'end_exclusive': 0x1008, 'sha256': sha(code)}],
        'loaded_static_data': {'table': {'start': 0x2000, 'end_exclusive': 0x2002, 'sha256': sha(data)}},
        'instruction_coverage': {'new_decoded': 1, 'new_visited': 1, 'unvisited_new': [],
            'all_decoded': 3, 'all_visited': 2, 'unvisited_inherited': [0x1006]}}
    def corpus(value=sample, parents=prior, ranges=known, declared=new):
        return corpus_evidence(value, raw_span, decode_span, parents, ranges, declared)
    assert corpus()['new_functions'] == 1; checks += 1
    mutations = [
        ((), 'original_sha256', '0'*64), ((), 'result', 'fail'), ((), 'functions', {}),
        ((), 'loaded_instruction_windows', []), ((), 'loaded_static_data', {}),
        (('functions', 'new'), 'new', False), (('functions', 'old'), 'new', True),
        (('functions', 'new'), 'instructions', 2), (('functions', 'new'), 'visited', 0),
        (('functions', 'old'), 'bytes_sha256', '0'*64),
        (('instruction_coverage',), 'all_decoded', 4), (('instruction_coverage',), 'all_visited', 3),
        (('instruction_coverage',), 'new_decoded', 2), (('instruction_coverage',), 'new_visited', 0),
        (('instruction_coverage',), 'unvisited_new', [0x1006]),
        (('instruction_coverage',), 'unvisited_inherited', [0x1000]),
        (('instruction_coverage',), 'unvisited_inherited', [0x1006, 0x1006]),
        (('loaded_static_data', 'table'), 'sha256', '0'*64)]
    for path, key, value in mutations:
        changed = copy.deepcopy(sample); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(corpus, changed)
    changed = copy.deepcopy(sample)
    changed['loaded_instruction_windows'][0] = {'start': 0x1002, 'end_exclusive': 0x1008,
        'sha256': sha(raw_span(0x1002, 0x1008))}
    rejected(corpus, changed)
    changed = copy.deepcopy(sample); changed['loaded_instruction_windows'] *= 2; rejected(corpus, changed)
    altered = copy.deepcopy(prior); altered[(0x1004, 0x1008)]['kind'] = 'parser_fragment'
    rejected(corpus, parents=altered); rejected(corpus, parents={}); rejected(corpus, ranges=[])
    rejected(corpus, declared={}); rejected(corpus, declared={'new': (0x1000, 0x1002)})
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'new_data_spans': 16,
        'new_data_bytes': 669, 'complete_consumers': 13, 'decoded_proof_sites': sum(map(len, PROOF_SITES.values())),
        'preserved_reports': 53, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    parser.add_argument('--configured-signal-report'); parser.add_argument('--model-report')
    parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true'); args = parser.parse_args()
    required = tuple(getattr(args, name.replace('-', '_')) for name in REQUIRED_OPTIONS)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report or args.configured_signal_report or args.model_report:
            parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required) or not args.configured_signal_report or not args.model_report:
        parser.error('choose --output or --check and provide every required report')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a fresh directory under build/')
    report = ModelsInventory(*required, configured_signal_report=args.configured_signal_report,
        model_report=args.model_report, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'model-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'model_data_exclusion_summary': report['model_data_exclusion_summary']}, indent=2))


if __name__ == '__main__': main()
