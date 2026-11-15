"""Measure a per-device Windows MCN pause, with retained reader B unchanged."""
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.mini_windows_mcn import MiniMediaChangePause
from tools.probe_mini_recovery import discover_windows_rom_disks

OUT=ROOT/'analysis/hardware/mini-mcn-probe-run.json'
B=0x1c28000
def now():return datetime.now(timezone.utc).isoformat()
def require(ok,message):
    if not ok:raise ValueError(message)

def main():
    require(ctypes.windll.shell32.IsUserAnAdmin(),'bounded Windows helper needs elevation')
    require(not OUT.exists(),'MCN probe already attempted')
    prior=json.loads((ROOT/'analysis/hardware/mini-partial-inspect3-run.json').read_text())
    require(prior['phase']=='partial_image_verified' and prior['known_live_slot']==B
            and prior['progress']=={'bytes':1048576,'total':1048576},'retained reader B not established')
    result={'phase':'prepare','started_utc':now(),'NOR_writes':False,'reset':False,
            'SCSI_data_write':False,'source_sha256':{},'mcn_events':[],'known_live_slot':B}
    for name in ['tools/mini_windows_mcn.py','tools/mini_windows_spt.py','tools/mini_windows_aligned.py',
                 'tools/probe_mini_recovery.py','analysis/hardware/probe_mini_mcn.py']:
        result['source_sha256'][name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    def save():
        temp=OUT.with_suffix('.json.tmp')
        temp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
        os.replace(temp,OUT)
    def log(event):result['mcn_events'].append(event);save()
    identity=b'\xfc\x70HYRN\x01\x03'+B.to_bytes(4,'big')+(32768).to_bytes(4,'big')
    save()
    try:
        disks=discover_windows_rom_disks();require(len(disks)==1,'ROM not unique')
        with WindowsBufferedRomTransport(disks[0]['path'],slot=B,profile='nor-reader') as transport:
            require(transport.exchange(b'\xfc\x70'+b'\xff'*14,read_length=16)==identity,'retained reader changed')
            before=transport.exchange(b'\xfc\x73'+b'\xff'*14,read_length=16)
            require(before[:4]==b'\xfc\x73\0\1' and int.from_bytes(before[12:16],'big')==0x100000,'reader counter changed')
            result.update(path=disks[0]['path'],inquiry=transport.inquiry,phase='baseline_16_seconds',
                          baseline_started_utc=now());save()
            time.sleep(16)
            result.update(baseline_finished_utc=now(),phase='pause_MCN_24_seconds');save()
            with MiniMediaChangePause(transport,log=log):
                result['during_started_utc']=now();save()
                deadline=time.monotonic()+24;count=0
                while time.monotonic()<deadline:
                    require(transport.exchange(b'\xfc\x70'+b'\xff'*14,read_length=16)==identity,'reader identity changed during MCN pause')
                    count+=1;time.sleep(.1)
                result.update(during_finished_utc=now(),identity_queries=count);save()
            result.update(phase='restored_16_seconds',restored_started_utc=now());save()
            time.sleep(16)
            result['restored_finished_utc']=now()
            after=transport.exchange(b'\xfc\x73'+b'\xff'*14,read_length=16)
            require(after==before,'reader status/counter changed')
            result.update(phase='MCN_pause_control_completed',reader_status_unchanged=True,
                          transport_identity_verified=True,MCN_explicitly_reenabled=True)
    except Exception as error:
        result.update(error_phase=result['phase'],error_type=type(error).__name__,error=str(error))
    finally:
        result['finished_utc']=now();save()
    print(json.dumps({k:result.get(k) for k in ['phase','error','identity_queries','MCN_explicitly_reenabled']}))

if __name__=='__main__':main()
