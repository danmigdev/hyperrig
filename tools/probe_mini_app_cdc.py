"""Explicit read-only CDC diagnostic with the original firmware's DTR gate open.

No hardware access by default or in --check-only. --execute requests DTR=true
and RTS=false before one serial open, waits one second, and sends one PING with
a three-second deadline. Only the frozen literal read allowlist follows PONG.
No command retry, reconnect, reset, line toggle or mutation API is exposed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_app as readonly
from tools import probe_mini_app_host_open as host
from tools.mini_host_journal import read_shared_bytes

PINS = {
    'tools/probe_mini_app.py': '055bf238d1ea9a1a2cba298259391406faa22a3bd75384e2b866b0b9af969b74',
    'tools/probe_mini_app_host_open.py': '8936ef30d0db27df4ffd91c600e7f1a2c911302f9f1b245df8048691d2ac9c8d',
    'tools/build_mini_app.py': '529e9be717919c52659249d1732ba7e1c7916cfd35ba94562f59104c4f7f8176',
}
Error = readonly.AppProbeError


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(args):
    """File-only; the manifest's image is verified by the frozen profile loader."""
    for name, expected in PINS.items():
        if sha(read_shared_bytes(ROOT/name)) != expected:
            raise Error('frozen dependency differs: '+name)
    manifest = Path(args.firmware_manifest).resolve()
    if not manifest.is_relative_to(ROOT):
        raise Error('workspace firmware manifest required')
    raw = read_shared_bytes(manifest)
    profile = readonly.load_profile(manifest)
    if profile['capabilities'].get('read') is not True or not profile.get('firmware_version'):
        raise Error('matching MINI manifest with read capability required')
    if not isinstance(args.port, str) or not args.port:
        raise Error('explicit serial port required')
    if len(set(args.queries)) != len(args.queries) or any(q not in readonly.QUERIES for q in args.queries):
        raise Error('unique literal read-only queries required; PING is implicit once')
    log = Path(args.log).resolve()
    if not log.is_relative_to(ROOT) or log.exists() or not log.parent.is_dir():
        raise Error('new workspace log in an existing directory required')
    return {'kind': 'mini-generic-CDC-host-open-v1', 'device_io': False, 'port_name': args.port,
            'manifest': {'path': manifest.relative_to(ROOT).as_posix(), 'sha256': sha(raw)},
            'expected_firmware': profile['firmware_version'], 'expected_image_sha256': profile['image_sha256'],
            'image_hash_attested_by_device': False, 'source': readonly.source_contract(),
            'source_sha256': {**PINS, 'tools/probe_mini_app_cdc.py': sha(Path(__file__).read_bytes())},
            'dtr_requested_before_open': True, 'rts_requested_before_open': False,
            'initial_wait_seconds': host.INITIAL_WAIT_SECONDS, 'PING_timeout_seconds': host.HOST_PING.timeout,
            'PING_timeout_origin': 'explicit diagnostic override; original editor first PING uses0.7s',
            'queries_after_exact_PONG': list(args.queries), 'automatic_retry': False,
            'mutations_enabled': False, 'reset_commands': False, 'control_line_toggles': False,
            'physical_control_lines_measured': False, 'DTR_control_delivery_verified': False,
            'audio_verified': False, 'general_capabilities_granted': {}}


def run(args, *, enumerate_fn=None, open_fn=None, clock=time.monotonic, sleep_fn=time.sleep):
    plan = prepare(args)
    journal = readonly.Journal(args.log, clock)
    transport = None
    try:
        try:
            journal('start', **{**plan, 'device_io': True})
            ports = (enumerate_fn or readonly.enumerate_ports)()
            candidates = [p for p in ports if (p.get('vid'), p.get('pid')) == (readonly.VID, readonly.PID)]
            if len(candidates) != 1:
                raise Error('exactly one current CDC3654:5155 device required')
            port = readonly.select_port(candidates, args.port)
            journal('port_selected', **port)
            journal('port_open_intent', dtr_requested=True, rts_requested=False,
                    settings_applied_before_open=True, automatic_retry=False)
            transport = (open_fn or host.HostOpenTransport.open)(port['device'])
            journal('port_opened', baud=readonly.BAUD, dtr_requested=True, rts_requested=False,
                    read_timeout=.05, write_timeout=1, physical_control_lines_measured=False)
            journal('initial_wait', seconds=host.INITIAL_WAIT_SECONDS)
            sleep_fn(host.INITIAL_WAIT_SECONDS)
            # Only these classes are reused. The old host CLI/preflight is tied
            # to historical v2 evidence and is deliberately never called here.
            probe = host.HostOpenProbe(transport, plan['expected_firmware'], log=journal, clock=clock)
            results = [probe.identify()]
            results.extend(probe.query(name) for name in args.queries)
            summary = {'read_only_session_completed': True, 'target': 'tank-mini', 'port': port,
                       'identity': probe.identity, 'expected_image_sha256': plan['expected_image_sha256'],
                       'image_hash_attested_by_device': False, 'commands': [r['command'] for r in results],
                       'dtr_requested': True, 'rts_requested': False, 'initial_wait_seconds': host.INITIAL_WAIT_SECONDS,
                       'PING_timeout_seconds': host.HOST_PING.timeout, 'automatic_retry': False,
                       'firmware_writes_tested': False, 'audio_verified': False, 'log': str(args.log)}
        finally:
            if transport is not None:
                try:
                    transport.close()
                except BaseException as error:
                    journal('port_close_failed', error=str(error))
                    raise
                journal('port_closed')
        summary['serial_port_closed'] = True
        journal('session_complete', **summary)
        return summary
    except BaseException as error:
        journal('session_failed', error=str(error), error_type=type(error).__name__, automatic_retry=False)
        raise
    finally:
        journal.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-only', action='store_true'); mode.add_argument('--execute', action='store_true')
    parser.add_argument('--port'); parser.add_argument('--firmware-manifest', type=Path)
    parser.add_argument('--log', type=Path)
    parser.add_argument('--queries', nargs='*', choices=sorted(readonly.QUERIES), default=list(readonly.DEFAULT_QUERIES),
                        help='--queries with no arguments sends only the mandatory PING')
    args = parser.parse_args(argv)
    if not (args.check_only or args.execute):
        print(json.dumps({'device_io': False, 'enumerated': False, 'inputs_read': False,
                          'requested_DTR_when_executed': True})); return 0
    try:
        if not args.port or args.firmware_manifest is None or args.log is None:
            raise Error('explicit port, firmware-manifest and new log required')
        result = run(args) if args.execute else prepare(args)
        print(json.dumps(result, indent=2)); return 0
    except (Error, ValueError, OSError, KeyError, ImportError) as error:
        print(json.dumps({'error': str(error), 'automatic_retry': False}), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
