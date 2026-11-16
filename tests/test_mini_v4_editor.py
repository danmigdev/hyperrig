import json
from pathlib import Path
import subprocess

from tests.test_mini_installer_bundle import PackageTests
from tools import build_mini_installer_bundle as bundle
from tools import derive_mini_v4_editor as v4


class QualifiedV4PackageTests(PackageTests):
    VARIANT = 'v4'

    @classmethod
    def setUpClass(cls):
        files, info = bundle.editor_assets(bundle.DEFAULT_EDITOR, variant='v4')
        cls.editor_files, cls.editor_info = v4.derive(files, info)

    def test_changed_evidence_cannot_be_promoted_by_resealing(self):
        name = 'editor/qualification.json'
        scope = json.loads((self.root / name).read_bytes())
        scope['baseline_restoration_verified'] = False
        raw = bundle.encoded(scope)
        (self.root / name).write_bytes(raw)
        self.manifest['files'][name] = bundle.sha(raw)
        self.publish()
        with self.assertRaisesRegex(ValueError, 'evidence or presentation differs'):
            self.check()

    def test_native_trial_replays_through_unchanged_editor_policy(self):
        payload = {'profile': json.loads(self.editor_files['editor/profile.json']),
                   'source': self.editor_files['editor/web/mini-profile.js'].decode(),
                   'rows': [json.loads(row) for row in (v4.REPORT.parent / 'wire.jsonl').read_bytes().splitlines()]}
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
globalThis.HYPERRIG_MINI_BUILD=input.profile; vm.runInThisContext(input.source);
let current=null, identified=false, tested=new Set();
for(const row of input.rows) {
  if(row.event==='tx') current={command:row.command, lines:[]};
  if(row.event==='line') current.lines.push(row.line);
  if(row.event!=='complete') continue;
  if(current.command==='PING') {
    assert.equal(HyperRigMini.acceptPong(current.lines.at(-1),'usb-cdc').write,true);
    identified=true; continue;
  }
  assert.equal(identified,true);
  const family=current.command.split(' ')[0];
  const permitted=HyperRigMini.commandPolicy(current.command,'usb-cdc').allowed;
  if(family==='PDEL') { assert.equal(permitted,false); continue; }
  assert.equal(permitted,true,current.command+' must pass the qualified policy');
  if(current.command.includes(' ')) tested.add(family);
  HyperRigMini.observeReply(current.command,current.lines,false,'usb-cdc');
}
assert.deepEqual([...tested].sort(),input.profile.family_capabilities['usb-cdc'].slice().sort());
assert.equal(HyperRigMini.fullWriteEnabled(),false);
assert.equal(HyperRigMini.familyWriteEnabled('ble-nus'),false);
for(const command of ['FXA Q 99 unknown','PLOAD 32','FXP 999 0 0','GAIN 13 0','FSPRESS 0','PDEL 0'])
  assert.equal(HyperRigMini.commandPolicy(command,'usb-cdc').allowed,false,command);
process.stdout.write('pass');
'''
        result = subprocess.run(['node', '-e', script], input=json.dumps(payload), text=True, capture_output=True, timeout=15)
        self.assertEqual((result.returncode, result.stdout), (0, 'pass'), result.stderr)

    def test_no_private_raw_records_in_editor_metadata(self):
        for name in ('editor/profile.json', 'editor/qualification.json', 'editor/DERIVATION.txt'):
            value = self.editor_files[name].decode()
            for text in ('COM3', 'Preset 1A', 'analysis/hardware', 'GUI_session', 'Users\\'):
                self.assertNotIn(text, value)
