"""Create and retain the first HyperRig_Test preset; default is offline.

The frozen mutation probe requires an existing saved preset for restoration.
This separate experiment starts with PLIST current=-1, proves PSAVE and scene A
by two marker/reload cycles, and intentionally keeps the newly created slot.
It never sends PDEL, PNEW, NAM/IR upload or firmware commands. Device I/O is
available only through the explicit create subcommand, on a boot-verified app.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_app as app
from tools import probe_mini_app as readonly
from tools import probe_mini_app_mutation as mutation

Error, require = mutation.Error, mutation.require
KIND = 'mini-app-first-preset-validation'
MODEL = 'representative-first-preset-v1'
NAME = 'HyperRig_Test'


def source_contract():
    result = mutation.source_contract()
    source = app.checked(app.SOURCE/'web/tankg.html', app.SOURCE_SHA).decode('utf-8')
    require(all(anchor in source for anchor in (
        'async function sceneAOnSave(n, since)',
        'Pedal.cmd("SNAPSAVE 0", "SNAPSAVE")',
        'Pedal.cmd(`GAIN ${S.gain[0]} ${S.gain[1]}`, "GAIN")',
        'min: -30, max: 12, val: S.gain[0]',
        'min: -30, max: 12, val: S.gain[1]')), 'original first-save/gain contract changed')
    firmware = app.checked(app.FW_SOURCE, app.FW_SHA)
    response = b'GAIN in=%d out=%d dB\n\0'
    require(firmware[0x365BE:0x365BE+len(response)] == response, 'original GAIN reply changed')
    return {**result, 'first_preset_kept': True, 'initial_current': -1,
            'PSAVE_requires': 'free slot, current=-1, unchanged observed state and retained state backup; no existing bank export',
            'first_save_requires_existing_bank_export': False,
            'gain_marker': 'one downward step only, range -30..12 dB; no GSAVE',
            'no_preexisting_preset_is_loaded_or_deleted': True,
            'PSAVE_followed_by_separately_verified_SNAPSAVE_0': True}


def select_marker(state, types, selection):
    """Select a real FXP/FXE or a decreasing GAIN marker, without any I/O."""
    require(isinstance(selection, dict) and set(selection) <= {'operation','block_id','parameter_index'},
            'bounded marker selection required')
    operation = selection.get('operation', 'auto')
    require(operation in ('auto','FXP','FXE','GAIN'), 'unsupported marker operation')
    def parameter_marker(block_id, index):
        block = mutation.block_in(state, block_id)
        require(type(index) is int and index in types.get(block['type'], {}).get('params', {}),
                'marker parameter absent from FXT')
        value = block['params'][index]
        require(value > types[block['type']]['params'][index]['min'], 'no downward parameter step available')
        return mutation.plan_live(state, types, block_id=block_id, parameter_index=index, value=value-1)
    if operation in ('FXP','FXE'):
        if operation == 'FXP': return parameter_marker(selection.get('block_id'), selection.get('parameter_index'))
        return mutation.plan_live(state, types, block_id=selection.get('block_id'), operation=operation,
                                  parameter_index=selection.get('parameter_index'))
    require(selection.get('block_id') is None and selection.get('parameter_index') is None,
            'auto/GAIN marker has no block or parameter argument')
    if operation == 'auto':
        for block in state['fxs']['blocks']:
            for index in types.get(block['type'], {}).get('params', {}):
                try:
                    return parameter_marker(block['id'], index)
                except Error:
                    pass
    gain = state['extra']['gain_db']
    require(len(gain) == 2, 'GAIN readback needs input and output')
    for value in gain: mutation.integer(value, -30, 12)
    index = 1 if gain[1] > -30 else 0
    require(gain[index] > -30, 'no decreasing GAIN marker available at the minimum; no save attempted')
    changed = list(gain); changed[index] -= 1
    return {'operation': 'GAIN', 'original': list(gain), 'requested': changed,
            'request': f'GAIN {changed[0]} {changed[1]}'}


class FirstPresetProbe(mutation.PresetMutationProbe):
    """Capture uses the original readers. Only create_first performs writes."""
    def _mark(self, state, marker):
        if isinstance(marker, mutation.LivePlan):
            old = mutation.block_in(self.baseline, marker.block_id)
            block = next((b for b in state['fxs']['blocks']
                          if (b['bank'],b['position'],b['type']) == (old['bank'],old['position'],old['type'])), None)
            require(block is not None, 'marker block changed after PLOAD')
            plan = mutation.plan_live(state, self.types, block_id=block['id'], operation=marker.operation,
                                      parameter_index=marker.parameter_index, value=marker.requested)
            actual, reply = self._mutate(plan.request, plan)
            expected = mutation.changed(state, plan, plan.requested)
            require(plan.operation != 'FXP' or actual == plan.requested, 'FXP marker effective value differs')
            request, ack = plan.request, reply['lines'][0]
        else:
            require(state['extra']['gain_db'] == marker['original'], 'GAIN changed before persistence marker')
            request = marker['request']
            left, right = marker['requested']
            ack, _ = self._ack(request, rf'GAIN in={left} out={right} dB')
            expected = copy.deepcopy(state)
            expected['extra']['gain_db'] = list(marker['requested'])
        observed, _ = self._snapshot()
        require(observed == expected, 'persistence marker lacks exact readback or changed unrelated state')
        self._observe(request, ack, observed)
        return observed

    def create_first(self, *, slot=None, marker_selection=None):
        require(self.baseline is not None and not self.finished and not self.wire.failed,
                'one captured first-preset trial required')
        selection = copy.deepcopy(marker_selection if marker_selection is not None else {'operation':'auto'})
        baseline = self.baseline
        plist = baseline['plist']
        require(plist.get('ok') is True and not plist.get('bad') and plist['current'] == -1,
                'first-preset trial requires coherent PLIST with no saved current preset')
        occupied = {p['slot'] for p in plist['presets']}
        if slot is None:
            slot = next((n for n in range(32) if n not in occupied), None)
        mutation.integer(slot, 0, 31)
        require(slot not in occupied, 'first-preset destination is occupied')
        require(baseline['snaps']['current'] >= 0 or baseline['snaps']['present'] == '0000',
                'unselected existing RAM scenes cannot be compared by this first-save trial')
        marker = select_marker(baseline, self.types, selection)  # Must exist before PSAVE.
        request = f'PSAVE {slot} {NAME}'
        self.result.update(plan={'operation':'PSAVE', 'request':request, 'before_sha256':mutation.digest(baseline)},
            phase='preflight', slot=slot, marker_selection=selection,
            initial_saved_preset_absent=True, slot_was_free=True,
            persistent_intent='retain-new-preset', preset_intentionally_retained=False,
            restoration_verified=False, preexisting_inventory_verified=False,
            first_preset_created=False, persistence_readback_verified=False,
            snapshot_persistence_readback_verified=False, final_sound_verified=False)
        try:
            current, _ = self._snapshot()
            require(current == baseline, 'state changed before first PSAVE')
            self.result.update(phase='save_first', mutation_submitted=True)
            ack, match = self._ack(request,
                rf"PSAVE ok {slot} '{NAME}' (\d+) blocks capture=(-?\d+) ir=(-?\d+)", 8)
            require(int(match[1]) == len(baseline['fxs']['blocks']), 'PSAVE block count differs')
            saved, _ = self._snapshot()
            require(saved['plist']['current'] == slot and mutation.sound_equal(saved, baseline),
                    'first PSAVE changed the observed sound/scene')
            entries = [p for p in saved['plist']['presets'] if p['slot'] == slot]
            require(len(entries) == 1 and entries[0]['name'] == NAME and entries[0]['blocks'] == int(match[1]),
                    'new preset missing or inconsistent in PLIST')
            created = entries[0]
            self._assert_listing(saved, created)
            self.result.update(first_preset_created=True, created_entry=copy.deepcopy(created),
                               phase='psave_marker')
            require(not baseline['fxs']['amp']['present'] or int(match[2]) >= 0,
                    'PSAVE reports an unpersisted active capture; no marker or reload attempted')
            self._mark(saved, marker)
            self.result['phase'] = 'reload_first'
            loaded, refs = self._load(slot, NAME, baseline['snaps']['current'], created)
            require(refs == (int(match[2]),int(match[3])), 'PLOAD capture/IR references differ from PSAVE')
            self._observe(request, ack, loaded, persistent=True)
            self.result.update(persistence_readback_verified=True, phase='save_scene_zero')
            scene_ack, _ = self._ack('SNAPSAVE 0', rf'SNAPSAVE ok 0 preset={slot}')
            scene_saved, _ = self._snapshot()
            expected = copy.deepcopy(loaded)
            expected['snaps'] = {'present':'1'+loaded['snaps']['present'][1:], 'current':0}
            created = {**created, 'snapshots':created['snapshots'] | 1}
            expected['plist']['presets'] = [created if p['slot'] == slot else p for p in expected['plist']['presets']]
            require(scene_saved == expected, 'SNAPSAVE changed unrelated state or did not select scene zero')
            self._assert_listing(scene_saved, created)
            self.result['phase'] = 'scene_marker'
            self._mark(scene_saved, marker)
            self.result['phase'] = 'reload_scene_zero'
            reloaded, refs2 = self._load(slot, NAME, 0, created, expected_state=scene_saved)
            require(refs2 == refs, 'scene reload capture/IR references changed')
            self._observe('SNAPSAVE 0', scene_ack, reloaded, persistent=True)
            final, _ = self._snapshot()
            require(final == reloaded and mutation.sound_equal(final, scene_saved), 'final state changed after reload')
            self._assert_listing(final, created)
            self.result.update(phase='complete', roundtrip_passed=True,
                snapshot_persistence_readback_verified=True, preset_intentionally_retained=True,
                preexisting_inventory_verified=True, final_sound_verified=True,
                final_state=final, created_entry=copy.deepcopy(created))
            return copy.deepcopy(self.result)
        except Exception as exc:
            self.wire.failed = True
            self.result.update(error=str(exc), failed_phase=self.result['phase'], phase='failed')
            self.log('first_preset_failed', **self.result)
            raise
        finally:
            self.finished = True


def implementation_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def first_evidence(result, profile, *, trace, backup, hardware_executed=False):
    require(result.get('roundtrip_passed') is True and result.get('preset_intentionally_retained') is True
            and result.get('restoration_verified') is False, 'completed intentional first-save trial required')
    app.local_evidence(trace, 'first-preset trace')
    retained = json.loads(app.local_evidence(backup, 'first-preset backup'))
    require(retained.get('kind') == 'mini-app-live-state-backup'
            and retained.get('image_sha256') == profile['image_sha256']
            and retained.get('firmware_version') == profile['firmware_version']
            and mutation.digest(retained['state']) == result['plan']['before_sha256'],
            'first-preset backup differs from observed baseline')
    observations = [copy.deepcopy(o) for o in result['observations'] if o['request'].split()[0] in app.FAMILY_COMMANDS]
    requests = {}
    for o in observations: requests.setdefault(o['request'].split()[0], set()).add(o['request'])
    requests = {k:sorted(v) for k,v in sorted(requests.items())}
    return {'schema':1, 'kind':KIND, 'evidence_model':MODEL, 'target':'tank-mini',
        'transport':'usb-cdc', 'firmware_version':profile['firmware_version'],
        'image_sha256':profile['image_sha256'], 'hardware_executed':hardware_executed is True,
        'editor_source_sha256':app.SOURCE_SHA, 'protocol_binding':copy.deepcopy(app.PROTOCOL_BINDING),
        'implementation_sha256':implementation_sha256(),
        'supported_by_protocol':sorted(app.FAMILY_COMMANDS),
        'physically_exercised_requests':requests if hardware_executed is True else {},
        'simulated_requests':requests if hardware_executed is not True else {},
        'representative_observations':observations, 'trace':trace, 'backup':backup,
        'trial':copy.deepcopy(result), 'restoration_verified':False,
        'preset_intentionally_retained':True, 'final_sound_verified':True,
        'image_hash_attested_by_device':False, 'every_value_physically_tested':False,
        'BLE_verified':False, 'all_required_editor_mutations_verified':False,
        'limits':['No power-cycle retention or audio-quality claim.',
                  'Initial current preset was absent; no restoration to an invented preset.',
                  'Only observed preexisting PLIST inventory is compared, not every other preset payload.',
                  'The new preset and scene A intentionally remain stored; no PDEL is sent.']}


class _TraceReplay:
    """Only retained bytes: never constructs a serial/USB/device transport."""
    def __init__(self, data):
        self.exchanges, active = [], None
        self.pending, self.position, self.now = [], 0, 0.0
        for line in data.decode('utf-8').splitlines():
            if not line: continue
            row = json.loads(line)
            if row.get('event') == 'tx':
                require(active is None, 'overlapping replay exchange')
                active = {'tx':bytes.fromhex(row['hex']), 'rx':[]}
            elif row.get('event') == 'rx':
                require(active is not None, 'replay RX without command')
                active['rx'].append(bytes.fromhex(row['hex']))
            elif row.get('event') == 'complete':
                require(active is not None, 'replay completion without command')
                self.exchanges.append(active); active = None
        require(active is None and self.exchanges, 'incomplete/empty first-preset replay')
    def clock(self): return self.now
    def write(self, data):
        require(not self.pending and self.position < len(self.exchanges), 'unexpected replay command')
        item = self.exchanges[self.position]
        require(data == item['tx'], 'first-preset trace command/order differs from executor')
        self.position += 1; self.pending = list(item['rx'])
        return len(data)
    def read(self, _size):
        self.now += .001
        return self.pending.pop(0) if self.pending else b''


def validate_first_preset_evidence(evidence, retained, raw_trace):
    """Replay all raw exchanges, then compare the claimed trial exactly.

    The builder has already checked image/transport/provenance/raw RX framing.
    This function establishes consistency, not physical authenticity.
    """
    require(evidence.get('kind') == KIND and evidence.get('evidence_model') == MODEL
            and evidence.get('implementation_sha256') == implementation_sha256()
            and evidence.get('restoration_verified') is False
            and evidence.get('preset_intentionally_retained') is True
            and evidence.get('final_sound_verified') is True, 'invalid retained-first-preset evidence')
    source_contract()
    tape = _TraceReplay(raw_trace)
    probe = FirstPresetProbe(tape, evidence['firmware_version'], clock=tape.clock)
    backup = probe.capture()
    require(backup['state'] == retained.get('state') and backup['FXT']['lines'] == retained.get('FXT',{}).get('lines'),
            'first-preset raw trace differs from state/FXT backup')
    trial = evidence['trial']
    result = probe.create_first(slot=trial['slot'], marker_selection=trial['marker_selection'])
    require(tape.position == len(tape.exchanges) and not tape.pending and not probe.wire.buffer,
            'first-preset trace has extra or unconsumed wire data')
    require(result == trial, 'first-preset trial differs from raw-trace replay')
    observed = [o for o in result['observations'] if o['request'].split()[0] in app.FAMILY_COMMANDS]
    require(observed == evidence.get('representative_observations'), 'first-preset observations differ from replay')
    actual = {}
    for o in observed: actual.setdefault(o['request'].split()[0], set()).add(o['request'])
    actual = {k:sorted(v) for k,v in sorted(actual.items())}
    require(actual == evidence.get('physically_exercised_requests'), 'first-preset exercised requests differ from replay')
    return True


def run_create(args, *, enumerate_fn=None, open_fn=None, clock=time.monotonic):
    contract, profile = source_contract(), app.load_profile(args.firmware_manifest)
    require(profile['hardware_verified'] and profile['capabilities']['read'], 'boot-verified read profile required')
    paths = [Path(p).resolve() for p in (args.log,args.backup,args.report)]
    require(len(set(paths)) == 3 and all(p.is_relative_to(ROOT) and p.parent.is_dir() and not p.exists() for p in paths),
            'three distinct new trace/backup/report files inside workspace required')
    selection = {'operation':args.operation, 'block_id':args.block, 'parameter_index':args.parameter}
    hardware, transport, probe = open_fn is None, None, None
    summary = {'roundtrip_passed':False, 'restoration_verified':False, 'preset_intentionally_retained':False}
    journal = readonly.Journal(paths[0], clock)
    try:
        journal('first_preset_start',expected_image_sha256=profile['image_sha256'],
                hardware_executed=hardware,protocol=contract,image_hash_attested_by_device=False)
        selected = readonly.select_port((enumerate_fn or readonly.enumerate_ports)(),args.port)
        transport = (open_fn or readonly.SerialTransport.open)(selected['device'])
        probe = FirstPresetProbe(transport,profile['firmware_version'],log=journal,clock=clock)
        backup = probe.capture()
        backup.update(image_sha256=profile['image_sha256'],transport='usb-cdc',hardware_executed=hardware)
        with paths[1].open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(backup,stream,indent=2);stream.write('\n');stream.flush()
        summary = probe.create_first(slot=args.slot,marker_selection=selection)
        journal('first_preset_complete',**summary)
    except Exception as exc:
        summary = copy.deepcopy(probe.result) if probe else summary
        summary['error'] = str(exc)
        journal('first_preset_failed',**summary)
    finally:
        try:
            if transport is not None:
                try: transport.close();journal('port_closed')
                except Exception as exc:
                    summary.update(roundtrip_passed=False,close_error=str(exc))
                    journal('port_close_failed',error=str(exc))
        finally: journal.close()
    hardware = hardware and probe is not None and probe.wire.identity is not None
    if summary.get('roundtrip_passed'):
        report = first_evidence(summary,profile,trace=mutation.file_reference(paths[0]),
                                backup=mutation.file_reference(paths[1]),hardware_executed=hardware)
    else:
        report = {'schema':1,'kind':'mini-app-first-preset-incomplete','target':'tank-mini','transport':'usb-cdc',
                  'hardware_executed':hardware,'trial':summary,'trace':mutation.file_reference(paths[0]),
                  'backup':mutation.file_reference(paths[1]) if paths[1].exists() else None,
                  'restoration_verified':False,'physically_exercised_requests':{}}
    with paths[2].open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action');sub.add_parser('plan')
    command = sub.add_parser('create',help='explicitly create and retain one free-slot HyperRig_Test preset')
    command.add_argument('--port',required=True)
    command.add_argument('--firmware-manifest',type=Path,required=True)
    command.add_argument('--slot',type=int,help='free slot0..31; default first free slot in complete PLIST')
    command.add_argument('--operation',choices=('auto','FXP','FXE','GAIN'),default='auto')
    command.add_argument('--block',type=int);command.add_argument('--parameter',type=int)
    for name in ('log','backup','report'):command.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args(argv)
    try:
        if args.action in (None,'plan'):
            result = {'device_io':False,'enumerated':False,'contract':source_contract(),
                      'sequence':['capture FXS/FXT/PLIST/SNAPS plus sound settings','recheck unchanged state and free slot',
                                  'PSAVE HyperRig_Test','live marker then PLOAD/readback',
                                  'SNAPSAVE0','second live marker then PLOAD/SNAP0/readback',
                                  'verify final sound and retain the new preset'],
                      'restoration_verified':False,'PDEL_available':False}
        else: result = run_create(args)
        print(json.dumps(result,indent=2))
        return 0 if args.action in (None,'plan') or result.get('kind') == KIND else 1
    except (Error,ValueError,OSError,KeyError) as exc:
        print(json.dumps({'error':str(exc),'automatic_retry':False}),file=sys.stderr);return 1


if __name__ == '__main__':
    raise SystemExit(main())
