"""Read retained HYRN B after inspect6's lost FD71 reply; no RAM/NOR writes.

Default is offline. --execute uses only FC70/FC73/FD71, with bounded attested
read/status recovery. The entire NOR must match the already reconciled writer
state before uncertainty is cleared. No upload, jump, reset or SPI init.
"""
import argparse
import ctypes
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import site
import sys
import time

# The pinned broker uses -I. Existing local transport dependencies are installed
# in this user's site; add that explicit directory without loading arbitrary .pth.
user_site=site.getusersitepackages()
if isinstance(user_site,str) and user_site not in sys.path:sys.path.append(user_site)
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'analysis/hardware'),str(ROOT/'tools'),str(ROOT)]
from read_mini_partial_install6 import prepare_inspection as stopped_prepare,require,B
from tools.build_mini_boot import verify_recorded_hashes
from tools.mini_host_journal import atomic_write_json
from tools.mini_windows_quiet import RomDiskAttestation,QuietBufferedRomTransport
from tools.probe_mini_recovery import MiniNorSession
from tools.mini_nor_read_recovery import NorReadRecoveryTransport,parse_status
from run_mini_receive_stress import attach_native_diagnostic

PREFIX='analysis/hardware/mini-partial-inspect6-recovered'
OUT,TRACE,RECOVERY=(ROOT/(PREFIX+suffix) for suffix in ('-run.json','-trace.jsonl','-read-recovery.jsonl'))
PINS=ROOT/(PREFIX+'-pins.json')
DUMP=ROOT/'artifacts/my-mini-flash/first-install/full-partial6.bin'
LAST_COUNTER,READ_BYTES=0xE3600,512


def now():return datetime.now(timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()


def prepare():
    pins=json.loads(PINS.read_bytes());verify_recorded_hashes(pins)
    _,installation,backup,artifact,payload,_,expected_images,old_writer=stopped_prepare()
    path=ROOT/'analysis/hardware/mini-partial-inspect6-run.json';prior_raw=path.read_bytes();prior=json.loads(prior_raw)
    verify_recorded_hashes(prior['source_pins'])
    require(prior.get('finished_utc') and prior['error_phase']=='full_NOR_read'
            and prior['program_outcome']=='prior_state_retained' and prior['writer_software_state_reconciled']
            and prior['known_live_slot']==B and not prior['jump_outcome_unknown'] and prior['jump_attempts']==1
            and prior['firmware_write_this_step'] is False and prior['reset_performed'] is False,
            'inspect6 did not reconcile the prior writer and start only readerB')
    raw=(ROOT/'analysis/hardware/mini-partial-inspect6-writer-audit.bin').read_bytes()
    require(raw==old_writer and sha(raw)==prior['writer_audit']['record_sha256']
            and prior['writer_audit']['sequence']==33,'retained fresh writer proof differs')
    reader=prior['reader_session'];spi=prior['reader_SPI']
    require(reader['slot']==B and reader['readback_verified'] and reader['reader_version']==1
            and reader['rom_readback_sha256']==reader['image_sha256']==artifact['flat_sha256']
            and spi=={'jedec_hex':'eb6014','capacity':0x100000,'baud_divisor':15,
                      'sys_div':0,'clk_con2':128,'successful_read_bytes':0},'retained HYRN/SPI provenance differs')
    rows=[json.loads(line) for line in (ROOT/'analysis/hardware/mini-partial-inspect6-trace.jsonl').read_text().splitlines()]
    require(len(rows)%2==0,'inspect6 trace has unmatched command')
    for before,after in zip(rows[::2],rows[1::2]):
        require(before['state']=='before' and after['state'] in ('after','error') and before['cdb']==after['cdb'],
                'inspect6 trace pairing differs')
    faults=[row for row in rows if row['state']=='error']
    require(len(faults)==1 and faults[0]==rows[-1]
            and rows[-1]['cdb']=='fd71000e36000200ffffffffffffffff'
            and rows[-1]['details']['win32_error']==31,'last failed FD71 witness differs')
    expected=expected_images['prior_state_retained']
    reads=[row for row in rows if row['state']=='after' and row['cdb'].startswith('fd71')]
    require(len(reads)==LAST_COUNTER//512,'partial physical read count differs')
    for address,row in zip(range(0,LAST_COUNTER,512),reads):
        require(row['cdb']=='fd71'+address.to_bytes(4,'big').hex()+'0200'+'ff'*8
                and row['response_bytes']==512 and row['response_sha256']==sha(expected[address:address+512]),
                'successful prior read differs from predicted partial NOR')
    statuses=[row for row in rows if row['state']=='after' and row['cdb'].startswith('fc73')]
    require(len(statuses)==len(reads)+1,'partial read status count differs')
    for count,row in zip(range(0,LAST_COUNTER+1,512),statuses):
        status=parse_status(bytes.fromhex(row['response_hex']))
        require(status=={'sys_div':0,'clk_con2':128,'successful_read_bytes':count},'previous reader counter/clock differs')
    require(rows[-3]['response_hex']=='fc7300010000000000000080000e3600',
            'immediately preceding physical status differs')
    permitted={'fc78','fd88','fb06','fd07','fb08','fc70','fc72','fc73','fd71'}
    require(all(row['cdb'][:4] in permitted for row in rows),'prior inspection contains unexpected operation')
    metadata=prior['reader_open_metadata']['attestation']
    attestation=RomDiskAttestation(metadata['path'],metadata['pnp_id'],metadata['usb_ancestor'],
        tuple(metadata['chain']),metadata['model'],metadata['interface_path'],metadata['last_arrival_filetime'])
    require(attestation.summary()==metadata,'retained PnP/arrival attestation changed')
    return pins,backup,expected,prior_raw,attestation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group();action.add_argument('--check-only',action='store_true');action.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    pins,backup,expected,prior_raw,attestation=prepare()
    if not args.execute:
        print(json.dumps({'preflight':'pass','device_io':False,'expected_full_sha256':sha(expected),
            'retained_reader_counters':[LAST_COUNTER,LAST_COUNTER+READ_BYTES],
            'allowed_commands':['FC70','FC73','FD71'],'upload':False,'jump':False,'SPI_init':False,'reset':False}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(),'bounded SPT helper requires elevation')
    require(not any(path.exists() for path in (OUT,OUT.with_suffix('.json.tmp'),TRACE,RECOVERY,DUMP)),
            'one-shot recovered inspection already attempted')
    result={'phase':'confirm_retained_reader','started_utc':now(),'source_pins':pins,
        'runner_sha256':sha(Path(__file__).read_bytes()),'prior_inspection_sha256':sha(prior_raw),
        'known_live_slot':B,'jump_outcome_unknown':False,'jump_attempts':0,'firmware_write_this_step':False,
        'upload_performed':False,'SPI_initialization_performed':False,'reset_performed':False,
        'mutation_completion_unknown':True,'expected_full_sha256':sha(expected),'max_read_recoveries':8}
    wrapper=reader=transport=None
    def save():atomic_write_json(OUT,result)
    def append(path,event):
        with path.open('a',encoding='utf-8',newline='\n') as stream:
            stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
    def open_logged():
        nonlocal attestation
        current=QuietBufferedRomTransport(attestation,slot=B,profile='nor-reader')
        attestation=current.attestation
        try:
            result.setdefault('transport_handles',[]).append(current.open_metadata);save()
            native=attach_native_diagnostic(current);original=current.exchange
            def exchange(cdb,data_out=None,read_length=0):
                require(data_out is None and cdb[:2] in (b'\xfc\x70',b'\xfc\x73',b'\xfd\x71'),
                        'retained reader permits no upload/jump/init/OUT')
                time.sleep(.005)
                event={'state':'before','utc':now(),'cdb':cdb.hex(),'read_length':read_length,'out_bytes':0}
                append(TRACE,event)
                try:raw=original(cdb,read_length=read_length)
                except Exception as error:
                    event.update(state='error',finished_utc=now(),error=repr(error),details=getattr(error,'details',{}),
                        native_transfer=current.last_transfer,native_failure_observation=native.last_failure)
                    append(TRACE,event);raise
                event.update(state='after',finished_utc=now(),response_bytes=len(raw),response_sha256=sha(raw),
                             native_transfer=current.last_transfer)
                if len(raw)<=128:event['response_hex']=raw.hex()
                append(TRACE,event);return raw
            current.exchange=exchange
            return current
        except BaseException:current.close();raise
    save()
    try:
        transport=open_logged()
        wrapper=NorReadRecoveryTransport(transport,log=lambda item:append(RECOVERY,item),
                                         reopen_factory=open_logged,max_recoveries=8)
        reader=MiniNorSession(wrapper,slot=B)
        result['retained_reader']=wrapper.attach_retained(reader,expected_counters=(LAST_COUNTER,LAST_COUNTER+512),
                                                         expected_clock=(0,128))
        result['initial_reader_counter']=reader.successful_bytes
        result['phase']='full_NOR_read';save()
        def progress(done,total):
            if done%65536==0:result['progress']={'bytes':done,'total':total};save()
        data=reader.read_flash(0,0x100000,progress=progress)
        require(reader.successful_bytes==result['initial_reader_counter']+len(data)+wrapper.lost_read_bytes,
                'final physical read counter does not include exactly all completed/lost reads')
        with DUMP.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        result.update(dump_path=DUMP.relative_to(ROOT).as_posix(),dump_sha256=sha(data),
            final_reader_counter=reader.successful_bytes,final_reader_status_hex=wrapper.last_status_raw.hex(),
            matches_expected_partial=data==expected,
            changed_sectors=[a for a in range(0,0x100000,4096) if data[a:a+4096]!=backup[a:a+4096]])
        require(data==expected,'complete NOR differs from reconciled writer proof')
        result.update(phase='partial_image_verified',mutation_completion_unknown=False)
    except Exception as error:
        result.update(error_phase=result['phase'],error_type=type(error).__name__,error=str(error))
    finally:
        if wrapper is not None:wrapper.close();result['read_recovery_final']=wrapper.summary()
        elif transport is not None:transport.close()
        if reader is not None:result['last_confirmed_reader_counter']=reader.successful_bytes
        result['finished_utc']=now();save()
    print(json.dumps({key:result.get(key) for key in ('phase','error','dump_sha256','matches_expected_partial','final_reader_counter')}))


if __name__=='__main__':main()
