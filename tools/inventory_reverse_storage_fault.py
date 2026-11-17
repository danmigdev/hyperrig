"""Audit the offline diagnostic storage closure while retaining inventory21.

Authenticate complete bodies, canonical windows, original call sites and primary
ISA records. Fatal observation is a reached self-loop, not a native return.
The initialized lock remains auxiliary mutable state and adds no data exclusion.
"""
from __future__ import annotations
import argparse
import ast
import copy
import functools
import json
import re
from pathlib import Path

from inventory_reverse import (Inventory, ROOT, REFERENCE, REFERENCE_SHA, APP,
    address, hex_address, local, sha, codec, table, unpack_app)
from inventory_reverse_effects import declared_constants
from inventory_reverse_integrations import REQUIRED_OPTIONS
from inventory_reverse_parameter_construction import span, static_identity
from inventory_reverse_storage_runtime import keyed, pc_set
from inventory_reverse_storage_platform import (StoragePlatformInventory,
    REPORT as PLATFORM_REPORT, PRESERVED_REPORTS as INVENTORY20_REPORTS)

ADAPTER = 'tools/inventory_reverse_storage_fault.py'
MODEL = 'tools/storage_fault_machine.py'
REPORT = 'build/reverse-storage-fault-01/verification.json'
REPORT_SHA = 'c46a56e99c8f0b003f58984fcd47466181f22b73bb1b28180128f7c2b145adfb'
MANIFEST_SHA = 'c2a4684c16479ce362b1308259ca69afd726dc50fe28e4cb916040f1eda27022'
PRIOR = 'build/reverse-inventory-21/inventory.json'
PRIOR_SHA = '4d1dffd56bcca944fc1950eaa7680997638999a685a76151dc5094eb3e285590'
PRIOR_MANIFEST_SHA = 'a14382a3adf9205c4b14b66162928bd1f1ae1078cb5c7d1238e96dfc0841845e'
PRESERVED_REPORTS = (*INVENTORY20_REPORTS, PLATFORM_REPORT)
REGIONS = {
    'tag': (0x02000730, 0x02000758), 'record_count': (0x02000758, 0x0200077c),
    'append': (0x0200077c, 0x02000800), 'checksum': (0x02000800, 0x02000830),
    'decode': (0x02000830, 0x0200088e), 'encode': (0x0200088e, 0x020008ee),
    'update': (0x020008ee, 0x02000952), 'once': (0x02000952, 0x0200096e),
    'fatal': (0x0200096e, 0x020009ca), 'acquire': (0x01c00e86, 0x01c00e9c),
    'exchange': (0x01c00e9c, 0x01c00eb6), 'release': (0x01c00eb6, 0x01c00ec8),
    'read_register': (0x01c00ec8, 0x01c00f0c), 'write_register': (0x01c00f0c, 0x01c00f4a),
    'masked_register': (0x01c00f4a, 0x01c00f72),
}
REUSED = {'irq_enter': (0x01c00e2e, 0x01c00e46), 'irq_leave': (0x01c00e46, 0x01c00e62)}
ARITIES = {'tag': 1, 'record_count': 0, 'append': 1, 'checksum': 3, 'decode': 1,
    'encode': 1, 'update': 2, 'once': 1, 'fatal': 0, 'acquire': 0, 'exchange': 1,
    'release': 0, 'read_register': 1, 'write_register': 2, 'masked_register': 4}
SCALAR = {'tag', 'record_count', 'checksum', 'decode', 'exchange', 'read_register'}
DIRECT_SITES = {
    0x02000782: 0x02000730, 0x02000786: 0x02000758, 0x02000846: 0x02000800,
    0x020008e2: 0x02000800, 0x020008f6: 0x02000830, 0x0200090e: 0x0200088e,
    0x0200096a: 0x020008ee, 0x0200097e: 0x0200077c, 0x02000984: 0x02000952,
    0x020009c2: 0x01c00f4a, 0x01c00e88: 0x01c00e2e, 0x01c00ec4: 0x01c00e46,
    0x01c00ece: 0x01c00e86, 0x01c00ef0: 0x01c00e9c, 0x01c00ef6: 0x01c00e9c,
    0x01c00efa: 0x01c00e9c, 0x01c00f06: 0x01c00eb6, 0x01c00f14: 0x01c00e86,
    0x01c00f32: 0x01c00e9c, 0x01c00f38: 0x01c00e9c, 0x01c00f3c: 0x01c00e9c,
    0x01c00f46: 0x01c00eb6, 0x01c00f62: 0x01c00ec8, 0x01c00f6e: 0x01c00f0c,
}
ISA_SITES = {
    0x0200096e: ('mov.r_sr', 'r5 = rets', '8090ea6ed09d708b0ea9a0c1f76cbcedcab50a9769242f29756e781821908031'),
    0x02000972: ('mov.r_sr', 'r6 = cnum', 'd424d7de3623e8607ff30e7a0a65ad801c598e98d2c351114a5124e19e0e0c57'),
    0x01c00e92: ('testset.b', 'testset b[r0]', '690e07f7700b22f965e8ee6245800c96e51f72367eea607c544a9c1b381157e5'),
    0x01c00e94: ('bc.eq', 'ifeq goto -6', 'ce1e6bda6e2c86ca7013f074a95af16da363605e436e16ae6d02a5b11e3d1a2d'),
    0x01c00e2e: ('cli', 'cli', '6e7ec874c2902d32ad705a7b05ffc762bf45d9bf802d428ec530732caa437412'),
    0x01c00e30: ('mov.r_sr', 'r0 = cnum', '1d54e052c2a0213eab323479d7973744f67f21c15e157db4def336f08a7dfc8d'),
    0x01c00e5e: ('sti', 'sti', '864f15571e33e214e973e089ef6071d325403f5da9d0d39eac8f0c5dfed1cd6c'),
    0x01c00ecc: ('ext.l.s', 'r4 = r2.l (s)', '54ad79f88cbc07550a9514f550e96b84bc834474cd2692e27d25ae1e177ba825'),
    0x01c00f12: ('ext.l.s', 'r5 = r3.l (s)', 'e0b965d897ba89d88149997939c84ff35c972ce98333bcb86533f405cfd2bdce'),
    0x01c00ea4: ('rmw.or.modimm', '[r1+0] |= 0x10', '92ae788ac2a6e4da934832099fb072dec4aa36132445c4e9d9185fbfefcd776d'),
    0x01c00eda: ('rmw.and.nmodimm', '[r3+0] &= 0xFFFFFEFF', '311918e3125c8e8f67aa348287bfc409cca97a6c7e97331b4aa6f9b0cd64dffe'),
    0x01c00ee4: ('rmw.or.r', '[r3+0] |= r0', 'd631f77a8197d5ed0a58a58bfbb5f83898a4b98d3b24d11b20c6d4f48c90b6a8'),
    0x01c00f00: ('rmw.and.r', '[r3+0] &= r1', '93cfcf9a47a056a8940c124886015749deea793608aeca84b1beac44a6dfd1bd'),
}
INITIAL = (0x01c1fa2c, 0x01c1fa30,
    'df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119')
INITIAL_ROLE = 'mutable initialized lock word, not immutable data'
MMIO = ((0x00013e08, 0x00013e10), (0x01eef07c, 0x01eef080), (0x01eef27c, 0x01eef280))
INCOMING = (0x02002b7a, 0x02002b7e, 0x0200096e)
INCOMING_SHA = 'ef3ec2832033ee0c498e58aad027aa9b505cd9ed07e54b0682ed1cc0e3d8e272'
CALLER = (0x020029be, 0x02002b80,
    'fc8b68a5dd3bf0681071a15297034710f11e01b904cd091a5cd3fec10e864f17')
HALT = 0x020009c8
MINI = 'd5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2'
OBSERVATION_LIMITS = (
    'Fifteen complete bodies and two unchanged IRQ helpers are compared offline; the four-byte incoming storage call is bound but no frozen caller or storage-runtime integration is executed.',
    'Fatal success observes the native self-loop at 0x020009c8; it is not a native return, restart, durable write or hardware reset.',
    'The lock and MMIO busy loops are unbounded in the original. Explicit completion fixtures and finite event/work guards do not establish fairness, inter-core atomicity, implicit ordering or timing.',
)


def fault_declarations(source):
    """Read the model's small constant expressions without executing its code."""
    values = declared_constants(source)
    def value(node):
        if isinstance(node, ast.Name): return values[node.id]
        if isinstance(node, (ast.Tuple, ast.List)): return tuple(value(item) for item in node.elts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            left, right = value(node.left), value(node.right)
            if type(left) is not int or type(right) is not int: raise ValueError('noninteger constant arithmetic')
            return left+right if isinstance(node.op, ast.Add) else left-right
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'dict' and not node.args and all(item.arg for item in node.keywords)):
            return {item.arg: value(item.value) for item in node.keywords}
        return ast.literal_eval(node)
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign): continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('ARITIES', 'MMIO', 'INITIAL_LOCK'):
                values[target.id] = value(node.value)
    return values


def registry_evidence(report, constants):
    if (report.get('result') != 'pass' or report.get('original_image_sha256') != REFERENCE_SHA
        or type(report.get('new_original_functions')) is not int or report['new_original_functions'] != 15
        or report.get('new_data_exclusions') != []):
        raise ValueError('fault evidence requires fifteen new bodies and no data exclusion for the pinned image')
    for key, expected in (('functions', REGIONS), ('reused_functions', REUSED)):
        if {name: span(item) for name, item in report[key].items()} != expected:
            raise ValueError('fault whole-body registry changed')
    declarations = {'REGIONS': REGIONS, 'REUSED': REUSED, 'ARITIES': ARITIES, 'SCALAR': SCALAR,
        'DIRECT_SITES': DIRECT_SITES, 'INITIAL_LOCK': INITIAL, 'MMIO': MMIO,
        'INCOMING': INCOMING, 'HALT': HALT, 'CONTROL': 0x00013e08, 'DATA': 0x00013e0c,
        'GLOBAL': 0x01c1f180, 'STATE': 0x01c26890, 'IRQ_COUNTS': 0x01c1fc54,
        'LOCK': INITIAL[0], 'HEADER': 0x01c7fba0, 'RECORDS': 0x01c7fba4,
        'METADATA': 0x01c7fbd4, 'CURRENT': 0x01c7fdd8, 'STACK': 0x30001000,
        'READ': 1, 'WRITE': 2, 'BARRIER': 3, 'CLI': 5, 'STI': 6, 'CNUM': 7, 'TESTSET': 8, 'RETS': 17,
        'ISA_SITES': {pc: item[0] for pc, item in ISA_SITES.items()},
        'ISA_RECORD_SHA256': {hex(pc): item[2] for pc, item in ISA_SITES.items()}}
    for key, expected in declarations.items():
        if constants.get(key) != expected: raise ValueError('fault model declaration changed: '+key)
    if any(report.get(key) is not False for key in ('hardware_test', 'device_access', 'audio_test', 'firmware_changed')):
        raise ValueError('fault offline evidence cannot become a hardware or firmware-change claim')
    if report['mini_binding'] != {'sha256': MINI, 'complete_regions': 17, 'instructions': 332,
            'auxiliary_mutable_bytes': 4, 'incoming_call_bytes': 4}:
        raise ValueError('fault reviewed MINI binding changed')
    if (any(item not in report['limitations'] for item in OBSERVATION_LIMITS)
        or type(report['fatal_observations']) is not int or report['fatal_observations'] != 54
        or type(report['portable_failure_cases']) is not int or report['portable_failure_cases'] != 279):
        raise ValueError('fault observation, first-fault or offline scope changed')


def runtime_evidence(report, constants, raw, decode, regions, data_ranges, isa):
    registry_evidence(report, constants)
    canonical, new_pcs, per_function = {}, set(), {}
    for key in ('functions', 'reused_functions'):
        for name, item in report[key].items():
            a, b = span(item); parent = regions.get((a, b)); body = decode(a, b)
            if (parent is None or parent['kind'] != 'function_region'
                or parent['sha256'] != item['bytes_sha256'] or sha(raw(a, b)) != item['bytes_sha256']
                or type(item['bytes']) is not int or item['bytes'] != b-a
                or type(item['instructions']) is not int or item['instructions'] != len(body)
                or type(item['visited_instructions']) is not int or item['visited_instructions'] != len(body)):
                raise ValueError('fault body bytes, parent, whole extent or coverage changed')
            pcs = {pc for pc, _, _ in body}
            if pcs & canonical.keys(): raise ValueError('fault body declarations overlap')
            if any(a < y and x < b for x, y, _ in data_ranges):
                raise ValueError('fault executable body overlaps a data exclusion')
            canonical.update({pc: (size, text) for pc, size, text in body})
            if key == 'functions': new_pcs.update(pcs)
            per_function[name] = {'decoded': len(pcs), 'visited': len(pcs), 'unvisited': 0,
                'reused': key == 'reused_functions'}
    coverage = report['instruction_coverage']
    expected = {'new_decoded': 315, 'new_visited': 315, 'all_decoded': 332, 'all_visited': 332}
    if (len(new_pcs) != 315 or len(canonical) != 332
        or sum(b-a for a, b in REGIONS.values()) != 902
        or any(type(coverage[k]) is not int or coverage[k] != v for k, v in expected.items())
        or coverage['unvisited_new'] != [] or coverage['unvisited_all'] != [] or report['gap_instructions'] != {}):
        raise ValueError('fault coverage differs from the canonical complete closure')
    visited = pc_set(report['visited'], set(canonical), 'fault visited PCs')
    if visited != canonical.keys(): raise ValueError('fault coverage omits a canonical instruction')
    windows = keyed(report['loaded_instruction_windows'], 'fault instruction windows')
    if windows.keys() != canonical.keys(): raise ValueError('fault loaded window set differs from complete bodies')
    for pc, item in windows.items():
        size, _ = canonical[pc]
        if type(item['bytes']) is not int or item['bytes'] != size or sha(raw(pc, pc+size)) != item['sha256']:
            raise ValueError('fault loaded window is not one exact original instruction')
    direct = {}
    for pc, (size, text) in canonical.items():
        if match := re.fullmatch(r'call (-?\d+)', text): direct[pc] = pc+size+int(match[1])
        elif text.startswith('call '): raise ValueError('fault closure contains an unexpected indirect call')
    if direct != DIRECT_SITES or report['indirect_sites'] != {}:
        raise ValueError('fault original direct or indirect site registry changed')
    recorded = keyed(report['direct_sites'], 'fault direct sites')
    if recorded.keys() != direct.keys(): raise ValueError('fault reported direct call set changed')
    entries = {a for a, _ in (*REGIONS.values(), *REUSED.values())}
    for pc, target in direct.items():
        item = recorded[pc]
        if address(item['target']) != target or item['visited'] is not True or pc not in visited or target not in visited or target not in entries:
            raise ValueError('fault direct call or complete callee entry is not authenticated and visited')
    records = keyed(report['isa_primary_evidence'], 'fault primary ISA records')
    if records.keys() != ISA_SITES.keys(): raise ValueError('fault primary ISA evidence set changed')
    for pc, (identifier, text, digest) in ISA_SITES.items():
        size, decoded_text = canonical[pc]
        found = codec.decode(isa, raw(pc, pc+size), 0)
        if found is None: raise ValueError('undecoded fault ISA observation')
        instruction, fields, decoded_size = found
        original = {'id': instruction.id, 'decoded': codec.format(instruction, fields),
            'summary': instruction.summary, 'notes': instruction.notes,
            'status': instruction.status, 'sources': instruction.sources}
        canonical_hash = sha(json.dumps(original, sort_keys=True, separators=(',', ':')).encode())
        if (decoded_size != size or decoded_text != text or instruction.id != identifier
            or original['decoded'] != text or canonical_hash != digest or records[pc] != original):
            raise ValueError('fault instruction or local primary ISA record changed')
    witness = report['auxiliary_initial_state']; a, b, digest = INITIAL
    if (static_identity(witness) != INITIAL or witness.get('classification') != INITIAL_ROLE
        or raw(a, b) != bytes(4) or sha(raw(a, b)) != digest
        or any(a < y and x < b for x, y, _ in data_ranges)):
        raise ValueError('fault mutable lock witness changed or became a data exclusion')
    # Bind the incoming edge to its complete, previously reconstructed parent.
    # Its return address is the end of this actual four-byte call, not a guessed
    # six-byte call width. Neither that caller nor its final self-loop ran here.
    ca, cb, cdigest = CALLER; parent = regions.get((ca, cb))
    if parent is None or parent['kind'] != 'function_region' or parent['sha256'] != cdigest or sha(raw(ca, cb)) != cdigest:
        raise ValueError('fault incoming call lost its frozen complete storage caller')
    caller_code = {pc: (size, text) for pc, size, text in decode(ca, cb)}
    a, b, target = INCOMING; incoming = report['incoming_storage_call']
    expected_incoming = {'start': hex(a), 'end_exclusive': hex(b), 'target': hex(target),
        'instruction': 'call -8720', 'sha256': INCOMING_SHA, 'arity': 0,
        'decoded_bytes': 4, 'caller_executed_in_this_module': False}
    if (incoming != expected_incoming or type(incoming['arity']) is not int
        or type(incoming['decoded_bytes']) is not int
        or incoming['caller_executed_in_this_module'] is not False
        or caller_code.get(a) != (4, f'call {target-b}')
        or caller_code.get(b) != (2, 'goto -2') or sha(raw(a, b)) != INCOMING_SHA
        or a in canonical or b in canonical or target not in visited
        or any(a < y and x < b+2 for x, y, _ in data_ranges)):
        raise ValueError('fault incoming call, four-byte width, RETS or execution scope changed')
    if (canonical.get(HALT) != (2, 'goto -2') or HALT+2 != REGIONS['fatal'][1]
        or any(text == 'rts' for pc, (_, text) in canonical.items() if REGIONS['fatal'][0] <= pc < HALT)):
        raise ValueError('fault observation must remain the complete fatal body self-loop, not a return')
    return {'new_whole_functions': 15, 'reused_whole_functions': 2, **expected,
        'canonical_instruction_windows': len(windows), 'direct_internal_sites': len(direct),
        'indirect_external_sites': 0, 'primary_ISA_records': len(records),
        'incoming_storage_call': {**incoming, 'return_address': hex_address(b),
            'complete_parent': {'start': hex_address(ca), 'end_exclusive': hex_address(cb), 'sha256': cdigest}},
        'fatal_observation': {'pc': hex_address(HALT), 'instruction': 'goto -2',
            'portable_status': 1, 'observations': report['fatal_observations'], 'native_return': False},
        'portable_failure_cases': report['portable_failure_cases'],
        'CPU_MMIO_completion_is_supplied': True, 'hardware_atomicity_or_durability_proven': False,
        'auxiliary_mutable_initial_state': witness, 'new_data_exclusions': 0,
        'per_function': per_function}


def require_preserved_reports(selected):
    if len(PRESERVED_REPORTS) != 63 or len(set(PRESERVED_REPORTS)) != 63:
        raise ValueError('inventory21 must retain exactly 63 distinct reports')
    if len(selected) != len(set(selected)) or not {*PRESERVED_REPORTS, REPORT} <= set(selected):
        raise ValueError('fault inventory omitted or duplicated earlier report evidence')


class StorageFaultInventory(StoragePlatformInventory):
    def __init__(self, *required, storage_fault_report, additional_reports=(), **options):
        if local(storage_fault_report).relative_to(ROOT).as_posix() != REPORT:
            raise ValueError('inventory requires frozen storage-fault01')
        additions = [local(name).relative_to(ROOT).as_posix() for name in additional_reports]
        if REPORT in additions: raise ValueError('fault report is already explicitly selected')
        self.fault_runtime = None
        super().__init__(*required, additional_reports=[*additions, REPORT], **options)

    def reports(self):
        omitted = super().reports(); self.audit_manifest(REPORT, MANIFEST_SHA)
        raw_report = self.read(REPORT)
        if sha(raw_report) != REPORT_SHA: raise ValueError('frozen fault report changed')
        report = json.loads(raw_report); source = self.read(MODEL)
        if report['source_sha256'].get(MODEL) != sha(source): raise ValueError('fault model source changed')
        constants = fault_declarations(source.decode('utf-8'))
        self.fault_runtime = runtime_evidence(report, constants, self.raw, self.decode,
            self.regions, self.data_ranges, self.instructions)
        module = next(item for item in self.modules if item['report'] == REPORT)
        module.update(reported_region_coverage=self.fault_runtime['per_function'],
            storage_fault_runtime_evidence=self.fault_runtime)
        return omitted

    def run(self):
        report = super().run(); require_preserved_reports(report['selected_reports']); self.read(ADAPTER)
        report.update(schema=20, storage_fault_inventory_adapter=ADAPTER,
            storage_fault_runtime_evidence=self.fault_runtime)
        report['audits'].update(inventory21_all_sixty_three_reports_retained=True,
            fault_complete_new_and_reused_bodies_and_canonical_windows_bound=True,
            fault_direct_calls_and_reused_entries_independently_decoded_and_visited=True,
            fault_has_no_indirect_calls=True, fault_primary_ISA_records_independently_decoded=True,
            fault_actual_four_byte_incoming_call_and_RETS_bound_without_executing_caller=True,
            fault_self_loop_observation_is_not_native_return=True,
            fault_lock_initial_state_remains_auxiliary_mutable=True, fault_adds_no_data_exclusions=True)
        report['scope_policy'].extend([
            'storage fault adds fifteen complete bodies and reuses two existing IRQ helpers without duplicate function entries',
            'all 332 canonical instruction windows, 24 direct internal sites, zero indirect sites and thirteen full primary ISA records are authenticated',
            'the incoming four-byte call at 0x02002b7a and its RETS 0x02002b7e are bound inside the existing complete storage-control parent; that caller was not executed in this module',
            'portable status one observes the native fatal self-loop at 0x020009c8; it does not mean native return, restart, durable write or hardware reset',
            'the four initialized lock bytes remain auxiliary mutable state and add no data exclusion',
            'all inventory21 report, known-data and exact setup-prefix supersession policies remain unchanged',
            'MMIO values and lock completion remain explicit fixtures; event/map prefix checks and portable work ceilings do not establish scheduling, atomicity, timing or physical storage retention'])
        report['input_sha256'] = dict(sorted(self.sources.items()))
        return report


def self_test():
    """Reject changed evidence without deriving an inventory or rerunning firmware."""
    packed, app = local(REFERENCE).read_bytes(), local(APP).read_bytes()
    if sha(packed) != REFERENCE_SHA or unpack_app(packed)[2]['app.bin'] != app:
        raise ValueError('self-check original image changed')
    prior_raw = local(PRIOR).read_bytes(); prior_manifest = local(PRIOR).with_name('build-manifest.json').read_bytes()
    if sha(prior_raw) != PRIOR_SHA or sha(prior_manifest) != PRIOR_MANIFEST_SHA:
        raise ValueError('self-check frozen inventory21 report/manifest changed')
    prior = json.loads(prior_raw)
    if set(prior['selected_reports']) != set(PRESERVED_REPORTS):
        raise ValueError('self-check inventory21 report set changed')
    inv = object.__new__(Inventory); inv.app = app; inv.instructions = table.load()
    inv.flash_start, inv.flash_end = 0x02000120, 0x02056780
    inv.ram_start, inv.ram_end, inv.ram_source = 0x01c00000, 0x01c2030c, 0x02056780
    inv.data_ranges = [(address(item['start']), address(item['end_exclusive']), item['kind'])
        for item in prior['known_data_ranges']]
    raw_report = local(REPORT).read_bytes()
    if sha(raw_report) != REPORT_SHA or sha(local(REPORT).with_name('build-manifest.json').read_bytes()) != MANIFEST_SHA:
        raise ValueError('self-check frozen fault report/manifest changed')
    report = json.loads(raw_report); model = local(MODEL).read_bytes()
    if sha(model) != report['source_sha256'][MODEL]: raise ValueError('self-check fault model changed')
    constants = fault_declarations(model.decode())
    regions = {span(item): item for item in prior['reconstructed_regions']}
    for item in report['functions'].values():
        if span(item) in regions: raise ValueError('fault new body was already counted')
        regions[span(item)] = {'kind': 'function_region', 'sha256': item['bytes_sha256']}
    decode = functools.lru_cache(None)(inv.decode); raw = functools.lru_cache(None)(inv.raw)
    checks = 0
    def rejected(function, *args):
        nonlocal checks
        try: function(*args)
        except (ValueError, KeyError, TypeError, IndexError): checks += 1; return
        raise AssertionError('invalid fault evidence accepted')
    def audit(item): return runtime_evidence(item, constants, raw, decode, regions, inv.data_ranges, inv.instructions)
    registry_evidence(report, constants); checks += 1
    evidence = audit(report)
    assert evidence['all_visited'] == 332 and evidence['fatal_observation']['native_return'] is False; checks += 1
    for key in ('functions', 'reused_functions'):
        for name in report[key]:
            for field, value in [('start', 0), ('end_exclusive', 0), ('bytes', True),
                    ('bytes_sha256', '0'*64), ('instructions', 0), ('visited_instructions', False)]:
                changed = copy.deepcopy(report); changed[key][name][field] = value; rejected(audit, changed)
    paths = [
        ((), 'result', 'fail'), ((), 'original_image_sha256', '0'*64), ((), 'new_original_functions', True),
        ((), 'new_original_functions', 17), ((), 'new_data_exclusions', [INITIAL[:2]]),
        ((), 'visited', report['visited'][:-1]), ((), 'visited', report['visited']+[report['visited'][0]]),
        ((), 'visited', ['0x02000731', *report['visited'][1:]]), ((), 'gap_instructions', {'0x020009c8': 'missing'}),
        (('instruction_coverage',), 'new_visited', 314), (('instruction_coverage',), 'all_decoded', True),
        (('instruction_coverage',), 'all_visited', 331), (('instruction_coverage',), 'unvisited_new', [HALT]),
        (('instruction_coverage',), 'unvisited_all', [0x01c00e2e]), ((), 'hardware_test', True),
        ((), 'device_access', True), ((), 'audio_test', True), ((), 'firmware_changed', True),
        (('mini_binding',), 'sha256', '0'*64), (('mini_binding',), 'auxiliary_mutable_bytes', 8),
        (('mini_binding',), 'incoming_call_bytes', 6), (('mini_binding',), 'complete_regions', 15),
        (('auxiliary_initial_state',), 'start', INITIAL[0]-4),
        (('auxiliary_initial_state',), 'end_exclusive', INITIAL[1]+4),
        (('auxiliary_initial_state',), 'sha256', '0'*64),
        (('auxiliary_initial_state',), 'classification', 'immutable table'),
        ((), 'direct_sites', {}), ((), 'indirect_sites', {'0x02000984': {'arity': 1}}),
        ((), 'isa_primary_evidence', {}), ((), 'loaded_instruction_windows', {}),
        ((), 'fatal_observations', 0), ((), 'fatal_observations', True),
        ((), 'portable_failure_cases', 0), ((), 'limitations', []),
        (('incoming_storage_call',), 'start', '0x02002b78'),
        (('incoming_storage_call',), 'end_exclusive', '0x02002b80'),
        (('incoming_storage_call',), 'target', '0x02000952'),
        (('incoming_storage_call',), 'instruction', 'call -8718'),
        (('incoming_storage_call',), 'sha256', '0'*64),
        (('incoming_storage_call',), 'arity', False), (('incoming_storage_call',), 'arity', 1),
        (('incoming_storage_call',), 'decoded_bytes', 6),
        (('incoming_storage_call',), 'caller_executed_in_this_module', True),
        (('incoming_storage_call',), 'caller_executed_in_this_module', 0),
    ]
    for path, key, value in paths:
        changed = copy.deepcopy(report); node = changed
        for part in path: node = node[part]
        node[key] = value; rejected(audit, changed)
    for pc in report['loaded_instruction_windows']:
        changed = copy.deepcopy(report); changed['loaded_instruction_windows'][pc]['sha256'] = '0'*64; rejected(audit, changed)
    key = next(iter(report['loaded_instruction_windows']))
    for width in (0, True, report['loaded_instruction_windows'][key]['bytes']+2):
        changed = copy.deepcopy(report); changed['loaded_instruction_windows'][key]['bytes'] = width; rejected(audit, changed)
    for field in ('loaded_instruction_windows', 'direct_sites', 'isa_primary_evidence'):
        changed = copy.deepcopy(report); key = next(iter(changed[field])); changed[field][str(address(key))] = changed[field][key]
        rejected(audit, changed)
    for pc in DIRECT_SITES:
        for field, value in [('target', '0x02000000'), ('visited', False), ('visited', 1)]:
            changed = copy.deepcopy(report); changed['direct_sites'][hex(pc)][field] = value; rejected(audit, changed)
    for pc in ISA_SITES:
        for field in ('id', 'decoded', 'notes', 'summary', 'status', 'sources'):
            changed = copy.deepcopy(report); changed['isa_primary_evidence'][hex(pc)][field] = 'altered'; rejected(audit, changed)
    for bounds in (*REGIONS.values(), *REUSED.values(), CALLER[:2]):
        changed = copy.deepcopy(regions); changed.pop(bounds)
        rejected(runtime_evidence, report, constants, raw, decode, changed, inv.data_ranges, inv.instructions)
        changed = copy.deepcopy(regions); changed[bounds]['kind'] = 'fragment'
        rejected(runtime_evidence, report, constants, raw, decode, changed, inv.data_ranges, inv.instructions)
    for key in ('REGIONS', 'REUSED', 'ARITIES', 'SCALAR', 'DIRECT_SITES', 'INITIAL_LOCK', 'MMIO',
            'INCOMING', 'HALT', 'CONTROL', 'DATA', 'GLOBAL', 'STATE', 'IRQ_COUNTS', 'LOCK', 'HEADER',
            'RECORDS', 'METADATA', 'CURRENT', 'STACK', 'READ', 'WRITE', 'BARRIER', 'CLI', 'STI', 'CNUM',
            'TESTSET', 'RETS', 'ISA_SITES', 'ISA_RECORD_SHA256'):
        changed = copy.deepcopy(constants); changed[key] = {}; rejected(registry_evidence, report, changed)
    for start, end in (INITIAL[:2], REGIONS['fatal'], INCOMING[:2], (INCOMING[1], INCOMING[1]+2)):
        rejected(runtime_evidence, report, constants, raw, decode, regions,
            [*inv.data_ranges, (start, end, 'invented_fault_data')], inv.instructions)
    # The caller and terminal self-loop are decoded independently of the report.
    for changed_pc, size, text in ((INCOMING[0], 6, 'call -8722'),
            (INCOMING[1], 2, 'rts'), (HALT, 2, 'rts')):
        def altered_decode(a, b, pc=changed_pc, width=size, replacement=text):
            return [(p, width, replacement) if p == pc else (p, n, t) for p, n, t in decode(a, b)]
        rejected(runtime_evidence, report, constants, raw, altered_decode, regions, inv.data_ranges, inv.instructions)
    selected = [*PRESERVED_REPORTS, REPORT]; require_preserved_reports(selected); checks += 1
    for name in selected: rejected(require_preserved_reports, [item for item in selected if item != name])
    rejected(require_preserved_reports, selected+[REPORT])
    print(json.dumps({'result': 'pass', 'self_test_checks': checks, 'preserved_reports': 63,
        'new_whole_functions': 15, 'new_data_exclusions': 0, 'fatal_is_native_return': False,
        'inventory_snapshot_generated': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in REQUIRED_OPTIONS: parser.add_argument('--'+name)
    names = ('configured_signal_report', 'model_report', 'ir_numerical_report',
        'parameter_construction_report', 'storage_control_report', 'storage_coordination_report',
        'sample_processing_report', 'storage_runtime_report', 'effect_setup_report',
        'storage_platform_report', 'storage_fault_report')
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
    report = StorageFaultInventory(*required, **extra, additional_reports=args.add_report).run()
    if output:
        output.mkdir(parents=True)
        (output/'inventory.json').write_bytes((json.dumps(report, indent=2)+'\n').encode('utf-8'))
        manifest = {'component': 'storage-fault-reverse-engineering-inventory', 'device_access': False,
            'files': {'inventory.json': sha((output/'inventory.json').read_bytes())}}
        (output/'build-manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode('utf-8'))
    print(json.dumps({'summary': report['summary'], 'audits': report['audits'],
        'storage_fault_runtime_evidence': {k: v for k, v in report['storage_fault_runtime_evidence'].items()
            if k != 'per_function'}}, indent=2))


if __name__ == '__main__': main()
