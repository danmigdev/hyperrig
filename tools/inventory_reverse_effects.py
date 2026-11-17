"""Extend the frozen stage inventory with exact verified effect data tables.

Table exclusions require pinned bytes, complete consumer bodies and original
address/index instructions. Embedded branch targets must be decoded packet
starts. Report selection retains every report from inventory 08.
"""
from __future__ import annotations
import argparse
import ast
import copy
import json
from pathlib import Path
import struct

from inventory_reverse import ROOT, REFERENCE_SHA, address, hex_address, local, sha, codec, table
from inventory_reverse_stage import StageInventory

PREVIOUS_RUNS = (
    'audio-task-03', 'biquad-01', 'biquad-chain-01', 'biquad-coefficients-01',
    'biquad-generator-01', 'biquad-pipeline-01', 'capture-async-03',
    'capture-command-01', 'capture-container-01', 'capture-dispatch-03',
    'capture-journal-02', 'capture-live-02', 'capture-loader-01',
    'capture-metadata-01', 'capture-native-02', 'capture-parser-03',
    'capture-processing-03', 'capture-reset-03', 'capture-warmup-02',
    'control-actions-01', 'controls-02', 'dsp-audio-path-01', 'dsp-dynamics-01',
    'dsp-dynamics-processing-02', 'dsp-initialization-01', 'dsp-stage-02',
    'dsp-transition-03', 'dsp-transition-notification-05', 'ir-convolution-02',
    'ir-installation-01', 'ir-loader-02', 'ir-processing-01',
    'preset-application-01', 'preset-assets-01', 'preset-loader-01',
    'preset-preflight-01', 'preset-storage-01', 'scene-application-03', 'selection-01')
PREVIOUS_REPORTS = tuple(f'build/reverse-{name}/verification.json' for name in PREVIOUS_RUNS)
MODULES = {
    'resampling': 'tools/effect_resampling_machine.py',
    'enable': 'tools/effect_enable_machine.py',
    'support': 'tools/effect_parameter_support_machine.py',
    'processing': 'tools/effect_processing_machine.py',
    'parameters': 'tools/effect_parameters_machine.py',
}
CONSUMERS = {
    ('resampling', 'up'): ((0x01C07986, 0x01C07A4C), (
        (0x01C07998, 6, 'r0 = 33798004'), (0x01C0799E, 4, 'r4 = [r0+r3<<2]'),
        (0x01C079A2, 6, 'r0 = 33797992'), (0x01C079A8, 4, 'r0 = [r0+r3<<2]'),
        (0x01C079AC, 4, 'r0 = 0x1 - r4'), (0x01C079B0, 2, '[sp+4] = r0'),
        (0x01C079F8, 2, 'r4 = [sp+4]'), (0x01C079FC, 2, 'r14 = [sp+8]'),
        (0x01C07A02, 2, 'r0 = [r4++=4]'), (0x01C07A0A, 4, 'r13_r12 += r2 * r0 (s)'),
        (0x01C07A12, 4, 'if (--r14 != 0) goto -20'))),
    ('resampling', 'down'): ((0x01C08A76, 0x01C08B34), (
        (0x01C08A86, 6, 'r4 = 33798004'), (0x01C08A8C, 4, 'r12 = [r4+r3<<2]'),
        (0x01C08A90, 6, 'r4 = 33797992'), (0x01C08A96, 4, 'r1 = [r4+r3<<2]'),
        (0x01C08AF2, 2, 'r3 = r1'), (0x01C08AF6, 2, 'r5_r4 = r13_r12'),
        (0x01C08AF8, 2, 'r7 = [r3++=4]'), (0x01C08B02, 4, 'r11_r10 += r8 * r7 (s)'),
        (0x01C08B0A, 4, 'if (--r4 != 0) goto -22'))),
    ('enable', 'fade'): ((0x01C069E4, 0x01C06B2C), (
        (0x01C06A38, 2, 'r1 = b[r4+0] (u)'), (0x01C06A3C, 2, 'r1 += -11'),
        (0x01C06A3E, 4, 'if (r1 > 28) goto 186'), (0x01C06A48, 2, 'tbb [r1]'))),
    ('support', 'selector'): ((0x01C060E6, 0x01C060FA), (
        (0x01C060E6, 2, 'r0 += -3'), (0x01C060E8, 4, 'if (r0 > 20) {'),
        (0x01C060EE, 6, 'r1 = 33798272'), (0x01C060F4, 4, 'r0 = [r1+r0<<2]'))),
    ('support', 'tempo'): ((0x0202ED38, 0x0202ED70), (
        (0x0202ED44, 6, 'r0 = 33797720'), (0x0202ED4A, 4, 'r0 = b[r3+r0] (u)'),
        (0x0202ED4E, 6, 'r1 = 33797733'), (0x0202ED54, 4, 'r1 = b[r3+r1] (u)'))),
    ('processing', 'cost'): ((0x01C058BC, 0x01C05C08), (
        (0x01C058BE, 2, 'r2 = b[r0+0] (u)'), (0x01C058C0, 4, 'r4 = r2 + -4'),
        (0x01C058C4, 6, 'r7 = 33796928'), (0x01C058CE, 4, 'if (r4 > 35) goto 244'),
        (0x01C058D2, 2, 'r5 = r4 << 1'), (0x01C058E0, 2, 'tbh [r5]'),
        (0x01C059CC, 4, 'r3 = [r7+r2<<2]'), (0x01C059D4, 4, 'r5 = r2 + -3'),
        (0x01C059E0, 4, 'if (r5 <= 20) {'), (0x01C059E4, 6, 'r4 = 33798368'),
        (0x01C059EA, 4, 'r4 = [r4+r5<<2]'), (0x01C05A86, 6, 'r0 = 33799616'),
        (0x01C05A8C, 4, 'r0 = h[r0+r3<<1] (u)'))),
    ('processing', 'extra_cost'): ((0x01C05C08, 0x01C05D02), (
        (0x01C05C14, 2, 'r7 = b[r4+0] (u)'), (0x01C05C94, 4, 'r0 = r7 + -5'),
        (0x01C05C98, 4, 'if (r0 > 34) goto 72'), (0x01C05CA0, 2, 'tbb [r0]'))),
    ('processing', 'dispatch'): ((0x01C0DEB6, 0x01C0F678), (
        (0x01C0DF34, 4, 'r12 = r15 * 0x6'), (0x01C0DF38, 6, 'r4 = 33798064'),
        (0x01C0DF3E, 4, 'r8 = r12 + r4'), (0x01C0DF42, 4, 'r4 = b[r8+0] (u)'),
        (0x01C0DF48, 4, 'r5 = b[r8+1] (u)'), (0x01C0DFE8, 6, 'r0 = 33798064'),
        (0x01C0DFEE, 4, 'r1 = b[r12+r0] (u)'),
        (0x01C0E086, 2, 'r1 = r0 << 1'), (0x01C0E0A6, 2, 'tbh [r1]'))),
    ('processing', 'individual'): ((0x01C0F678, 0x01C10446), (
        (0x01C101F8, 4, 'r1 = r2 + -11'), (0x01C101FC, 4, 'if (r1 > 28) goto 426'),
        (0x01C10200, 2, 'r2 = r1 << 1'), (0x01C10202, 2, 'tbh [r2]'))),
    ('parameters', 'word_kind'): ((0x0202F502, 0x0202F6B4), (
        (0x0202F506, 4, 'r3 = r0 + -1'), (0x0202F50C, 4, 'if (r3 > 38) goto 240'),
        (0x0202F510, 2, 'r4 = r3 << 1'), (0x0202F516, 2, 'tbh [r4]'))),
}

# Each tuple is (module, report key, exact bounds, hash, complete consumers,
# optional branch entry width/count/padding). Adjacent spans remain separate.
TABLES = {
    'resampling_pointers': ('resampling', 'coefficient_pointers', (0x0203B768, 0x0203B774),
        '0b7509d70901780674ffeaf5e6ea3cbea636dde0bc1ce793f772c18c80f8b628', ('up', 'down'), None),
    'resampling_counts': ('resampling', 'tap_counts', (0x0203B774, 0x0203B780),
        'bd62d5246f9fcbe9b2173ed98aa4cb2946971dffc4b05f7647c09c7b889ff44f', ('up', 'down'), None),
    'resampling_five_taps': ('resampling', 'five_taps', (0x0203B780, 0x0203B794),
        'b096b46c18335e62616b66a3e62dc5cfd1247a40ff1f42eb42a867f216f19f45', ('up', 'down'), None),
    'resampling_three_taps': ('resampling', 'three_taps', (0x0203B794, 0x0203B7A0),
        '1ad834bf5f01c61a57488136acd64398ee13d41b096e68d49c3897d8ae367f9e', ('up', 'down'), None),
    'resampling_four_taps': ('resampling', 'four_taps', (0x0203B7A0, 0x0203B7B0),
        '2ff6b84d0433cee00b632aef3a64e4e5529d52875f12f6963775f4262c4b2cee', ('up', 'down'), None),
    'enable_fade_branches': ('enable', 'fade_table', (0x01C06A4A, 0x01C06A67),
        'b938b1435b794419e01db5cff039782e3016382ba2ad689a0035d9c81d8319bb', ('fade',), (1, 29, 0)),
    'enable_fade_alignment': ('enable', 'fade_alignment', (0x01C06A67, 0x01C06A68),
        '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d', ('fade',), None),
    'support_selector': ('support', 'selector', (0x0203B880, 0x0203B8D4),
        '3d558f81b50146dd3006396db32da015bd93e4df55bf01c78d52e76cdda324a4', ('selector',), None),
    'support_tempo': ('support', 'tempo', (0x0203B658, 0x0203B672),
        '51c8bacfb9be4ddf3d0f1324e14593277b2bda2ee71a584dbe06ce3653369f51', ('tempo',), None),
    'processing_cost_branches': ('processing', 'cost_branches', (0x01C058E2, 0x01C0592A),
        '1e469c98cd068329be84fbabffe564e08d0b3243e0235f1005658ea76b5063d5', ('cost',), (2, 36, 0)),
    'processing_extra_cost_branches': ('processing', 'extra_cost_branches', (0x01C05CA2, 0x01C05CC6),
        'd3c7a92cd18e75cbc114f3c0878e46a39111dd9caea9c47c815f1fb229cd0740', ('extra_cost',), (1, 35, 1)),
    'processing_dispatch_branches': ('processing', 'dispatch_branches', (0x01C0E0A8, 0x01C0E0F6),
        'cc9241147fc9219fe8ae57f8eefdcf927feeb9f3169ff33d3a07d9d86ffcb094', ('dispatch',), (2, 39, 0)),
    'processing_individual_branches': ('processing', 'individual_branches', (0x01C10204, 0x01C1023E),
        '8373d1d4abc4676c66b9248473baeca7e5513252e16c972cd43f517eb3efa000', ('individual',), (2, 29, 0)),
    'processing_state_copy': ('processing', 'state_copy', (0x0203B7B0, 0x0203B7C8),
        'c6e557b7ece1f5efd110083ec906fc5c3d5bfd4c925ae6ef445ff9910c782670', ('dispatch',), None),
    'processing_costs': ('processing', 'costs', (0x0203B340, 0x0203B3E0),
        'c109932101ee624a247811f7ec2c6b71817313c9c9a60be282ca84cda98f09c9', ('cost',), None),
    'processing_oversampling_costs': ('processing', 'oversampling_costs', (0x0203B8E0, 0x0203B934),
        'f7e1484048511cb0adbdfdedbc5caee0f523c75319756c2f6dbca61d381ab875', ('cost',), None),
    'processing_capture_costs': ('processing', 'capture_costs', (0x0203BDC0, 0x0203BDC8),
        '4f6809b3a29ad606b706650c3f3b7779f91c13514655d2956c11e94ee65992de', ('cost',), None),
    'parameter_word_kind_branches': ('parameters', 'word_kind_branches', (0x0202F518, 0x0202F566),
        'ef7dfe06236071b96fb4261b5ea693b50877f96dbc892be919449804158c539d', ('word_kind',), (2, 39, 0)),
}
NEW_TABLE_NAMES = tuple(TABLES)
PRIOR_MODULES = {
    'prior_coefficients': 'tools/biquad_coefficients_machine.py',
    'prior_initialization': 'tools/dsp_initialization_machine.py',
    'prior_gain': 'tools/dsp_transition_notification_machine.py',
}
PRIOR_REPORTS = {
    'prior_coefficients': 'build/reverse-biquad-coefficients-01/verification.json',
    'prior_initialization': 'build/reverse-dsp-initialization-01/verification.json',
    'prior_gain': 'build/reverse-dsp-transition-notification-05/verification.json',
}
CONSUMERS.update({
    ('prior_coefficients', 'setup'): ((0x02028892, 0x020288D6), (
        (0x020288B8, 6, 'r2 = 33793372'), (0x020288BE, 4, 'r0 = h[r2+r0<<1] (u)'),
        (0x020288C2, 4, 'r2 = utof(r0)'), (0x020288CE, 4, 'call -414'))),
    ('prior_initialization', 'setup'): ((0x0202898E, 0x020289D4), (
        (0x020289AA, 6, 'r3 = 33793382'), (0x020289B0, 4, 'r0 = h[r3+r0<<1] (u)'),
        (0x020289C2, 4, 'r5 = utof(r0)'), (0x020289CA, 2, 'r2 = r5'),
        (0x020289CC, 4, 'call -668'))),
    ('prior_gain', 'gain_clamp'): ((0x02007ECE, 0x02007EE2), (
        (0x02007ED0, 4, 'ifs (r0 >= 24) {'), (0x02007ED4, 2, 'r2 = 24'),
        (0x02007ED6, 2, 'r1 = -24'), (0x02007ED8, 4, 'ifs (r0 >= -24) {'),
        (0x02007EDE, 2, 'r0 = r1'))),
    ('prior_gain', 'gain_scale'): ((0x02007EE2, 0x02007EF2), (
        (0x02007EE4, 2, 'call -24'), (0x02007EE6, 6, 'r1 = 33766440'),
        (0x02007EEC, 4, 'r0 = [r1+r0<<2]'))),
})
TABLES.update({
    'prior_coefficient_selector': ('prior_coefficients', 'table', (0x0203A55C, 0x0203A566),
        '54f4a53a7dfc1bfa17702e31c5d031ce4f6e0dc2f6125463b53ffe00edb415c7', ('setup',), None),
    'prior_initialization_coefficients': ('prior_initialization', 'table', (0x0203A566, 0x0203A570),
        'fe845985ec7e666fcd26dd0d255b41a84b7863843d04287ac14ab38b19da76a6', ('setup',), None),
    'prior_gain_scale': ('prior_gain', 'gain_table', (0x02033BC8, 0x02033C8C),
        'cd539f2ab0183841f5adecc529273af02213eeb221c7723ef556f9229aa620da', ('gain_clamp', 'gain_scale'), None),
})
ALL_MODULES = MODULES | PRIOR_MODULES


def declared_constants(source):
    """Read literal registries without executing a reconstruction model."""
    values = {}
    def value(node):
        if isinstance(node, ast.Name): return values[node.id]
        if isinstance(node, (ast.Tuple, ast.List)): return tuple(value(item) for item in node.elts)
        if isinstance(node, ast.Dict):
            result = {}
            for key, item in zip(node.keys, node.values):
                try:
                    if key is None: result.update(value(item))
                    else: result[value(key)] = value(item)
                except (KeyError, ValueError, TypeError): pass
            return result
        return ast.literal_eval(node)
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign): continue
        try: result = value(node.value)
        except (KeyError, ValueError, TypeError): continue
        for target in node.targets:
            if isinstance(target, ast.Name): values[target.id] = result
            elif isinstance(target, ast.Tuple) and len(target.elts) == len(result):
                values.update((item.id, item_value) for item, item_value in zip(target.elts, result)
                              if isinstance(item, ast.Name))
    return values


def check_declarations(registries):
    for _, (module, key, bounds, _, consumers, _) in TABLES.items():
        constants = registries[module]
        if module == 'enable':
            declared = ((constants['TABLE_START'], constants['TABLE_END']) if key == 'fade_table'
                        else (constants['TABLE_END'], constants['ALIGNMENT_END']))
        elif module == 'prior_coefficients': declared = constants['TABLE'], constants['TABLE']+10
        elif module == 'prior_initialization': declared = constants['TABLE']
        elif module == 'prior_gain': declared = constants['GAIN_TABLE'], constants['GAIN_TABLE']+constants['GAIN_BYTES']
        else: declared = constants.get('STATIC', {}).get(key)
        if declared != bounds: raise ValueError('effect table declaration changed from the reviewed exact range')
        for function in consumers:
            if module == 'prior_gain': actual = constants.get('GAIN_REGIONS', {}).get(function.removeprefix('gain_'))
            else: actual = constants.get('REGIONS', {}).get(function)
            if actual != CONSUMERS[module, function][0]:
                raise ValueError('effect table consumer declaration changed')


def normalized_report(module, report, raw):
    """Adapt old table field names without altering any frozen report."""
    if module not in PRIOR_MODULES: return report
    try:
        if module == 'prior_coefficients':
            record = report['static_evidence']['table']
            values = record['uint16_values']
            if values != list(struct.unpack('<5H', raw)): raise ValueError('coefficient table values differ')
            start = address(record['address'])
            record = {'start': start, 'end_exclusive': start+2*len(values), 'sha256': record['sha256']}
            key = 'table'
        else:
            key = 'table' if module == 'prior_initialization' else 'gain_table'
            record = report[key]
    except (KeyError, TypeError, struct.error) as error:
        raise ValueError('missing previously verified table record') from error
    return dict(report, static_data={key: record})


def table_evidence(name, report, raw, consumer_raw, decoded, parallel_seconds):
    module, key, bounds, digest, consumers, branch = TABLES[name]
    if report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA:
        raise ValueError('effect data requires passing evidence for the pinned original')
    try:
        record = report['static_data'][key]
        actual = address(record['start']), address(record['end_exclusive'])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('missing exact effect data record') from error
    if actual != bounds or len(raw) != bounds[1]-bounds[0] or sha(raw) != digest or record.get('sha256') != digest:
        raise ValueError('effect table range or bytes differ from pinned evidence')
    result = {'start': hex_address(bounds[0]), 'end_exclusive': hex_address(bounds[1]),
              'bytes': len(raw), 'sha256': digest, 'kind': 'effect_'+name, 'consumers': {}}
    for function in consumers:
        expected, sites = CONSUMERS[module, function]
        try:
            item = report.get('functions', report.get('regions'))[function]
            actual = address(item['start']), address(item['end_exclusive'])
            data, instructions = consumer_raw[function], decoded[function]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('missing complete effect table consumer') from error
        if (actual != expected or len(data) != expected[1]-expected[0]
            or item.get('bytes_sha256', item.get('sha256')) != sha(data)
            or not all(site in instructions for site in sites)):
            raise ValueError('effect table lacks its complete consumer and original index sites')
        result['consumers'][function] = {'start': hex_address(expected[0]), 'end_exclusive': hex_address(expected[1]),
            'sha256': sha(data), 'instruction_sites': [{'address': hex_address(pc), 'size': size, 'instruction': text}
                                                    for pc, size, text in sites]}
    if branch:
        width, count, padding = branch
        if len(raw) != width*count+padding or any(raw[width*count:]):
            raise ValueError('invalid branch table entries or alignment')
        function = consumers[0]
        instructions = {pc for pc, _, _ in decoded[function]}
        targets = [bounds[0]+2*int.from_bytes(raw[i*width:(i+1)*width], 'little') for i in range(count)]
        start, end = CONSUMERS[module, function][0]
        if (any(not start <= target < end or target not in instructions or target in parallel_seconds[function]
                for target in targets) or any(bounds[0] <= pc < bounds[1] for pc in instructions)):
            raise ValueError('effect branch targets are not decoded consumer packet starts')
        result.update(entry_width=width, entries=count, targets=list(map(hex_address, targets)),
                      padding_bytes=padding, dispatch=hex_address(bounds[0]-2))
        if padding: result['alignment_start'] = hex_address(bounds[0]+width*count)
    if name == 'enable_fade_alignment':
        if raw != b'\0': raise ValueError('fade alignment is not the pinned zero byte')
        result['alignment_only'] = True
    return result


def resampling_links(tables):
    """Bind the indirect coefficient pointers to all three exact tap spans."""
    pointers = struct.unpack('<3I', tables['resampling_pointers'])
    counts = struct.unpack('<3I', tables['resampling_counts'])
    names = ('resampling_five_taps', 'resampling_three_taps', 'resampling_four_taps')
    if pointers != (0x0203B780, 0x0203B794, 0x0203B7A0) or counts != (5, 3, 4):
        raise ValueError('resampling pointer/count relationship differs from the original')
    if any(len(tables[name]) != count*4 for name, count in zip(names, counts)):
        raise ValueError('resampling coefficient length does not match the count')
    return [{'selector': index, 'table': name, 'pointer': hex_address(pointer), 'words': count}
            for index, (name, pointer, count) in enumerate(zip(names, pointers, counts))]


class EffectsInventory(StageInventory):
    def __init__(self, parser_report, processing_report, ir_report, application_report,
                 ir_processing_report, audio_report, stage_report, resampling_report,
                 enable_report, support_report, effect_processing_report, parameters_report,
                 additional_reports=()):
        self.effect_reports = dict(zip(MODULES, (local(name).relative_to(ROOT).as_posix() for name in
            (resampling_report, enable_report, support_report, effect_processing_report, parameters_report))))
        self.effect_reports.update(PRIOR_REPORTS)
        self.effect_tables = {}
        super().__init__(parser_report, processing_report, ir_report, application_report,
            ir_processing_report, audio_report, stage_report,
            [*PREVIOUS_REPORTS, *self.effect_reports.values(), *additional_reports])

    def add_known_data(self):
        super().add_known_data()
        records = {module: json.loads(self.read(path)) for module, path in self.effect_reports.items()}
        registries = {module: declared_constants(self.read(path).decode('utf-8')) for module, path in ALL_MODULES.items()}
        check_declarations(registries)
        for name, (module, key, bounds, _, consumers, _) in TABLES.items():
            if any(start < bounds[1] and bounds[0] < end for start, end, _ in self.data_ranges):
                raise ValueError('effect data overlaps an existing exclusion')
            self.data_ranges.append((*bounds, 'effect_'+name))
        # Decode only after all embedded data/alignment spans are excluded.
        decoded, raw_consumers, seconds = {}, {}, {}
        for (module, name), (bounds, _) in CONSUMERS.items():
            instructions = self.decode(*bounds)
            decoded[module, name] = instructions
            raw_consumers[module, name] = self.raw(*bounds)
            seconds[module, name] = set()
            for pc, size, _ in instructions:
                instruction, fields, _ = codec.decode(self.instructions, self.raw(pc, pc+size), 0)
                if codec.format(instruction, fields).endswith('  #'): seconds[module, name].add(pc+size)
        for name, (module, _, bounds, _, consumers, _) in TABLES.items():
            raw = self.raw(*bounds)
            evidence = table_evidence(name, normalized_report(module, records[module], raw), raw,
                {function: raw_consumers[module, function] for function in consumers},
                {function: decoded[module, function] for function in consumers},
                {function: seconds[module, function] for function in consumers})
            evidence.update(report=self.effect_reports[module], declaration=ALL_MODULES[module],
                            previously_verified_table=module in PRIOR_MODULES)
            self.effect_tables[name] = evidence
        self.resampling_links = resampling_links({name: self.raw(*spec[2]) for name, spec in TABLES.items()
                                                  if spec[0] == 'resampling'})

    def run(self):
        report = super().run()
        previous = {*PREVIOUS_REPORTS, 'research/native-verification.json'}
        if not previous <= set(report['selected_reports']): raise ValueError('an inventory08 report was omitted')
        self.read('tools/inventory_reverse_effects.py')
        report.update(schema=7, effects_inventory_adapter='tools/inventory_reverse_effects.py',
                      effect_data_tables=self.effect_tables, effect_resampling_links=self.resampling_links)
        report['effect_data_exclusion_summary'] = {
            'new_module_spans': len(NEW_TABLE_NAMES), 'new_module_bytes': sum(TABLES[name][2][1]-TABLES[name][2][0] for name in NEW_TABLE_NAMES),
            'previously_verified_spans': len(TABLES)-len(NEW_TABLE_NAMES),
            'previously_verified_bytes': sum(spec[2][1]-spec[2][0] for name, spec in TABLES.items() if name not in NEW_TABLE_NAMES)}
        report['audits'].update(effect_tables_exact_bytes_declarations_and_complete_consumers_verified=True,
            effect_branch_targets_are_decoded_packet_starts=True, effect_alignment_is_not_a_branch_entry=True,
            inventory08_all_forty_reports_retained=True)
        report['scope_policy'].extend([
            'the 18 new-module data spans (810 bytes) and three previously verified spans (216 bytes) are individually authenticated; adjacent and intervening bytes retain exact independent classifications',
            'the extra-cost branch table has 35 one-byte entries followed by one zero alignment byte; alignment is never a target entry',
            'immutable table proofs do not expand the execution domain, remove unresolved services, or promote loaded code to reconstructed functions'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Audit binding failures and exact endpoints without selected run artifacts."""
    app = local('analysis/firmware/m571_g_app/app.bin').read_bytes()
    def raw(bounds):
        a, b = bounds
        offset = a-0x02000120 if a >= 0x02000000 else 0x02056780-0x02000120+a-0x01C00000
        return app[offset:offset+b-a]
    inventory = object.__new__(EffectsInventory)
    inventory.app = app; inventory.instructions = table.load()
    inventory.flash_start, inventory.flash_end = 0x02000120, 0x02000120+len(app)
    inventory.ram_source, inventory.ram_size = 0x02056780, 0x2030C
    inventory.ram_start, inventory.ram_end = 0x01C00000, 0x01C2030C
    inventory.data_ranges = [(spec[2][0], spec[2][1], 'effect_'+name) for name, spec in TABLES.items()]
    check_declarations({module: declared_constants(local(path).read_text(encoding='utf-8')) for module, path in ALL_MODULES.items()})
    checks = 1
    for name, (module, key, bounds, digest, consumers, branch) in TABLES.items():
        data = raw(bounds)
        bodies = {function: raw(CONSUMERS[module, function][0]) for function in consumers}
        decoded = {function: inventory.decode(*CONSUMERS[module, function][0]) for function in consumers}
        seconds = {function: set() for function in consumers}
        for function in consumers:
            for pc, size, _ in decoded[function]:
                instruction, fields, _ = codec.decode(inventory.instructions, raw((pc, pc+size)), 0)
                if codec.format(instruction, fields).endswith('  #'): seconds[function].add(pc+size)
        if branch:
            width, count, _ = branch
            targets = [bounds[0]+2*int.from_bytes(data[i*width:(i+1)*width], 'little') for i in range(count)]
        valid = {'result': 'pass', 'original_image_sha256': REFERENCE_SHA,
            'static_data': {key: {'start': bounds[0], 'end_exclusive': bounds[1], 'sha256': digest}},
            'functions': {function: {'start': CONSUMERS[module, function][0][0],
                'end_exclusive': CONSUMERS[module, function][0][1], 'sha256': sha(bodies[function])}
                for function in consumers}}
        assert table_evidence(name, valid, data, bodies, decoded, seconds)['bytes'] == len(data)
        checks += 1
        if module in PRIOR_MODULES:
            legacy = copy.deepcopy(valid); del legacy['static_data']
            if module == 'prior_coefficients':
                legacy['static_evidence'] = {'table': {'address': bounds[0], 'sha256': digest,
                                                      'uint16_values': list(struct.unpack('<5H', data))}}
            else: legacy[key] = valid['static_data'][key]
            adapted = normalized_report(module, legacy, data)
            assert table_evidence(name, adapted, data, bodies, decoded, seconds)['sha256'] == digest
            assert 'static_data' not in legacy
            checks += 1
            broken = copy.deepcopy(legacy)
            if module == 'prior_coefficients': broken['static_evidence']['table']['uint16_values'][0] ^= 1
            else: broken[key]['end_exclusive'] += 1
            try: table_evidence(name, normalized_report(module, broken, data), data, bodies, decoded, seconds)
            except ValueError: checks += 1
            else: raise AssertionError('altered legacy table evidence accepted')
        mutations = [((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
            (('static_data', key), 'start', bounds[0]+1), (('static_data', key), 'end_exclusive', bounds[1]+1),
            (('static_data', key), 'sha256', '0'*64), ((), 'functions', {})]
        for function in consumers:
            mutations.extend([(('functions', function), 'start', CONSUMERS[module, function][0][0]+2),
                (('functions', function), 'end_exclusive', CONSUMERS[module, function][0][1]-2),
                (('functions', function), 'sha256', '0'*64)])
        for path, key_, value in mutations:
            bad = copy.deepcopy(valid); node = bad
            for part in path: node = node[part]
            node[key_] = value
            try: table_evidence(name, bad, data, bodies, decoded, seconds)
            except ValueError: checks += 1
            else: raise AssertionError('altered effect table evidence accepted')
        invalid = [(data[:-1], bodies, decoded, seconds), (data+b'\0', bodies, decoded, seconds),
                   (bytes([data[0]^1])+data[1:], bodies, decoded, seconds)]
        for function in consumers:
            altered = dict(bodies); altered[function] = b'wrong'
            invalid.append((data, altered, decoded, seconds))
            for site in CONSUMERS[module, function][1]:
                altered = dict(decoded); altered[function] = [item for item in decoded[function] if item != site]
                invalid.append((data, bodies, altered, seconds))
        if branch:
            altered = copy.deepcopy(seconds); altered[consumers[0]].add(targets[0])
            invalid.append((data, bodies, decoded, altered))
            altered = copy.deepcopy(decoded); altered[consumers[0]] = [item for item in altered[consumers[0]] if item[0] != targets[0]]
            invalid.append((data, bodies, altered, seconds))
            altered = copy.deepcopy(decoded); altered[consumers[0]].append((bounds[0], 2, 'not code'))
            invalid.append((data, bodies, altered, seconds))
        for arguments in invalid:
            try: table_evidence(name, valid, *arguments)
            except ValueError: checks += 1
            else: raise AssertionError('unbound effect table or consumer accepted')
    for name, (_, _, (a, b), _, _, _) in TABLES.items():
        inventory.data_ranges = [(a, b, 'effect_'+name)]
        ordinary = 'initialized_ram' if a < 0x02000000 else 'flash_outside_known_data'
        for pc, expected in ((a-1, ordinary), (a, 'effect_'+name), (b-1, 'effect_'+name), (b, ordinary)):
            assert inventory.classification(pc) == expected; checks += 1
    links = {name: raw(spec[2]) for name, spec in TABLES.items() if spec[0] == 'resampling'}
    assert len(resampling_links(links)) == 3; checks += 1
    for name in links:
        changed = dict(links); changed[name] = changed[name][:-1]
        try: resampling_links(changed)
        except (ValueError, struct.error): checks += 1
        else: raise AssertionError('invalid indirect coefficient span accepted')
    assert len(PREVIOUS_REPORTS) == 39 and len(set(PREVIOUS_REPORTS)) == 39
    checks += 1
    print(json.dumps({'result': 'pass', 'self_test_checks': checks,
                      'exact_new_data_spans': len(NEW_TABLE_NAMES), 'exact_prior_data_spans': len(TABLES)-len(NEW_TABLE_NAMES),
                      'exact_new_data_bytes': sum(TABLES[name][2][1]-TABLES[name][2][0] for name in NEW_TABLE_NAMES),
                      'exact_prior_data_bytes': sum(spec[2][1]-spec[2][0] for name, spec in TABLES.items() if name not in NEW_TABLE_NAMES),
                      'exact_excluded_bytes': sum(b-a for _, _, (a, b), _, _, _ in TABLES.values())}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    names = ('parser-report', 'processing-report', 'ir-report', 'application-report',
        'ir-processing-report', 'audio-report', 'stage-report', 'resampling-report',
        'enable-report', 'support-report', 'effect-processing-report', 'parameters-report')
    for name in names: parser.add_argument('--'+name)
    parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(); required = tuple(getattr(args, name.replace('-', '_')) for name in names)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report: parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required):
        parser.error('choose --output or --check and provide all twelve required reports')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a new output directory under build/')
    report = EffectsInventory(*required, args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'effects-reverse-engineering-inventory', 'device_access': False,
                    'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
                     'instruction_coverage_limits': report['instruction_coverage_limits']}, indent=2))


if __name__ == '__main__': main()
