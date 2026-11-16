"""Independent offline verification of the one-sector MINI PC-limit upgrade.

No device API or hardware runner is invoked. The original installation
inspector remains frozen; only its protocol/history parsers are reused.
Runtime partitions are compared with the fresh preimage, not reset to stock.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import inspect_mini_installed as history
from tools import plan_mini_pc_limit_upgrade as upgrade
from tools.mini_host_journal import read_shared_bytes

require, sha, crc = history.require, history.sha, history.crc
APP_START, APP_END, CAPACITY = 0x4000, 0x82000, 0x100000
OLD_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
NEW_SHA = '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c'
DEFAULT_RUN = ROOT/'analysis/hardware/mini-pc-limit-install-run.json'
FROZEN_PARSERS = {
    'tools/inspect_mini_installed.py': '8cc89c335c33ecf5aacdbc6a56f1e7f16f26dfa8d49c004bb217aec3b57bdbe9',
    'tools/build_mini_app_writer.py': '39941618458365ca9c151a33e468a8b83e531f700fd7bfb3aedb581dd61c2ec2',
}


def local(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), 'retained input must stay inside workspace')
    return path


def ref(path, raw):
    return {'path': local(path).relative_to(ROOT).as_posix(), 'sha256': sha(raw), 'bytes': len(raw)}


def compare_images(stock, before, candidate, after):
    require(all(type(x) is bytes for x in (stock, before, candidate, after)), 'immutable image bytes required')
    require(len(stock) == len(before) == len(after) == CAPACITY and len(candidate) == APP_END-APP_START,
            'complete NOR and application extents required')
    require(sha(stock) == upgrade.BACKUP_SHA and sha(before[APP_START:APP_END]) == OLD_SHA
            and sha(candidate) == NEW_SHA, 'unit backup, current v2 or candidate v3 differs')
    require(before[:APP_START] == stock[:APP_START] and before[0xFF000:] == stock[0xFF000:],
            'unit SPL or keymac differs from stock backup')
    require(after == before[:APP_START]+candidate+before[APP_END:],
            'full NOR differs from v3 or current runtime partitions')
    sectors = [a for a in range(0, CAPACITY, 4096) if before[a:a+4096] != after[a:a+4096]]
    require(sectors == [APP_START], 'upgrade changed more than sector0x4000')
    regions = []
    for lo, hi, name in history.REGIONS:
        regions.append({'name': name, 'range': [lo, hi], 'sha256': sha(after[lo:hi]),
                        'bytes': hi-lo, 'unchanged_from_fresh_read': True,
                        'differs_from_stock_backup': before[lo:hi] != stock[lo:hi]})
    return {'application_exact': True, 'candidate_sha256': sha(candidate),
            'full_NOR_sha256': sha(after), 'changed_sectors': sectors,
            'external_regions_unchanged_from_fresh_read': True, 'preserved_regions': regions}


def writer_audits(journal, before, candidate, *, slot, build_tag):
    """Replay actual successful CDBs and each raw audit against a virtual NOR.

    The model uses wire addresses/CRCs and measured poll deltas. It never uses
    the installer's expected-state dictionaries or its claimed final counters.
    """
    memory = bytearray(before)
    expected = dict.fromkeys(('phase','token','sequence','sector','page','preimage_crc32',
        'target_crc32','page_crc32','last_crc32','jedec','wren_attempts','erase_attempts',
        'program_attempts','read_bytes','status_polls','page_bitmap','staged','echoed'), 0)
    expected['raw_receive_return'] = -2147483648
    pending = last_reply = None
    audit_due = mutation_due = False
    audits, pages, erase_count, finished = [], [], 0, False

    def status(opcode):
        return opcode.to_bytes(2,'big')+bytes((0,expected['phase']))+struct.pack('>III',
            expected['token'],expected['sequence'],expected['last_crc32'])

    for row in journal:
        event = row['event']
        require(event != 'terminal_error', 'terminal writer journal cannot verify')
        if event == 'command_intent':
            require(pending is None and not audit_due, 'missing command reply/raw audit')
            require(not mutation_due or row['opcode'] == 'fd88', 'mutation was not immediately audited')
            pending = row
        elif event == 'command_reply':
            require(pending is not None and pending['opcode'] == row['opcode'], 'unpaired writer reply')
            command = pending; pending = None
            cdb = bytes.fromhex(command['cdb_hex']); op = int.from_bytes(cdb[:2],'big')
            require(len(cdb) == 16, 'writer CDB extent differs')
            raw = None
            if op == 0xFC78:
                raw = b'\xfc\x78HYW1\1\1'+struct.pack('>II',slot,32768)
            elif op == 0xFC79:
                require(expected['phase'] == 0, 'duplicate SPI init')
                expected.update(phase=1,jedec=0xEB6014,last_crc32=0xEB6014)
                raw = status(op)
            elif op == 0xFD7F:
                address, length = struct.unpack_from('>IH',cdb,2)
                require(APP_START <= address < address+length <= APP_END and 0 < length <= 512,
                        'writer read outside application')
                raw = bytes(memory[address:address+length])
                expected['read_bytes'] += length; expected['last_crc32'] = crc(raw)
            elif op == 0xFC7A:
                address, old_crc, new_crc = struct.unpack_from('>III',cdb,2)
                require(address == APP_START and expected['phase'] == 1 and
                        (old_crc,new_crc) == (crc(before[APP_START:APP_START+4096]),crc(candidate[:4096])),
                        'ARM sector/preimage/candidate CRC differs')
                expected.update(phase=2,token=1,sequence=1,sector=address,
                    preimage_crc32=old_crc,target_crc32=new_crc,last_crc32=old_crc)
                expected['read_bytes'] += 4096; raw = status(op)
            elif op in (0xFB7C,0xFC7B,0xFC7D,0xFC80):
                token, sequence, address = struct.unpack_from('>III',cdb,2)
                require(token == expected['token'] == 1 and sequence == expected['sequence']+1,
                        'consumed or wrong operation sequence/token')
                expected['sequence'] = sequence
                if op == 0xFB7C:
                    require(expected['phase'] in (2,3) and not expected['staged'] and
                            address == history.page_order(APP_START)[len(pages)], 'stage page order differs')
                    page = candidate[address-APP_START:address-APP_START+256]
                    require(command['data_out_sha256'] == sha(page+struct.pack('>I',crc(page))),
                            'staged OUT260 does not contain exact candidate page+CRC')
                    expected.update(phase=4,page=address,page_crc32=crc(page),last_crc32=crc(page),
                                    staged=1,echoed=0,raw_receive_return=260); raw = b''
                elif op == 0xFC7B:
                    require(address == APP_START and not erase_count and expected['staged'] == expected['echoed'] == 1,
                            'erase without exact pre-staged/echoed page or repeated erase')
                    memory[address:address+4096] = b'\xff'*4096; erase_count += 1
                    expected['wren_attempts'] += 1; expected['erase_attempts'] += 1
                    expected['read_bytes'] += 8192; expected['last_crc32'] = crc(b'\xff'*4096)
                    mutation_due = True; raw = status(op)
                elif op == 0xFC7D:
                    require(erase_count == 1 and expected['phase'] == 4 and
                            expected['staged'] == expected['echoed'] == 1 and address == expected['page']
                            and bytes(memory[address:address+256]) == b'\xff'*256, 'unsafe/repeated page program')
                    page = candidate[address-APP_START:address-APP_START+256]
                    memory[address:address+256] = page; pages.append(address)
                    expected.update(phase=3,staged=0,echoed=0,last_crc32=crc(page))
                    expected['page_bitmap'] |= 1 << ((address-APP_START)//256)
                    expected['wren_attempts'] += 1; expected['program_attempts'] += 1
                    expected['read_bytes'] += 512; mutation_due = True; raw = status(op)
                else:
                    require(not finished and address == APP_START and expected['page_bitmap'] == 65535
                            and not expected['staged'] and memory[address:address+4096] == candidate[:4096],
                            'FINISH without complete candidate sector')
                    finished = True; expected.update(phase=5,token=0,last_crc32=crc(candidate[:4096]))
                    expected['read_bytes'] += 4096; raw = status(op)
            elif op == 0xFD87:
                token, sequence, address = struct.unpack_from('>III',cdb,2)
                require((token,sequence,address) == (expected['token'],expected['sequence'],expected['page'])
                        and expected['staged'] == 1 and not expected['echoed'], 'RAM echo state differs')
                raw = candidate[address-APP_START:address-APP_START+256]; expected['echoed'] = 1
            elif op == 0xFC7E: raw = status(op)
            elif op == 0xFD88: audit_due = True
            else: raise ValueError('unexpected writer journal opcode: '+hex(op))
            if raw is not None:
                require(row['bytes'] == len(raw) and row['sha256'] == sha(raw),
                        'actual command reply differs from modeled NOR/status/page')
            last_reply = row
        elif event == 'audit_raw':
            require(audit_due and last_reply['opcode'] == 'fd88', 'raw audit lacks its received FD88')
            raw = bytes.fromhex(row['record_hex'])
            require(sha(raw) == row['sha256'] == last_reply['sha256'] and last_reply['bytes'] == 128,
                    'raw audit and received reply hash differ')
            item = history.validate_audit_record(raw,base=slot,build_tag=build_tag,expected_mutations_enabled=True)
            require(item['error'] == 0 and item['rx_guards_ok'] == item['stack_guards_ok'] == 1
                    and not item['sr1'] & 0x7F and not item['sr2'] & 0x40, 'target error/guard/WIP/WEL/protection')
            if mutation_due:
                require(1 <= item['status_polls']-expected['status_polls'] <= 65536, 'WIP poll budget differs')
                expected['status_polls'] = item['status_polls']; mutation_due = False
            require(all(item[name] == value for name,value in expected.items()), 'raw target state differs from CDB replay')
            require(item['stack_observed_bytes'] > 0 if expected['jedec'] else item['stack_observed_bytes'] == 0,
                    'entry/initialized private stack observation differs')
            if not expected['jedec']: require(item['sr1'] == item['sr2'] == 0, 'SPI accessed before explicit init')
            audits.append(item); audit_due = False
    require(pending is None and not audit_due and not mutation_due and finished and audits,
            'incomplete writer history')
    require(pages == history.page_order(APP_START) and expected['phase'] == 5 and expected['token'] == 0
            and expected['sequence'] == 35 and expected['wren_attempts'] == 17
            and expected['erase_attempts'] == 1 and expected['program_attempts'] == 16
            and expected['read_bytes'] == 2*len(candidate)+40960,
            'completed one-sector writer counters/state differ')
    return {'raw_records_checked':len(audits),'final_raw_audit':audits[-1],
            'erase':1,'program':16,'wren':17,'program_order':pages,
            'all_audits_match_wire_replay':True,'virtual_NOR_matches_candidate':bytes(memory[APP_START:APP_END]) == candidate}


def split_reader_evidence(trace, events):
    """Both fresh HYRN sessions share one log; preserve chronology explicitly."""
    starts = [i for i,row in enumerate(events) if row['event'] == 'nor_reader_bound']
    require(len(starts) == 2 and starts[0] == 0, 'two fresh reader binding records required')
    writer = next((i for i,row in enumerate(trace) if row['stage'] == 'writer'),None)
    after = next((i for i,row in enumerate(trace) if row['stage'] == 'full_after'),None)
    require(writer is not None and after is not None and writer < after and writer % 2 == after % 2 == 0,
            'reader/writer/reader transport chronology differs')
    initial = [dict(row,stage='full_after') if row['stage'] == 'full_before' else row for row in trace[:writer]]
    return initial, trace[writer:], (events[:starts[1]],events[starts[1]:])


def bind_writer_replies(journal, trace):
    """Every journal reply must have a real successful response in wire order.

    Recovery identity/audit probes may occur between the original journaled
    request and its actual reply; they never substitute a synthetic response.
    """
    wire = [row for row in trace if row['state'] == 'after' and
            row['stage'] in ('writer','writer-read-recovery-reopen')]
    position, pending = 0, None
    for row in journal:
        if row['event'] == 'command_intent': pending = row
        elif row['event'] == 'command_reply':
            require(pending is not None, 'unpaired journal reply')
            while position < len(wire):
                actual = wire[position]; position += 1
                if (actual['cdb'] == pending['cdb_hex'] and actual['response_sha256'] == row['sha256']
                        and actual['response_bytes'] == row['bytes']): break
            else: raise ValueError('writer reply/raw audit has no actual ordered transport response')
            pending = None
    require(pending is None, 'missing final writer reply')


def inspect_bundle(run_path=DEFAULT_RUN):
    run_path = local(run_path); run_raw = read_shared_bytes(run_path); run = json.loads(run_raw)
    require(run.get('finished_utc') and not run.get('error') and
            run.get('phase') == 'upgraded_verified_waiting_for_normal_boot', 'completed successful upgrade required')
    require(run['installed_image_verified'] and run['full_NOR_verified'] and run['known_live_slot'] == 0x1C28000
            and not run['jump_outcome_unknown'] and not run['mutation_completion_unknown']
            and run['MCN_pause_closed'] and run['MCN_explicitly_reenabled']
            and run['automatic_reset'] is False and run['fresh_ROM_verified'], 'run ended with unresolved lifecycle/cleanup')
    require(run['candidate_sha256'] == NEW_SHA, 'run identifies another candidate')
    pins = run['source_pins']
    for source_set in (pins,FROZEN_PARSERS):
        for name,digest in source_set.items():
            require(sha(local(ROOT/name).read_bytes()) == digest, 'recorded/frozen source changed: '+name)
    before_path, after_path = (local(ROOT/run[key]['path']) for key in ('full_before','full_after'))
    before, after = before_path.read_bytes(), after_path.read_bytes()
    require(sha(before) == run['full_before']['sha256'] and sha(after) == run['full_after']['sha256'], 'dump binding differs')
    planned = upgrade.prepare_upgrade(before_path,expected_full_sha256=sha(before),expected_target_sha256=NEW_SHA)
    plan_path = local(ROOT/run['new_preimage_plan']); plan_raw = plan_path.read_bytes()
    require(plan_raw == planned.plan_bytes and run['installation'] == planned.installation.summary()
            and run['upgrade_plan']['path'] == plan_path.relative_to(ROOT).as_posix()
            and run['upgrade_plan']['sha256'] == sha(plan_raw), 'run plan or operational artifact binding differs')
    candidate = planned.installation.candidate; candidate_path = upgrade.NEW_DIR/'hyperrig-mini.app-area.bin'
    stock_path = local(ROOT/upgrade.BACKUP_PATH); stock = stock_path.read_bytes()
    images = compare_images(stock,before,candidate,after)
    require(run_path.name.endswith('-run.json'), 'named run/log bundle required')
    prefix = str(run_path)[:-len('-run.json')]
    paths = {name:Path(prefix+suffix) for name,suffix in (
        ('journal','-journal.jsonl'),('trace','-trace.jsonl'),('recovery','-read-recovery.jsonl'),
        ('nor','-nor-read-recovery.jsonl'),('mcn','-mcn.jsonl'))}
    raw_logs = {key:(path.read_bytes() if path.exists() else b'') for key,path in paths.items()
                if key == 'recovery' or path.exists()}
    require(set(raw_logs) == set(paths), 'required transport/audit/NOR/MCN log missing')
    logs = {key:[json.loads(line) for line in raw.splitlines()] for key,raw in raw_logs.items()}
    mcn = [row['event'] for row in logs['mcn']]
    require(mcn.count('mcn_disabled') == mcn.count('mcn_reenabled') == 1
            and mcn.index('mcn_disabled') < mcn.index('mcn_reenabled'), 'MCN actual disable/reenable record differs')
    recovery = {'summary':run['read_recovery_final'],'policy':run['read_recovery_policy'],
        'events':logs['recovery'],'slot':run['installation']['slot'],'build_tag':run['installation']['build_tag'],
        **{f'v{n}_source_pinned':f'tools/recover_mini_read_v{n}.py' in pins for n in (3,4,5,6)}}
    history.validate_v4_policy(recovery)
    initial, remaining, nor_events = split_reader_evidence(logs['trace'],logs['nor'])
    nor = []
    for label,events in zip(('full_before','full_after'),nor_events):
        nor.append({'summary':run[label+'_read_recovery'],'events':events,'slot':0x1C28000,
            'target_read_counter':run[label+'_target_read_counter'],
            'source_pinned':'tools/mini_nor_read_recovery.py' in pins})
    before_reads = history.inspect_final_nor_read(initial,before,nor[0])
    operations = history.inspect_history(logs['journal'],remaining,before,candidate,[APP_START],
        recovery=recovery,nor_recovery=nor[1],observed_nor=after)
    for label,proof in (('full_before',before_reads),('full_after',operations['final_NOR_read'])):
        require(run[label+'_lost_read_bytes'] == proof['lost_read_bytes'],
                'run lost-read count differs from actual NOR recovery trace')
    bind_writer_replies(logs['journal'],remaining)
    audits = writer_audits(logs['journal'],before,candidate,slot=planned.installation.slot,build_tag=planned.installation.build_tag)
    final = run['writer_final']
    require(not final['failed'] and final['phase'] == 'complete' and final['image_verified'] and final['preimage_verified']
            and not final['mutation_completion_unknown'] and final['verified_sectors'] == [APP_START]
            and not final['journal_error'] and final['ambiguous_operation'] is None
            and final['last_audit'] == audits['final_raw_audit'], 'writer summary differs from raw CDB/audit replay')
    for name,wanted in (('whole_preimage_verified',sha(before[APP_START:APP_END])),('application_verified',sha(candidate))):
        rows = [row for row in logs['journal'] if row['event'] == name]
        require(len(rows) == 1 and rows[0].get('sha256',rows[0].get('application_sha256')) == wanted,
                'complete application preimage/final verification missing')
    require(read_shared_bytes(run_path) == run_raw, 'completed run changed during independent inspection')
    inputs = {run_path:run_raw,plan_path:plan_raw,before_path:before,after_path:after,
              candidate_path:candidate,stock_path:stock,**{paths[key]:raw for key,raw in raw_logs.items() if paths[key].exists()}}
    return {'schema':1,'kind':'mini-pc-limit-upgrade-independent','verified':True,
        'run':ref(run_path,run_raw),'plan':ref(plan_path,plan_raw),'full_before':ref(before_path,before),
        'full_after':ref(after_path,after),'candidate':ref(candidate_path,candidate),**images,
        'writer_audit':audits,'history':operations,'initial_full_NOR_read':before_reads,
        'final_reader_counter':operations['final_NOR_read']['physical_read_counter'],
        'final_read_lost_bytes':operations['final_NOR_read']['lost_read_bytes'],
        'inputs':{local(path).relative_to(ROOT).as_posix():sha(raw) for path,raw in inputs.items()},
        'source_sha256':{local(path).relative_to(ROOT).as_posix():sha(Path(path).read_bytes()) for path in
                         (Path(__file__),Path(upgrade.__file__),Path(history.__file__))},
        'source_pins_match':True,'finished_utc':run['finished_utc'],'boot_attempted':False,
        'audio_verified':False,'application_execution_proven':False,'power_loss_atomicity_proven':False,
        'device_io_performed_by_verifier':False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect',action='store_true'); parser.add_argument('--run',type=Path,default=DEFAULT_RUN)
    parser.add_argument('--output',type=Path); args = parser.parse_args(argv)
    if not args.inspect:
        require(args.output is None, '--output requires completed-run inspection')
        print(json.dumps({'device_io':False,'logs_read':False})); return
    report = inspect_bundle(args.run)
    if args.output:
        with local(args.output).open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(json.dumps(report,indent=2)+'\n')
    else: print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
