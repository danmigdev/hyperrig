"""Versioned connection-help DOM fix for the unchanged original UI trial.

Historical evidence is checked with the frozen app. Only the new trial serves
the derived app copy, whose sole change preserves fuB/fuC for original setLock.
No inert flag, focus check, command policy or hardware state is overridden.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import run_mini_v3_first_preset_a2_v2 as base

SOURCE_NAME=Path(__file__).relative_to(ROOT).as_posix()
BASE_SHA='9dec40a7b14a3c07bc5a556779902dcb32d713868518da97177c3abeefca17c9'
OLD_APP=ROOT/'build/hyperrig-mini-audio-v3/app/web'
COPY_ROOT=ROOT/'build/hyperrig-mini-ui-v2'
NEW_APP=COPY_ROOT/'app/web'
COPY_REPORT=COPY_ROOT/'ui-derivation.json'
UI_SOURCE=ROOT/'app/mini/mini-ui-v2.js'
UI_SHA='d12cfa13ed3e414b600f23ec6cb8be3989632f4990d50079855b5beebaea663d'
BASE_FILES={
    'index.html':'4090b0510aefb6a32faf548b37ea94f8092d7361860de6cc18ded567d1c978bc',
    'mini-profile.js':'237d6db737a23a24b91417c47d08c40b69f30556197b6de5e3ffb08d3cd04e23',
    'mini-ui.js':'b54aa4258391102ed66b06aeab21aa0936466d51c9e56afbaffb990837046007',
    'nam2chip.js':'af584a732fa8a0b03a388871947d490a383c5094d9391fed0f48b6336f255183',
    'tankmini.html':'6aa1383c7d644f3dbb3c8b0ce5e2d287d7d24756b8b21b9c4352ed720cde1842',
}


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def description():
    return {'kind':'original-setLock-help-node-preservation-v1',
        'historical_app_directory':OLD_APP.relative_to(ROOT).as_posix(),
        'served_app_directory':NEW_APP.relative_to(ROOT).as_posix(),
        'base_files':dict(BASE_FILES),'served_files':{**BASE_FILES,'mini-ui.js':UI_SHA},
        'changed_files':['mini-ui.js'],
        'UI_source':{'path':UI_SOURCE.relative_to(ROOT).as_posix(),'sha256':UI_SHA},
        'fix':'preserve original fuB/fuC nodes and their cached text; replace only the firmware-help step',
        'original_setLock_used':True,'inert_or_hidden_state_assigned_by_adapter':False,
        'focus_guard_changed':False,'protocol_or_capabilities_changed':False,'frozen_files_modified':False}


def verify_dependencies():
    require(sha(Path(base.__file__).read_bytes())==BASE_SHA,'frozen bootstrap driver changed')
    base.verify_dependencies()
    require(sha(UI_SOURCE.read_bytes())==UI_SHA,'versioned UI source changed')
    require({p.name for p in OLD_APP.iterdir()}==set(BASE_FILES),'frozen original app inventory changed')
    for name,digest in BASE_FILES.items():require(sha((OLD_APP/name).read_bytes())==digest,'original app source changed: '+name)


def validate_ui_copy():
    verify_dependencies()
    require(NEW_APP.is_dir() and {p.name for p in NEW_APP.iterdir()}==set(BASE_FILES),'derived app inventory differs')
    for name,digest in description()['served_files'].items():
        require(sha((NEW_APP/name).read_bytes())==digest,'derived app file differs: '+name)
    require(json.loads(COPY_REPORT.read_bytes())==description(),'app derivation report differs')
    return description()


def build_ui_copy():
    verify_dependencies()
    if COPY_ROOT.exists():return validate_ui_copy()
    NEW_APP.mkdir(parents=True)
    for name in BASE_FILES:
        (NEW_APP/name).write_bytes(UI_SOURCE.read_bytes() if name=='mini-ui.js' else (OLD_APP/name).read_bytes())
    COPY_REPORT.write_text(json.dumps(description(),indent=2)+'\n',encoding='utf-8')
    return validate_ui_copy()


def annotated_writer(original,driver_sha):
    def write(path,value,**kwargs):
        require(value.get('kind')=='mini-browser-first-preset-v3-trial','only a new UI trial may be annotated')
        published=copy.deepcopy(value)
        require('ui_compatibility_extension' not in published,'UI extension cannot be overwritten')
        sources=published.setdefault('source_sha256',{})
        require(SOURCE_NAME not in sources or sources[SOURCE_NAME]==driver_sha,'UI driver source conflict')
        sources[SOURCE_NAME]=driver_sha;sources[UI_SOURCE.relative_to(ROOT).as_posix()]=UI_SHA
        # Original files are derivation inputs, not the served app: both are explicit.
        for name,digest in BASE_FILES.items():sources[(OLD_APP/name).relative_to(ROOT).as_posix()]=digest
        published['ui_compatibility_extension']=description()
        return original(path,published,**kwargs)
    return write


@contextmanager
def ui_adapter(trial):
    validate_ui_copy()
    desktop=trial.desktop
    old_app,old_prepare,old_writer=desktop.APP,trial.prepare,trial.atomic_write_json
    require(old_app.resolve()==OLD_APP.resolve(),'expected the frozen app as historical baseline')
    def prepare(**refs):
        runtime_app=desktop.APP
        try:
            desktop.APP=OLD_APP
            prepared=old_prepare(**refs)
        finally:
            desktop.APP=runtime_app
        prepared['app_directory']=NEW_APP.relative_to(ROOT).as_posix()
        prepared['ui_compatibility_extension']=validate_ui_copy()
        return prepared
    desktop.APP=NEW_APP;trial.prepare=prepare
    trial.atomic_write_json=annotated_writer(old_writer,sha(Path(__file__).read_bytes()))
    try:
        yield
    finally:
        desktop.APP,trial.prepare,trial.atomic_write_json=old_app,old_prepare,old_writer


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(json.dumps({'device_io':False,'browser_started':False,'inputs_read':False,
            'plan':'Original first-preset UI with preserved connection-help nodes','profile_modified':False}));return 0
    if args==['--build-ui-copy']:
        print(json.dumps({'built':build_ui_copy(),'device_io':False,'hardware_verified':False}));return 0
    verify_dependencies()
    _,trial=base.base.bridge.modules('first-preset')
    with ui_adapter(trial):return base.main(args)


if __name__=='__main__':raise SystemExit(main())
