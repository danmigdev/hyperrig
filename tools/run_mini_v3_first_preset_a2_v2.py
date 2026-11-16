"""Versioned first-preset bootstrap fix; default does not access a device.

Delegate every A2/provenance/UI/close check to the frozen driver. Only the new
guard recognizes the original editor's exact local rejection of BLE key. The
command remains forbidden on the serial wire; no BLE capability is granted.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import run_mini_v3_first_preset_a2 as base

SOURCE_NAME = Path(__file__).relative_to(ROOT).as_posix()
BASE_SHA = 'c234aa9d36f9b0c95e71a692881f81342773d6e237766f1a2d1ed49df65ac2ab'
BASE_GUARD = ROOT/'tools/mini_browser_first_preset_guard.js'
BASE_GUARD_SHA = '4157be429799c27b404f9d8762866515492af595cbbe432ba6e17d3298d394ce'
GUARD = ROOT/'tools/mini_browser_first_preset_guard_v2.js'
GUARD_SHA = 'af14b3c7a71e72dffa23228e252b88053a075f0bdeffb024b22783761fc49367'
LOCAL_REPLY = 'ERR MINI_APP firmware mutations are not validated for this MINI build'
FAILURE_REFERENCE = {'path':'build/mini-first-preset-ui-01/report.json',
                     'sha256':'292bfed0f1aeea5cfae969ccfe0aaf98535d0403ba52ecb992e56820e88bbd4a'}


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()


def description():
    return {'kind':'exact-local-BLE-key-rejection-v2',
        'base_guard':{'path':BASE_GUARD.relative_to(ROOT).as_posix(),'sha256':BASE_GUARD_SHA},
        'guard':{'path':GUARD.relative_to(ROOT).as_posix(),'sha256':GUARD_SHA},
        'historical_failed_trial':dict(FAILURE_REFERENCE),
        'local_request':'BLE key','local_reply':LOCAL_REPLY,
        'BLE_key_on_wire_allowed':False,'BLE_capability_granted':False,
        'original_UI_and_mutation_sequence_unchanged':True,
        'frozen_files_modified':False,'hardware_claims_added':False}


def annotated_writer(original, driver_sha):
    def write(path, value, **kwargs):
        require(value.get('kind') == 'mini-browser-first-preset-v3-trial', 'only a new delegated trial may be annotated')
        published = copy.deepcopy(value)
        require('bootstrap_guard_extension' not in published, 'existing bootstrap extension cannot be replaced')
        sources = published.setdefault('source_sha256', {})
        require(SOURCE_NAME not in sources or sources[SOURCE_NAME] == driver_sha, 'bootstrap driver source conflict')
        sources[SOURCE_NAME] = driver_sha
        sources[GUARD.relative_to(ROOT).as_posix()] = GUARD_SHA
        published['bootstrap_guard_extension'] = description()
        published['bootstrap_guard_extension']['observed_local_rejections'] = [
            copy.deepcopy(event) for event in value.get('guard', {}).get('events', [])
            if event.get('kind') == 'local_editor_policy_rejection' and event.get('line') == 'BLE key']
        return original(path, published, **kwargs)
    return write


@contextmanager
def guard_adapter(trial):
    old_guard, old_writer = trial.GUARD, trial.atomic_write_json
    require(old_guard.resolve() == BASE_GUARD.resolve(), 'expected the frozen original trial guard')
    trial.GUARD = GUARD
    trial.atomic_write_json = annotated_writer(old_writer, sha(Path(__file__).read_bytes()))
    try:
        yield
    finally:
        trial.GUARD, trial.atomic_write_json = old_guard, old_writer


def verify_dependencies():
    for path, expected in ((Path(base.__file__), BASE_SHA), (BASE_GUARD, BASE_GUARD_SHA), (GUARD, GUARD_SHA)):
        require(sha(path.read_bytes()) == expected, 'bootstrap dependency changed: '+str(path))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(json.dumps({'device_io':False,'browser_started':False,'inputs_read':False,
            'plan':'Frozen A2 first-preset UI trial with exact local BLE key denial recognized',
            'automatic_retry':False,'BLE_key_on_wire_allowed':False,'profile_modified':False})); return 0
    verify_dependencies()
    _, trial = base.bridge.modules('first-preset')
    with guard_adapter(trial):
        return base.main(args)


if __name__ == '__main__': raise SystemExit(main())
