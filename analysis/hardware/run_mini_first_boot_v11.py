"""One normal software boot to CDC after the v3 upgrade is fully verified.

The user requested desktop communication and cannot press the footswitches.
Buttons are assumed released, never recorded as confirmed or tested. The
held-button recovery trial remains untested. No serial port is opened here;
the separate v3 WebSerial editor performs the first handshake. No retry, hub
restart, NOR write or second reset occurs. Import/check-only do no device I/O.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import site

# Python -I in the session broker omits this PC's existing pyserial install.
sys.path.append(site.getusersitepackages())

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT)]
from tools.build_mini_boot import verify_recorded_hashes
from tools.probe_mini_recovery import (discover_windows_rom_disks, MiniRamSession,
                                      validate_reset_artifact)
from tools.mini_windows_spt import WindowsBufferedRomTransport
from tools.mini_host_journal import atomic_write_json, read_shared_bytes
from tools import probe_mini_app as readonly

A, B = 0x1C20000, 0x1C28000
INSTALL_RUN = ROOT / 'analysis/hardware/mini-pc-limit-install-run.json'
PINS = ROOT / 'analysis/hardware/mini-first-boot-v11-pins.json'
MCN_LOG = ROOT / 'analysis/hardware/mini-pc-limit-install-mcn.jsonl'
INDEPENDENT = ROOT / 'research/mini-pc-limit-install-independent.json'
PLAN = ROOT / 'build/mini-pc-limit-install/upgrade-plan.json'
FULL_BEFORE = ROOT / 'artifacts/my-mini-flash/pc-limit-v3/full-before.bin'
FULL_AFTER = ROOT / 'artifacts/my-mini-flash/pc-limit-v3/full-after.bin'
CANDIDATE = ROOT / 'build/hyperrig-mini-audio-v3/hyperrig-mini.app-area.bin'
EXPECTED_CANDIDATE_SHA = '9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c'
EXPECTED_PREVIOUS_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
BASE_PROFILE = ROOT / 'build/hyperrig-mini-audio-v3/firmware-manifest.json'
EXPECTED_PROFILE_SHA = 'd901cc0d673b7f477bc9000be16d95d195b916ffb4e26f512ed00048b6c27deb'
EXPECTED_VERSION = 'tankm_fw M5.71 rel ble'


def require(condition, message):
    if not condition: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def load(name): return json.loads((ROOT / name).read_text(encoding='utf-8'))


def arrivals():
    script = r'''
$ErrorActionPreference = 'Stop'
$items = @(foreach ($device in Get-PnpDevice -PresentOnly) {
    if ($device.InstanceId -like 'USB\VID_4C4A&PID_8057\*') {
        $arrival = (Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName DEVPKEY_Device_LastArrivalDate -ErrorAction Stop).Data
        [pscustomobject]@{instance_id=$device.InstanceId; arrival_utc=$arrival.ToUniversalTime().ToString('o')}
    }
})
ConvertTo-Json -InputObject $items -Compress
'''
    done = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                          capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    result = json.loads(done.stdout)
    require(isinstance(result, list), 'unexpected USB arrival metadata')
    return result


def require_final_mcn_cleanup(install):
    require(install.get('MCN_pause_started') is True and install.get('MCN_pause_closed') is True
            and install.get('MCN_explicitly_reenabled') is True
            and 'MCN_cleanup_error' not in install and install.get('finished_utc')
            and install.get('known_live_slot') == B and install.get('jump_outcome_unknown') is False,
            'v3 upgrade lacks final explicit MCN cleanup or retained reader B')
    events = [json.loads(line) for line in read_shared_bytes(MCN_LOG).decode('utf-8').splitlines() if line]
    require([item.get('event') for item in events] == [
        'mcn_open_intent', 'mcn_disable_intent', 'mcn_disabled',
        'mcn_enable_intent', 'mcn_reenabled', 'mcn_handle_closed'],
        'MCN log does not contain one complete matched disable/enable/close sequence')
    require(all(item.get('path') == install['ROM_disk']['path'] for item in events)
            and events[-1].get('close_ok') is True
            and events[-1].get('explicit_enable_succeeded') is True
            and events[-1].get('windows_file_object_cleanup_required') is False
            and events[-1].get('error') is None,
            'MCN final handle cleanup differs or failed')
    stamps = [datetime.fromisoformat(install['started_utc'])]
    stamps += [datetime.fromisoformat(item['utc']) for item in events]
    stamps.append(datetime.fromisoformat(install['finished_utc']))
    require(all(stamp.tzinfo is not None for stamp in stamps)
            and all(left <= right for left, right in zip(stamps, stamps[1:])),
            'MCN cleanup chronology is outside the completed installation')


def retained(path, pins):
    path = path.resolve()
    require(path.is_relative_to(ROOT), 'evidence must stay in the workspace')
    raw = read_shared_bytes(path)
    name = path.relative_to(ROOT).as_posix()
    require(pins.get(name) == sha(raw), 'actual boot evidence must be pinned: '+name)
    return raw, {'path': name, 'sha256': sha(raw)}


def check_ref(record, expected):
    require(isinstance(record, dict) and
            all(record.get(key) == value for key, value in expected.items()),
            'independent or installation evidence reference differs: '+expected['path'])


def validate_upgrade(pins):
    """Recheck completed evidence and the full byte relation without device I/O."""
    install_raw, install_ref = retained(INSTALL_RUN, pins)
    independent_raw, independent_ref = retained(INDEPENDENT, pins)
    plan_raw, plan_ref = retained(PLAN, pins)
    before, before_ref = retained(FULL_BEFORE, pins)
    after, after_ref = retained(FULL_AFTER, pins)
    _, mcn_ref = retained(MCN_LOG, pins)
    install, independent, plan = map(json.loads, (install_raw, independent_raw, plan_raw))
    candidate = read_shared_bytes(CANDIDATE)
    candidate_ref = {'path': CANDIDATE.relative_to(ROOT).as_posix(), 'sha256': sha(candidate)}
    require(sha(candidate) == EXPECTED_CANDIDATE_SHA and len(candidate) == 0x7E000,
            'exact v3 candidate required')
    require(install['phase'] == 'upgraded_verified_waiting_for_normal_boot'
            and install['full_NOR_verified'] is True and install['installed_image_verified'] is True
            and install['known_live_slot'] == B and install['jump_outcome_unknown'] is False
            and install['mutation_completion_unknown'] is False and not install.get('error')
            and install['backend'] == 'IOCTL_SCSI_PASS_THROUGH buffered'
            and install['installation']['candidate_sha256'] == EXPECTED_CANDIDATE_SHA
            and install['independent_full_validation']['application_verified'] is True
            and install['independent_full_validation']['external_regions_unchanged_from_fresh_read'] is True
            and install['independent_full_validation']['external_regions_restored_to_stock'] is False
            and install['independent_full_validation']['full_NOR_sha256'] == sha(after),
            'MCN-scoped v3 upgrade is not fully verified')
    require_final_mcn_cleanup(install)
    check_ref(install['full_before'], before_ref)
    check_ref(install['full_after'], after_ref)
    require(len(before) == len(after) == 0x100000
            and sha(before[0x4000:0x82000]) == EXPECTED_PREVIOUS_SHA
            and after == before[:0x4000]+candidate+before[0x82000:],
            'full readback must retain the current unit data and contain exact v3')
    changed = [address for address in range(0, 0x100000, 4096)
               if before[address:address+4096] != after[address:address+4096]]
    require(changed == [0x4000], 'upgrade changed an unexpected sector')
    require(plan.get('kind') == 'mini-v2-v3-pc-limit-upgrade'
            and plan.get('target_app_sha256') == EXPECTED_CANDIDATE_SHA
            and plan.get('preimage_app_sha256') == EXPECTED_PREVIOUS_SHA
            and plan.get('sector_order') == [0x4000]
            and plan.get('expected_full_readback_sha256') == sha(after), 'retained upgrade plan differs')
    check_ref(plan['fresh_full_read'], before_ref)
    check_ref(plan['candidate'], candidate_ref)
    require(independent.get('kind') == 'mini-pc-limit-upgrade-independent'
            and independent.get('verified') is True and independent.get('application_exact') is True
            and independent.get('external_regions_unchanged_from_fresh_read') is True
            and independent.get('boot_attempted') is False and independent.get('audio_verified') is False
            and type(independent.get('final_reader_counter')) is int,
            'independent verification is incomplete or its retained reader differs')
    for key, value in (('run', install_ref), ('plan', plan_ref), ('full_before', before_ref),
                       ('full_after', after_ref), ('candidate', candidate_ref)):
        check_ref(independent.get(key), value)
    counter = independent['final_reader_counter']
    lost = independent.get('final_read_lost_bytes')
    require(type(lost) is int and 0 <= lost <= 4096 and lost % 512 == 0
            and counter == 0x100000+lost
            and type(install.get('full_after_target_read_counter')) is int
            and install['full_after_target_read_counter'] == counter
            and type(install.get('full_after_lost_read_bytes')) is int
            and install['full_after_lost_read_bytes'] == lost
            and type(install.get('full_after_read_recovery', {}).get('lost_read_bytes')) is int
            and install['full_after_read_recovery']['lost_read_bytes'] == lost,
            'retained reader counter/lost-read audit differs from independent verification')
    return install, {'run': install_ref, 'independent': independent_ref, 'plan': plan_ref,
                     'full_before': before_ref, 'full_after': after_ref, 'MCN': mcn_ref,
                     'candidate': candidate_ref, 'changed_sectors': changed,
                     'final_reader_counter': counter, 'final_read_lost_bytes': lost,
                     'external_regions_preserved_from_current_read': True,
                     'external_regions_assumed_stock': False}


def prepare(bootmode):
    require(bootmode == 'released', 'only normal software boot is supported')
    pins = json.loads(read_shared_bytes(PINS))
    require(isinstance(pins, dict) and pins, 'nonempty reviewed source/evidence pins required')
    verify_recorded_hashes(pins)
    install, verification = validate_upgrade(pins)
    require(sha(BASE_PROFILE.read_bytes()) == EXPECTED_PROFILE_SHA, 'pinned base app profile changed')
    profile = readonly.load_profile(BASE_PROFILE)
    require(profile['image_sha256'] == EXPECTED_CANDIDATE_SHA and profile['firmware_version'] == EXPECTED_VERSION
            and profile['capabilities']['read'] is True, 'exact MINI base read profile required')
    readonly.source_contract()
    resets = load('research/mini-rom-reset.json')
    verify_recorded_hashes(resets['source_sha256'])
    reset = next(a for a in resets['artifacts'] if a['slot'] == A)
    payload, elf = (ROOT / reset['file']).read_bytes(), (ROOT / reset['elf']).read_bytes()
    validate_reset_artifact(payload, elf, reset, slot=A)
    return pins, install, verification, reset, payload, elf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bootmode', choices=('released',), help='normal software boot; buttons assumed released')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    pins, install, verification, reset, payload, elf = prepare(args.bootmode)
    if args.check_only:
        print(json.dumps({'preflight': 'pass', 'buttons_confirmed_by_user': False, 'buttons_assumed': 'released',
            'held_button_boot_trial_performed': False,
            'candidate_sha256': EXPECTED_CANDIDATE_SHA, 'backend': 'spt-buffered',
            'serial_port_opened': False, 'first_handshake_client': 'separate WebSerial editor'}))
        return
    require(ctypes.windll.shell32.IsUserAnAdmin(), 'bounded SPT helper requires Windows elevation')
    prefix = 'analysis/hardware/mini-first-boot-v11-released'
    out, trace = ROOT / (prefix + '-run.json'), ROOT / (prefix + '-trace.jsonl')
    require(not any(p.exists() for p in (out, out.with_suffix('.json.tmp'), trace)),
            'this one-shot boot already has output; do not repeat')
    result = {'phase': 'prepare', 'started_utc': now(), 'buttons_confirmed_by_user': False,
              'buttons_assumed': 'released', 'held_button_boot_trial_performed': False,
              'boot_mode': 'normal-software-boot', 'slot_A_inactive_verified': False,
              'app_identity_verified': False, 'audio_verified': False, 'serial_port_opened': False,
              'PING_attempted': False, 'first_handshake_client': 'separate WebSerial editor',
              'candidate_sha256': EXPECTED_CANDIDATE_SHA, 'source_pins': pins,
              'installation_evidence_path': INSTALL_RUN.relative_to(ROOT).as_posix(),
              'installation_evidence_sha256': verification['run']['sha256'],
              'upgrade_verification': verification,
              'MCN_cleanup_evidence_path': MCN_LOG.relative_to(ROOT).as_posix(),
              'MCN_cleanup_evidence_sha256': sha(read_shared_bytes(MCN_LOG)),
              'automatic_retry': False, 'firmware_write': False, 'reset_submitted': False,
              'fresh_ROM_verified': False, 'application_USB_enumerated': False,
              'cold_power_cycle_tested': False, 'guard_causality_confirmed': False,
              'backend': 'IOCTL_SCSI_PASS_THROUGH buffered', 'command_spacing_seconds': 0.005}

    def save():
        atomic_write_json(out, result)

    def append(event):
        with trace.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(event) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def logged(transport, label):
        require(isinstance(transport, WindowsBufferedRomTransport), 'buffered transport required')
        result.setdefault('transport_handles', []).append({'label': label, 'path': transport.disk['path'],
            'slot': transport.slot, 'profile': transport.profile, 'inquiry': transport.inquiry,
            'adapter_descriptor': transport.adapter_descriptor})
        save()
        original = transport.exchange
        def exchange(cdb, data_out=None, read_length=0):
            time.sleep(0.005)
            event = {'stage': label, 'started_utc': now(), 'state': 'before', 'cdb': cdb.hex(),
                     'out_bytes': len(data_out) if data_out is not None else 0, 'in_bytes': read_length,
                     'backend': 'spt-buffered'}
            if cdb[:2] == b'\xfb\x08':
                require(not result['reset_submitted'], 'only one reset submission is permitted')
                result['reset_submitted'] = True
                save()
            append(event)
            try:
                raw = original(cdb, data_out=data_out, read_length=read_length)
            except Exception as error:
                event.update(state='error', finished_utc=now(), error=repr(error),
                             details=getattr(error, 'details', {}),
                             native_transfer=getattr(transport, 'last_transfer', None))
                append(event)
                raise
            event.update(state='after', finished_utc=now(), response_bytes=len(raw), response_sha256=sha(raw),
                         native_transfer=getattr(transport, 'last_transfer', None))
            if len(raw) <= 36: event['response_hex'] = raw.hex()
            append(event)
            return raw
        transport.exchange = exchange

    save()
    try:
        disks, before = discover_windows_rom_disks(), arrivals()
        require(len(disks) == len(before) == 1, 'one live ROM and arrival required')
        result['arrival_before'] = before[0]
        path = disks[0]['path']
        require(before[0]['instance_id'].casefold() == disks[0]['usb_ancestor'].casefold(),
                'ROM disk and arrival metadata identify different USB parents')
        with WindowsBufferedRomTransport(path, slot=B, profile='nor-reader') as transport:
            logged(transport, 'retained-reader')
            identity = transport.exchange(b'\xfc\x70' + b'\xff' * 14, read_length=16)
            require(identity == b'\xfc\x70HYRN\x01\x03' + B.to_bytes(4, 'big') + (32768).to_bytes(4, 'big'),
                    'retained reader B no longer active; slot A is not proven inactive')
            status = transport.exchange(b'\xfc\x73' + b'\xff' * 14, read_length=16)
            require(type(install['full_after_target_read_counter']) is int
                    and len(status) == 16 and status[:4] == b'\xfc\x73\0\1'
                    and int.from_bytes(status[12:16], 'big') == verification['final_reader_counter'],
                    'live readback counter differs from the independently attested value')
            result['reader_identity_hex'], result['reader_status_hex'] = identity.hex(), status.hex()
        require(arrivals() == before, 'ROM arrival changed during retained-reader verification')
        initial_cdc = [p for p in readonly.enumerate_ports() if (p['vid'], p['pid']) == (0x3654, 0x5155)]
        require(not initial_cdc, 'candidate CDC already present before reset; cannot attribute new arrival')
        result.update(slot_A_inactive_verified=True, known_live_slot_before_reset=B,
                      candidate_CDC_absent_before_reset=True)
        result['phase'] = 'reset_once'
        save()
        with WindowsBufferedRomTransport(path, slot=A) as transport:
            logged(transport, 'single-reset')
            session = MiniRamSession(transport, slot=A, known_free_slot=True)
            result['reset_upload'] = session.upload_only(payload, expected_sha256=reset['image_sha256'])
            save()
            result['reset_request'] = session.start_reset_once(payload, elf=elf, manifest=reset)
        result['phase'] = 'observe_application_USB'
        save()
        devices = []
        for _ in range(30):
            devices = [p for p in readonly.enumerate_ports() if (p['vid'], p['pid']) == (0x3654, 0x5155)]
            if devices:
                break
            time.sleep(1)
        result['application_ports'] = devices
        require(len(devices) == 1 and re.fullmatch(r'COM[1-9][0-9]{0,3}', devices[0]['device']),
                'application CDC not uniquely observed; no reset retry')
        result.update(application_USB_enumerated=True, phase='application_USB_observed')
        save()
        result['image_hash_attested_by_device'] = False
    except Exception as error:
        result.update(error_phase=result['phase'], error_type=type(error).__name__, error=str(error),
                      error_details=getattr(error, 'details', {}))
    finally:
        result['finished_utc'] = now()
        save()
    print(json.dumps({k: result.get(k) for k in ('phase', 'error', 'application_USB_enumerated', 'app_identity_verified')}))


if __name__ == '__main__': main()
