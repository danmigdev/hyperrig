"""Extend the effect inventory with exact resource branch-table evidence.

Preserve every report selected for inventory09, including the final parameter03
and processing02 runs. Resource01 adds nineteen complete bodies and exactly
three embedded data spans. Historical tools and reports are never rewritten.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from inventory_reverse import (ROOT, REFERENCE, REFERENCE_SHA, APP, NATIVE_REPORT,
    address, hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_effects import EffectsInventory, PREVIOUS_REPORTS, declared_constants

MODEL = 'tools/effect_parameter_resources_machine.py'
RESOURCE_REPORT = 'build/reverse-effect-parameter-resources-01/verification.json'
CURRENT_EFFECT_REPORTS = (
    'build/reverse-effect-resampling-02/verification.json',
    'build/reverse-effect-enable-03/verification.json',
    'build/reverse-effect-parameter-support-01/verification.json',
    'build/reverse-effect-processing-02/verification.json',
    'build/reverse-effect-parameters-03/verification.json',
)
PRESERVED_REPORTS = (*PREVIOUS_REPORTS, *CURRENT_EFFECT_REPORTS, NATIVE_REPORT)
CONSUMERS = {
    'reset': {
        'bounds': (0x01C068E0, 0x01C06926), 'instructions': 18,
        'sha256': '499c45cde1e02d136dd41ba88e784d175d6a1048d9ce22e51e6aa32bfbd6edc2',
    },
    'fingerprint': {
        'bounds': (0x0202EEFA, 0x0202EFE2), 'instructions': 78,
        'sha256': '322ab1e1133b9b7dc792370ed90c96f8ae6a4de4a1264197656793345426bf37',
    },
}
TABLES = {
    'reset_branches': {
        'bounds': (0x01C068EE, 0x01C06904),
        'sha256': '364714e6758d1e612d58b7417c4f2d6f083606b97788ef99aef496999f432930',
        'consumer': 'reset', 'entries': 21, 'padding': 1,
        'sites': ((0x01C068E0, 2, 'r1 = b[r0+0] (u)'),
                  (0x01C068E2, 4, 'r2 = r1 + -3'),
                  (0x01C068E6, 4, 'if (r2 > 20) goto 58'),
                  (0x01C068EC, 2, 'tbb [r2]')),
    },
    'fingerprint_high_branches': {
        'bounds': (0x0202EF12, 0x0202EF22),
        'sha256': '8c849a46f8332905a3cefae75d7a283637b818d31c0506571934e129b064906a',
        'consumer': 'fingerprint', 'entries': 15, 'padding': 1,
        'sites': ((0x0202EEFE, 2, 'r0 = b[r4+0] (u)'),
                  (0x0202EF00, 4, 'r3 = r0 + -25'),
                  (0x0202EF0C, 4, 'if (r3 > 14) goto 38'),
                  (0x0202EF10, 2, 'tbb [r3]')),
    },
    'fingerprint_low_branches': {
        'bounds': (0x0202EF3E, 0x0202EF48),
        'sha256': '9df17c4d5cb6efffbb8ce9e5ddffbdd1f42f6d0058eb696717eda747beb80da7',
        'consumer': 'fingerprint', 'entries': 10, 'padding': 0,
        # Include the earlier type load/range branch: r0 still holds the type
        # when the upper-range fallback reaches the second table's subtraction.
        'sites': ((0x0202EEFE, 2, 'r0 = b[r4+0] (u)'),
                  (0x0202EF00, 4, 'r3 = r0 + -25'),
                  (0x0202EF0C, 4, 'if (r3 > 14) goto 38'),
                  (0x0202EF36, 2, 'r0 += -4'),
                  (0x0202EF38, 4, 'if (r0 > 9) goto 94'),
                  (0x0202EF3C, 2, 'tbb [r0]')),
    },
}


def check_declarations(constants):
    """Bind the frozen literal region/table registry without executing a model."""
    expected = {name: spec['bounds'] for name, spec in TABLES.items()}
    if constants.get('TABLES') != expected:
        raise ValueError('resource table registry differs from the three reviewed spans')
    for name, bounds in expected.items():
        if constants.get('STATIC', {}).get(name) != bounds:
            raise ValueError('resource static declaration differs from its table range')
    for name, spec in CONSUMERS.items():
        if constants.get('REGIONS', {}).get(name) != spec['bounds']:
            raise ValueError('resource complete consumer declaration changed')


def with_resource_ranges(previous):
    """Append exactly three disjoint exclusions; reject partial/prior overlaps."""
    additions = [(*spec['bounds'], 'resource_'+name) for name, spec in TABLES.items()]
    spans = [*previous, *additions]
    for i, (start, end, _) in enumerate(spans):
        if any(start < other_end and other_start < end for other_start, other_end, _ in spans[i+1:]):
            raise ValueError('resource data overlaps an existing exclusion')
    return spans


def decode_consumer(name, raw, isa):
    """Decode every consumer instruction, independently skipping exact data."""
    spec = CONSUMERS[name]; start, end = spec['bounds']
    if len(raw) != end-start or sha(raw) != spec['sha256']:
        raise ValueError('resource complete consumer bytes differ from the pinned function')
    decoded, seconds, cursor = [], set(), 0
    exclusions = [value['bounds'] for value in TABLES.values() if value['consumer'] == name]
    while cursor < len(raw):
        data = next(((a, b) for a, b in exclusions if a <= start+cursor < b), None)
        if data:
            if start+cursor != data[0]: raise ValueError('resource instruction crosses a data boundary')
            cursor = data[1]-start; continue
        result = codec.decode(isa, raw, cursor)
        if result is None: raise ValueError('resource consumer contains an undecoded instruction')
        instruction, fields, size = result; pc = start+cursor
        if pc+size > end or any(pc < b and a < pc+size for a, b in exclusions):
            raise ValueError('resource instruction crosses a complete function/data boundary')
        text = codec.format(instruction, fields)
        decoded.append((pc, size, text.removesuffix('  #')))
        if text.endswith('  #'): seconds.add(pc+size)
        cursor += size
    if len(decoded) != spec['instructions'] or not seconds <= {pc for pc, _, _ in decoded}:
        raise ValueError('resource consumer instruction/packet layout changed')
    return decoded, seconds


def branch_targets(name, raw, decoded, parallel_seconds):
    """Bound every one-byte table entry to a complete consumer packet start."""
    spec = TABLES[name]; start, end = spec['bounds']; count, padding = spec['entries'], spec['padding']
    if len(raw) != count+padding or end-start != count+padding or any(raw[count:]):
        raise ValueError('resource branch entry count or zero alignment padding changed')
    consumer = CONSUMERS[spec['consumer']]['bounds']; instructions = {pc for pc, _, _ in decoded}
    exclusions = [value['bounds'] for value in TABLES.values() if value['consumer'] == spec['consumer']]
    if any(a <= pc < b for pc in instructions for a, b in exclusions):
        raise ValueError('resource table or padding was decoded as code')
    targets = [start+2*value for value in raw[:count]]
    if any(not consumer[0] <= target < consumer[1] or target not in instructions or target in parallel_seconds
           for target in targets):
        raise ValueError('resource branch target is not a decoded consumer packet start')
    return targets


def table_evidence(name, report, raw, consumer_raw, decoded, parallel_seconds, isa):
    spec = TABLES[name]; bounds, consumer_name = spec['bounds'], spec['consumer']; consumer = CONSUMERS[consumer_name]
    if report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA:
        raise ValueError('resource data requires passing evidence for the pinned original')
    try:
        record = report['static_data'][name]
        recorded_bounds = address(record['start']), address(record['end_exclusive'])
        function = report['functions'][consumer_name]
        function_bounds = address(function['start']), address(function['end_exclusive'])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('missing exact resource table or complete consumer evidence') from error
    if (recorded_bounds != bounds or len(raw) != bounds[1]-bounds[0]
        or sha(raw) != spec['sha256'] or record.get('sha256') != spec['sha256']):
        raise ValueError('resource table bytes, range or report hash differ')
    if (function_bounds != consumer['bounds'] or function.get('bytes_sha256') != consumer['sha256']
        or function.get('instructions') != consumer['instructions']):
        raise ValueError('resource report lacks the exact complete consumer')
    canonical, seconds = decode_consumer(consumer_name, consumer_raw, isa)
    if decoded != canonical or parallel_seconds != seconds or not all(site in decoded for site in spec['sites']):
        raise ValueError('resource consumer decoding, index sites or packet boundaries differ')
    offset = bounds[0]-consumer['bounds'][0]
    if consumer_raw[offset:offset+len(raw)] != raw:
        raise ValueError('resource table is not the claimed embedded consumer span')
    targets = branch_targets(name, raw, decoded, parallel_seconds)
    evidence = {'start': hex_address(bounds[0]), 'end_exclusive': hex_address(bounds[1]),
        'bytes': len(raw), 'sha256': spec['sha256'], 'kind': 'resource_'+name,
        'entry_width': 1, 'entries': spec['entries'], 'padding_bytes': spec['padding'],
        'dispatch': hex_address(bounds[0]-2), 'targets': list(map(hex_address, targets)),
        'targets_are_packet_starts': True, 'complete_consumer': {
            'name': consumer_name, 'start': hex_address(consumer['bounds'][0]),
            'end_exclusive': hex_address(consumer['bounds'][1]), 'sha256': consumer['sha256'],
            'decoded_instructions': len(decoded), 'parallel_second_addresses': list(map(hex_address, sorted(seconds))),
            'instruction_sites': [{'address': hex_address(pc), 'size': size, 'instruction': text}
                                  for pc, size, text in spec['sites']]}}
    if spec['padding']:
        evidence['alignment_start'] = hex_address(bounds[0]+spec['entries'])
        evidence['alignment_hex'] = raw[spec['entries']:].hex()
    return evidence


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 45 or len(set(PRESERVED_REPORTS)) != 45:
        raise ValueError('the reviewed inventory09 selection no longer contains 45 unique reports')
    required = {*PRESERVED_REPORTS, RESOURCE_REPORT}
    if len(selected) != len(set(selected)) or not required <= set(selected):
        raise ValueError('resource inventory omitted an inventory09 report or frozen resources01')


class ResourcesInventory(EffectsInventory):
    def __init__(self, parser_report, processing_report, ir_report, application_report,
                 ir_processing_report, audio_report, stage_report, resampling_report,
                 enable_report, support_report, effect_processing_report, parameters_report,
                 resources_report, additional_reports=()):
        selected_effects = tuple(local(name).relative_to(ROOT).as_posix() for name in
            (resampling_report, enable_report, support_report, effect_processing_report, parameters_report))
        if selected_effects != CURRENT_EFFECT_REPORTS:
            raise ValueError('resource adapter requires the five final inventory09 effect reports')
        self.resource_report = local(resources_report).relative_to(ROOT).as_posix()
        if self.resource_report != RESOURCE_REPORT: raise ValueError('resource adapter requires frozen resources01')
        self.resource_tables = {}
        super().__init__(parser_report, processing_report, ir_report, application_report,
            ir_processing_report, audio_report, stage_report, resampling_report, enable_report,
            support_report, effect_processing_report, parameters_report,
            [self.resource_report, *additional_reports])

    def add_known_data(self):
        super().add_known_data()
        report = json.loads(self.read(self.resource_report)); source = self.read(MODEL)
        if report.get('source_sha256', {}).get(MODEL) != sha(source):
            raise ValueError('resource model declarations do not match the passing report')
        check_declarations(declared_constants(source.decode('utf-8')))
        self.data_ranges = with_resource_ranges(self.data_ranges)
        for name, spec in TABLES.items():
            bounds = CONSUMERS[spec['consumer']]['bounds']; body = self.raw(*bounds)
            decoded, seconds = decode_consumer(spec['consumer'], body, self.instructions)
            # Independently compare with the inherited inventory decoder, whose
            # source/target classification now excludes these exact three spans.
            if self.decode(*bounds) != decoded: raise ValueError('inventory and resource consumer decoders disagree')
            evidence = table_evidence(name, report, self.raw(*spec['bounds']), body, decoded, seconds, self.instructions)
            evidence.update(report=self.resource_report, declaration=MODEL)
            self.resource_tables[name] = evidence

    def run(self):
        report = super().run()
        require_preserved_reports(report['selected_reports'])
        self.read('tools/inventory_reverse_resources.py')
        report.update(schema=8, resources_inventory_adapter='tools/inventory_reverse_resources.py',
            resource_data_tables=self.resource_tables,
            resource_data_exclusion_summary={'spans': 3, 'bytes': 48, 'branch_entries': 46,
                'padding_bytes': 2, 'complete_consumers': 2, 'report': self.resource_report})
        report['audits'].update(inventory09_all_forty_five_reports_retained=True,
            resource_tables_exact_bytes_declarations_and_complete_consumers_verified=True,
            resource_index_sites_and_full_consumers_independently_decoded=True,
            resource_branch_targets_are_decoded_packet_starts=True,
            resource_alignment_is_not_a_branch_entry=True)
        report['scope_policy'].extend([
            'exactly three resource data spans totaling 48 bytes are excluded; the 46 one-byte branch entries and two zero alignment bytes remain separate quantities',
            'the reset table has 21 entries and one padding byte; the upper fingerprint table has 15 entries and one padding byte; the lower fingerprint table has ten entries',
            'resource table proofs retain all previous report selections, fragment rules, overlap rejection and execution limits; they do not infer a total firmware function count'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Exercise valid original proofs and adversarial evidence without snapshots."""
    original, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(original) != REFERENCE_SHA or unpack_app(original)[2]['app.bin'] != app:
        raise ValueError('resource self-check requires the pinned original application')
    inventory = object.__new__(ResourcesInventory)
    inventory.app = app; inventory.instructions = table.load()
    inventory.flash_start, inventory.flash_end = 0x02000120, 0x02000120+len(app)
    inventory.ram_source, inventory.ram_size = 0x02056780, 0x2030C
    inventory.ram_start, inventory.ram_end = 0x01C00000, 0x01C2030C
    inventory.data_ranges = with_resource_ranges([])
    constants = declared_constants(local(MODEL).read_text(encoding='utf-8'))
    check_declarations(constants); checks = 1
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except ValueError: checks += 1
        else: raise AssertionError('invalid resource evidence accepted')
    for key in TABLES:
        bad = copy.deepcopy(constants); bad['TABLES'][key] = (0, 1); rejected(check_declarations, bad)
        bad = copy.deepcopy(constants); bad['STATIC'][key] = (0, 1); rejected(check_declarations, bad)
    bad = copy.deepcopy(constants); bad['TABLES']['unknown'] = (1, 2); rejected(check_declarations, bad)
    for key in CONSUMERS:
        bad = copy.deepcopy(constants); bad['REGIONS'][key] = (0, 2); rejected(check_declarations, bad)
    for name, spec in TABLES.items():
        bounds, consumer_name = spec['bounds'], spec['consumer']; consumer = CONSUMERS[consumer_name]
        raw, body = inventory.raw(*bounds), inventory.raw(*consumer['bounds'])
        decoded, seconds = decode_consumer(consumer_name, body, inventory.instructions)
        assert decoded == inventory.decode(*consumer['bounds']); checks += 1
        valid = {'result': 'pass', 'original_image_sha256': REFERENCE_SHA,
            'static_data': {name: {'start': bounds[0], 'end_exclusive': bounds[1], 'sha256': spec['sha256']}},
            'functions': {consumer_name: {'start': consumer['bounds'][0], 'end_exclusive': consumer['bounds'][1],
                'bytes_sha256': consumer['sha256'], 'instructions': consumer['instructions']}}}
        evidence = table_evidence(name, valid, raw, body, decoded, seconds, inventory.instructions)
        assert evidence['bytes'] == bounds[1]-bounds[0] and len(evidence['targets']) == spec['entries']; checks += 1
        mutations = (((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
            ((), 'static_data', {}), ((), 'functions', {}),
            (('static_data', name), 'start', bounds[0]+1), (('static_data', name), 'end_exclusive', bounds[1]-1),
            (('static_data', name), 'sha256', '0'*64),
            (('functions', consumer_name), 'start', consumer['bounds'][0]+2),
            (('functions', consumer_name), 'end_exclusive', consumer['bounds'][1]-2),
            (('functions', consumer_name), 'bytes_sha256', '0'*64),
            (('functions', consumer_name), 'instructions', consumer['instructions']+1))
        for path, key, value in mutations:
            bad = copy.deepcopy(valid); node = bad
            for part in path: node = node[part]
            node[key] = value
            rejected(table_evidence, name, bad, raw, body, decoded, seconds, inventory.instructions)
        for changed in (raw[:-1], raw+b'\0', bytes([raw[0]^1])+raw[1:]):
            rejected(table_evidence, name, valid, changed, body, decoded, seconds, inventory.instructions)
        rejected(table_evidence, name, valid, raw, body[:-2], decoded, seconds, inventory.instructions)
        rejected(table_evidence, name, valid, raw, bytes([body[0]^1])+body[1:], decoded, seconds, inventory.instructions)
        for site in spec['sites']:
            altered = [item for item in decoded if item != site]
            rejected(table_evidence, name, valid, raw, body, altered, seconds, inventory.instructions)
        altered = list(decoded); pc, size, _ = altered[-1]; altered[-1] = pc, size, 'not original'
        rejected(table_evidence, name, valid, raw, body, altered, seconds, inventory.instructions)
        target = address(evidence['targets'][0])
        rejected(table_evidence, name, valid, raw, body, decoded, seconds | {target}, inventory.instructions)
        rejected(branch_targets, name, raw, decoded, seconds | {target})
        rejected(branch_targets, name, raw, [item for item in decoded if item[0] != target], seconds)
        rejected(branch_targets, name, raw, decoded+[(bounds[0], 2, 'not code')], seconds)
        for changed in (raw[:-1], raw+b'\0', b'\0'+raw[1:], bytes([255])+raw[1:]):
            rejected(branch_targets, name, changed, decoded, seconds)
        middle = next(pc+2 for pc, size, _ in decoded if size > 2 and bounds[1] <= pc < bounds[0]+508)
        changed = bytes([(middle-bounds[0])//2])+raw[1:]
        rejected(branch_targets, name, changed, decoded, seconds)
        if spec['padding']:
            rejected(branch_targets, name, raw[:-1]+b'\1', decoded, seconds)
        previous = [(bounds[0]+1, bounds[1], 'conflicting_data')]
        rejected(with_resource_ranges, previous)
        assert previous == [(bounds[0]+1, bounds[1], 'conflicting_data')]; checks += 1
        ordinary = 'initialized_ram' if bounds[0] < 0x02000000 else 'flash_outside_known_data'
        for pc, expected in ((bounds[0]-1, ordinary), (bounds[0], 'resource_'+name),
            (bounds[1]-1, 'resource_'+name), (bounds[1], ordinary)):
            assert inventory.classification(pc) == expected; checks += 1
    selected = [*PRESERVED_REPORTS, RESOURCE_REPORT]
    require_preserved_reports(selected); checks += 1
    for omitted in selected: rejected(require_preserved_reports, [path for path in selected if path != omitted])
    rejected(require_preserved_reports, selected+[RESOURCE_REPORT])
    assert sum(spec['bounds'][1]-spec['bounds'][0] for spec in TABLES.values()) == 48
    assert sum(spec['entries'] for spec in TABLES.values()) == 46
    assert sum(spec['padding'] for spec in TABLES.values()) == 2
    checks += 3
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 45,
        'exact_resource_data_spans': 3, 'exact_resource_data_bytes': 48,
        'branch_entries': 46, 'padding_bytes': 2, 'complete_consumers': 2,
        'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    names = ('parser-report', 'processing-report', 'ir-report', 'application-report',
        'ir-processing-report', 'audio-report', 'stage-report', 'resampling-report',
        'enable-report', 'support-report', 'effect-processing-report', 'parameters-report', 'resources-report')
    for name in names: parser.add_argument('--'+name)
    parser.add_argument('--add-report', action='append', default=[])
    parser.add_argument('--output', type=Path); parser.add_argument('--check', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(); required = tuple(getattr(args, name.replace('-', '_')) for name in names)
    if args.self_test:
        if args.output or args.check or any(required) or args.add_report:
            parser.error('--self-test is a separate read-only operation')
        self_test(); return
    if bool(args.output) == bool(args.check) or not all(required):
        parser.error('choose --output or --check and provide all thirteen required reports')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a new output directory under build/')
    report = ResourcesInventory(*required, args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'resource-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'resource_data_exclusion_summary': report['resource_data_exclusion_summary'],
        'instruction_coverage_limits': report['instruction_coverage_limits']}, indent=2))


if __name__ == '__main__': main()
