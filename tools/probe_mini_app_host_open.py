"""One CDC host-open diagnostic after the recorded normal MINI boot.

Default/check-only is offline. Execute opens the exact recorded CDC port once,
with DTR requested true and RTS false before open, waits one second, and sends
one PING with a three-second deadline. Only literal read queries follow a valid
MINI PONG. No reconnect, reset, control-line toggle or command retry is exposed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import site
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# The elevated broker uses -I. Make the existing pyserial package importable
# without processing user .pth files or installing any package.
if site.getusersitepackages() not in sys.path:
    sys.path.append(site.getusersitepackages())
from tools import probe_mini_app as readonly
from tools.mini_host_journal import read_shared_bytes

PROFILE = ROOT/'build/hyperrig-mini-audio-v2/firmware-manifest.json'
PROFILE_SHA = 'f119ab571a6cb04c8ca72513b5d18d614e079e756d209ce5794fbaeb4fe77d12'
IMAGE_SHA = '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff'
VERSION = 'tankm_fw M5.71 rel ble'
BOOT = 'analysis/hardware/mini-first-boot-v10-released-run.json'
FAILED_LOGS = ('analysis/hardware/mini-first-app-v10-ping.jsonl',
               'analysis/hardware/mini-app-settled-read-01.jsonl',
               'analysis/hardware/mini-app-settled-read-02.jsonl')
HISTORICAL_SHA = {
    BOOT: 'b18df35377459059ae59ff2ef2def87798510ceda78fe10ef676e57fb4551f49',
    FAILED_LOGS[0]: '57c4c207fa1f8f066dce72d12b083ee759197785ca8f6c2cf0234ddefe4996aa',
    FAILED_LOGS[1]: '01bc3a22489a4f78112baf76ac09fdb972e3454d768fb50e053f6e4d5fee8417',
    FAILED_LOGS[2]: 'f7013a506c73ea71fabf4bfadf8dab4160f0d6598a03eda954a7fc9355fae227',
    'tools/probe_mini_app.py': '055bf238d1ea9a1a2cba298259391406faa22a3bd75384e2b866b0b9af969b74',
}
QUERIES = ('MODEL', 'MEM', 'LVL', 'FXT', 'FXS', 'PLIST', 'PSTAT', 'SNAPS', 'SNAPNAME')
INITIAL_WAIT_SECONDS = 1.0
HOST_PING = readonly.Query('PING', 3.0, ('PONG',), source_line=10351)
Error = readonly.AppProbeError


def sha(data):
    return hashlib.sha256(data).hexdigest()


def preflight(args):
    """Read completed local evidence only; never enumerate a serial port."""
    evidence = {}
    for name, expected in HISTORICAL_SHA.items():
        raw = read_shared_bytes(ROOT/name)
        if sha(raw) != expected:
            raise Error('historical source/evidence changed: '+name)
        evidence[name] = raw
    boot = json.loads(evidence[BOOT])
    if (not boot.get('finished_utc') or boot.get('reset_submitted') is not True
            or boot.get('application_USB_enumerated') is not True
            or boot.get('app_identity_verified') is not False
            or boot.get('candidate_sha256') != IMAGE_SHA
            or boot.get('boot_mode') != 'normal-software-boot'
            or boot.get('buttons_confirmed_by_user') is not False
            or boot.get('held_button_boot_trial_performed') is not False):
        raise Error('completed normal boot with CDC and unproved PONG is required')
    ports = boot.get('application_ports', [])
    if len(ports) != 1:
        raise Error('normal boot must identify exactly one CDC port')
    port = readonly.select_port(ports, args.port)
    for name in FAILED_LOGS:
        rows = [json.loads(line) for line in evidence[name].decode('utf-8').splitlines()]
        if (not rows or rows[-1].get('event') != 'port_closed'
                or sum(r.get('event') == 'port_opened' for r in rows) != 1
                or sum(r.get('event') == 'session_failed' for r in rows) != 1
                or any(r.get('event') in ('identity_accepted', 'session_complete') for r in rows)
                or [r.get('command') for r in rows if r.get('event') == 'tx'] != ['PING']
                or [r.get('device') for r in rows if r.get('event') == 'port_selected'] != [args.port]):
            raise Error('earlier failed PING must have a closed session: '+name)
        start = rows[0]
        if start.get('expected_image_sha256') != IMAGE_SHA or start.get('expected_firmware') != VERSION:
            raise Error('earlier serial session has different firmware binding')
    if sha(read_shared_bytes(PROFILE)) != PROFILE_SHA:
        raise Error('base firmware profile changed')
    profile = readonly.load_profile(PROFILE)
    if (profile.get('image_sha256') != IMAGE_SHA or profile.get('firmware_version') != VERSION
            or profile.get('capabilities', {}).get('read') is not True):
        raise Error('exact MINI image/version/read profile required')
    if len(set(args.queries)) != len(args.queries) or any(q not in readonly.QUERIES for q in args.queries):
        raise Error('unique literal read-only queries required')
    if args.log.exists():
        raise Error('new output log required; existing evidence is never overwritten')
    return {'device_io': False, 'port': port, 'profile_path': str(PROFILE), 'profile_sha256': PROFILE_SHA,
            'expected_firmware': VERSION, 'expected_image_sha256': IMAGE_SHA,
            'historical_sha256': dict(HISTORICAL_SHA), 'source': readonly.source_contract(),
            'dtr_requested_before_open': True, 'rts_requested_before_open': False,
            'initial_wait_seconds': INITIAL_WAIT_SECONDS, 'PING_timeout_seconds': HOST_PING.timeout,
            'PING_timeout_origin': 'explicit diagnostic override; original editor uses 0.7 seconds',
            'queries_after_exact_PONG': list(args.queries), 'automatic_retry': False,
            'reset_commands': False, 'mutations_enabled': False, 'control_line_toggles': False,
            'held_button_boot_trial_performed': False, 'audio_verified': False}


class HostOpenTransport(readonly.SerialTransport):
    @classmethod
    def open(cls, name):
        import serial
        port = serial.Serial(port=None, baudrate=readonly.BAUD, bytesize=serial.EIGHTBITS,
                             parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                             timeout=.05, write_timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
        try:
            port.dtr = True
            port.rts = False
            port.port = name
            port.open()
        except BaseException:
            port.close()
            raise
        return cls(port)


class HostOpenProbe(readonly.ReadOnlyProbe):
    def identify(self):
        if self.identity is not None:
            raise Error('identity already established; repeat PING is not allowed')
        result = self._exchange(HOST_PING)
        try:
            self.identity = readonly.inspect_pong(result['lines'][-1], self.version)
        except Error as exc:
            self.failed = True
            self.log('identity_rejected', error=str(exc))
            raise
        self.log('identity_accepted', **self.identity)
        return result


def run(args, *, enumerate_fn=None, open_fn=None, clock=time.monotonic, sleep_fn=time.sleep):
    plan = preflight(args)
    journal = readonly.Journal(args.log, clock)
    transport, summary = None, None
    try:
        journal('start', **{**plan, 'device_io': True}, image_hash_attested_by_device=False)
        ports = (enumerate_fn or readonly.enumerate_ports)()
        candidates = [p for p in ports if (p.get('vid'), p.get('pid')) == (readonly.VID, readonly.PID)]
        if len(candidates) != 1:
            raise Error('exactly one current CDC 3654:5155 port required')
        port = readonly.select_port(candidates, args.port)
        journal('port_selected', **port)
        journal('port_open_intent', dtr_requested=True, rts_requested=False,
                settings_applied_before_open=True, automatic_retry=False)
        transport = (open_fn or HostOpenTransport.open)(port['device'])
        journal('port_opened', baud=readonly.BAUD, dtr_requested=True, rts_requested=False,
                read_timeout=.05, write_timeout=1, physical_control_lines_measured=False)
        journal('initial_wait', seconds=INITIAL_WAIT_SECONDS)
        sleep_fn(INITIAL_WAIT_SECONDS)
        probe = HostOpenProbe(transport, VERSION, log=journal, clock=clock)
        results = [probe.identify()]
        results.extend(probe.query(name) for name in args.queries)
        summary = {'read_only_session_completed': True, 'target': 'tank-mini', 'port': port,
                   'identity': probe.identity, 'expected_image_sha256': IMAGE_SHA,
                   'image_hash_attested_by_device': False, 'commands': [r['command'] for r in results],
                   'dtr_requested': True, 'rts_requested': False, 'PING_timeout_seconds': HOST_PING.timeout,
                   'initial_wait_seconds': INITIAL_WAIT_SECONDS, 'automatic_retry': False,
                   'firmware_writes_tested': False, 'audio_verified': False,
                   'held_button_boot_trial_performed': False, 'log': str(args.log)}
        journal('session_complete', **summary)
    except BaseException as exc:
        journal('session_failed', error=str(exc), error_type=type(exc).__name__, automatic_retry=False)
        raise
    finally:
        try:
            if transport is not None:
                try:
                    transport.close()
                except BaseException as exc:
                    journal('port_close_failed', error=str(exc))
                    raise
                journal('port_closed')
        finally:
            journal.close()
    summary['serial_port_closed'] = True
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-only', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--port', default='COM3')
    parser.add_argument('--log', type=Path, default=ROOT/'analysis/hardware/mini-app-host-open-01.jsonl')
    parser.add_argument('--queries', nargs='*', choices=sorted(readonly.QUERIES), default=list(QUERIES))
    args = parser.parse_args(argv)
    try:
        result = run(args) if args.execute else preflight(args)
        print(json.dumps(result, indent=2))
        return 0
    except (Error, ValueError, OSError, KeyError, ImportError) as exc:
        print(json.dumps({'error': str(exc), 'automatic_retry': False}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
