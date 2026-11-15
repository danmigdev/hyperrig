"""Temporary local queue for explicitly pinned HyperRig administrative runners.

Default/import is offline. init/submit/status/stop only manage workspace files;
serve requires the single user-elevated process created by the PS1 launcher.
No TCP, shell jobs, service, scheduled task, reset, command retry or UAC change.
Expiry/STOP prevent new jobs. An active firmware runner is NEVER killed on a
deadline: the broker records the overrun, waits for exit and closes its session.
Hashes bind reviewed artifacts; they are not authentication against the same
local user who controls this workspace and submits the jobs.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.mini_host_journal import atomic_write_json, read_shared_json

CONFIG = 'session.json'
SOURCE_FILES = ('tools/mini_admin_session.py', 'tools/mini_host_journal.py',
                'tools/start_mini_admin_session.ps1')
MAX_SECONDS, MAX_JOB_SECONDS = 5400, 3600
HEX32, HEX64 = re.compile(r'[0-9a-f]{32}\Z'), re.compile(r'[0-9a-f]{64}\Z')
KINDS = {
    'inspect': (r'read_mini_partial_install[1-9][0-9]?\.py', {'execute': ['--execute']}),
    'install': (r'run_mini_[a-z0-9_]{1,48}install\.py',
                {'plain': [], 'recover-read-only': ['--recover-read-only'],
                 'recover-read-once': ['--recover-read-once'],
                 'recover-audited-commands': ['--recover-audited-commands']}),
    'boot': (r'run_mini_first_boot_v[1-9][0-9]?\.py', {'held': ['held'], 'released': ['released']}),
    'boot-ping': (r'run_mini_first_boot_v[1-9][0-9]?_released_ping\.py', {'plain': []}),
    'access': (r'probe_mini_[a-z0-9_]{1,48}access\.py', {'execute': ['--execute']}),
}


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')
def utc(): return datetime.now(timezone.utc).isoformat()


def _no_reparse(path):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
            'symlink/reparse path rejected: ' + str(path))
    return info


def safe_path(name, *, root=ROOT, file=True):
    """Require a real, existing workspace path without traversal/ADS/reparse."""
    require(type(name) is str and 0 < len(name) <= 512 and not any(
        ord(ch) < 32 or ch in '\\:"<>|?*' for ch in name), 'invalid relative workspace path')
    parts = name.split('/')
    require(all(part and part not in ('.', '..') and not part.endswith((' ', '.')) for part in parts),
            'absolute/traversal/Windows-normalized path rejected')
    root = Path(root).absolute()
    for ancestor in reversed((root, *root.parents)):
        require(stat.S_ISDIR(_no_reparse(ancestor).st_mode), 'workspace ancestor is not a directory')
    path = root
    for index, part in enumerate(parts):
        path = path / part
        info = _no_reparse(path)
        require(stat.S_ISDIR(info.st_mode) if index < len(parts)-1 or not file else stat.S_ISREG(info.st_mode),
                'unexpected directory/file type: ' + name)
    require(os.path.commonpath((str(root.resolve()), str(path.resolve()))) == str(root.resolve()),
            'resolved path leaves workspace')
    return path


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def _read_json(path, *, maximum=2*1024*1024):
    _check_output(path)
    require(path.stat().st_size <= maximum, 'JSON exceeds bounded size')
    value = read_shared_json(path)
    require(type(value) is dict, 'JSON object required')
    return value


def verify_pins(pins, *, root=ROOT):
    require(type(pins) is dict and 1 <= len(pins) <= 1024, 'bounded explicit source pins required')
    for name, digest in pins.items():
        require(type(digest) is str and HEX64.fullmatch(digest), 'invalid SHA256 pin')
        require(file_sha(safe_path(name, root=root)) == digest, 'source pin mismatch: ' + name)


def load_session(relative, expected_sha, *, root=ROOT):
    require(type(relative) is str and re.fullmatch(r'analysis/hardware/mini-admin-[0-9a-f]{32}', relative),
            'explicit generated session directory required')
    require(type(expected_sha) is str and HEX64.fullmatch(expected_sha), 'session SHA256 required')
    directory = safe_path(relative, root=root, file=False)
    path = safe_path(relative + '/' + CONFIG, root=root)
    require(file_sha(path) == expected_sha, 'session manifest changed')
    config = _read_json(path, maximum=16384)
    require(config.get('schema') == 1 and config['session_id'] == relative.rsplit('-', 1)[1]
            and config['workspace'] == str(Path(root).resolve())
            and type(config['duration_seconds']) is int and 60 <= config['duration_seconds'] <= MAX_SECONDS
            and config['expires_epoch'] == config['created_epoch'] + config['duration_seconds'],
            'session identity/lifetime/workspace differs')
    require(set(config['source_pins']) == set(SOURCE_FILES), 'broker source package differs')
    verify_pins(config['source_pins'], root=root)
    require(os.path.normcase(config['python_path']) == os.path.normcase(str(Path(sys.executable).resolve()))
            and file_sha(config['python_path']) == config['python_sha256'], 'Python executable differs')
    for name in ('catalog', 'pending', 'claimed', 'results', 'logs', 'rejected'):
        safe_path(relative + '/' + name, root=root, file=False)
    return directory, config


def create_session(*, root=ROOT, duration=MAX_SECONDS, now=None):
    require(type(duration) is int and 60 <= duration <= MAX_SECONDS, 'session duration must be60..5400seconds')
    base = safe_path('analysis/hardware', root=root, file=False)
    source_pins = {name: file_sha(safe_path(name, root=root)) for name in SOURCE_FILES}
    session_id = uuid.uuid4().hex
    directory = base / ('mini-admin-' + session_id)
    directory.mkdir()
    for name in ('catalog', 'pending', 'claimed', 'results', 'logs', 'rejected'):
        (directory / name).mkdir()
    started = time.time() if now is None else now
    config = {'schema': 1, 'session_id': session_id, 'workspace': str(Path(root).resolve()),
        'created_epoch': started, 'expires_epoch': started+duration, 'duration_seconds': duration,
        'python_path': str(Path(sys.executable).resolve()), 'python_sha256': file_sha(sys.executable),
        'source_pins': source_pins, 'network': False, 'permanent_installation': False,
        'active_child_killed_on_timeout': False, 'security_scope': 'local same-user session; hashes are not authentication'}
    publish(directory / CONFIG, config)
    return {'session': directory.relative_to(Path(root)).as_posix(), 'session_sha256': file_sha(directory / CONFIG),
            'expires_epoch': config['expires_epoch'], 'requires_one_initial_elevation': True}


def job_arguments(kind, mode, runner):
    require(kind in KINDS and type(runner) is str and runner.startswith('analysis/hardware/'),
            'runner outside the explicit supported families')
    pattern, modes = KINDS[kind]
    name = runner[len('analysis/hardware/'):]
    require(re.fullmatch(pattern, name) and mode in modes, 'runner filename/mode rejected')
    return modes[mode].copy()


def validate_package(package, *, root=ROOT):
    require(type(package) is dict and set(package) == {'schema','kind','mode','runner','args',
            'runner_sha256','pins_file','pins_sha256','timeout_seconds'}, 'job package fields differ')
    require(package['schema'] == 1 and package['args'] == job_arguments(
            package['kind'], package['mode'], package['runner']), 'arbitrary command arguments rejected')
    require(type(package['timeout_seconds']) is int and 1 <= package['timeout_seconds'] <= MAX_JOB_SECONDS,
            'job timeout exceeds session bound')
    require(type(package['pins_file']) is str and re.fullmatch(
            r'analysis/hardware/[a-z0-9_-]{1,100}-pins\.json', package['pins_file']), 'explicit hardware pins manifest required')
    runner = safe_path(package['runner'], root=root)
    pins_path = safe_path(package['pins_file'], root=root)
    require(file_sha(pins_path) == package['pins_sha256'], 'pins manifest changed')
    pins = _read_json(pins_path)
    require(pins.get(package['runner']) == package['runner_sha256'], 'runner absent from frozen source pins')
    verify_pins(pins, root=root)
    require(file_sha(runner) == package['runner_sha256'], 'runner changed')
    return runner


def _exclusive_json(path, value):
    _check_output(path)
    raw = canonical(value)
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def _check_output(path):
    for ancestor in reversed((path.parent, *path.parent.parents)):
        require(stat.S_ISDIR(_no_reparse(ancestor).st_mode), 'output ancestor is not a real directory')
    for leaf in (path,path.with_suffix(path.suffix+'.tmp')):
        if leaf.exists() or leaf.is_symlink():
            require(stat.S_ISREG(_no_reparse(leaf).st_mode), 'output is not a regular file')


def publish(path, value):
    _check_output(path)
    atomic_write_json(path,value)


def review_gate(directory, previous_job, *, submitted_epoch=None, ignore_claim=None):
    status_path=directory/'status.json'
    state=_read_json(status_path,maximum=16384) if status_path.exists() else {'state':'not_started'}
    require(state['state'] in ('not_started','ready','awaiting_review'),
            'session is running/stopped; no queue-ahead or new job allowed')
    for claim in (directory/'claimed').iterdir():
        require(re.fullmatch(r'[0-9a-f]{32}\.json',claim.name),'unexpected claim filename')
        _no_reparse(claim)
        if claim.stem==ignore_claim:continue
        result=directory/'results'/claim.name
        require(result.exists() and _read_json(result,maximum=16384).get('state')=='completed',
                'previous claimed job has no completed result; no queue-ahead')
    last=state.get('last_job_id')
    require(previous_job==last and (previous_job is None or
            type(previous_job) is str and HEX32.fullmatch(previous_job)),
            'explicit review acknowledgement of the previous job ID required')
    if last is not None and submitted_epoch is not None:
        require(submitted_epoch>=state['last_completed_epoch'],
                'job was submitted before previous execution finished; queue-ahead rejected')
    return last


def submit_job(relative, expected_sha, *, runner, pins_file, kind, mode, timeout=1200,
               previous_job=None, root=ROOT, now=None):
    directory, config = load_session(relative, expected_sha, root=root)
    current = time.time() if now is None else now
    require(current < config['expires_epoch'] and not (directory/'STOP').exists(), 'session expired or stopped')
    # One pending request, serialized even if two local clients race. A stale
    # submission lock is terminal for submissions, never an automatic retry.
    lock=directory/'submission.lock'
    _exclusive_json(lock,{'utc':utc(),'pid':os.getpid()})
    try:
        require(not list((directory/'pending').iterdir()), 'one pending job is already queued')
        review_gate(directory,previous_job,submitted_epoch=current)
        return _submit_locked(directory,config,runner=runner,pins_file=pins_file,
                              kind=kind,mode=mode,timeout=timeout,root=root,
                              previous_job=previous_job,submitted_epoch=current)
    finally:
        lock.unlink()


def _submit_locked(directory,config,*,runner,pins_file,kind,mode,timeout,root,previous_job,submitted_epoch):
    package = {'schema':1,'kind':kind,'mode':mode,'runner':runner,'args':job_arguments(kind,mode,runner),
        'runner_sha256':file_sha(safe_path(runner,root=root)), 'pins_file':pins_file,
        'pins_sha256':file_sha(safe_path(pins_file,root=root)), 'timeout_seconds':timeout}
    validate_package(package, root=root)
    job_id = uuid.uuid4().hex
    catalog = {'schema':1,'session_id':config['session_id'],'job_id':job_id,'submitted_utc':utc(),
               'submitted_epoch':submitted_epoch,'reviewed_previous_job_id':previous_job,'package':package}
    _exclusive_json(directory/'catalog'/(job_id+'.json'),catalog)
    request = {'schema':1,'session_id':config['session_id'],'job_id':job_id,
               'catalog_sha256':file_sha(directory/'catalog'/(job_id+'.json'))}
    publish(directory/'pending'/(job_id+'.json'),request)
    return {'job_id':job_id,'catalog_sha256':request['catalog_sha256'],'runner':runner,'args':package['args']}


def claim_job(directory, config, request_path, *, root=ROOT):
    require(request_path.parent == directory/'pending' and re.fullmatch(r'[0-9a-f]{32}\.json',request_path.name),
            'pending request filename rejected')
    safe_path(request_path.relative_to(root).as_posix(),root=root)
    request = _read_json(request_path,maximum=4096)
    require(set(request)=={'schema','session_id','job_id','catalog_sha256'} and request['schema']==1
            and request['session_id']==config['session_id'] and HEX32.fullmatch(request['job_id'])
            and request_path.stem==request['job_id'] and HEX64.fullmatch(request['catalog_sha256']),
            'request identity or catalog binding differs')
    claim = directory/'claimed'/(request['job_id']+'.json')
    # Persistent, exclusive claim BEFORE launch. A broker crash cannot replay it.
    _exclusive_json(claim, {'claimed_utc':utc(),**request})
    request_path.unlink()
    catalog_path = safe_path((directory/'catalog'/(request['job_id']+'.json')).relative_to(root).as_posix(),root=root)
    require(file_sha(catalog_path)==request['catalog_sha256'],'job catalog changed')
    catalog = _read_json(catalog_path,maximum=16384)
    require(set(catalog)=={'schema','session_id','job_id','submitted_utc','submitted_epoch',
                          'reviewed_previous_job_id','package'} and catalog['schema']==1
            and catalog['job_id']==request['job_id'] and catalog['session_id']==config['session_id'],
            'catalog identity differs')
    review_gate(directory,catalog['reviewed_previous_job_id'],submitted_epoch=catalog['submitted_epoch'],
                ignore_claim=request['job_id'])
    validate_package(catalog['package'],root=root)
    return request['job_id'],catalog['package']


def execute_claimed(directory, job_id, package, config, *, root=ROOT, popen=subprocess.Popen,
                    monotonic=time.monotonic, sleep=time.sleep, session_deadline=None):
    runner=validate_package(package,root=root)
    result_path=directory/'results'/(job_id+'.json')
    result={'schema':1,'job_id':job_id,'state':'launch_intent','started_utc':utc(),
        'runner':package['runner'],'args':package['args'],'package_sha256':sha(canonical(package)),
        'automatic_retry':False,'automatic_reset':False,'timeout_seconds':package['timeout_seconds']}
    require(not result_path.exists(),'job result already exists; replay rejected')
    publish(result_path,result)
    command=[config['python_path'],'-I','-B','-X','utf8',str(runner),*package['args']]
    started=monotonic();overrun=False;child=None
    try:
        with (directory/'logs'/(job_id+'.log')).open('xb') as output:
            child=popen(command,cwd=str(Path(root).resolve()),shell=False,stdin=subprocess.DEVNULL,
                stdout=output,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            result.update(state='running',pid=child.pid);publish(result_path,result)
            while child.poll() is None:
                deadline = monotonic()-started >= package['timeout_seconds'] or (
                    session_deadline is not None and monotonic() >= session_deadline) or (directory/'STOP').exists()
                if deadline and not overrun:
                    overrun=True
                    if not (directory/'STOP').exists():
                        publish(directory/'STOP',{'utc':utc(),'reason':'deadline; no further jobs'})
                    result.update(state='deadline_or_stop_waiting_for_active_runner',
                                  accepts_more_jobs=False,child_termination_requested=False)
                    publish(result_path,result)
                sleep(0.25)
            result.update(state='completed',exit_code=child.returncode,finished_utc=utc(),
                          deadline_or_stop_observed=overrun,exit_code_does_not_prove_hardware_success=True)
    except BaseException as error:
        # Never relaunch or kill a firmware runner because local journaling failed.
        if child is not None and child.poll() is None:
            child.wait()
        result.update(state='broker_job_error',error=repr(error),finished_utc=utc(),
                      child_termination_requested=False)
        publish(result_path,result)
        raise
    publish(result_path,result)
    return result,overrun


def serve(relative, expected_sha, *, root=ROOT):
    require(os.name=='nt' and ctypes.windll.shell32.IsUserAnAdmin(),'serve requires the one explicitly elevated Windows session')
    directory,config=load_session(relative,expected_sha,root=root)
    require(time.time()<config['expires_epoch'] and not (directory/'STOP').exists(),'session expired or stopped')
    _exclusive_json(directory/'serve.lock',{'pid':os.getpid(),'started_utc':utc()})
    deadline=time.monotonic()+min(config['duration_seconds'],config['expires_epoch']-time.time())
    state={'state':'ready','pid':os.getpid(),'started_utc':utc(),'session_id':config['session_id'],
           'expires_epoch':config['expires_epoch'],'automatic_retry':False,'network':False}
    status=directory/'status.json';publish(status,state)
    try:
        while time.monotonic()<deadline and not (directory/'STOP').exists():
            pending=sorted((directory/'pending').iterdir(),key=lambda p:p.name)
            require(len(pending)<=1,'only one pending request is permitted')
            if not pending:
                time.sleep(0.25);continue
            request=pending[0];job_id=None
            try:
                load_session(relative,expected_sha,root=root)
                job_id,package=claim_job(directory,config,request,root=root)
                require(time.monotonic()<deadline and not (directory/'STOP').exists(),'stopped before launch')
                state.update(state='running',job_id=job_id);publish(status,state)
                result,overrun=execute_claimed(directory,job_id,package,config,root=root,session_deadline=deadline)
                state.update(state='awaiting_review',last_job_id=job_id,last_exit_code=result['exit_code'],
                             last_completed_epoch=time.time(),requires_explicit_review_ack=True)
                state.pop('job_id',None)
                publish(status,state)
                if overrun:break
            except BaseException as error:
                # Reject once and STOP the session. Root inspects evidence before any new session.
                _exclusive_json(directory/'rejected'/(uuid.uuid4().hex+'.json'),
                    {'utc':utc(),'request_name':request.name,'job_id':job_id,'error':repr(error)})
                state.update(state='stopped_error',error=repr(error));break
    finally:
        if state['state']!='stopped_error':state['state']='stopped'
        state['finished_utc']=utc();publish(status,state)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action')
    sub.add_parser('init')
    for name in ('serve','submit','status','stop'):
        command=sub.add_parser(name)
        command.add_argument('--session',required=True)
        command.add_argument('--session-sha',required=True)
        if name=='submit':
            command.add_argument('--runner',required=True)
            command.add_argument('--pins',required=True)
            command.add_argument('--kind',required=True,choices=tuple(KINDS))
            command.add_argument('--mode',required=True)
            command.add_argument('--timeout',type=int,default=1200)
            command.add_argument('--reviewed-job',help='previous completed job ID reviewed by the local operator')
    args=parser.parse_args()
    if args.action is None: result={'device_io':False,'elevated_process_started':False,'jobs_submitted':False}
    elif args.action=='init':result=create_session()
    elif args.action=='serve':serve(args.session,args.session_sha);return
    elif args.action=='submit':result=submit_job(args.session,args.session_sha,runner=args.runner,
        pins_file=args.pins,kind=args.kind,mode=args.mode,timeout=args.timeout,previous_job=args.reviewed_job)
    else:
        directory,config=load_session(args.session,args.session_sha)
        if args.action=='stop':
            publish(directory/'STOP',{'session_id':config['session_id'],'utc':utc()})
            result={'stop_requested':True,'active_runner_will_not_be_killed':True}
        else:
            result={'session_id':config['session_id'],'status':read_shared_json(directory/'status.json')
                    if (directory/'status.json').exists() else {'state':'not_started'},
                    'results':{p.stem:read_shared_json(p) for p in sorted((directory/'results').glob('*.json'))}}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
