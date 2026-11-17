"""Audit storage coordination while retaining every inventory16 report and policy.

CPU observations are bound to original instructions and pinned ISA records.
Initially zero IRQ words remain mutable runtime state, not data exclusions.
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
from inventory_reverse_storage_control import (StorageControlInventory,
    REPORT as CONTROL_REPORT, PRESERVED_REPORTS as INVENTORY15_REPORTS, bounds)

ADAPTER = 'tools/inventory_reverse_storage_coordination.py'
MODEL = 'tools/storage_coordination_machine.py'
REPORT = 'build/reverse-storage-coordination-01/verification.json'
REPORT_SHA = '8cedc6d10c791856aee0999efce8860ee8e4c79f84ec39a1be40624056eed8cb'
MANIFEST_SHA = 'a0a26deca273efc47f5e1a036e35391ab3e04f1cceab83279bc7a0e47d73b14f'
PRESERVED_REPORTS = (*INVENTORY15_REPORTS, CONTROL_REPORT)
REGIONS = {
    'ready_threshold': (0x020028f2, 0x02002920), 'wait_ready': (0x02002920, 0x0200294e),
    'poll_forward': (0x02002bec, 0x02002bf6), 'gate_core': (0x02002bf6, 0x02002d06),
    'gate': (0x02002d06, 0x02002d10), 'notify': (0x02002d10, 0x02002d70),
    'event': (0x02002d70, 0x02002d9e), 'irq_enter': (0x01c00e2e, 0x01c00e46),
    'irq_leave': (0x01c00e46, 0x01c00e62),
}
REUSED = {'rate': (0x02002bd8, 0x02002bec)}
DIRECT_SITES = {
    0x02002940: (0x0203feb8, 1), 0x02002bee: (0x0203ea6e, 0),
    0x02002c2e: (0x01c04862, 0), 0x02002c3c: (0x01c04862, 0),
    0x02002c68: (0x0203feb8, 1), 0x02002c7c: (0x0203feb8, 1),
    0x02002cd4: (0x01c04862, 0), 0x02002ce6: (0x01c04862, 0),
    0x02002d78: (0x01c04862, 0),
}
RATE_CALLS = {0x02002c36, 0x02002cdc, 0x02002d80}
CPU_SITES = {
    0x02002d30: ('testset.b', 'testset b[r1]', '58a8309bdef2a4381ea7815ca30ad2b636a000f6a9d1cd8f6b46b64ab15864be'),
    0x02002d32: ('bc.eq', 'ifeq goto -6', 'ce1e6bda6e2c86ca7013f074a95af16da363605e436e16ae6d02a5b11e3d1a2d'),
    0x01c00e2e: ('cli', 'cli', '6e7ec874c2902d32ad705a7b05ffc762bf45d9bf802d428ec530732caa437412'),
    0x01c00e30: ('mov.r_sr', 'r0 = cnum', '1d54e052c2a0213eab323479d7973744f67f21c15e157db4def336f08a7dfc8d'),
    0x01c00e5e: ('sti', 'sti', '864f15571e33e214e973e089ef6071d325403f5da9d0d39eac8f0c5dfed1cd6c'),
}
INITIAL = (0x01c1fc54, 0x01c1fc5c, 'af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc')


def registry_evidence(report, constants):
    if report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA:
        raise ValueError('coordination requires passing pinned-image evidence')
    for key, expected in (('functions', REGIONS), ('reused_functions', REUSED)):
        if {name: bounds(item) for name, item in report[key].items()} != expected:
            raise ValueError('coordination whole-body registry changed')
    if constants.get('REGIONS') != REGIONS or constants.get('REUSED') != REUSED:
        raise ValueError('coordination model registry changed')
    if report['new_data_exclusions'] != []:
        raise ValueError('coordination must not add a data exclusion')


def runtime_evidence(report, raw, decode, regions, isa):
    registry_evidence(report, {'REGIONS': REGIONS, 'REUSED': REUSED})
    decoded, new_pcs, per_function = {}, set(), {}
    for key in ('functions', 'reused_functions'):
        for name, item in report[key].items():
            a, b = bounds(item); parent = regions.get((a, b)); body = decode(a, b)
            if (parent is None or parent['kind'] != 'function_region'
                or parent['sha256'] != item['bytes_sha256'] or sha(raw(a, b)) != item['bytes_sha256']
                or type(item['bytes']) is not int or item['bytes'] != b-a
                or type(item['instructions']) is not int or item['instructions'] != len(body)):
                raise ValueError('coordination body bytes, parent or instruction extent changed')
            pcs = {pc for pc, _, _ in body}
            if pcs & decoded.keys(): raise ValueError('coordination body declarations overlap')
            decoded.update({pc: (size, text) for pc, size, text in body})
            if key == 'functions': new_pcs.update(pcs)
            per_function[name] = {'decoded': len(pcs), 'visited': len(pcs), 'unvisited': 0,
                'reused': key == 'reused_functions'}
    coverage = report['instruction_coverage']
    expected = {'new_decoded': 178, 'new_visited': 178, 'all_decoded': 184, 'all_visited': 184}
    if (len(new_pcs) != 178 or len(decoded) != 184
        or any(type(coverage[k]) is not int or coverage[k] != v for k, v in expected.items())
        or coverage['unvisited_new'] != [] or coverage['unvisited_all'] != [] or report['gap_instructions'] != {}):
        raise ValueError('coordination coverage differs from canonical complete bodies')
    visited = [address(pc) for pc in report['visited']]
    if len(visited) != len(set(visited)) or set(visited) != set(decoded):
        raise ValueError('coordination visited PCs must equal all canonical instruction starts')
    recorded = {}
    for pc, item in report['service_sites'].items():
        if type(item['arity']) is not int: raise ValueError('coordination service arity is not an integer')
        at = address(pc)
        if at in recorded: raise ValueError('duplicate coordination service site')
        recorded[at] = (address(item['target']), item['arity'])
    if recorded != DIRECT_SITES: raise ValueError('coordination service registry changed')
    entries = {a for a, _ in (*REGIONS.values(), *REUSED.values())}
    observed, rate_calls = {}, set()
    for pc, (size, text) in decoded.items():
        if not text.startswith('call '): continue
        match = re.fullmatch(r'call (-?\d+)', text)
        if match is None: raise ValueError('unreviewed coordination indirect call')
        target = pc+size+int(match[1])
        if target == REUSED['rate'][0]: rate_calls.add(pc)
        if target not in entries:
            if pc not in DIRECT_SITES or DIRECT_SITES[pc][0] != target:
                raise ValueError('coordination direct call leaves its reviewed closure')
            observed[pc] = DIRECT_SITES[pc]
    if observed != DIRECT_SITES or rate_calls != RATE_CALLS:
        raise ValueError('coordination original external/rate call sites changed')
    cpu = report['cpu_primary_evidence']; records = cpu['records']; digests = cpu['canonical_record_sha256']
    if set(records) != {hex(pc) for pc in CPU_SITES} or set(digests) != set(records):
        raise ValueError('coordination CPU evidence set changed')
    for pc, (identifier, text, digest) in CPU_SITES.items():
        size, decoded_text = decoded[pc]
        found = codec.decode(isa, raw(pc, pc+size), 0)
        if found is None: raise ValueError('undecoded original CPU observation')
        instruction, fields, decoded_size = found
        original = {'id': instruction.id, 'decoded': codec.format(instruction, fields),
            'summary': instruction.summary, 'notes': instruction.notes,
            'status': instruction.status, 'sources': instruction.sources}
        canonical = sha(json.dumps(original, sort_keys=True, separators=(',', ':')).encode())
        if (decoded_size != size or decoded_text != text or instruction.id != identifier
            or original['decoded'] != text or canonical != digest
            or records[hex(pc)] != original or digests[hex(pc)] != digest):
            raise ValueError('coordination CPU instruction or primary ISA record changed')
    witness = report['auxiliary_initial_state']; a, b, digest = INITIAL
    if (bounds(witness) != (a, b) or witness['sha256'] != digest
        or type(witness['bytes']) is not int or witness['bytes'] != 8
        or raw(a, b) != bytes(8) or sha(raw(a, b)) != digest):
        raise ValueError('coordination auxiliary initial-state witness changed')
    return {'new_whole_functions': 9, 'reused_whole_functions': 1, **expected,
        'direct_platform_sites': 9, 'direct_platform_targets': 3, 'new_indirect_sites': 0,
        'reused_rate_call_sites': [hex_address(pc) for pc in sorted(rate_calls)],
        'CPU_primary_records': 5, 'CPU_observations_are_synthetic': True,
        'auxiliary_mutable_initial_state': witness, 'new_data_exclusions': 0,
        'per_function': per_function}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 58 or len(set(PRESERVED_REPORTS)) != 58:
        raise ValueError('inventory16 must contain 58 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('coordination inventory omitted or duplicated prior evidence')


class StorageCoordinationInventory(StorageControlInventory):
    def __init__(self, *required, storage_coordination_report, additional_reports=(), **options):
        if local(storage_coordination_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen storage-coordination01')
        additions = [local(p).relative_to(ROOT).as_posix() for p in additional_reports]
        if REPORT in additions: raise ValueError('coordination report is already selected')
        self.coordination_runtime = None
        super().__init__(*required, additional_reports=[*additions, REPORT], **options)

    def reports(self):
        omitted = super().reports(); self.audit_manifest(REPORT, MANIFEST_SHA)
        raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen coordination report changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report['source_sha256'].get(MODEL) != sha(source): raise ValueError('coordination model source changed')
        registry_evidence(report, declared_constants(source.decode('utf-8')))
        self.coordination_runtime = runtime_evidence(report, self.raw, self.decode, self.regions, self.instructions)
        module = next(item for item in self.modules if item['report'] == REPORT)
        module.update(reported_region_coverage=self.coordination_runtime['per_function'],
            storage_coordination_runtime_evidence=self.coordination_runtime)
        return omitted

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=15, storage_coordination_inventory_adapter=ADAPTER,
            storage_coordination_runtime_evidence=self.coordination_runtime)
        report['audits'].update(inventory16_all_fifty_eight_reports_retained=True,
            coordination_new_and_reused_complete_bodies_and_coverage_bound=True,
            coordination_direct_platform_and_reused_rate_sites_independently_decoded=True,
            coordination_CPU_instructions_and_primary_ISA_records_bound=True,
            coordination_initial_IRQ_words_remain_auxiliary_mutable_state=True,
            coordination_adds_no_data_exclusions=True)
        report['scope_policy'].extend([
            'storage coordination adds nine complete bodies and reuses the existing rate helper at three original call sites',
            'all nine direct platform sites and five CPU instruction/ISA records are independently authenticated',
            'the eight initially zero IRQ bytes remain auxiliary mutable runtime state, not a data exclusion or BSS-reset execution',
            'synthetic CPU observations and finite event/service prefixes do not prove atomicity, interrupt delivery or inter-core scheduling'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject contradictory coordination records without generating an inventory."""
    packed, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(packed) != REFERENCE_SHA or unpack_app(packed)[2]['app.bin'] != app:
        raise ValueError('self-check original image changed')
    inv = object.__new__(Inventory); inv.app = app; inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    inv.data_ranges = []
    raw_report = local(REPORT).read_bytes()
    if sha(raw_report) != REPORT_SHA: raise ValueError('self-check frozen coordination report changed')
    report = json.loads(raw_report); constants = declared_constants(local(MODEL).read_text())
    regions = {bounds(item): {'kind': 'function_region', 'sha256': item['bytes_sha256']}
        for item in (*report['functions'].values(), *report['reused_functions'].values())}
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError): checks += 1; return
        raise AssertionError('invalid coordination evidence accepted')
    def audit(item): return runtime_evidence(item, inv.raw, inv.decode, regions, inv.instructions)
    registry_evidence(report, constants); checks += 1
    assert audit(report)['all_visited'] == 184; checks += 1
    for key in ('functions', 'reused_functions'):
        for name in report[key]:
            for field, value in [('start', 0), ('end_exclusive', 0), ('bytes', True),
                    ('bytes_sha256', '0'*64), ('instructions', 0)]:
                changed = copy.deepcopy(report); changed[key][name][field] = value; rejected(audit, changed)
    for path, key, value in [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64),
        ((), 'new_data_exclusions', [INITIAL[:2]]), ((), 'visited', report['visited'][:-1]),
        ((), 'visited', report['visited']+[report['visited'][0]]), ((), 'visited', ['0x020028f3', *report['visited'][1:]]),
        ((), 'gap_instructions', {'0x020028f2': 'missing'}),
        (('instruction_coverage',), 'new_visited', 177), (('instruction_coverage',), 'all_decoded', 185),
        (('instruction_coverage',), 'unvisited_new', [hex(REGIONS['gate'][0])]),
        (('auxiliary_initial_state',), 'end_exclusive', hex(INITIAL[1]+4)),
        (('auxiliary_initial_state',), 'sha256', '0'*64), (('auxiliary_initial_state',), 'bytes', True)]:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(audit, changed)
    for pc in DIRECT_SITES:
        for field, value in [('target', '0x02000000'), ('arity', True), ('arity', 12)]:
            changed = copy.deepcopy(report); changed['service_sites'][hex(pc)][field] = value; rejected(audit, changed)
    for pc in CPU_SITES:
        for field in ('id', 'decoded', 'notes', 'summary', 'status', 'sources'):
            changed = copy.deepcopy(report); changed['cpu_primary_evidence']['records'][hex(pc)][field] = 'altered'
            rejected(audit, changed)
        changed = copy.deepcopy(report); changed['cpu_primary_evidence']['canonical_record_sha256'][hex(pc)] = '0'*64
        rejected(audit, changed)
    for span in (*REGIONS.values(), *REUSED.values()):
        changed = copy.deepcopy(regions); changed.pop(span)
        rejected(runtime_evidence, report, inv.raw, inv.decode, changed, inv.instructions)
    for key in ('REGIONS', 'REUSED'):
        changed = copy.deepcopy(constants); changed[key] = {}; rejected(registry_evidence, report, changed)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 58,
        'new_data_exclusions': 0, 'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report', 'storage_coordination_report')
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
    report = StorageCoordinationInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'storage-coordination-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'storage_coordination_runtime_evidence': {k: v for k, v in report['storage_coordination_runtime_evidence'].items()
            if k != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
