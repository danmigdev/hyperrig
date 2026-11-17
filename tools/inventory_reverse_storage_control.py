"""Audit storage-control bodies, five branch tables and auxiliary reset evidence.

Preserve every inventory15 report and code/data policy. Mutable runtime records
and the reset instruction witness do not become immutable data or new functions.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
from pathlib import Path
from inventory_reverse import (Inventory, ROOT, REFERENCE, REFERENCE_SHA, APP,
    address, hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_effects import declared_constants
from inventory_reverse_integrations import REQUIRED_OPTIONS
from inventory_reverse_parameter_construction import (ParameterConstructionInventory,
    REPORT as PARAMETER_REPORT, PRESERVED_REPORTS as INVENTORY14_REPORTS)

ADAPTER = 'tools/inventory_reverse_storage_control.py'
MODEL = 'tools/storage_control_machine.py'
REPORT = 'build/reverse-storage-control-01/verification.json'
REPORT_SHA = '333bf4a506f550afea10d660cb1700a4c5f0b7b5794da17681df44d970d293d8'
MANIFEST_SHA = '7795e4410720ca5a7cfa481e3b9e0e7ed2decf83a1d22a45a6964d19501d9321'
PRESERVED_REPORTS = (*INVENTORY14_REPORTS, PARAMETER_REPORT)
CONSUMERS = {
    'control': ((0x020029be, 0x02002b80), 144, 'fc8b68a5dd3bf0681071a15297034710f11e01b904cd091a5cd3fec10e864f17'),
    'ioctl': ((0x02002b80, 0x02002bcc), 25, 'cb8bd76b0cff30fbffdd90525c5ac952eb661c7a1d9104217fab708884b8510a'),
    'transfer_read': ((0x01c00290, 0x01c003d4), 111, '2c7aafe98bd76cf5408fa5d8270b41a21d91a6075aa08d7581481e2fdb57d1b3'),
    'device_erase': ((0x01c00640, 0x01c006d2), 49, '3ed795561bde83677f9412a36a1c61fa33a0113c387734626af03a84c6f6967f'),
}
TABLES = {
    'control200': {'bounds': (0x02002a2a, 0x02002a32), 'entries': 7, 'padding': 1, 'consumer': 'control',
        'sha256': '9836f1b872721858b1192da003e69649c3bbab55c3d27b6278eb8d944a7fac43',
        'sites': ((0x020029e0, 4, 'r0 = r7 + -200'), (0x020029ec, 4, 'if (r0 <= 6) goto 56'), (0x02002a28, 2, 'tbb [r0]'))},
    'control100': {'bounds': (0x02002a42, 0x02002a46), 'entries': 4, 'padding': 0, 'consumer': 'control',
        'sha256': 'eb9d350e3bbbcf98dd77f5b8e02bd5c3b4ade52eb0d62f588a2f8033bf25fa3b',
        'sites': ((0x020029f0, 4, 'r0 = r7 + -100'), (0x020029f4, 4, 'if (r0 <= 3) goto 72'), (0x02002a40, 2, 'tbb [r0]'))},
    'ioctl200': {'bounds': (0x02002b90, 0x02002b96), 'entries': 5, 'padding': 1, 'consumer': 'ioctl',
        'sha256': 'aa61f01dbc3bcf924f704acc5d907ff0a4775c9adf338f1ad979a90315f07dce',
        'sites': ((0x02002b84, 4, 'r0 = r4 + -200'), (0x02002b8a, 4, 'if (r0 > 4) goto 14'), (0x02002b8e, 2, 'tbb [r0]'))},
    'read_modes': {'bounds': (0x01c002bc, 0x01c002c4), 'entries': 8, 'padding': 0, 'consumer': 'transfer_read',
        'sha256': 'd42e5576b24bc188b82926ddcc9f94ca173cce8ae306c8bff3714b1001c3d406',
        'sites': ((0x01c002ae, 4, 'r0 = sextra(r5, p:8, l:4)'), (0x01c002b2, 4, 'ifs (r0 < 0) goto 34'),
                  (0x01c002b6, 4, 'r0 = uextra(r5, p:8, l:4)'), (0x01c002ba, 2, 'tbb [r0]'))},
    'erase200': {'bounds': (0x01c0065a, 0x01c00660), 'entries': 5, 'padding': 1, 'consumer': 'device_erase',
        'sha256': '9dd98328868b63a856fcc63cf57942f4d7cf52619e525dfda5e4db2876e97145',
        'sites': ((0x01c00642, 4, 'r2 = r0 + -200'), (0x01c00648, 4, 'if (r2 > 4) goto 130'), (0x01c00658, 2, 'tbb [r2]'))},
}
DIRECT_SITES = {0x0200271e: (0x020005ac, 4), 0x0200272c: (0x020005ac, 4), 0x02002736: (0x0203fb92, 1),
    0x0200278a: (0x01c04862, 0), 0x0200282e: (0x01c04862, 0), 0x020027fe: (0x0203ea6e, 0),
    0x020029d0: (0x02040614, 1), 0x02002e8e: (0x02040614, 1), 0x01c0000c: (0x02040614, 1),
    0x02002b6a: (0x0204074c, 1), 0x02002ee8: (0x0204074c, 1), 0x01c00444: (0x0204074c, 1),
    0x02002b74: (0x0203e742, 0), 0x02002b7a: (0x0200096e, 0), 0x01c0002a: (0x01c01108, 2), 0x01c00430: (0x01c011da, 0)}
RESET = (0x0200019c, 0x020001b2, '05221f085384369277a7fbdc7eefa5a1e46770c9c0f3ccb24b4d2e735267e930')
RESET_SITES = ((0x0200019c, 6, 'r3 = 29491980'), (0x020001a2, 2, 'r1 = 0'),
    (0x020001a4, 6, 'r2 = 97604'), (0x020001aa, 2, 'r2 = r2 >> 2'),
    (0x020001ac, 2, 'rep 2 r2 {'), (0x020001ae, 2, '[r3++=4] = r1'), (0x020001b0, 2, 'if (r2 != 0) goto -6'))


def bounds(item): return address(item['start']), address(item['end_exclusive'])


def passing(report):
    if report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA:
        raise ValueError('storage control requires passing pinned-image evidence')


def check_declarations(constants, report):
    passing(report)
    expected = {name: (*spec['bounds'], spec['entries'], spec['sites'][-1][0], spec['sha256']) for name, spec in TABLES.items()}
    if constants.get('TABLES') != expected or constants.get('DIRECT_SITES') != DIRECT_SITES or constants.get('BSS_WITNESS') != RESET:
        raise ValueError('storage table, platform-site or reset registry changed')
    proof = {name: {pc: text for pc, _, text in spec['sites']} for name, spec in TABLES.items()}
    if constants.get('TABLE_PROOFS') != proof:
        raise ValueError('storage table proof declarations changed')
    declared = {name: bounds(item) for name, item in report['functions'].items()}
    if len(declared) != 45 or constants.get('REGIONS') != declared or sum(b-a for a, b in declared.values()) != 3444:
        raise ValueError('storage must retain all 45 complete region declarations')
    for name, (span, count, digest) in CONSUMERS.items():
        item = report['functions'][name]
        if declared[name] != span or item['instructions'] != count or item['bytes_sha256'] != digest:
            raise ValueError('storage complete table consumer changed')


def with_storage_ranges(previous):
    spans = [*previous, *((*spec['bounds'], 'storage_'+name) for name, spec in TABLES.items())]
    for i, (a, b, _) in enumerate(spans):
        if any(a < d and c < b for c, d, _ in spans[i+1:]):
            raise ValueError('storage data overlaps prior classification')
    return spans


def decode_consumer(name, raw, isa):
    span, count, digest = CONSUMERS[name]; start, end = span
    if len(raw) != end-start or sha(raw) != digest:
        raise ValueError('storage complete consumer bytes changed')
    exclusions = [spec['bounds'] for spec in TABLES.values() if spec['consumer'] == name]
    decoded, seconds, cursor = [], set(), 0
    while cursor < len(raw):
        skip = next(((a, b) for a, b in exclusions if a <= start+cursor < b), None)
        if skip:
            if start+cursor != skip[0]: raise ValueError('storage instruction enters table interior')
            cursor = skip[1]-start; continue
        result = codec.decode(isa, raw, cursor)
        if result is None: raise ValueError('undecoded storage table consumer')
        instruction, fields, size = result; pc = start+cursor
        if pc+size > end or any(pc < b and a < pc+size for a, b in exclusions):
            raise ValueError('storage instruction crosses function or table boundary')
        text = codec.format(instruction, fields)
        decoded.append((pc, size, text.removesuffix('  #')))
        if text.endswith('  #'): seconds.add(pc+size)
        cursor += size
    if len(decoded) != count or not seconds <= {pc for pc, _, _ in decoded}:
        raise ValueError('storage consumer instruction or packet count changed')
    return decoded, seconds


def table_evidence(report, raw, isa):
    passing(report)
    if set(report['branch_tables']) != set(TABLES): raise ValueError('storage requires exactly five branch tables')
    decoded = {name: decode_consumer(name, raw(*spec[0]), isa) for name, spec in CONSUMERS.items()}
    evidence = {}
    for name, spec in TABLES.items():
        record = report['branch_tables'][name]; a, b = spec['bounds']; count = spec['entries']; data = raw(a, b)
        if (bounds(record) != (a, b) or sha(data) != spec['sha256'] or record['sha256'] != spec['sha256']
            or type(record['active_bytes']) is not int or record['active_bytes'] != count
            or type(record['padding_bytes']) is not int or record['padding_bytes'] != spec['padding']
            or len(data) != count+spec['padding'] or any(data[count:])
            or address(record['consumer']) != a-2 or spec['sites'][-1][0] != a-2):
            raise ValueError('storage exact table bytes, entry count or padding changed')
        instructions, seconds = decoded[spec['consumer']]
        if not all(site in instructions for site in spec['sites']): raise ValueError('storage index/consumer proof changed')
        declared_proof = {address(pc): text for pc, text in record['index_proof'].items()}
        if declared_proof != {pc: text for pc, _, text in spec['sites']}:
            raise ValueError('storage report index proof changed')
        targets = [a+2*v for v in data[:count]]; pcs = {pc for pc, _, _ in instructions}
        if (any(pc not in pcs or pc in seconds for pc in targets)
            or [address(pc) for pc in record['targets']] != targets):
            raise ValueError('storage branch target is not a complete consumer packet start')
        item = report['functions'][spec['consumer']]; span, decoded_count, digest = CONSUMERS[spec['consumer']]
        if bounds(item) != span or item['bytes_sha256'] != digest or item['instructions'] != decoded_count:
            raise ValueError('storage table lacks its exact complete consumer')
        evidence[name] = {'start': hex_address(a), 'end_exclusive': hex_address(b), 'sha256': spec['sha256'],
            'bytes': b-a, 'entries': count, 'padding_bytes': spec['padding'], 'consumer': spec['consumer'],
            'complete_consumer': {'start': hex_address(span[0]), 'end_exclusive': hex_address(span[1]),
                'sha256': digest, 'decoded_instructions': decoded_count},
            'targets': list(map(hex_address, targets)), 'targets_are_consumer_packet_starts': True,
            'index_sites': [{'address': hex_address(pc), 'size': size, 'instruction': text} for pc, size, text in spec['sites']]}
    return evidence, decoded


def runtime_evidence(report, raw, decode, regions):
    passing(report)
    pcs, decoded, per_function = set(), {}, {}
    for name, item in report['functions'].items():
        a, b = bounds(item); parent = regions.get((a, b)); body = decode(a, b)
        if (parent is None or parent['kind'] != 'function_region' or parent['sha256'] != item['bytes_sha256']
            or sha(raw(a, b)) != item['bytes_sha256'] or item['bytes'] != b-a
            or type(item['instructions']) is not int or item['instructions'] != len(body)):
            raise ValueError('storage whole-body bytes or instruction extent changed')
        body_pcs = {pc for pc, _, _ in body}
        if pcs & body_pcs: raise ValueError('storage body declarations overlap')
        pcs.update(body_pcs); decoded.update({pc: (size, text) for pc, size, text in body}); per_function[name] = body_pcs
    coverage = report['instruction_coverage']
    for key in ('unvisited_new', 'unvisited_all'):
        if [address(pc) for pc in coverage[key]] != [0x02002b7e]:
            raise ValueError('storage fatal-loop observation must remain the sole unvisited instruction')
    expected = {'new_decoded': len(pcs), 'new_visited': len(pcs)-1, 'all_decoded': len(pcs), 'all_visited': len(pcs)-1}
    if len(pcs) != 1165 or any(type(coverage[k]) is not int or coverage[k] != v for k, v in expected.items()):
        raise ValueError('storage whole-body coverage differs from original decoding')
    if decoded.get(0x02002b7e) != (2, 'goto -2'):
        raise ValueError('storage fixed observation is not the original fatal self-loop')
    recorded = {address(pc): (address(item['target']), item['arity']) for pc, item in report['service_sites'].items()}
    if recorded != DIRECT_SITES: raise ValueError('storage direct service registry changed')
    entries = {bounds(item)[0] for item in report['functions'].values()}; observed = {}
    for pc, (size, text) in decoded.items():
        if not text.startswith('call '): continue
        match = re.fullmatch(r'call (-?\d+)', text)
        if match is None: raise ValueError('storage contains an unreviewed indirect call')
        target = pc+size+int(match[1])
        if target not in entries:
            if pc not in DIRECT_SITES or DIRECT_SITES[pc][0] != target:
                raise ValueError('storage direct call is outside its complete closure and explicit services')
            observed[pc] = DIRECT_SITES[pc]
    if observed != DIRECT_SITES: raise ValueError('storage report omits an original direct service')
    witness = report['auxiliary_reset_witness']; a, b, digest = RESET
    if (bounds(witness) != (a, b) or witness['sha256'] != digest or sha(raw(a, b)) != digest
        or tuple(decode(a, b)) != RESET_SITES or address(witness['cleared_start']) != 0x01c2030c
        or address(witness['cleared_end_exclusive']) != 0x01c38050 or witness['runtime_BSS_not_immutable_data'] is not True):
        raise ValueError('storage auxiliary reset witness or BSS extent changed')
    timeouts = report['instruction_timeouts']
    if timeouts != {'transfer_wait': 50000000, 'busy_wait': 5000000, 'terminal_timeout_paths_executed': False}:
        raise ValueError('storage timeout constants or unexecuted terminal-path limit changed')
    return {'whole_functions': len(per_function), **expected, 'direct_platform_sites': len(observed),
        'direct_platform_targets': len({target for target, _ in observed.values()}), 'new_indirect_sites': 0,
        'sole_gap': hex_address(0x02002b7e), 'fatal_loop_observed_before_execution': True,
        'terminal_timeout_paths_executed': False, 'auxiliary_reset_witness': witness,
        'per_function': {name: {'decoded': len(p), 'visited': len(p-{0x02002b7e}),
            'unvisited': len(p & {0x02002b7e})} for name, p in per_function.items()}}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 57 or len(set(PRESERVED_REPORTS)) != 57:
        raise ValueError('inventory15 must contain 57 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('storage-control inventory omitted or duplicated prior evidence')


class StorageControlInventory(ParameterConstructionInventory):
    def __init__(self, *required, storage_control_report, additional_reports=(), **options):
        if local(storage_control_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen storage-control01')
        additions = [local(p).relative_to(ROOT).as_posix() for p in additional_reports]
        if REPORT in additions: raise ValueError('storage control report is already explicitly selected')
        self.storage_tables, self.storage_runtime = {}, None
        super().__init__(*required, additional_reports=[*additions, REPORT], **options)

    def add_known_data(self):
        super().add_known_data(); raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen storage-control report changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report['source_sha256'].get(MODEL) != sha(source): raise ValueError('storage registry source changed')
        check_declarations(declared_constants(source.decode('utf-8')), report)
        self.storage_tables, independent = table_evidence(report, self.raw, self.instructions)
        self.data_ranges = with_storage_ranges(self.data_ranges)
        for name, (decoded, _) in independent.items():
            if self.decode(*CONSUMERS[name][0]) != decoded:
                raise ValueError('inventory and independent storage consumer decoders disagree')

    def reports(self):
        omitted = super().reports(); self.audit_manifest(REPORT, MANIFEST_SHA)
        report = json.loads(self.read(REPORT))
        self.storage_runtime = runtime_evidence(report, self.raw, self.decode, self.regions)
        module = next(item for item in self.modules if item['report'] == REPORT)
        module.update(reported_region_coverage=self.storage_runtime['per_function'],
            reported_coverage_notes={'fatal_loop_is_observed_before_execution': True,
                'full_transfer_and_busy_timeout_outcomes_remain_unexecuted': True,
                'fixed_event_prefixes_do_not_prove_physical_atomicity_or_durability': True},
            storage_runtime_evidence=self.storage_runtime)
        return omitted

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=14, storage_control_inventory_adapter=ADAPTER,
            storage_control_tables=self.storage_tables, storage_control_runtime_evidence=self.storage_runtime,
            storage_control_data_exclusion_summary={'spans': 5, 'bytes': 32, 'embedded_bytes': 32,
                'branch_entries': 29, 'padding_bytes': 3, 'complete_consumers': 4, 'decoded_proof_sites': 16})
        report['audits'].update(inventory15_all_fifty_seven_reports_retained=True,
            storage_tables_and_complete_consumers_independently_decoded=True,
            storage_branch_targets_are_consumer_packet_starts=True,
            storage_whole_body_coverage_and_direct_platform_sites_bound=True,
            storage_reset_witness_remains_auxiliary_with_mutable_BSS=True,
            storage_timeout_outcomes_not_promoted_to_executed_coverage=True)
        report['scope_policy'].extend([
            'storage control adds 45 complete bodies and only five embedded data spans: 29 branch-entry bytes and three zero padding bytes',
            'all four table consumers, 16 index/dispatch sites, branch targets and original direct platform calls are independently decoded',
            'the 22-byte reset witness remains auxiliary; mutable device records, IRQ tokens and BSS state add no reconstructed function or immutable-data exclusion',
            'the fatal self-loop is observed before execution; full polling timeouts remain unexecuted despite shared instruction coverage',
            'synthetic MMIO, cache/barrier and platform observations do not establish physical transfer completion, durability, scheduling or inter-core behavior'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Audit real original proofs and reject altered evidence without snapshots."""
    packed, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(packed) != REFERENCE_SHA or unpack_app(packed)[2]['app.bin'] != app:
        raise ValueError('self-check original image changed')
    inv = object.__new__(Inventory); inv.app = app; inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    inv.data_ranges = with_storage_ranges([])
    raw_report = local(REPORT).read_bytes()
    if sha(raw_report) != REPORT_SHA: raise ValueError('self-check frozen storage report changed')
    report = json.loads(raw_report); constants = declared_constants(local(MODEL).read_text())
    regions = {bounds(item): {'kind': 'function_region', 'sha256': item['bytes_sha256']} for item in report['functions'].values()}
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid storage-control evidence accepted')
    check_declarations(constants, report); checks += 1
    proof, decoded = table_evidence(report, inv.raw, inv.instructions); assert len(proof) == 5; checks += 1
    assert runtime_evidence(report, inv.raw, inv.decode, regions)['new_visited'] == 1164; checks += 1
    for name, spec in TABLES.items():
        a, b = spec['bounds']
        for field, value in (('start', a+2), ('end_exclusive', b+2), ('sha256', '0'*64),
                ('active_bytes', spec['entries']+1), ('padding_bytes', spec['padding']+1), ('consumer', a)):
            changed = copy.deepcopy(report); changed['branch_tables'][name][field] = value
            rejected(table_evidence, changed, inv.raw, inv.instructions)
        for index in range(spec['entries']):
            changed = copy.deepcopy(report); changed['branch_tables'][name]['targets'][index] = a
            rejected(table_evidence, changed, inv.raw, inv.instructions)
        for pc, _, _ in spec['sites']:
            changed = copy.deepcopy(report); changed['branch_tables'][name]['index_proof'][hex(pc)] = 'rts'
            rejected(table_evidence, changed, inv.raw, inv.instructions)
        for span in ((a, b, 'duplicate'), (a-1, a+1, 'left'), (b-1, b+1, 'right')):
            rejected(with_storage_ranges, [span])
        changed = copy.deepcopy(constants); changed['TABLES'][name] = (a, b+2, 0, 0, '0'*64)
        rejected(check_declarations, changed, report)
    for name, (span, _, _) in CONSUMERS.items():
        damaged = bytearray(inv.raw(*span)); damaged[0] ^= 1
        rejected(decode_consumer, name, bytes(damaged), inv.instructions)
        changed = copy.deepcopy(report); changed['functions'][name]['instructions'] += 1
        rejected(table_evidence, changed, inv.raw, inv.instructions)
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
        (('instruction_coverage',), 'new_visited', 1165), (('instruction_coverage',), 'unvisited_new', []),
        (('instruction_coverage',), 'unvisited_all', [0x02002b7e, 0x02002b7e]),
        (('auxiliary_reset_witness',), 'cleared_end_exclusive', 0x01c38054),
        (('auxiliary_reset_witness',), 'runtime_BSS_not_immutable_data', False),
        (('instruction_timeouts',), 'transfer_wait', 5000000),
        (('instruction_timeouts',), 'terminal_timeout_paths_executed', True)]:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(runtime_evidence, changed, inv.raw, inv.decode, regions)
    for pc in DIRECT_SITES:
        changed = copy.deepcopy(report); changed['service_sites'][hex(pc)]['arity'] += 1
        rejected(runtime_evidence, changed, inv.raw, inv.decode, regions)
    changed = copy.deepcopy(constants); changed['REGIONS'].pop('power2'); rejected(check_declarations, changed, report)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 57,
        'new_data_spans': 5, 'new_data_bytes': 32, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report')
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
    report = StorageControlInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'storage-control-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'storage_control_data_exclusion_summary': report['storage_control_data_exclusion_summary'],
        'storage_control_runtime_evidence': {k: v for k, v in report['storage_control_runtime_evidence'].items()
            if k != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
