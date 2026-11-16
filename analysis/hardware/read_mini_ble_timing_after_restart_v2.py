"""Root-operated readonly BLE timing v2; LVL supplies derived gain context."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import site
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append(site.getusersitepackages())
from tools import probe_mini_app as protocol, probe_mini_app_ble as ble
from tools import mini_latency_observation as timing, probe_mini_browser_latency as measurement
from tools.mini_host_journal import atomic_write_json, read_shared_bytes

SPECS = {name: protocol.Query(name, timeout, ends) for name, timeout, ends in (
    ('BLE', 2, ('BLE',)), ('CLKSTATE', 2, ('CLKSTATE',)),
    ('LIFE', 3, ('LIFE',)), ('CRASH', 4, ('CRASH end', 'TRAP')),
    ('STAT', 4, ('NIVEL',)), ('EVT 0', 4, ('EVT end', 'EVT fin')))}
ALLOWED = frozenset((s+'\n').encode('ascii') for s in ('PING', *protocol.QUERIES, *SPECS))
ADDRESS = '33:68:A9:0C:6E:73'
PONG = 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'


def gain_context_from_lvl(lines):
    """Normalize the actual LVL g=in/out field for the frozen analyzer only."""
    if (not isinstance(lines, list) or len(lines) != 1
            or not isinstance(lines[0], str) or not lines[0].startswith('LVL ')
            or len(lines[0]) > protocol.MAX_LINE or any(c in lines[0] for c in '\r\n')):
        raise protocol.AppProbeError('One bounded raw LVL reply required for derived gain')
    fields = [field for field in lines[0].split() if field.startswith('g=')]
    match = re.fullmatch(r'g=(-?\d+)/(-?\d+)', fields[0]) if len(fields) == 1 else None
    if match is None or not all(-30 <= int(value) <= 12 for value in match.groups()):
        raise protocol.AppProbeError('LVL must contain exactly one bounded g=in/out field')
    gains = list(map(int, match.groups()))
    return {'source_command': 'LVL', 'raw_reply': list(lines), 'gain': gains,
            'derived_GAIN': [f'GAIN in={gains[0]} out={gains[1]} dB'],
            'raw_GAIN_reply': False}


class DiagnosticTransport(ble.BleNusTransport):
    def write(self, data):
        self._worker()
        if not isinstance(data, bytes) or data not in ALLOWED:
            raise protocol.AppProbeError('Only fixed reviewed read packets are allowed')
        future = asyncio.run_coroutine_threadsafe(self._write(data), self.loop)
        try:
            future.result(timeout=ble.WRITE_TIMEOUT)
        except BaseException as error:
            future.cancel()
            self._poison(error)
            raise protocol.AppProbeError('BLE write failed; no retry') from error
        return len(data)


class ReadEditor:
    def __init__(self, probe):
        self.probe = probe
        self.derived_gain_from_LVL = []

    def query(self, name):
        if name == 'GAIN':
            derived = gain_context_from_lvl(self.probe.query('LVL')['lines'])
            self.derived_gain_from_LVL.append(derived)
            self.probe.log('derived_gain_from_LVL', **derived)
            return derived['derived_GAIN']
        if name in SPECS:
            return self.probe._exchange(SPECS[name])['lines']
        if name in ('MODEL', 'FXS', 'MEM'):
            return self.probe.query(name)['lines']
        raise ValueError('No such diagnostic read')

    def context(self):
        return {k: self.query(k) for k in ('CLKSTATE', 'MODEL', 'GAIN', 'FXS', 'MEM')}


async def run(output):
    output = output.resolve()
    assert output.is_relative_to(ROOT/'build') and not output.exists()
    timing.verify_sources()
    output.mkdir()
    journal = protocol.Journal(output/'trace.jsonl')
    sources = [Path(__file__), *(ROOT/p for p in (
        'analysis/hardware/read_mini_ble_timing_after_restart.py',
        'tools/probe_mini_app.py', 'tools/probe_mini_app_ble.py',
        'tools/mini_latency_observation.py', 'tools/probe_mini_browser_latency.py'))]
    report = {'kind': 'mini-real-BLE-readonly-timing-v2', 'result': 'running',
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'firmware_write': False, 'configuration_mutations': False,
              'analog_latency_measured': False, 'effects_added': 0,
              'stimulus_controlled': False, 'pair_requested': False,
              'GAIN_context_fields_derived_from_LVL': True,
              'source_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(read_shared_bytes(p)).hexdigest() for p in sources}}
    def save():
        atomic_write_json(output/'report.json', report)
    transport = None
    try:
        journal('start', transport='ble-nus', pair_requested=False, mutations_enabled=False,
                expected_image_sha256='9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c',
                image_hash_attested_by_device=False, GAIN_context_fields_derived_from_LVL=True,
                exact_read_packets=[p.decode().strip() for p in sorted(ALLOWED)])
        device, _, record = ble.choose(await ble.discover(timeout=5), ADDRESS)
        report['device'] = record
        save()
        journal('ble_device_selected', **record)
        transport = await DiagnosticTransport.open(device)
        journal('ble_connected', pair_requested=False)
        probe = protocol.ReadOnlyProbe(transport, ble.EXPECTED_VERSION, log=journal)
        def read_session():
            report['identity'] = probe.identify()
            assert report['identity']['lines'] == [PONG]
            editor = ReadEditor(probe)
            report['derived_gain_from_LVL'] = editor.derived_gain_from_LVL
            report['diagnostics'] = {}
            for name in ('BLE', 'CLKSTATE', 'LIFE', 'CRASH', 'EVT 0'):
                report['diagnostics'][name] = editor.query(name)
                save()
            report['phase'] = 'baseline_timing'
            save()
            def progress(value):
                report['progress'] = value
                save()
            report['measurement'] = measurement.measure(editor, publish=progress)
            report['phase'] = 'readonly_measurement_complete'
            report['result'] = 'pass'
            save()
        await asyncio.to_thread(read_session)
    except Exception as error:
        report.update(result='fail', error=repr(error))
        journal('session_failed', error=repr(error))
    finally:
        if transport is not None:
            try:
                await transport.aclose()
                report['ble_disconnected'] = True
                journal('ble_disconnected')
            except Exception as error:
                report.update(result='fail', close_error=repr(error))
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
        journal.close()
    print(json.dumps({k: report.get(k) for k in ('result', 'error', 'diagnostics', 'ble_disconnected')}))
    return 0 if report['result'] == 'pass' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'hardware_io': False, 'fixed_read_packets': len(ALLOWED),
                          'GAIN_context_fields_derived_from_LVL': True}))
    else:
        assert args.output is not None
        raise SystemExit(asyncio.run(run(args.output)))
