"""Delegate to frozen v3 desktop/trial with two exact closed-file read exceptions.

This is a host evidence-file adapter, not a device driver. It changes only the
desktop module's in-memory reader and annotates new session/trial publications.
All other readers, files, protocols, guards and capability checks are unchanged.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE_NAME = Path(__file__).relative_to(ROOT).as_posix()
EXPANDED_MAXIMUM = 32 * 1024 * 1024
ORIGINAL_MAXIMUM = 8 * 1024 * 1024
EXACT_TRACES = {
    'analysis/hardware/mini-pc-limit-install-trace.jsonl': {
        'bytes': 17590011,
        'sha256': '2258850d612c9971e251fdcc581db0dc97b2e6cb3f355cd015e204624ea7bde4'},
    'analysis/hardware/mini-complete-install-trace.jsonl': {
        'bytes': 10133042,
        'sha256': '8561aff779032f599f6aa4590b8f8ae2c1b60a58bc2fda67911d6f62914bc501'},
}
FROZEN = {
    'tools/launch_mini_desktop_v3.py': '4bb838dd9a18839685ee5211af64ce014ac858975d9b3faca61ffa984a25d754',
    'tools/validate_mini_webserial_v3.py': '4d01fe626e0d55a02e34a7fbe5b80d192caea57e8e53a2a27ec13a24c7a280c1',
    'tools/probe_mini_browser_first_preset.py': '87b4063f8e50cabb2d0cd230b1db279770211636842698d7048f748080831c3b',
    'tools/mini_host_journal.py': '1105371aeede4094739c5e8d34b441770ea700db861ed504fbc98167842b5f1f',
}


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()


class ExactTraceReader:
    def __init__(self, original):
        self.original = original
        self.verified_reads = {name: 0 for name in EXACT_TRACES}

    def __call__(self, path, **kwargs):
        resolved = Path(path).resolve()
        name = next((name for name in EXACT_TRACES if resolved == (ROOT/name).resolve()), None)
        if name is None:
            # No maximum argument is added: even the original default stays8MiB.
            return self.original(path, **kwargs)
        require(not kwargs, 'exact trace exception accepts only the frozen default-reader call')
        expected = EXACT_TRACES[name]
        data = self.original(path, maximum=EXPANDED_MAXIMUM)
        require(len(data) == expected['bytes'], 'closed trace size differs: '+name)
        require(sha(data) == expected['sha256'], 'closed trace SHA256 differs: '+name)
        self.verified_reads[name] += 1
        return data

    def description(self):
        return {'kind': 'exact-closed-trace-read-bound-v1', 'scope': 'host evidence files only',
            'expanded_maximum_bytes': EXPANDED_MAXIMUM, 'unchanged_other_default_maximum_bytes': ORIGINAL_MAXIMUM,
            'exceptions': {name: {**value, 'successful_verified_reads': self.verified_reads[name]}
                           for name, value in EXACT_TRACES.items()},
            'frozen_files_modified': False, 'device_protocol_modified': False, 'capabilities_modified': False}


def annotated_writer(original, reader, driver_sha):
    def write(path, value, **kwargs):
        require(value.get('kind') in ('mini-desktop-readonly-v3-session', 'mini-browser-first-preset-v3-trial'),
                'adapter can annotate only a new delegated session/trial report')
        # Do not change the frozen module's prepared evidence or in-memory report.
        published = copy.deepcopy(value)
        require('evidence_io_extension' not in published, 'existing evidence extension cannot be overwritten')
        sources = published.setdefault('source_sha256', {})
        require(SOURCE_NAME not in sources or sources[SOURCE_NAME] == driver_sha, 'driver source pin conflict')
        sources[SOURCE_NAME] = driver_sha
        published['evidence_io_extension'] = reader.description()
        return original(path, published, **kwargs)
    return write


@contextmanager
def evidence_io_adapter(desktop, delegated):
    old_reader, old_writer = desktop.read_shared_bytes, delegated.atomic_write_json
    reader = ExactTraceReader(old_reader)
    driver_sha = sha(Path(__file__).read_bytes())
    desktop.read_shared_bytes = reader
    delegated.atomic_write_json = annotated_writer(old_writer, reader, driver_sha)
    try:
        yield reader
    finally:
        delegated.atomic_write_json = old_writer
        desktop.read_shared_bytes = old_reader


def modules(mode):
    require(mode in ('desktop', 'first-preset'), 'choose desktop or first-preset')
    for name, expected in FROZEN.items():
        require(sha((ROOT/name).read_bytes()) == expected, 'frozen dependency changed: '+name)
    desktop = importlib.import_module('tools.launch_mini_desktop_v3')
    if mode == 'desktop': return desktop, desktop
    delegated = importlib.import_module('tools.probe_mini_browser_first_preset')
    require(delegated.desktop is desktop and delegated.evidence.desktop is desktop,
            'trial/validator must share the frozen desktop module')
    return desktop, delegated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', choices=('desktop', 'first-preset'))
    parser.add_argument('delegate_args', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.mode is None:
        print(json.dumps({'device_io': False, 'browser_started': False, 'inputs_read': False,
                          'modes': ['desktop', 'first-preset'], 'exact_trace_exceptions': EXACT_TRACES})); return 0
    desktop, delegated = modules(args.mode)
    with evidence_io_adapter(desktop, delegated):
        return delegated.main(args.delegate_args)


if __name__ == '__main__': raise SystemExit(main())
