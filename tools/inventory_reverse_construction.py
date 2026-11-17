"""Extend the resource inventory with exact effect-construction table evidence.

Preserve all 46 inventory10 reports and frozen construction02. Authenticate the
eight new data spans and the already excluded tempo table without inferring
data across alignment gaps. Additional completed reports remain opt-in.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from inventory_reverse import (ROOT, REFERENCE, REFERENCE_SHA, APP, address,
    hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_expanded import coverage_summary
from inventory_reverse_resources import (ResourcesInventory, PRESERVED_REPORTS
    as INVENTORY09_REPORTS, RESOURCE_REPORT, declared_constants)

ADAPTER = 'tools/inventory_reverse_construction.py'
MODEL = 'tools/effect_construction_machine.py'
CONSTRUCTION_REPORT = 'build/reverse-effect-construction-02/verification.json'
CONSTRUCTION_SHA = '5a4a64c7598fc2ac4809dcd8fd1cba7cdb577270a9333f6a59c38390c38a5479'
CONSTRUCTION_MANIFEST_SHA = '9cae1c3f1db3c5eea5d509c6265d7062fbfc07255eb47134b753ab426ece8fc5'
PRESERVED_REPORTS = (*INVENTORY09_REPORTS, RESOURCE_REPORT)
CONSUMERS = {
    'construct': {'bounds': (0x0202CF62, 0x0202DDFC), 'instructions': 971,
        'sha256': '6095a50f77b2e4e8301b568bd4b1240708fd8c27aba54a69a8ff64df6f76e717'},
    'tempo_parameter': {'bounds': (0x0202A7F6, 0x0202A814), 'instructions': 10,
        'sha256': '54dd7b57ecfd68a67d9b56820876c6e7d2bf682b150b58c728502376ed024b07'},
    'tempo_samples': {'bounds': (0x0202A76C, 0x0202A7A8), 'instructions': 20,
        'sha256': '537274085c0769055f2dccc300f706e06878ee4f19a22f08cf1e288aeda501aa'},
    'tempo_value': {'bounds': (0x0202A814, 0x0202A872), 'instructions': 25,
        'sha256': '21fc98a0a02175ef24eb7e37f47ed0521d4b19f826f3254eeade4a0c58d63e4f'},
    'tempo_selector': {'bounds': (0x0202A75E, 0x0202A76C), 'instructions': 5,
        'sha256': 'cb5ea826f53be418bc752dd710d18cb60380d84a1a8bcc19fbb2ff7f1335991b'},
}
# Sites bind address loads, index initialization/updates, loop bounds and actual
# arithmetic use. Complete consumers are independently decoded as well.
TABLES = {
    'construct_branches': {
        'bounds': (0x0202CFAC, 0x0202CFFA),
        'sha256': '73f79d8dc1afbd4df994398bd75ed346524cab2a5f541af435f98aa89bbaf8f8',
        'branch': (2, 39, 0), 'sites': {'construct': (
            (0x0202CF82, 4, 'r6 = b[r15+0] (u)'),
            (0x0202CF86, 4, 'r0 = r6 + -1'),
            (0x0202CF8A, 6, 'if (r0 > 38) goto 684'),
            (0x0202CF94, 2, 'r1 = r0 << 1'),
            (0x0202CFAA, 2, 'tbh [r1]'))}},
    'tempo_branches': {
        'bounds': (0x0202A802, 0x0202A808),
        'sha256': 'a6d1b05f6815cd3af9431b999bc042cbcf33ba409ce4a6a4ac80aab85c4358af',
        'branch': (1, 5, 1), 'sites': {'tempo_parameter': (
            (0x0202A7F6, 4, 'r1 = r0 + -11'),
            (0x0202A7FA, 4, 'if (r1 > 4) goto 14'),
            (0x0202A800, 2, 'tbb [r1]'))}},
    'frequencies36': {
        'bounds': (0x0203A550, 0x0203A55C),
        'sha256': 'ac240e09c282d7260aa15cb88a408af8d58dfc3d22c03dc0d540a1a3cca3fa78',
        'element_width': 2, 'elements': 6, 'sites': {'construct': (
            (0x0202D958, 2, 'r5 = 0'),
            (0x0202D95E, 6, 'r10 = 33793360'),
            (0x0202D964, 2, 'r7_r6 = 0'),
            (0x0202D96A, 4, 'r1 = h[r10+r7<<1] (u)'),
            (0x0202D96E, 4, 'r2 = utof(r1)'),
            (0x0202D97C, 4, 'call -21068'),
            (0x0202D99E, 2, 'r5 = r5 + 16'),
            (0x0202D9A0, 2, 'r7 = r7 + 1'),
            (0x0202D9A2, 4, 'if (r5 != 96) goto -64'))}},
    'frequencies37_seven': {
        'bounds': (0x0203B608, 0x0203B616),
        'sha256': '415885c1c1bef3d19396971db4c6c7e6e8ca2511f77b534d38e1d8c7a4e6244b',
        'element_width': 2, 'elements': 7, 'sites': {'construct': (
            (0x0202D142, 2, 'r7_r6 = 0'),
            (0x0202D15C, 6, 'r10 = 33797640'),
            (0x0202D162, 2, 'goto 8'),
            (0x0202D168, 2, 'r7 = r7 + 1'),
            (0x0202D170, 4, 'r0 = h[r10+r7<<1] (u)'),
            (0x0202D174, 4, 'r2 = utof(r0)'),
            (0x0202D182, 4, 'call -19026'),
            (0x0202D19E, 4, 'if (r7 != 6) goto -62'))}},
    'widths37_seven': {
        'bounds': (0x0203B618, 0x0203B634),
        'sha256': 'ee1d7b1de56e95ba0b078520b849c6eb8f1ccbc892fbddaa8cd31ea7ff0e78e4',
        'element_width': 4, 'elements': 7, 'sites': {'construct': (
            (0x0202D142, 2, 'r7_r6 = 0'),
            (0x0202D156, 6, 'r5 = 33797656'),
            (0x0202D162, 2, 'goto 8'),
            (0x0202D168, 2, 'r7 = r7 + 1'),
            (0x0202D16C, 4, 'r12 = [r5++=4]'),
            (0x0202D180, 2, '[sp] = r12'),
            (0x0202D182, 4, 'call -19026'),
            (0x0202D19E, 4, 'if (r7 != 6) goto -62'))}},
    'limits37_five': {
        'bounds': (0x0203B634, 0x0203B639),
        'sha256': 'cbeaabea67ab45c75640447f3134812c89e3506a30eb2b1446f20c531c56a996',
        'element_width': 1, 'elements': 5, 'sites': {'construct': (
            (0x0202D1A6, 2, 'r7_r6 = 0'),
            (0x0202D1AE, 6, 'r9 = 33797684'),
            (0x0202D1BA, 2, 'r4 = 0'),
            (0x0202D1D4, 4, 'r3 = b[r4+r9] (s)'),
            (0x0202D1D8, 4, 'r2 = 0x0 - r3'),
            (0x0202D1DC, 4, 'ifs (r0 >= r2) {'),
            (0x0202D1E0, 4, 'r2 = smin(r0, r3)'),
            (0x0202D1E8, 4, 'r3 = itof(r2)'),
            (0x0202D1F2, 4, 'call -19138'),
            (0x0202D218, 2, 'r7 = r7 + 20'),
            (0x0202D21A, 2, 'r4 = r4 + 1'),
            (0x0202D21C, 4, 'if (r7 != 100) goto -100'))}},
    'frequencies37_five': {
        'bounds': (0x0203B63A, 0x0203B644),
        'sha256': '7a372a1f46cd5d87947d46f955e6786b2eb0fd4cd6c44fd862f05c5733af14ab',
        'element_width': 2, 'elements': 5, 'sites': {'construct': (
            (0x0202D1A6, 2, 'r7_r6 = 0'),
            (0x0202D1B4, 6, 'r10 = 33797690'),
            (0x0202D1BA, 2, 'r4 = 0'),
            (0x0202D1E4, 4, 'r0 = h[r10+r4<<1] (u)'),
            (0x0202D1EC, 4, 'r2 = utof(r0)'),
            (0x0202D1F2, 4, 'call -19138'),
            (0x0202D218, 2, 'r7 = r7 + 20'),
            (0x0202D21A, 2, 'r4 = r4 + 1'),
            (0x0202D21C, 4, 'if (r7 != 100) goto -100'))}},
    'widths37_five': {
        'bounds': (0x0203B644, 0x0203B658),
        'sha256': '0d35c5757039c8a7f29e4e2e68ca3e248e9ff75fb575664569d1fad60f413cb6',
        'element_width': 4, 'elements': 5, 'sites': {'construct': (
            (0x0202D1A6, 2, 'r7_r6 = 0'),
            (0x0202D1A8, 6, 'r11 = 33797700'),
            (0x0202D1BA, 2, 'r4 = 0'),
            (0x0202D1C0, 4, 'r1 = [r11++=4]'),
            (0x0202D1C4, 2, '[sp] = r1'),
            (0x0202D1F2, 4, 'call -19138'),
            (0x0202D218, 2, 'r7 = r7 + 20'),
            (0x0202D21A, 2, 'r4 = r4 + 1'),
            (0x0202D21C, 4, 'if (r7 != 100) goto -100'))}},
    'tempo': {
        'bounds': (0x0203B658, 0x0203B672),
        'sha256': '51c8bacfb9be4ddf3d0f1324e14593277b2bda2ee71a584dbe06ce3653369f51',
        'existing_kind': 'effect_support_tempo', 'element_width': 1, 'elements': 26,
        'sites': {
            'tempo_selector': ((0x0202A75E, 4, 'r1 = r0 + -1'),
                (0x0202A762, 2, 'r0 = 1'),
                (0x0202A764, 4, 'if (r1 >= 9) {'),
                (0x0202A768, 2, 'r0 = 0')),
            'tempo_samples': ((0x0202A76E, 2, 'r2 = r0'),
                (0x0202A770, 2, 'call -20'),
                (0x0202A772, 2, 'if (r0 == 0) goto 48'),
                (0x0202A774, 6, 'r0 = 33797720'),
                (0x0202A77A, 4, 'r0 = b[r2+r0] (u)'),
                (0x0202A784, 6, 'r3 = 33797733'),
                (0x0202A78A, 4, 'r2 = b[r2+r3] (u)'),
                (0x0202A790, 2, 'r0 *= r3'),
                (0x0202A794, 2, 'r1 *= r2'),
                (0x0202A79E, 4, 'r0 = r1 / r0 (u)')),
            'tempo_parameter': ((0x0202A7F6, 4, 'r1 = r0 + -11'),
                (0x0202A7FA, 4, 'if (r1 > 4) goto 14'),
                (0x0202A800, 2, 'tbb [r1]')),
            'tempo_value': ((0x0202A81A, 2, 'call -38'),
                (0x0202A81C, 4, 'ifs (r0 < 0) goto 12'),
                (0x0202A820, 4, 'r0 = h[r2+r0<<1] (s)'),
                (0x0202A824, 4, 'r1 = r0 + -1'),
                (0x0202A828, 4, 'if (r1 < 12) goto 10'),
                (0x0202A836, 6, 'r1 = 33797733'),
                (0x0202A83C, 4, 'r1 = b[r0+r1] (u)'),
                (0x0202A840, 6, 'r2 = 33797720'),
                (0x0202A846, 4, 'r0 = b[r0+r2] (u)'),
                (0x0202A85C, 4, 'r1 = r1 * r3 (f)'),
                (0x0202A868, 4, 'r0 = r2 * r0 (f)'),
                (0x0202A86C, 4, 'r0 = r0 / r1 (f)'))}},
}
NEW_TABLE_NAMES = tuple(name for name, spec in TABLES.items() if 'existing_kind' not in spec)


def check_declarations(constants):
    expected = {name: spec['bounds'] for name, spec in TABLES.items()}
    if constants.get('STATIC') != expected:
        raise ValueError('construction static registry differs from the nine reviewed spans')
    embedded = {name: spec['bounds'] for name, spec in TABLES.items() if 'branch' in spec}
    if constants.get('TABLES') != embedded:
        raise ValueError('construction embedded table registry changed')
    for name, spec in CONSUMERS.items():
        registry = 'REUSED' if name == 'tempo_selector' else 'REGIONS'
        if constants.get(registry, {}).get(name) != spec['bounds']:
            raise ValueError('construction complete consumer declaration changed')


def with_construction_ranges(previous):
    """Keep the old tempo exclusion once, append only the eight new spans."""
    for spec in TABLES.values():
        if 'existing_kind' in spec and previous.count((*spec['bounds'], spec['existing_kind'])) != 1:
            raise ValueError('construction requires the exact prior tempo exclusion once')
    spans = [*previous, *((*TABLES[name]['bounds'], 'construction_'+name) for name in NEW_TABLE_NAMES)]
    for i, (start, end, _) in enumerate(spans):
        if start >= end or any(start < b and a < end for a, b, _ in spans[i+1:]):
            raise ValueError('construction data overlaps another exclusion')
    return spans


def decode_consumer(name, raw, isa):
    """Independently decode a whole consumer, excluding exact embedded data."""
    spec = CONSUMERS[name]; start, end = spec['bounds']
    if len(raw) != end-start or sha(raw) != spec['sha256']:
        raise ValueError('construction complete consumer bytes differ')
    exclusions = [item['bounds'] for item in TABLES.values() if 'branch' in item
                  and start <= item['bounds'][0] < item['bounds'][1] <= end]
    decoded, seconds, cursor = [], set(), 0
    while cursor < len(raw):
        data = next(((a, b) for a, b in exclusions if a <= start+cursor < b), None)
        if data:
            if start+cursor != data[0]: raise ValueError('construction decoding entered the middle of data')
            cursor = data[1]-start; continue
        found = codec.decode(isa, raw, cursor)
        if found is None: raise ValueError('construction consumer contains an undecoded instruction')
        instruction, fields, size = found; pc = start+cursor
        if pc+size > end or any(pc < b and a < pc+size for a, b in exclusions):
            raise ValueError('construction instruction crosses a function or data boundary')
        rendered = codec.format(instruction, fields)
        decoded.append((pc, size, rendered.removesuffix('  #')))
        if rendered.endswith('  #'): seconds.add(pc+size)
        cursor += size
    if len(decoded) != spec['instructions'] or not seconds <= {pc for pc, _, _ in decoded}:
        raise ValueError('construction consumer instruction or packet layout changed')
    return decoded, seconds


def branch_targets(name, raw, decoded, seconds):
    spec = TABLES[name]; start, end = spec['bounds']; width, count, padding = spec['branch']
    if len(raw) != width*count+padding or len(raw) != end-start or any(raw[width*count:]):
        raise ValueError('construction branch entry count or zero padding changed')
    consumer = CONSUMERS[next(iter(spec['sites']))]['bounds']
    addresses = {pc for pc, _, _ in decoded}
    if any(start <= pc < end for pc in addresses):
        raise ValueError('construction table or padding was decoded as code')
    targets = [start+2*int.from_bytes(raw[i*width:(i+1)*width], 'little') for i in range(count)]
    if any(not consumer[0] <= target < consumer[1] or target not in addresses or target in seconds
           for target in targets):
        raise ValueError('construction branch target is not a decoded consumer packet start')
    return targets


def normalized_construction_report(report):
    """Adapt the frozen original-hash field in memory, never the source bytes."""
    if (report.get('result') != 'pass' or report.get('original_sha256') != REFERENCE_SHA
        or report.get('original_image_sha256', REFERENCE_SHA) != REFERENCE_SHA):
        raise ValueError('construction report is not passing evidence for the pinned original')
    return dict(report, original_image_sha256=REFERENCE_SHA)


def table_evidence(name, report, raw, bodies, decoded, seconds, isa):
    normalized_construction_report(report)
    spec = TABLES[name]; start, end = spec['bounds']
    try:
        record = report['static_data'][name]
        recorded_bounds = address(record['start']), address(record['end_exclusive'])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('missing exact construction table evidence') from error
    if (recorded_bounds != spec['bounds'] or len(raw) != end-start
        or sha(raw) != spec['sha256'] or record.get('sha256') != spec['sha256']):
        raise ValueError('construction table bytes, range or report hash differ')
    consumers = {}
    for function, sites in spec['sites'].items():
        wanted = CONSUMERS[function]
        try:
            record = report['functions'][function]
            bounds = address(record['start']), address(record['end_exclusive'])
            body, instructions, parallel = bodies[function], decoded[function], seconds[function]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('missing complete construction table consumer') from error
        if (bounds != wanted['bounds'] or record.get('bytes_sha256') != wanted['sha256']
            or record.get('instructions') != wanted['instructions']):
            raise ValueError('construction report lacks the exact complete consumer')
        canonical, packet_seconds = decode_consumer(function, body, isa)
        if instructions != canonical or parallel != packet_seconds or not all(site in canonical for site in sites):
            raise ValueError('construction consumer decoding, index/use sites or packets differ')
        if 'branch' in spec and body[start-bounds[0]:end-bounds[0]] != raw:
            raise ValueError('construction table is not the claimed embedded consumer span')
        consumers[function] = {'start': hex_address(bounds[0]), 'end_exclusive': hex_address(bounds[1]),
            'sha256': wanted['sha256'], 'decoded_instructions': len(instructions),
            'parallel_second_addresses': list(map(hex_address, sorted(parallel))),
            'instruction_sites': [{'address': hex_address(pc), 'size': size, 'instruction': text}
                                  for pc, size, text in sites]}
    evidence = {'start': hex_address(start), 'end_exclusive': hex_address(end),
        'bytes': len(raw), 'sha256': spec['sha256'],
        'kind': spec.get('existing_kind', 'construction_'+name),
        'new_exclusion': name in NEW_TABLE_NAMES, 'complete_consumers': consumers}
    if 'branch' in spec:
        function = next(iter(spec['sites'])); width, count, padding = spec['branch']
        targets = branch_targets(name, raw, decoded[function], seconds[function])
        evidence.update(entry_width=width, entries=count, padding_bytes=padding,
            dispatch=hex_address(start-2), targets=list(map(hex_address, targets)),
            targets_are_packet_starts=True)
        if padding:
            evidence.update(alignment_start=hex_address(start+width*count), alignment_hex=raw[width*count:].hex())
    else:
        if spec['element_width']*spec['elements'] != len(raw):
            raise ValueError('construction array element extent changed')
        evidence.update(element_width=spec['element_width'], elements=spec['elements'])
        if name == 'tempo':
            evidence.update(numerator_start=hex_address(start), denominator_start=hex_address(start+13),
                elements_per_half=13, samples_reached_indices=[1, 9], value_reached_indices=[1, 12],
                note='The prior complete 26-byte exclusion is retained. These new consumers do not read either index-zero byte.')
    return evidence


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 46 or len(set(PRESERVED_REPORTS)) != 46:
        raise ValueError('the reviewed inventory10 selection must contain 46 unique reports')
    required = {*PRESERVED_REPORTS, CONSTRUCTION_REPORT}
    if len(selected) != len(set(selected)) or not required <= set(selected):
        raise ValueError('construction inventory omitted an inventory10 report or frozen construction02')


class ConstructionInventory(ResourcesInventory):
    def __init__(self, parser_report, processing_report, ir_report, application_report,
                 ir_processing_report, audio_report, stage_report, resampling_report,
                 enable_report, support_report, effect_processing_report, parameters_report,
                 resources_report, construction_report, additional_reports=()):
        self.construction_report = local(construction_report).relative_to(ROOT).as_posix()
        if self.construction_report != CONSTRUCTION_REPORT:
            raise ValueError('construction adapter requires frozen construction02')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if self.construction_report in additions:
            raise ValueError('construction report is already selected explicitly')
        self.construction_tables = {}
        # The new report uses original_sha256. The narrow reports() adapter
        # below audits its unmodified bytes separately; all earlier reports use
        # the unchanged inherited loader and its overlap/provenance policies.
        super().__init__(parser_report, processing_report, ir_report, application_report,
            ir_processing_report, audio_report, stage_report, resampling_report,
            enable_report, support_report, effect_processing_report, parameters_report,
            resources_report, additions)

    def add_known_data(self):
        super().add_known_data()
        raw_report = self.read(self.construction_report)
        if sha(raw_report) != CONSTRUCTION_SHA: raise ValueError('frozen construction report digest changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report.get('source_sha256', {}).get(MODEL) != sha(source):
            raise ValueError('construction model declarations do not match the passing report')
        check_declarations(declared_constants(source.decode('utf-8')))
        self.data_ranges = with_construction_ranges(self.data_ranges)
        bodies, decoded, seconds = {}, {}, {}
        for name, spec in CONSUMERS.items():
            bodies[name] = self.raw(*spec['bounds'])
            decoded[name], seconds[name] = decode_consumer(name, bodies[name], self.instructions)
            if self.decode(*spec['bounds']) != decoded[name]:
                raise ValueError('inventory and construction consumer decoders disagree')
        for name, spec in TABLES.items():
            evidence = table_evidence(name, report, self.raw(*spec['bounds']), bodies, decoded, seconds, self.instructions)
            evidence.update(report=self.construction_report, declaration=MODEL)
            self.construction_tables[name] = evidence

    def reports(self):
        omitted = super().reports()
        path = local(self.construction_report)
        raw_report = self.read(self.construction_report)
        if sha(raw_report) != CONSTRUCTION_SHA: raise ValueError('frozen construction report digest changed')
        report = normalized_construction_report(json.loads(raw_report))
        self.audit_sources(report['source_sha256'])
        manifest_path = (path.parent/'build-manifest.json').relative_to(ROOT).as_posix()
        raw_manifest = self.read(manifest_path)
        if sha(raw_manifest) != CONSTRUCTION_MANIFEST_SHA: raise ValueError('frozen construction manifest digest changed')
        manifest = json.loads(raw_manifest)
        for name, digest in manifest['files'].items():
            artifact = (path.parent/name).relative_to(ROOT).as_posix()
            if sha(self.read(artifact)) != digest: raise ValueError('construction artifact differs from its frozen manifest')
            self.audited_artifacts.add(artifact)
        coverage, instructions, new_instructions, region_coverage = report['instruction_coverage'], set(), set(), {}
        declared_visited = 0
        for name, function in report['functions'].items():
            start, end = address(function['start']), address(function['end_exclusive'])
            decoded = self.decode(start, end)
            count, visited = function['instructions'], function['visited']
            if not isinstance(count, int) or not isinstance(visited, int) or count != len(decoded) or not 0 <= visited <= count:
                raise ValueError('construction function coverage differs from original decoding')
            self.add_region(path.parent.name, name, start, end, function['bytes_sha256'])
            instructions.update(pc for pc, _, _ in decoded)
            if function['new']: new_instructions.update(pc for pc, _, _ in decoded)
            declared_visited += visited
            region_coverage[name] = {'decoded': count, 'visited': visited, 'unvisited': count-visited}
        summary = coverage_summary(report)
        if summary['decoded'] != len(new_instructions): raise ValueError('construction new coverage differs from its declared bodies')
        loaded = set()
        for window in report['loaded_instruction_windows']:
            start, end = address(window['start']), address(window['end_exclusive'])
            if sha(self.raw(start, end)) != window['sha256']: raise ValueError('construction loaded instruction bytes changed')
            addresses = {pc for pc, _, _ in self.decode(start, end)}
            if loaded & addresses: raise ValueError('construction loaded instruction windows overlap')
            loaded.update(addresses)
        unvisited = [address(pc) for pc in coverage['unvisited_inherited']]
        if (len(loaded) != coverage['all_decoded'] or not instructions <= loaded
            or len(set(unvisited)) != len(unvisited) or not set(unvisited) <= loaded-new_instructions
            or len(unvisited) != coverage['all_decoded']-coverage['all_visited']
            or declared_visited != len(instructions-set(unvisited))):
            raise ValueError('construction declared and loaded coverage lists disagree')
        # Do not promote loaded windows or ABI-only disassemblies to functions.
        self.modules.append({'module': path.parent.name, 'report': self.construction_report,
            'report_sha256': self.sources[self.construction_report], 'declared_regions': len(report['functions']),
            'source_hashes_checked': len(report['source_sha256']),
            'scope_limits': [report['joined_boundary'],
                'Six larger type-specific builders remain explicit services; instruction comparison is not a hardware or audio test.'],
            'instruction_coverage': summary, 'reported_region_coverage': region_coverage,
            'reported_coverage_notes': {'declared_unvisited_addresses': list(map(hex_address, sorted(instructions & set(unvisited)))),
                'loaded_windows_are_not_additional_reconstructed_regions': True},
            'declared_region_coverage': {'decoded': len(instructions), 'visited': declared_visited,
                'unvisited': len(instructions)-declared_visited},
            'original_hash_field_adapter': 'original_sha256 -> original_image_sha256 in memory only'})
        return [name for name in omitted if name != self.construction_report]

    def run(self):
        report = super().run()
        require_preserved_reports(report['selected_reports'])
        self.read(ADAPTER)
        report.update(schema=9, construction_inventory_adapter=ADAPTER,
            construction_data_tables=self.construction_tables,
            construction_data_exclusion_summary={'new_spans': 8, 'new_bytes': 173,
                'new_embedded_spans': 2, 'new_embedded_bytes': 84,
                'branch_entries': 44, 'branch_entry_bytes': 83, 'padding_bytes': 1,
                'new_external_spans': 6, 'new_external_bytes': 89,
                'reused_spans': 1, 'reused_bytes': 26, 'complete_consumers': 5,
                'report': self.construction_report})
        report['audits'].update(inventory10_all_forty_six_reports_retained=True,
            construction_tables_exact_bytes_declarations_and_complete_consumers_verified=True,
            construction_address_index_and_use_sites_independently_decoded=True,
            construction_branch_targets_are_decoded_packet_starts=True,
            construction_alignment_is_not_a_branch_entry=True,
            construction_original_hash_schema_adapted_without_changing_evidence=True,
            construction_loaded_and_declared_instruction_coverage_bound=True)
        report['scope_policy'].extend([
            'eight new construction data spans total 173 bytes: 83 branch-entry bytes, one zero alignment byte and 89 external array bytes; the previously excluded 26-byte tempo table is authenticated again without duplication',
            'the two-byte gap at 0x0203b616 and one-byte gap at 0x0203b639 remain unclassified; adjacent reviewed tables do not imply larger contiguous data ranges',
            'construction02 retains its original_sha256 field and exact report/manifest bytes; this adapter normalizes only an in-memory copy for report validation',
            'construction declared functions are counted once; loaded numerical/caller windows and ABI-only evidence are not additional reconstructed regions, and every inherited coverage gap remains explicit',
            'construction table evidence preserves all prior report selections, fragment/overlap rules and execution limits; no total function count or completion percentage is inferred'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Validate original proofs and reject altered evidence without snapshots."""
    original, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(original) != REFERENCE_SHA or unpack_app(original)[2]['app.bin'] != app:
        raise ValueError('construction self-check requires the pinned original application')
    inventory = object.__new__(ConstructionInventory)
    inventory.app = app; inventory.instructions = table.load()
    inventory.flash_start, inventory.flash_end = 0x02000120, 0x02000120+len(app)
    inventory.ram_source, inventory.ram_size = 0x02056780, 0x2030C
    inventory.ram_start, inventory.ram_end = 0x01C00000, 0x01C2030C
    previous = [(*TABLES['tempo']['bounds'], TABLES['tempo']['existing_kind'])]
    inventory.data_ranges = with_construction_ranges(previous)
    constants = declared_constants(local(MODEL).read_text(encoding='utf-8'))
    check_declarations(constants); checks = 1
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except ValueError: checks += 1
        else: raise AssertionError('invalid construction evidence accepted')
    for key in TABLES:
        bad = copy.deepcopy(constants); bad['STATIC'][key] = (0, 1); rejected(check_declarations, bad)
    for key in ('construct_branches', 'tempo_branches'):
        bad = copy.deepcopy(constants); bad['TABLES'][key] = (0, 1); rejected(check_declarations, bad)
    bad = copy.deepcopy(constants); bad['STATIC']['unknown'] = (1, 2); rejected(check_declarations, bad)
    bad = copy.deepcopy(constants); bad['TABLES']['unknown'] = (1, 2); rejected(check_declarations, bad)
    for key in CONSUMERS:
        bad = copy.deepcopy(constants); bad['REUSED' if key == 'tempo_selector' else 'REGIONS'][key] = (0, 2)
        rejected(check_declarations, bad)
    bodies, decoded, seconds = {}, {}, {}
    for name, spec in CONSUMERS.items():
        bodies[name] = inventory.raw(*spec['bounds'])
        decoded[name], seconds[name] = decode_consumer(name, bodies[name], inventory.instructions)
        assert decoded[name] == inventory.decode(*spec['bounds']); checks += 1
    for name, spec in TABLES.items():
        bounds = spec['bounds']; raw = inventory.raw(*bounds)
        valid = {'result': 'pass', 'original_sha256': REFERENCE_SHA,
            'static_data': {name: {'start': bounds[0], 'end_exclusive': bounds[1], 'sha256': spec['sha256']}},
            'functions': {key: {'start': CONSUMERS[key]['bounds'][0], 'end_exclusive': CONSUMERS[key]['bounds'][1],
                'bytes_sha256': CONSUMERS[key]['sha256'], 'instructions': CONSUMERS[key]['instructions']}
                for key in spec['sites']}}
        evidence = table_evidence(name, valid, raw, bodies, decoded, seconds, inventory.instructions)
        assert evidence['bytes'] == bounds[1]-bounds[0] and evidence['new_exclusion'] == (name in NEW_TABLE_NAMES)
        checks += 1
        mutations = [((), 'result', 'fail'), ((), 'original_sha256', '0'*64),
            ((), 'original_image_sha256', '0'*64), ((), 'static_data', {}), ((), 'functions', {}),
            (('static_data', name), 'start', bounds[0]+1), (('static_data', name), 'end_exclusive', bounds[1]-1),
            (('static_data', name), 'sha256', '0'*64)]
        for consumer in spec['sites']:
            a, b = CONSUMERS[consumer]['bounds']
            mutations.extend([(('functions', consumer), 'start', a+2),
                (('functions', consumer), 'end_exclusive', b-2),
                (('functions', consumer), 'bytes_sha256', '0'*64),
                (('functions', consumer), 'instructions', CONSUMERS[consumer]['instructions']+1)])
        for path, key, value in mutations:
            bad = copy.deepcopy(valid); node = bad
            for part in path: node = node[part]
            node[key] = value
            rejected(table_evidence, name, bad, raw, bodies, decoded, seconds, inventory.instructions)
        for changed in (raw[:-1], raw+b'\0', bytes([raw[0]^1])+raw[1:]):
            rejected(table_evidence, name, valid, changed, bodies, decoded, seconds, inventory.instructions)
        for consumer, sites in spec['sites'].items():
            for changed in (bodies[consumer][:-2], bytes([bodies[consumer][0]^1])+bodies[consumer][1:]):
                altered = dict(bodies); altered[consumer] = changed
                rejected(table_evidence, name, valid, raw, altered, decoded, seconds, inventory.instructions)
            for site in sites:
                altered = dict(decoded); altered[consumer] = [item for item in decoded[consumer] if item != site]
                rejected(table_evidence, name, valid, raw, bodies, altered, seconds, inventory.instructions)
            altered = dict(seconds); altered[consumer] = seconds[consumer] | {CONSUMERS[consumer]['bounds'][0]}
            rejected(table_evidence, name, valid, raw, bodies, decoded, altered, inventory.instructions)
        if 'branch' in spec:
            consumer = next(iter(spec['sites'])); width, count, padding = spec['branch']
            targets = list(map(address, evidence['targets']))
            assert len(targets) == count; checks += 1
            for target in set(targets):
                rejected(branch_targets, name, raw, decoded[consumer], seconds[consumer] | {target})
                rejected(branch_targets, name, raw, [item for item in decoded[consumer] if item[0] != target], seconds[consumer])
            rejected(branch_targets, name, raw, decoded[consumer]+[(bounds[0], 2, 'not code')], seconds[consumer])
            for changed in (raw[:-1], raw+b'\0', b'\0'*width+raw[width:], b'\xff'*width+raw[width:]):
                rejected(branch_targets, name, changed, decoded[consumer], seconds[consumer])
            if padding: rejected(branch_targets, name, raw[:-1]+b'\1', decoded[consumer], seconds[consumer])
        if name in NEW_TABLE_NAMES:
            conflicting = previous+[(bounds[0]+1, bounds[1], 'conflicting_data')]
            before = list(conflicting); rejected(with_construction_ranges, conflicting)
            assert conflicting == before; checks += 1
        # Isolate a single exclusion to test half-open endpoints even when its
        # real neighbor is separately known data.
        kind = spec.get('existing_kind', 'construction_'+name)
        inventory.data_ranges = [(*bounds, kind)]
        for pc, expected in ((bounds[0]-1, 'flash_outside_known_data'), (bounds[0], kind),
            (bounds[1]-1, kind), (bounds[1], 'flash_outside_known_data')):
            assert inventory.classification(pc) == expected; checks += 1
    inventory.data_ranges = with_construction_ranges(previous)
    for pc in (0x0203B616, 0x0203B617, 0x0203B639):
        assert inventory.classification(pc) == 'flash_outside_known_data'; checks += 1
    assert previous == [(*TABLES['tempo']['bounds'], 'effect_support_tempo')]; checks += 1
    for invalid in ([], previous+previous, [(0x0203B658, 0x0203B672, 'wrong_kind')],
                    [(0x0203B658, 0x0203B674, 'effect_support_tempo')]):
        rejected(with_construction_ranges, invalid)
    valid = {'result': 'pass', 'original_sha256': REFERENCE_SHA}
    adapted = normalized_construction_report(valid)
    assert 'original_image_sha256' not in valid and adapted['original_image_sha256'] == REFERENCE_SHA; checks += 1
    rejected(normalized_construction_report, {'result': 'pass', 'original_image_sha256': REFERENCE_SHA})
    selected = [*PRESERVED_REPORTS, CONSTRUCTION_REPORT]
    require_preserved_reports(selected); checks += 1
    for omitted in selected: rejected(require_preserved_reports, [name for name in selected if name != omitted])
    rejected(require_preserved_reports, selected+[CONSTRUCTION_REPORT])
    assert len(NEW_TABLE_NAMES) == 8 and sum(TABLES[name]['bounds'][1]-TABLES[name]['bounds'][0] for name in NEW_TABLE_NAMES) == 173
    assert sum(spec['branch'][1] for spec in TABLES.values() if 'branch' in spec) == 44
    assert sum(spec['branch'][2] for spec in TABLES.values() if 'branch' in spec) == 1
    checks += 3
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 46,
        'new_data_spans': 8, 'new_data_bytes': 173, 'reused_data_bytes': 26,
        'branch_entries': 44, 'padding_bytes': 1, 'complete_consumers': len(CONSUMERS),
        'distinct_proof_sites': len({site for spec in TABLES.values() for sites in spec['sites'].values() for site in sites}),
        'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    names = ('parser-report', 'processing-report', 'ir-report', 'application-report',
        'ir-processing-report', 'audio-report', 'stage-report', 'resampling-report',
        'enable-report', 'support-report', 'effect-processing-report', 'parameters-report',
        'resources-report', 'construction-report')
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
        parser.error('choose --output or --check and provide all fourteen required reports')
    output = args.output.resolve() if args.output else None
    if output and (output.exists() or not output.is_relative_to(ROOT/'build')):
        parser.error('use a new output directory under build/')
    report = ConstructionInventory(*required, args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'construction-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'construction_data_exclusion_summary': report['construction_data_exclusion_summary'],
        'instruction_coverage_limits': report['instruction_coverage_limits']}, indent=2))


if __name__ == '__main__': main()
