"""Temporary files and fake children only; no elevation or hardware access."""
import copy
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import mini_admin_session as broker


class FakeChild:
    pid=1234
    def __init__(self, polls=2, code=0):
        self.remaining=polls;self.code=code;self.returncode=None;self.wait_calls=0
    def poll(self):
        if self.remaining:
            self.remaining-=1;return None
        self.returncode=self.code;return self.code
    def wait(self):
        self.wait_calls+=1;self.remaining=0;self.returncode=self.code;return self.code
    def terminate(self):raise AssertionError('broker killed an active runner')
    def kill(self):raise AssertionError('broker killed an active runner')


class AdminSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'analysis/hardware').mkdir(parents=True)
        for name in broker.SOURCE_FILES:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(name)
        self.runner='analysis/hardware/read_mini_partial_install6.py'
        (self.root/self.runner).write_text('raise SystemExit(0)\n')
        self.pins='analysis/hardware/test-pins.json'
        self.source_pins={self.runner:broker.file_sha(self.root/self.runner)}
        (self.root/self.pins).write_text(json.dumps(self.source_pins))
        self.info=broker.create_session(root=self.root,duration=60,now=1000)
        self.directory,self.config=broker.load_session(self.info['session'],self.info['session_sha256'],root=self.root)

    def submit(self,**changes):
        values={'runner':self.runner,'pins_file':self.pins,'kind':'inspect','mode':'execute',
                'root':self.root,'now':1001,'timeout':30}
        values.update(changes)
        return broker.submit_job(self.info['session'],self.info['session_sha256'],**values)

    def claim(self):
        queued=self.submit()
        job,package=broker.claim_job(self.directory,self.config,
            self.directory/'pending'/(queued['job_id']+'.json'),root=self.root)
        return job,package

    def test_init_and_submit_are_only_files_with_exact_bound_arguments(self):
        result=self.submit()
        self.assertEqual(result['args'],['--execute'])
        self.assertEqual(len(list((self.directory/'pending').iterdir())),1)
        self.assertFalse((self.directory/'serve.lock').exists())

    def test_allowlist_rejects_arbitrary_paths_modes_and_shell_arguments(self):
        invalid=(('inspect','execute','../read_mini_partial_install6.py'),
                 ('inspect','execute','analysis/hardware/read_mini_partial_install6.ps1'),
                 ('inspect','execute','analysis/hardware/nested/read_mini_partial_install6.py'),
                 ('install','--foo','analysis/hardware/run_mini_echo_install.py'),
                 ('boot','held;shutdown','analysis/hardware/run_mini_first_boot_v7.py'))
        for kind,mode,runner in invalid:
            with self.subTest(runner=runner,mode=mode),self.assertRaises(ValueError):
                broker.job_arguments(kind,mode,runner)
        self.assertEqual(broker.job_arguments('install','recover-audited-commands',
            'analysis/hardware/run_mini_reconciled_install.py'),['--recover-audited-commands'])
        self.assertEqual(broker.job_arguments('boot-ping','plain',
            'analysis/hardware/run_mini_first_boot_v7_released_ping.py'),[])
        self.assertEqual(broker.job_arguments('access','execute',
            'analysis/hardware/probe_mini_exclusive_access.py'),['--execute'])

    def test_traversal_absolute_ADS_and_windows_alias_paths_rejected(self):
        for name in ('../x','/x','C:/x','\\\\server\\x','analysis/../x',
                     'analysis/hardware/x:stream','analysis//hardware','analysis/hardware./x',
                     'analysis/hardware /x','analysis\\hardware'):
            with self.subTest(name=name),self.assertRaises(ValueError):
                broker.safe_path(name,root=self.root)

    def test_reparse_and_symlink_attributes_rejected(self):
        for info in (SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400),
                     SimpleNamespace(st_mode=stat.S_IFLNK,st_file_attributes=0)):
            fake=SimpleNamespace(lstat=lambda:info)
            with self.assertRaises(ValueError):broker._no_reparse(fake)

    def test_every_source_pin_checked_and_runner_required(self):
        job,package=self.claim()
        (self.root/self.runner).write_text('changed after registration')
        with self.assertRaises(ValueError):broker.validate_package(package,root=self.root)
        (self.root/self.runner).write_text('raise SystemExit(0)\n')
        forged=copy.deepcopy(package);forged['runner_sha256']='0'*64
        with self.assertRaises(ValueError):broker.validate_package(forged,root=self.root)

    def test_catalog_and_manifest_hash_changes_stop_before_execution(self):
        queued=self.submit();catalog=self.directory/'catalog'/(queued['job_id']+'.json')
        catalog.write_bytes(catalog.read_bytes()+b' ')
        with self.assertRaises(ValueError):
            broker.claim_job(self.directory,self.config,self.directory/'pending'/(queued['job_id']+'.json'),root=self.root)
        self.assertTrue((self.directory/'claimed'/(queued['job_id']+'.json')).exists())
        (self.directory/'session.json').write_text('{}')
        with self.assertRaises(ValueError):
            broker.load_session(self.info['session'],self.info['session_sha256'],root=self.root)

    def test_replayed_claim_is_never_launched_again(self):
        queued=self.submit();request=self.directory/'pending'/(queued['job_id']+'.json')
        raw=request.read_bytes()
        broker.claim_job(self.directory,self.config,request,root=self.root)
        request.write_bytes(raw)
        with self.assertRaises(FileExistsError):broker.claim_job(self.directory,self.config,request,root=self.root)

    def test_only_one_pending_or_claimed_job_no_queue_ahead(self):
        queued=self.submit()
        with self.assertRaises(ValueError):self.submit()
        broker.claim_job(self.directory,self.config,self.directory/'pending'/(queued['job_id']+'.json'),root=self.root)
        with self.assertRaises(ValueError):self.submit()

    def test_submission_lock_never_retried(self):
        (self.directory/'submission.lock').write_text('retained crash marker')
        with self.assertRaises(FileExistsError):self.submit()
        self.assertFalse(list((self.directory/'pending').iterdir()))

    def test_timeout_and_stop_reject_new_jobs_without_any_process(self):
        with self.assertRaises(ValueError):self.submit(now=1060)
        (self.directory/'STOP').write_text('stop')
        with self.assertRaises(ValueError):self.submit()

    def test_previous_completion_requires_explicit_reviewed_id_and_timestamp(self):
        job='a'*32
        broker.publish(self.directory/'status.json',{'state':'awaiting_review','last_job_id':job,
            'last_exit_code':7,'last_completed_epoch':1002})
        with self.assertRaises(ValueError):self.submit(now=1003)
        with self.assertRaises(ValueError):self.submit(previous_job='b'*32,now=1003)
        with self.assertRaises(ValueError):self.submit(previous_job=job,now=1001)
        queued=self.submit(previous_job=job,now=1003)
        catalog=json.loads((self.directory/'catalog'/(queued['job_id']+'.json')).read_bytes())
        self.assertEqual(catalog['reviewed_previous_job_id'],job)

    def test_running_or_closed_session_rejects_explicit_future_submission(self):
        for state in ('running','stopped','stopped_error'):
            broker.publish(self.directory/'status.json',{'state':state})
            with self.subTest(state=state),self.assertRaises(ValueError):self.submit()

    def test_child_is_fixed_python_no_shell_and_job_result_is_not_hardware_success(self):
        job,package=self.claim();child=FakeChild();calls=[]
        def popen(command,**kwargs):calls.append((command,kwargs));return child
        result,overrun=broker.execute_claimed(self.directory,job,package,self.config,root=self.root,
            popen=popen,sleep=lambda _:None)
        command,kwargs=calls[0]
        self.assertEqual(command,[self.config['python_path'],'-I','-B','-X','utf8',str(self.root/self.runner),'--execute'])
        self.assertFalse(kwargs['shell']);self.assertEqual(kwargs['cwd'],str(self.root.resolve()))
        self.assertEqual(result['exit_code'],0);self.assertTrue(result['exit_code_does_not_prove_hardware_success'])
        self.assertFalse(overrun);self.assertEqual(len(calls),1)

    def test_active_timeout_waits_without_kill_or_retry_and_closes_new_submissions(self):
        job,package=self.claim();package['timeout_seconds']=1
        child=FakeChild(polls=8);clock=[0.0];calls=[]
        def tick(_):clock[0]+=.5
        def popen(*args,**kwargs):calls.append(args);return child
        result,overrun=broker.execute_claimed(self.directory,job,package,self.config,root=self.root,
            popen=popen,sleep=tick,monotonic=lambda:clock[0])
        self.assertTrue(overrun and result['deadline_or_stop_observed'])
        self.assertTrue((self.directory/'STOP').exists());self.assertEqual(len(calls),1)
        self.assertEqual(child.returncode,0)

    def test_journal_failure_after_launch_waits_for_child_and_never_relaunches(self):
        job,package=self.claim();child=FakeChild(polls=20);original=broker.publish;failed=[False]
        def publish(path,value):
            if value.get('state')=='running' and not failed[0]:
                failed[0]=True;raise OSError('mock publication failure')
            original(path,value)
        with patch.object(broker,'publish',side_effect=publish),self.assertRaises(OSError):
            broker.execute_claimed(self.directory,job,package,self.config,root=self.root,
                popen=lambda *a,**k:child,sleep=lambda _:None)
        self.assertEqual(child.wait_calls,1)
        self.assertEqual(json.loads((self.directory/'results'/(job+'.json')).read_bytes())['state'],'broker_job_error')

    def test_nonzero_child_keeps_admin_broker_waiting_for_new_explicit_review(self):
        queued=self.submit();observed=[]
        def execute(directory,job,package,config,**kwargs):
            result={'state':'completed','exit_code':7}
            broker.publish(directory/'results'/(job+'.json'),result)
            return result,False
        def idle(_):
            state=json.loads((self.directory/'status.json').read_bytes());observed.append(state)
            self.assertEqual(state['state'],'awaiting_review')
            self.assertEqual(state['last_job_id'],queued['job_id'])
            self.assertEqual(state['last_exit_code'],7)
            broker.publish(self.directory/'STOP',{'test_stop':True})
        fake_windows=SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda:True))
        with patch.object(broker.ctypes,'windll',fake_windows),patch.object(broker.time,'time',return_value=1002),\
             patch.object(broker.time,'sleep',side_effect=idle),patch.object(broker,'execute_claimed',side_effect=execute):
            broker.serve(self.info['session'],self.info['session_sha256'],root=self.root)
        self.assertEqual(len(observed),1)


if __name__=='__main__':unittest.main()
