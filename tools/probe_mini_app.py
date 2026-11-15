"""Read-only USB CDC protocol probe for the standalone HyperRig MINI port.

Import and the default CLI path do not enumerate or open any device. Only the
explicit `read` subcommand opens a selected VID3654:PID5155 serial port. No
arbitrary-command, MIDI, firmware upload, preset write or retry API is exposed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_mini_app import SOURCE, SOURCE_SHA, checked, load_profile

VID, PID, BAUD = 0x3654, 0x5155, 115200
MAX_LINE, MAX_RESPONSE, MAX_LINES = 8192, 262144, 4096


class AppProbeError(RuntimeError):
    pass


@dataclass(frozen=True)
class Query:
    name: str
    timeout: float
    ends: tuple[str, ...]
    mode: str = 'prefix'
    source_line: int = 0

    def complete(self, line):
        if self.mode == 'exact':
            return line in self.ends
        if self.mode == 'fxs':
            return re.match(r'^FXS (?:peak|pico)\b', line) is not None
        return any(line == p or line.startswith(p+' ') for p in self.ends)


# Literal commands only. In particular, argument-bearing forms such as
# SNAPNAME 0 name and FXMIX P 0 50 50 are deliberately not supported.
PING = Query('PING', .700, ('PONG',), source_line=10351)
QUERIES = {
    q.name: q for q in (
        Query('MODEL', 1.500, ('MODEL',), source_line=5451),
        Query('MEM', 3.000, ('MEM',), source_line=5466),
        Query('LVL', .800, ('LVL',), source_line=5413),
        Query('FXT', 3.000, ('FXT end', 'FXT fin'), 'exact', 5392),
        Query('FXS', 2.500, (), 'fxs', 5414),
        Query('FXMIX', 1.500, ('FXMIX end', 'FXMIX fin'), 'exact', 5426),
        Query('FXXO', 1.200, ('FXXO end',), 'exact', 14215),
        Query('PLIST', 4.000, ('PLIST end', 'PLIST fin'), source_line=12067),
        Query('PSTAT', 2.000, ('PSTAT',), source_line=11075),
        Query('SNAPS', 1.500, ('SNAPS',), source_line=8380),
        Query('SNAPNAME', 1.500, ('SNAPNAME end',), source_line=8388),
        Query('CLIST', 4.000, ('CLIST end', 'CLIST fin'), source_line=14089),
    )
}
DEFAULT_QUERIES = ('MODEL', 'MEM', 'LVL', 'FXS', 'PLIST', 'PSTAT', 'SNAPS', 'SNAPNAME')


def source_contract():
    source = checked(SOURCE/'web/tankg.html', SOURCE_SHA).decode('utf-8')
    anchors = (
        'this.port.open({ baudRate: 115200 })',
        'this.tr.write(line + "\\n")',
        'const FXT_END = l => l === "FXT end" || l === "FXT fin";',
        'const FXS_END = l => /^FXS (?:peak|pico)\\b/.test(l);',
        'const PRESET_N = 32, PRESET_NAME_MAX = 23, PLIST_TRIES = 3;',
    )
    if not all(anchor in source for anchor in anchors):
        raise AppProbeError('pinned editor protocol anchors changed')
    for q in (PING, *QUERIES.values()):
        if f'Pedal.cmd("{q.name}"' not in source:
            raise AppProbeError('query not found in original editor: '+q.name)
    return {'editor': (SOURCE/'web/tankg.html').relative_to(ROOT).as_posix(),
            'editor_sha256': SOURCE_SHA, 'newline': 'LF', 'baud': BAUD,
            'timeouts_source': 'original Pedal.cmd call sites',
            'retries': 0, 'default_queries': list(DEFAULT_QUERIES),
            'queries': {q.name: {'seconds': q.timeout, 'end_prefixes': q.ends,
                               'mode': q.mode, 'source_line': q.source_line}
                        for q in (PING, *QUERIES.values())}}


def inspect_pong(line, expected_version):
    # Same version/date boundary as pongVer() and mini-profile.js. The expected
    # artifact hash is an operator/build association, NOT measured by PONG.
    match = re.match(r'^PONG (.+?) \w{3} [ \d]\d \d{4}(?: |$)', line)
    if not match:
        raise AppProbeError('unstructured PONG; no MINI identity accepted')
    version = match[1]
    if not re.fullmatch(r'tankm_fw M\d+\.\d+(?: [a-zA-Z0-9+_.-]+)*', version) or re.search(r'\btank[gb]\b', version):
        raise AppProbeError('wrong firmware: requires standalone tankm_fw, not stock MINI or Tank-G/B')
    if version != expected_version:
        raise AppProbeError(f'firmware version differs: expected {expected_version!r}, got {version!r}')
    return {'target': 'tank-mini', 'firmware_version': version, 'pong': line,
            'binary_hash_attested_by_device': False}


def parse_plist(lines):
    """Port of the editor's PLIST parser and consistency checks, without retries."""
    pattern = re.compile(r"^PRE (\d+) (\d+) (-?\d+) (-?\d+) '(.*)'(?: t=(-|[pq]\d+[ab]?(?:,[pq]\d+[ab]?)*) s=(\d+))?(?: col=([0-9a-f]{6}))?(?: amp=(\d))?\s*$")
    presets, bad, current, last = [], [], None, -1
    for line in lines:
        if re.match(r'^PLIST (?:end|fin)\b', line):
            match = re.fullmatch(r'PLIST (?:end|fin) (?:current|actual)=(-?\d+)\s*', line)
            if match and current is None:
                current = int(match[1])
            else:
                bad.append(line)
            continue
        if line.startswith('ERR'):
            bad.append(line)
            continue
        match = pattern.fullmatch(line)
        if not match:
            if re.search(r"^PRE\b|PRE \d|PLIST|' t=[-pq]", line):
                bad.append(line)
            continue
        slot = int(match[1])
        name_units = len(match[5].encode('utf-16-le'))//2  # JavaScript .length
        if slot >= 32 or slot <= last or name_units > 23:
            bad.append(line)
            continue
        last = slot
        presets.append({'slot': slot, 'name': match[5], 'blocks': int(match[2]),
                        'types': match[6].split(',') if match[6] and match[6] != '-' else [],
                        'snapshots': int(match[7] or 0), 'amp': 0 if match[9] == '0' else 1,
                        'color': match[8]})
    reason = ('no_end' if current is None else 'garbled' if bad else
              'current_missing' if current >= 0 and not any(p['slot'] == current for p in presets) else '')
    return {'presets': presets, 'current': current, 'ok': not reason, 'reason': reason, 'bad': bad}


def port_record(port):
    vid, pid = getattr(port, 'vid', None), getattr(port, 'pid', None)
    role = ('ultrarig-cdc-candidate-needs-tankm-pong' if (vid, pid) == (VID, PID) else
            'stock-mini-usb-midi-incompatible' if (vid, pid) == (0x4C4A, 0xC755) else
            'jieli-rom-recovery-incompatible' if (vid, pid) == (0x4C4A, 0x8057) else 'other')
    return {'device': str(getattr(port, 'device', '')), 'vid': vid, 'pid': pid,
            'description': getattr(port, 'description', None),
            'manufacturer': getattr(port, 'manufacturer', None),
            'product': getattr(port, 'product', None), 'role': role}


def enumerate_ports():
    # This read-only OS enumeration is performed only by an explicit CLI action.
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise AppProbeError('pyserial is required for explicit serial operations: python -m pip install pyserial') from exc
    return [port_record(p) for p in list_ports.comports()]


def select_port(ports, name):
    matches = [p for p in ports if p['device'] == name]
    if len(matches) != 1:
        raise AppProbeError('select exactly one enumerated serial port by its device name')
    result = matches[0]
    if (result['vid'], result['pid']) != (VID, PID):
        raise AppProbeError('selected port is not CDC 3654:5155; stock MIDI and ROM ports are incompatible')
    return result


class SerialTransport:
    def __init__(self, port):
        self.port = port

    @classmethod
    def open(cls, name):
        try:
            import serial
        except ImportError as exc:
            raise AppProbeError('pyserial is required for explicit serial operations') from exc
        port = serial.Serial(port=None, baudrate=BAUD, bytesize=serial.EIGHTBITS,
                             parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                             timeout=.05, write_timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
        # Set before opening. There is no reset pulse or later line toggle here;
        # OS/driver control-line behavior still requires board qualification.
        port.dtr = False
        port.rts = False
        port.port = name
        try:
            port.open()
        except Exception:
            port.close()
            raise
        return cls(port)

    def write(self, data):
        return self.port.write(data)

    def read(self, size):
        return self.port.read(size)

    def close(self):
        self.port.close()


class Journal:
    def __init__(self, path, clock=time.monotonic):
        # Never overwrite an earlier diagnostic run.
        self.file = Path(path).open('x', encoding='utf-8', newline='\n')
        self.clock = clock

    def __call__(self, event, **fields):
        entry = {'utc': datetime.now(timezone.utc).isoformat(), 'monotonic': self.clock(), 'event': event, **fields}
        self.file.write(json.dumps(entry, ensure_ascii=True)+'\n')
        self.file.flush()

    def close(self):
        self.file.close()


class ReadOnlyProbe:
    """Synchronous single-command session over an explicitly supplied transport.

    Constructors perform no reads/writes. Any timeout, malformed reply or
    transport failure poisons the session so late replies cannot satisfy a
    subsequent command. There is no automatic retry or reconnect.
    """
    def __init__(self, transport, expected_version, *, log=None, clock=time.monotonic):
        if not re.fullmatch(r'tankm_fw M\d+\.\d+(?: [a-zA-Z0-9+_.-]+)*', expected_version):
            raise AppProbeError('expected version must identify the standalone MINI port')
        self.transport, self.version, self.clock = transport, expected_version, clock
        self.log = log or (lambda event, **fields: None)
        self.identity = None
        self.failed = False
        self.buffer = bytearray()

    def _drain(self):
        if self.buffer:
            self.log('stale_buffer', bytes=len(self.buffer), hex=self.buffer.hex())
            self.buffer.clear()
        deadline, count = self.clock()+.5, 0
        while self.clock() < deadline:
            data = self.transport.read(512)
            if not isinstance(data, bytes):
                raise AppProbeError('transport read did not return bytes')
            if not data:
                return
            count += len(data)
            self.log('stale_rx', bytes=len(data), hex=data.hex())
            if count > MAX_RESPONSE:
                raise AppProbeError('stale input exceeds response bound')
        raise AppProbeError('input did not become idle before command; no command sent')

    def _exchange(self, spec):
        if self.failed:
            raise AppProbeError('session already failed; no retry or further query allowed')
        lines, asynchronous, total = [], [], 0
        try:
            self._drain()
            packet = (spec.name+'\n').encode('ascii')
            self.log('tx', command=spec.name, hex=packet.hex(), timeout_seconds=spec.timeout)
            started = self.clock()
            written = self.transport.write(packet)
            if written != len(packet):
                raise AppProbeError('partial command write; session stopped without retry')
            deadline = started+spec.timeout
            while self.clock() < deadline:
                data = self.transport.read(512)
                if not isinstance(data, bytes):
                    raise AppProbeError('transport read did not return bytes')
                if not data:
                    continue
                total += len(data)
                self.log('rx', command=spec.name, bytes=len(data), hex=data.hex())
                if total > MAX_RESPONSE:
                    raise AppProbeError('response byte bound exceeded')
                self.buffer += data
                if self.clock() > deadline:
                    break
                while b'\n' in self.buffer:
                    raw, _, rest = self.buffer.partition(b'\n')
                    self.buffer = bytearray(rest)
                    if len(raw) > MAX_LINE:
                        raise AppProbeError('response line bound exceeded')
                    line = raw.removesuffix(b'\r').decode('utf-8', errors='strict')
                    if '\0' in line or '\r' in line:
                        raise AppProbeError('unexpected control byte in response line')
                    if not line.strip():
                        continue
                    if line.startswith(('@', 'NOISE ms=', 'CALIB ', 'ERR CALIB stopped')):
                        asynchronous.append(line)
                        self.log('async_line', command=spec.name, line=line)
                        if len(lines)+len(asynchronous) > MAX_LINES:
                            raise AppProbeError('response line count exceeded')
                        continue
                    lines.append(line)
                    self.log('line', command=spec.name, line=line)
                    if len(lines)+len(asynchronous) > MAX_LINES:
                        raise AppProbeError('response line count exceeded')
                    if line.startswith('ERR'):
                        raise AppProbeError('firmware rejected '+spec.name+': '+line)
                    if spec.complete(line):
                        result = {'command': spec.name, 'lines': lines, 'asynchronous_lines': asynchronous,
                                  'elapsed_seconds': self.clock()-started, 'complete': True}
                        self.log('complete', command=spec.name, elapsed_seconds=result['elapsed_seconds'], lines=len(lines))
                        return result
                if len(self.buffer) > MAX_LINE:
                    raise AppProbeError('unterminated response line bound exceeded')
            raise AppProbeError('response timeout for '+spec.name)
        except Exception as exc:
            self.failed = True
            self.log('failed', command=spec.name, error=str(exc), received_lines=lines,
                     partial_hex=self.buffer.hex(), retries=0)
            if isinstance(exc, AppProbeError):
                raise
            raise AppProbeError(f'{spec.name} transport/decoder failed: {exc}') from exc

    def identify(self):
        if self.identity is not None:
            raise AppProbeError('identity already established; no implicit repeat PING')
        result = self._exchange(PING)
        try:
            self.identity = inspect_pong(result['lines'][-1], self.version)
        except AppProbeError as exc:
            self.failed = True
            self.log('identity_rejected', error=str(exc))
            raise
        self.log('identity_accepted', **self.identity)
        return result

    def query(self, name):
        if name not in QUERIES:
            raise AppProbeError('command is outside the literal read-only allowlist')
        if self.identity is None:
            raise AppProbeError('valid tankm_fw PONG is required before queries')
        result = self._exchange(QUERIES[name])
        if name == 'PLIST':
            parsed = parse_plist(result['lines'])
            result['parsed'] = parsed
            if not parsed['ok']:
                self.failed = True
                self.log('plist_incoherent', **parsed)
                raise AppProbeError('incoherent preset list: '+parsed['reason'])
        return result


def run_read(args, *, enumerate_fn=None, open_fn=None, clock=time.monotonic):
    evidence = source_contract()
    profile = load_profile(args.firmware_manifest)
    if not profile['capabilities']['read'] or not profile['firmware_version']:
        raise AppProbeError('read requires a matching candidate manifest with read capability')
    if len(set(args.queries)) != len(args.queries) or any(q not in QUERIES for q in args.queries):
        raise AppProbeError('queries must be unique literal read-only commands')
    journal = Journal(args.log, clock)
    transport = None
    try:
        journal('start', expected_firmware=profile['firmware_version'], expected_image_sha256=profile['image_sha256'],
                image_hash_attested_by_device=False, source=evidence, mutations_enabled=False)
        port = select_port((enumerate_fn or enumerate_ports)(), args.port)
        journal('port_selected', **port)
        transport = (open_fn or SerialTransport.open)(port['device'])
        journal('port_opened', baud=BAUD, read_timeout=.05, write_timeout=1)
        probe = ReadOnlyProbe(transport, profile['firmware_version'], log=journal, clock=clock)
        results = [probe.identify()]
        results += [probe.query(q) for q in args.queries]
        summary = {'read_only_session_completed': True, 'target': 'tank-mini', 'port': port,
                   'identity': probe.identity, 'expected_image_sha256': profile['image_sha256'],
                   'image_hash_attested_by_device': False, 'commands': [r['command'] for r in results],
                   'firmware_writes_tested': False, 'audio_verified': False, 'log': str(args.log)}
        journal('session_complete', **summary)
        return summary
    except Exception as exc:
        journal('session_failed', error=str(exc), automatic_retry=False)
        raise
    finally:
        try:
            if transport is not None:
                transport.close()
                journal('port_closed')
        finally:
            journal.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action')
    sub.add_parser('plan', help='print the pinned protocol plan; no device enumeration')
    sub.add_parser('enumerate', help='list OS serial-port metadata; opens no port')
    read = sub.add_parser('read', help='explicitly open one CDC port and send only documented queries')
    read.add_argument('--port', required=True)
    read.add_argument('--firmware-manifest', type=Path, required=True)
    read.add_argument('--log', type=Path, required=True, help='new JSONL path; an existing file is never overwritten')
    read.add_argument('--queries', nargs='*', choices=sorted(QUERIES), default=list(DEFAULT_QUERIES),
                      help='omit for the standard set; specify --queries alone for PING only')
    args = parser.parse_args(argv)
    try:
        if args.action in (None, 'plan'):
            result = {'device_io': False, 'enumerated': False, 'protocol': source_contract(),
                      'expected_usb': {'vid': VID, 'pid': PID, 'class': 'CDC-ACM'},
                      'identity': 'exact manifest tankm_fw version before every state/preset session',
                      'write_commands_implemented': False}
        elif args.action == 'enumerate':
            result = {'ports': enumerate_ports(), 'ports_opened': False}
        else:
            result = run_read(args)
        print(json.dumps(result, indent=2))
        return 0
    except (AppProbeError, ValueError, OSError, KeyError) as exc:
        print(json.dumps({'error': str(exc), 'automatic_retry': False}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
