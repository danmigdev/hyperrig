"""Bounded original-editor PING handshake on one DTR-enabled CDC session.

Up to five PING/700ms attempts, matching the pinned editor. A repeated PING
requires zero native RX bytes, one full completed write and an ordinary empty
response timeout. Partial/garbled replies or any transport error are terminal.
Default/check-only are offline. No mutation, reconnect or control-line toggle.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import probe_mini_app_cdc as v1

readonly, host, Error = v1.readonly, v1.host, v1.Error
V1_SHA = '72b3e7faea396a6f271a1d4adc5805df0389daef57962acc7c893eba31d58e37'
MAX_ATTEMPTS = 5
ANCHOR = 'for (let k = 0; k < 5 && !pong; k++) pong = (await Pedal.cmd("PING", "PONG", 700)).find(l => l.startsWith("PONG")) || "";'


def prepare(args):
    if v1.sha(Path(v1.__file__).read_bytes()) != V1_SHA:
        raise Error('frozen single-PING client changed')
    plan = v1.prepare(args)
    source = readonly.checked(readonly.SOURCE/'web/tankg.html', readonly.SOURCE_SHA).decode('utf-8')
    if ANCHOR not in source or readonly.PING.timeout != .7:
        raise Error('original five-PING/700ms handshake differs')
    plan.update(kind='mini-generic-CDC-host-open-v2', PING_timeout_seconds=.7,
        PING_max_attempts=MAX_ATTEMPTS, PING_timeout_origin='original editor connect loop at line10351',
        automatic_retry=True, automatic_retry_scope='PING only after witnessed entirely empty response timeout',
        automatic_retry_max=MAX_ATTEMPTS-1, query_retries=0, reconnects=0,
        late_PONG_causally_attributed_to_attempt=False)
    plan['source_sha256'].update({'tools/probe_mini_app_cdc.py': V1_SHA,
        'tools/probe_mini_app_cdc_handshake.py': v1.sha(Path(__file__).read_bytes())})
    return plan


class NativeObservation:
    """Observe native results before the frozen parser can discard stale bytes."""
    def __init__(self, transport, log):
        self.transport, self.log, self.attempt = transport, log, 0

    def begin(self, attempt):
        self.attempt = attempt
        self.handshake = True
        self.rx_bytes, self.reads_after_write, self.write_calls = 0, 0, 0
        self.write_results, self.errors = [], []

    def event(self, event, **fields):
        self.log(event, handshake_attempt=self.attempt, **fields)

    def write(self, data):
        if self.handshake and (data != b'PING\n' or self.rx_bytes or self.write_calls):
            self.errors.append('prewrite_input_or_duplicate')
            raise Error('unexpected input or duplicate before handshake write; no command sent')
        self.write_calls += 1
        self.event('native_tx_intent', hex=data.hex(), bytes=len(data))
        try:
            count = self.transport.write(data)
        except BaseException as error:
            self.errors.append('write'); self.event('native_tx_error', error=repr(error)); raise
        self.write_results.append(count)
        self.event('native_tx_complete', written=count, expected=len(data))
        return count

    def read(self, size):
        if self.write_results:
            self.reads_after_write += 1
        try:
            data = self.transport.read(size)
        except BaseException as error:
            self.errors.append('read'); self.event('native_rx_error', error=repr(error)); raise
        if isinstance(data, bytes):
            self.rx_bytes += len(data)
            if data:
                self.event('native_rx', hex=data.hex(), bytes=len(data))
        else:
            self.errors.append('read_type')
        return data

    def witness(self):
        return {'native_RX_bytes': self.rx_bytes, 'reads_after_completed_write': self.reads_after_write,
                'native_write_calls': self.write_calls, 'native_write_results': list(self.write_results),
                'native_transport_errors': list(self.errors)}


def identify(transport, version, *, log, clock=time.monotonic):
    observed = NativeObservation(transport, log)
    attempts = []
    for number in range(1, MAX_ATTEMPTS+1):
        observed.begin(number)
        log('handshake_attempt', attempt=number, maximum=MAX_ATTEMPTS, timeout_seconds=.7,
            same_open_port=True, line_state_unchanged=True)
        # A failed parser is never unpoisoned. A fresh parser is permitted only
        # after the preceding immutable empty-response witness; the port stays open.
        probe = readonly.ReadOnlyProbe(observed, version, log=observed.event, clock=clock)
        try:
            result = probe.identify()
        except Error as error:
            witness = observed.witness()
            empty = (str(error) == 'response timeout for PING' and probe.failed is True
                     and not probe.buffer and probe.identity is None
                     and witness['native_RX_bytes'] == 0 and witness['reads_after_completed_write'] > 0
                     and witness['native_write_calls'] == 1 and witness['native_write_results'] == [5]
                     and not witness['native_transport_errors'])
            attempts.append({'attempt': number, 'outcome': 'empty_timeout' if empty else 'terminal_error',
                             'error': str(error), **witness})
            log('handshake_attempt_failed', **attempts[-1], repeat_permitted=empty and number < MAX_ATTEMPTS)
            if not empty or number == MAX_ATTEMPTS:
                raise
        else:
            attempts.append({'attempt': number, 'outcome': 'PONG_received', **observed.witness()})
            log('handshake_complete', attempts=attempts, PONG=result['lines'][-1],
                repeated_PING_count=number-1, late_reply_attribution_verified=False)
            observed.handshake = False
            observed.attempt = None  # Subsequent literal queries are outside the handshake.
            return probe, result, attempts
    raise AssertionError('finite handshake exhausted without a terminal outcome')


def run(args, *, enumerate_fn=None, open_fn=None, clock=time.monotonic, sleep_fn=time.sleep):
    plan = prepare(args); journal = readonly.Journal(args.log, clock); transport = None
    try:
        try:
            journal('start', **{**plan, 'device_io': True})
            candidates = [p for p in (enumerate_fn or readonly.enumerate_ports)()
                          if (p.get('vid'), p.get('pid')) == (readonly.VID, readonly.PID)]
            if len(candidates) != 1:
                raise Error('exactly one current CDC3654:5155 device required')
            port = readonly.select_port(candidates, args.port); journal('port_selected', **port)
            journal('port_open_intent', dtr_requested=True, rts_requested=False,
                    settings_applied_before_open=True, reopen_permitted=False)
            transport = (open_fn or host.HostOpenTransport.open)(port['device'])
            journal('port_opened', baud=readonly.BAUD, dtr_requested=True, rts_requested=False,
                    read_timeout=.05, write_timeout=1, physical_control_lines_measured=False)
            journal('initial_wait', seconds=1.0); sleep_fn(1.0)
            probe, first, attempts = identify(transport, plan['expected_firmware'], log=journal, clock=clock)
            results = [first] + [probe.query(q) for q in args.queries]
            summary = {'read_only_session_completed': True, 'target': 'tank-mini', 'port': port,
                'identity': probe.identity, 'expected_image_sha256': plan['expected_image_sha256'],
                'image_hash_attested_by_device': False, 'queries_completed': [x['command'] for x in results],
                'handshake_attempts': attempts, 'PING_sent': len(attempts), 'automatic_retry': True,
                'automatic_retry_scope': plan['automatic_retry_scope'], 'query_retries': 0, 'reconnects': 0,
                'firmware_writes_tested': False, 'audio_verified': False, 'log': str(args.log)}
        finally:
            if transport is not None:
                try:
                    transport.close()
                except BaseException as error:
                    journal('port_close_failed', error=str(error)); raise
                journal('port_closed')
        summary['serial_port_closed'] = True; journal('session_complete', **summary); return summary
    except BaseException as error:
        journal('session_failed', error=str(error), error_type=type(error).__name__,
                further_commands_permitted=False, reconnect_permitted=False)
        raise
    finally:
        journal.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-only', action='store_true'); mode.add_argument('--execute', action='store_true')
    parser.add_argument('--port'); parser.add_argument('--firmware-manifest', type=Path); parser.add_argument('--log', type=Path)
    parser.add_argument('--queries', nargs='*', choices=sorted(readonly.QUERIES), default=list(readonly.DEFAULT_QUERIES))
    args = parser.parse_args(argv)
    if not (args.check_only or args.execute):
        print(json.dumps({'device_io': False, 'inputs_read': False, 'maximum_PING_when_executed': MAX_ATTEMPTS})); return 0
    try:
        if not args.port or args.firmware_manifest is None or args.log is None:
            raise Error('explicit port, firmware-manifest and new log required')
        print(json.dumps(run(args) if args.execute else prepare(args), indent=2)); return 0
    except (Error, ValueError, OSError, KeyError, ImportError) as error:
        print(json.dumps({'error': str(error), 'further_commands_permitted': False}), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
