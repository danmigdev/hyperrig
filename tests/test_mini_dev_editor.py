"""The development editor of builds from source: what its policy permits, what it claims, and what stays unchanged."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_mini_dev_editor as editor

ROOT = Path(__file__).resolve().parents[1]
AREA = {'area_sha256': 'a' * 64, 'record_sha256': 'b' * 64, 'source_files': 1}
PONG = 'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11'
WIRE = ROOT / 'build/mini-v4-controls-01/wire.jsonl'


def node(script, payload):
    done = subprocess.run(['node', '-e', script], input=json.dumps(payload), capture_output=True, text=True,
                          encoding='utf-8', timeout=60)
    if done.returncode:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


HEAD = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
globalThis.HYPERRIG_MINI_BUILD=input.profile; vm.runInThisContext(input.rules); vm.runInThisContext(input.source);
const allowed=(c,t='usb-cdc')=>HyperRigMini.commandPolicy(c,t).allowed;
'''


@unittest.skipUnless(editor.BASE.is_dir(), 'the v4 editor package is not here')
class DevelopmentEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = editor.files_of(AREA)
        cls.profile = json.loads(cls.files['editor/profile.json'])
        cls.policy = cls.files['editor/web/mini-profile.js'].decode('utf-8')
        cls.tested_policy = (ROOT / 'app/mini/mini-profile-fx.js').read_text(encoding='utf-8')
        cls.v4_profile = json.loads((editor.BASE / 'profile.json').read_bytes())

    def payload(self, profile=None, source=None, **more):
        return {'profile': profile or self.profile, 'source': source or self.policy, 'pong': PONG,
                'rules': self.files['editor/web/mini-dev-rules.js'].decode('utf-8'), **more}

    def test_tap_and_tuner_within_the_firmware_limits_over_usb_only(self):
        node(HEAD + r'''
assert.equal(allowed('BPM 1200'),false,'before identification');
const id=HyperRigMini.acceptPong(input.pong,'usb-cdc');
assert.equal(id.ok,true); assert.equal(id.write,true); assert.equal(id.write_scope,'protocol-families');
for(const c of ['BPM','BPM 400','BPM 1200','BPM 3000','TUNER','TUNE','TUNER 0','TUNER 1 0 440','TUNER 1 1 415','TUNER 0 1 466'])
  assert.equal(allowed(c),true,c);
for(const c of ['AMP 0','AMP 1','AMPX 0','AMPX 1','AMPX 1 2','AMPEQ','AMPEQ 0 600','AMPEQ 5 -1200','AMPEQ 0 0 0 0 0',
                'AMPEQ 0 0 0 0 0 0','STW 0','STW 100','PNEW','FXMIX P 0 0 0','FXXO Q 1 800 1','FSA','FSA 0 0 1 0 255','FSMODE',
                'FSMODE layout=scenes','FSPRESS 2 1','FSLED 0 auto','FSLED 3 ff0000 200000','LEDCFG bright=80','FSDO a','FSDO ab hold',
                'GSAVE','PCOLOR none','PCOLOR 00ff88'])
  assert.equal(allowed(c),true,c);
for(const c of ['AMP','AMP 2','AMP 01','AMPX 2','AMPEQ 6 0','AMPEQ 0','AMPEQ 0 0 0','AMPEQ 0 40000','AMPEQ 0 0 0 0 0 0 0',
                'AMPEQ 0  1','AMPEQ reset','STW 50','PNEW 1','FXMIX R 0 0 0','FXMIX P 4 0 0','FXXO P 0 -1','FSA 4 0 1 0 0',
                'FSA 0 3 1 0 0','FSA 0 0 1 256 0','FSMODE layout=other','FSPRESS 4 1','FSLED 0 red','LEDCFG colour=1','FSDO e',
                'GSAVE all','PCOLOR red']) assert.equal(allowed(c),false,c);
for(const c of ['BPM 399','BPM 3001','BPM 120.0','BPM -1','BPM 0400','TUNER 1','TUNER 2 0 440','TUNER 1 2 440',
                'TUNER 1 1 414','TUNER 1 1 467','TUNER 1 1 440 1','TAP'])
  assert.equal(allowed(c),false,c);
HyperRigMini.acceptPong(input.pong,'ble-nus');
for(const c of ['BPM 1200','TUNER 0','AMP 1','AMPEQ 0 0','GAIN 0 0']) assert.equal(allowed(c,'ble-nus'),false,'BLE '+c);
''', self.payload())

    def test_everything_else_stays_blocked(self):
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
for(const c of ['CSAVE 0 A','CLOAD 0','CDEL 0','CTRIM 0 0','CALIB 1','ISAVE 0 A','ILOAD 0','IDEL 0','IRBEGIN 1','LDBEGIN 1','GEQ 0 0',
                'LIM 1 0 0','HPF 80','SPUR 1','GLIDE 1','SPILL 1','LEDTEST boot','BLE key','BLE pair 1','UBOOT','AUTH x','FACTORY'])
  assert.equal(allowed(c),false,c);
for(const c of ['PDEL 0','PNAME 0 A','PLOAD 0','GAIN 0 0','FXA Q 99 gate','FXM 0 P 0','FXL 0 1','FXR 0','FXOS 0 1','SNAP 0','SNAPDEL 0',
                'SNAPNAME 0 A'])
  assert.equal(allowed(c),false,c);      // these still need what the pedal reported
assert.equal(HyperRigMini.fullWriteEnabled(),false);
''', self.payload())

    def test_the_tested_policy_gives_a_development_profile_nothing(self):
        node(HEAD + r'''
const id=HyperRigMini.acceptPong(input.pong,'usb-cdc');
assert.equal(id.write,false);
for(const c of ['BPM 1200','TUNER 0','TUNER 1 0 440','AMP 0','AMPEQ 0 0','GAIN 0 0']) assert.equal(allowed(c),false,c);
''', self.payload(source=self.tested_policy))

    def test_the_new_policy_gives_the_qualified_v4_profile_nothing_more(self):
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
for(const c of ['BPM 1200','TUNER 0','TUNER 1 0 440','AMP 0','AMPEQ 0 0']) assert.equal(allowed(c),false,c);
const p=JSON.parse(JSON.stringify(input.profile));
p.hardware_verified=false; p.development={kind:'source-build',commands_qualified_on_this_build:true};
globalThis.HYPERRIG_MINI_BUILD=p; vm.runInThisContext(input.source);
assert.equal(HyperRigMini.developmentBuild(),false,'a profile that claims qualification is no development build');
''', self.payload(profile=self.v4_profile))

    LIVE = r'''
const see=(c,...l)=>HyperRigMini.observeReply(c,l,false,'usb-cdc');
const LVL=p=>`LVL in=-240 out=-253 m=2 g=0/0 b=1200 s=0 a=1 am=118688 c=5 p=${p} tu=0 lim=0`;
const FXS=(...b)=>see('FXS',...b.map(([bank,i,id,type,lane=0])=>`FX ${bank}${i} id=${id} ${type} on=1 p=0,0,0,0,0,0,0 ticks=1 l=${lane} g=-1 fu=0 mem=0`),
  'FXS amp=1 on=1','FXS peak=0 ticks skipped=0');
HyperRigMini.acceptPong(input.pong,'usb-cdc');
see('FXT','FXT 1 gate cost=490 cat=dynamics mem=0','FXT  0 umbral_db -90..0 (-70)','FXT 2 boost cost=340 cat=drive mem=0',
  'FXT  0 ganancia_db -12..24 (6)','FXT end');
see('PLIST',"PRE 0 1 -1 -1 'One' t=q1 s=1","PRE 1 1 -1 -1 'Two' t=q1 s=1",'PLIST end current=1');
FXS(['Q',0,0,'gate']); see('SNAPS','SNAPS 1000 current=0'); see('LVL',LVL(1));
'''

    def test_after_a_footswitch_the_editor_still_edits_and_saves(self):
        # The page's order after a preset change of the pedal: LVL, FXS, SNAPS, PLIST. The v4 policy threw FXS and SNAPS
        # away when PLIST showed the new preset, and refused every edit and Save.
        after = r'''
assert.equal(allowed('SNAPSAVE 0'),true);
see('LVL',LVL(0)); FXS(['Q',0,0,'gate']); see('SNAPS','SNAPS 1000 current=0');
see('PLIST',"PRE 0 1 -1 -1 'One' t=q1 s=1","PRE 1 1 -1 -1 'Two' t=q1 s=1",'PLIST end current=0');
const now=['SNAPSAVE 0','FXE 0 0','FXP 0 0 -60','SNAP 0'].map(c=>allowed(c));
'''
        node(HEAD + self.LIVE + after + "assert.deepEqual(now,[true,true,true,true]);", self.payload())
        node(HEAD + self.LIVE + after + "assert.deepEqual(now,[false,false,false,false]);",
             self.payload(profile=self.v4_profile, source=self.tested_policy))

    def test_a_preset_change_clears_what_was_read_before_it(self):
        node(HEAD + self.LIVE + r'''
see('LVL',LVL(0));
for(const c of ['SNAPSAVE 0','SNAP 0','FXE 0 0','FXP 0 0 -60','FXM 0 P 0']) assert.equal(allowed(c),false,c);
''', self.payload())

    def test_blocks_are_followed_through_adds_moves_lanes_and_removals(self):
        node(HEAD + self.LIVE + r'''
assert.equal(allowed('FXA P 99 boost'),true); assert.equal(allowed('FXA P 1 boost'),false); assert.equal(allowed('FXA P 99 laser'),false);
see('FXA P 99 boost','FXA id=1 boost','FX cpu=490/21418 ticks (2%) mem_fx=0 B');
assert.equal(allowed('FXM 1 Q 1'),true); assert.equal(allowed('FXM 2 Q 0'),false); assert.equal(allowed('FXM 1 Q 16'),false);
see('FXM 1 Q 1','FXM ok cpu=0/20762 ticks (0%) mem_fx=0 B');
assert.equal(allowed('FXL 1 2'),true); assert.equal(allowed('FXL 1 3'),false);
see('FXL 1 2','FXL ok 1 2');
assert.equal(allowed('FXR 1'),true); assert.equal(allowed('FXA Q 99 gate'),true);
assert.equal(HyperRigMini.preflight(['FXR 0','FXR 1'],'usb-cdc').allowed,true);
assert.equal(HyperRigMini.preflight(['FXR 0','FXM 0 P 0'],'usb-cdc').allowed,false,'a removed block is not moved');
see('FXR 1','FXR ok cpu=0/20762 ticks (0%) mem_fx=0 B');
assert.equal(allowed('FXR 1'),false); assert.equal(allowed('FXR 0'),true);
see('FXM 0 P 0','ERR FXM no such block'); assert.equal(allowed('FXR 0'),true,'a refused move changes nothing known');
''', self.payload())

    def test_a_section_holds_ten_blocks(self):
        node(HEAD + self.LIVE + r'''
FXS(...Array.from({length:10},(_,i)=>['P',i,i,'gate']),['Q',0,10,'gate']);
assert.equal(allowed('FXA P 99 gate'),false); assert.equal(allowed('FXA Q 99 gate'),true);
assert.equal(allowed('FXM 10 P 0'),false); assert.equal(allowed('FXM 3 P 0'),true); assert.equal(allowed('FXM 3 Q 0'),true);
''', self.payload())

    def test_scenes_presets_and_a_new_chain(self):
        node(HEAD + self.LIVE + r'''
for(const c of ['SNAPNAME 0 Verse','SNAPNAME 0','SNAPDEL 0','PNAME 1 Lead','PDEL 0','PLOAD 0','PSAVE 2 New']) assert.equal(allowed(c),true,c);
for(const c of ['SNAPNAME 1 Verse','SNAPDEL 2','PNAME 5 Lead','PNAME 1 '+'x'.repeat(24),'PDEL 5']) assert.equal(allowed(c),false,c);
see('SNAP 0','SNAP ok 0 missing=0 ms=0'); assert.equal(allowed('FXP 0 0 -60'),true,'a scene keeps the blocks');
see('PNEW','PNEW ok');
for(const c of ['SNAPSAVE 0','FXP 0 0 -60','SNAP 0']) assert.equal(allowed(c),false,c);
assert.equal(HyperRigMini.preflight(['PSAVE 2 New'],'usb-cdc').allowed,false,'the new chain is read first');
FXS(); assert.equal(HyperRigMini.preflight(['PSAVE 2 New'],'usb-cdc').allowed,true);
''', self.payload())

    @unittest.skipUnless(WIRE.is_file(), 'the recorded v4 trial is not here')
    def test_the_recorded_v4_trial_replays_through_the_new_policy(self):
        out = node(HEAD + r'''
let current=null, tested=new Set();
for(const row of input.rows) {
  if(row.event==='tx') current={command:row.command, lines:[]};
  if(row.event==='line') current.lines.push(row.line);
  if(row.event!=='complete') continue;
  if(current.command==='PING') { HyperRigMini.acceptPong(current.lines.at(-1),'usb-cdc'); continue; }
  const family=current.command.split(' ')[0], permitted=allowed(current.command);
  assert.equal(permitted,true,current.command);
  if(current.command.includes(' ')) tested.add(family);
  HyperRigMini.observeReply(current.command,current.lines,false,'usb-cdc');
}
process.stdout.write([...tested].sort().join(' '));
''', self.payload(rows=[json.loads(row) for row in WIRE.read_bytes().splitlines()]))
        self.assertEqual(out.split(), sorted(editor.FAMILIES + ['PDEL']))

    def test_it_claims_no_qualification_and_says_so(self):
        self.assertIs(self.profile['hardware_verified'], False)
        self.assertEqual((self.profile['family_validation'], self.profile['family_qualification']), ({}, {}))
        self.assertIs(self.profile['development']['commands_qualified_on_this_build'], False)
        self.assertEqual(self.profile['image_sha256'], AREA['area_sha256'])
        scope = json.loads(self.files['editor/qualification.json'])
        self.assertIs(scope['hardware_verified'], False)
        self.assertIs(scope['audio_tested'], False)
        ui = self.files['editor/web/mini-ui.js'].decode('utf-8')
        self.assertIn('not qualified', ui)
        self.assertEqual(ui.count(editor.REVISION), 2, 'the tab title and the bar name the revision')
        page = self.files['editor/web/tank-mini.html'].decode('utf-8')
        self.assertNotIn('v4 preview', page)
        self.assertIn('MINI source build', page)

    def test_the_page_holds_the_same_profile(self):
        page = self.files['editor/web/tank-mini.html'].decode('utf-8')
        embedded, _ = json.JSONDecoder().raw_decode(page.split(editor.MARKER, 1)[1])
        self.assertEqual(embedded, self.profile)

    def test_the_protocol_code_of_the_page_is_the_v4_one(self):
        # Only the profile, three version labels and the changes for a new preset differ.
        old = (editor.BASE / 'web/tankmini.html').read_bytes().decode('utf-8')
        new = self.files['editor/web/tank-mini.html'].decode('utf-8')
        for before, after in editor.PAGE:
            new = new.replace(after, before)
        strip = lambda h: (h.split(editor.MARKER, 1)[0],
                           h.split(editor.MARKER, 1)[1][json.JSONDecoder().raw_decode(h.split(editor.MARKER, 1)[1])[1]:])
        self.assertEqual(strip(old), strip(new))

    def test_a_changed_input_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as temp:
            base = Path(temp) / 'editor'
            shutil.copytree(editor.BASE, base)
            path = base / 'web/mini-profile.js'
            path.write_bytes(path.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'pinned editor file differs'):
                editor.files_of(AREA, base)

    def test_a_changed_bundle_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as temp:
            out = Path(temp) / 'bundle'
            with mock.patch.object(editor, 'area_of', return_value=AREA):
                editor.build(out, 'ignored')
            self.assertEqual(editor.check(out)['result'], 'pass')
            path = out / 'editor/profile.json'
            profile = json.loads(path.read_bytes())
            profile['hardware_verified'] = True
            path.write_bytes(editor.encoded(profile))
            with self.assertRaisesRegex(ValueError, 'a bundle file differs'):
                editor.check(out)
            meta = json.loads((out / 'bundle.json').read_bytes())
            meta['files']['editor/profile.json'] = editor.sha(path.read_bytes())
            (out / 'bundle.json').write_bytes(editor.encoded(meta))
            with self.assertRaisesRegex(ValueError, 'claims more than it may'):
                editor.check(out)

    def test_a_damaged_build_gets_no_editor(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as temp:
            directory = Path(temp)
            image = b'area'
            (directory / 'hyperrig-mini.app-area.bin').write_bytes(image)
            for capture, good in (({'intact': True}, True), ({'intact': False}, False), (None, False)):
                manifest = {'area_sha256': editor.sha(image), 'source_sha256': {}}
                if capture is not None:
                    manifest['embedded_capture'] = capture
                (directory / 'build-manifest.json').write_bytes(editor.encoded(manifest))
                if good:
                    self.assertEqual(editor.area_of(directory)['area_sha256'], editor.sha(image))
                else:
                    with self.assertRaisesRegex(ValueError, 'embedded capture'):
                        editor.area_of(directory)


@unittest.skipUnless(editor.BASE.is_dir(), 'the v4 editor package is not here')
class ProductEditor(unittest.TestCase):
    PRODUCT = {'version': '0.2.0-dev.1', 'build_id': '0123456789abcdef'}

    @classmethod
    def setUpClass(cls):
        cls.area = {**AREA, 'product': cls.PRODUCT}
        cls.files = editor.files_of(cls.area)
        cls.profile = json.loads(cls.files['editor/profile.json'])
        cls.page = cls.files['editor/web/tank-mini.html'].decode('utf-8')

    def payload(self, **more):
        return {'profile': self.profile, 'source': self.files['editor/web/mini-profile.js'].decode('utf-8'), 'pong': PONG,
                'rules': self.files['editor/web/mini-dev-rules.js'].decode('utf-8'), **more}

    def test_changes_only_on_the_build_it_is_for(self):
        node(HEAD + r'''
const changes=['GAIN 0 0','BPM 1200','TUNER 0','AMP 0','STW 100','PNEW','GSAVE','KNOB off','FSDO a','FSMODE mode=live'];
const reads=['PING','HRID','HRST','KNOB','FXT','FXS','PLIST','LVL','FSMODE','TUNER'];
const right='HRID 1 0.2.0-dev.1 0123456789abcdef banks=3';
assert.equal(HyperRigMini.acceptPong(input.pong,'usb-cdc').ok,true);
for(const c of reads) assert.equal(allowed(c),true,c);
for(const c of changes) assert.equal(allowed(c),false,'before HRID: '+c);
for(const lines of [['HRID 1 0.2.0-dev.1 0123456789abcdee banks=3'],['HRID 1 0.2.0 0123456789abcdef banks=3'],['ERR unknown command'],[],null,
                    ['HRID 1 0.2.0-dev.1 0123456789abcdef banks=4'],['HRID 2 0.2.0-dev.1 0123456789abcdef banks=3'],['x '+right]]) {
  const b=HyperRigMini.acceptBuild(lines); assert.equal(b.same,false);
  for(const c of changes) assert.equal(allowed(c),false,JSON.stringify(lines)+c);
  for(const c of reads) assert.equal(allowed(c),true,c);
}
assert.deepEqual(HyperRigMini.acceptBuild([right]),{known:true,same:true,version:'0.2.0-dev.1',build_id:'0123456789abcdef'});
HyperRigMini.observeReply('LVL',['LVL in=-240 out=-253 g=0/0 b=1200 p=-1'],false,'usb-cdc');
for(const c of changes) assert.equal(allowed(c),true,c);
for(const c of ['KNOB 5','KNOB on off','UBOOT','BLE forget','AUTH x','CALIB sens 12','HRID x']) assert.equal(allowed(c),false,c);
assert.equal(allowed('BPM 1200','ble-nus'),false,'not over Bluetooth');
HyperRigMini.acceptPong(input.pong,'usb-cdc');
for(const c of changes) assert.equal(allowed(c),false,'after a new connection: '+c);
HyperRigMini.acceptBuild([right]); HyperRigMini.resetIdentity(); HyperRigMini.acceptPong(input.pong,'usb-cdc');
for(const c of changes) assert.equal(allowed(c),false,'after the identity was reset: '+c);
''', self.payload())

    def test_no_bluetooth_from_a_computer_yet(self):
        self.assertIn('  available() { return !!capBle(); },', self.page)
        self.assertNotIn('navigator.bluetooth && navigator.bluetooth.requestDevice); },', self.page)

    def test_midi_settings_are_permitted_as_the_firmware_takes_them(self):
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
assert.equal(allowed('MIDI'),true);
const plain='010001141516171807'+'66'+'ff00000064'.repeat(4), at=(i,v)=>'MIDI ='+plain.slice(0,2*i)+v+plain.slice(2*i+2);
const right=['MIDI on','MIDI off','MIDI ='+plain,at(0,'00'),at(1,'10'),at(1,'ff'),at(2,'10'),at(2,'ff'),at(3,'00'),at(6,'ff'),at(8,'77'),at(9,'68'),at(10,'0b'),at(11,'0f'),at(12,'06'),at(13,'64'),at(29,'00')];
for(const c of right) assert.equal(allowed(c),false,'before HRID: '+c);
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
for(const c of right) assert.equal(allowed(c),true,c);
for(const c of ['MIDI >c005','MIDI x','MIDI on off','MIDI =','MIDI ='+plain+'00','MIDI ='+plain.slice(2),'MIDI ='+plain.toUpperCase(),'MIDI = '+plain,at(0,'02'),at(1,'11'),at(2,'00'),at(2,'11'),at(3,'78'),at(9,'69'),
  at(10,'78'),at(11,'10'),at(12,'07'),at(13,'65'),at(29,'65'),'midi on']) assert.equal(allowed(c),false,c);
assert.equal(allowed('MIDI on','ble-nus'),false,'not over Bluetooth');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 ffffffffffffffff banks=3']);
for(const c of right) assert.equal(allowed(c),false,'another build: '+c);
''', self.payload())
        for text in ('<script src="product-midi.js"></script>', '/^(MIDI =|GEQ', 'hrMidiLines()', 'await hrMidiSay("")'):
            self.assertIn(text, self.page)

    def test_a_scene_without_a_preset_stays_in_the_pedals_memory(self):
        """An import saves its scenes before its preset has a slot: allowed when the pedal says that no preset is loaded, and only then."""
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
const say=(c,lines)=>HyperRigMini.observeReply(c,lines,false,'usb-cdc');
assert.equal(allowed('SNAPSAVE 0'),false,'nothing is known');
say('PLIST',["PRE 3 0 -1 -1 'A' t=- s=1",'PLIST end current=3']); say('SNAPS',['SNAPS 10000000 current=0']);
assert.equal(allowed('SNAPSAVE 1'),true,'a loaded preset');
say('PNEW',['PNEW ok']);
assert.equal(allowed('SNAPSAVE 1'),false,'the scenes are not known after PNEW');
say('SNAPS',['SNAPS 00000000 current=-1']);
for(const k of [0,1,2,3,4,5,6,7]) assert.equal(allowed('SNAPSAVE '+k),true,'no preset is loaded: '+k);
for(const c of ['SNAPSAVE 8','SNAPSAVE','SNAPSAVE 0 x','SNAP 0','SNAPNAME 0 A']) assert.equal(allowed(c),false,c);
say('SNAPSAVE 6',['SNAPSAVE ok 6 preset=-1']); assert.equal(allowed('SNAP 6'),true); assert.equal(allowed('SNAPNAME 6 Far'),true); assert.equal(allowed('SNAP 7'),false);
say('SNAPSAVE 2',['SNAPSAVE ok 2 preset=-1']);
assert.equal(allowed('SNAPNAME 2 Chorus'),true); assert.equal(allowed('SNAP 2'),true); assert.equal(allowed('SNAPNAME 1 A'),false); assert.equal(allowed('SNAPSAVE 0'),true);
say('LVL',['LVL in=-240 out=-253 g=0/0 b=1200 p=5']);
assert.equal(allowed('SNAPSAVE 0'),false,'a preset was loaded on the pedal in the middle of it');
say('PLIST',["PRE 5 0 -1 -1 'A' t=- s=7",'PLIST end current=5']); say('SNAPS',['SNAPS 11100000 current=1']);
say('SNAPDEL 1',['SNAPDEL ok 1 preset=5']);
assert.equal(allowed('SNAP 1'),false,'it is gone'); assert.equal(allowed('SNAP 2'),true); assert.equal(allowed('SNAPSAVE 1'),true,'and can be made again');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 ffffffffffffffff banks=3']);
say('PNEW',['PNEW ok']); say('SNAPS',['SNAPS 00000000 current=-1']);
assert.equal(allowed('SNAPSAVE 0'),false,'another build');
''', self.payload())

    def test_the_measure_of_loudness(self):
        """Strokes within the pedal's memory, runs of a few seconds, gains into presets that are there; a refusal loses nothing of what is known."""
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
const keep='7f7f7f7f7f7f7f7f';
for(const c of ['HRLV','HRLV 0203'+'7f'+keep]) assert.equal(allowed(c),false,'before HRID: '+c);
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
const say=(c,lines)=>HyperRigMini.observeReply(c,lines,false,'usb-cdc');
assert.equal(allowed('HRLV 020301'+keep),false,'the presets are not known');
say('PLIST',["PRE 3 0 -1 -1 'A' t=- s=1",'PLIST end current=3']); say('SNAPS',['SNAPS 10000000 current=0']);
for(const c of ['HRLV','HRLV 01','HRLV 05','HRLV 06b002406c','HRLV 06b0034098','REC 4 184','REC 4 1142','RECD 0','RECD 1120','INJBEGIN 1408','INJB 0 0123456789abcdef','INJB 2815 ff',
                'HRLV 0203e2'+keep,'HRLV 02030c0c00e27f7f7f7f7f','HRLV 02037f'+keep]) assert.equal(allowed(c),true,c);
for(const c of ['HRLV 00','HRLV 02','HRLV 03','HRLV 06','HRLV 06b1024040','HRLV 06b0094040','HRLV 06b0024099','HRLV 06b0024000','HRLV 06B002406C','HRLV 05 1','HRLV 0203e1'+keep,'HRLV 02030d'+keep,
                'HRLV 020400'+keep,'HRLV 0203'+keep,'HRLV 020300'+keep+'00','REC 4 8192','REC 1 184','REC','REC free','RECD','RECD 01','INJBEGIN 1409','INJBEGIN 0','INJ on','INJ','INJB 2815 ffff','INJB 0 f',
                'INJB 0 xy','INJB 0 '+'00'.repeat(91)]) assert.equal(allowed(c),false,c);
assert.equal(allowed('HRLV 05','ble-nus'),false,'not over Bluetooth');
say('RECD 0',['ERR RECD nothing at 0 (recorded 0)']); say('REC 4 184',['ERR REC out of memory']); HyperRigMini.observeReply('HRLV',[],true,'usb-cdc');
assert.equal(allowed('SNAP 0'),true,'what is known of the preset'); assert.equal(allowed('PLOAD 3'),true);
''', self.payload())

    def test_a_name_does_not_lose_the_list_of_the_presets(self):
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
assert.equal(allowed('PNAME'),true,'what the page asks');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
const say=(c,lines)=>HyperRigMini.observeReply(c,lines,false,'usb-cdc');
say('PLIST',["PRE 3 0 -1 -1 'A' t=- s=1","PRE 4 0 -1 -1 'B' t=- s=1",'PLIST end current=3']); say('SNAPS',['SNAPS 10000000 current=0']);
say('PNAME',['ERR PNAME 0..31 <name>']);
assert.equal(allowed('PNAME 3 New name'),true); assert.equal(allowed('PNAME 5 X'),false); assert.equal(allowed('PNAME 3 '+'x'.repeat(24)),false);
say('PNAME 3 New name',["PNAME ok 3 'New name'"]);
for(const c of ['PLOAD 4','PNAME 4 Y','SNAPSAVE 0','SNAPNAME 0 Intro']) assert.equal(allowed(c),true,'after a name: '+c);
''', self.payload())

    def test_which_hyperrig_is_the_older_one(self):
        source = (ROOT / 'app/mini/product-ui.js').read_text(encoding='utf-8')
        function = source[source.index('function hrVersions('):source.index('async function hrUpdate(')]
        script = "const assert = require('node:assert');\n" + function + '''
const order = ['0.0.1', '0.2.0-dev.2', '0.2.0-dev.3', '0.2.0-dev.12', '0.2.0', '0.2.1-dev.1', '0.10.0', '1.0.0'];
order.forEach((a, i) => order.forEach((b, k) => assert.equal(hrVersions(a, b), Math.sign(i - k), a + ' ' + b)));
for (const v of ['', null, undefined, '0.2', 'x', '0.2.0-beta', '0.2.0-dev', '0.2.0 ']) { assert.equal(hrVersions(v, '0.2.0'), null); assert.equal(hrVersions('0.2.0', v), null); }
'''
        done = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stderr), (0, ''))

    def test_where_the_sections_of_a_chain_meet(self):
        source = (ROOT / 'app/mini/product-ui.js').read_text(encoding='utf-8')
        part = source[source.index('/* The places of the chain.'):source.index('/* Saving, in one line')]
        script = '''
const assert = require('node:assert'), PQ = ['P', 'Q'], FX_MAXGRP = 3, PIO_OS_P = 'os';
const pioObj = v => !!v && typeof v === 'object' && !Array.isArray(v), pioArr = v => Array.isArray(v) ? v : [], pioInt = v => Number.isInteger(v) ? v : null;
''' + part + '''
const one = n => Array.from({length: n}, () => ({n: 1})), least = (k, p) => [0, p], splits = n => Array.from({length: n}, () => ({n: 2, split: true}));
for (let n = 0; n <= 16; n++) assert.equal(hrMeet(one(n), null, least), Math.max(0, n - 10), 'of ' + n);
assert.equal(hrMeet(one(21), null, least), -1);
assert.equal(hrMeet([...one(4), {n: 8, split: true}, ...one(4)], null, least), -1);                      // four and eight on one side, four and eight on the other
assert.equal(hrMeet([...one(2), {n: 8, split: true}, ...one(6)], null, least), 3);
assert.equal(hrMeet(splits(6), null, least), 3);
assert.equal(hrMeet(splits(7), null, least), -1);
assert.equal(hrMeet(one(8), 4, least), 4);
assert.equal(hrMeet(one(12), 1, least), -1);
assert.equal(hrMeet(one(12), null, (k, p) => [k === 2 ? 1 : 0, p]), 3);                                  // not between two that belong together
assert.equal(hrMeet(one(12), null, (k, p) => [k === 2 || k < 0 ? 0 : 0, -p]), 10);
// the firmware's own table of drives that are worked as one
assert.equal(hrTogether({id: 9, os: 1}, {id: 10, os: 1}), true);
assert.equal(hrTogether({id: 9, os: 3}, {id: 10, os: 1}), true);
for (const [a, b] of [[{id: 9, os: 0}, {id: 10, os: 1}], [{id: 9, os: 1}, {id: 10, os: 3}], [{id: 9, os: 1}, {id: 16, os: 1}], [{id: 2, os: 1}, {id: 9, os: 1}], [null, {id: 9, os: 1}], [{id: 9, os: 1}, null]])
  assert.equal(hrTogether(a, b), false);
// the moves, in an order that no section overflows: ten and six, and two change places
const sim = {P: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], Q: [10, 11, 12, 13, 14, 15]}, tid = {P: [10, 0, 1, 2, 3, 4, 5, 6, 7, 8], Q: [9, 11, 12, 13, 14, 15]}, placed = new Set([0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15]), went = [];
for (const [b, id] of hrMoves(sim, tid, placed)) {
  for (const x of PQ) if (sim[x].includes(id)) sim[x].splice(sim[x].indexOf(id), 1);
  sim[b].splice(tid[b].indexOf(id), 0, id); placed.add(id); went.push(b + id);
  assert.ok(sim.P.length <= 10 && sim.Q.length <= 10, went.join());
}
assert.deepEqual([went, sim], [['Q9', 'P10'], tid]);
// a file: as it is when it fits, and when there is a capture; otherwise the place of the amp is found
const types = Object.fromEntries(['a', 'b', 'c'].map(n => [n, {id: 2, params: []}])), blocks = n => Array.from({length: n}, (_, i) => ({type: 'abc'[i % 3]})), off = {present: false}, where = c => c.findIndex(x => x.amp === true);
for (const c of [[...blocks(3), {amp: true}, ...blocks(5)], [...blocks(8)]]) assert.equal(hrImportChain(c, off, types), c);
assert.equal(where(hrImportChain(blocks(14), off, types)), 4);
assert.equal(where(hrImportChain([{amp: true}, ...blocks(16)], off, types)), 6);
assert.equal(where(hrImportChain([...blocks(20)], off, types)), 6);                                       // the last four are left out, as with a capture
assert.equal(where(hrImportChain([{amp: true}, ...blocks(3), {type: 'unknown'}, ...blocks(9)], off, types)), 2);
const c = [{amp: true}, ...blocks(14)];
assert.equal(hrImportChain(c, {present: true}, types), c); assert.equal(hrImportChain(c, undefined, types), c);
'''
        done = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stderr), (0, ''))

    def test_cab_irs(self):
        '''One upload at a time, its pieces within it; eight slots; an IR for a block that is one.'''
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
const always=['IRBEGIN 4076 -1500 48','IRBEGIN 1 0 24','IRBEGIN 4096 20000 48','IRBEGIN 0 0 48','ISAVE 0 My cab','ISAVE 7 V30 (SM57) è','ILOAD 0','IDEL 7',
              'IREAD 0','IREAD 7 8152'];
for(const c of always) assert.equal(allowed(c),false,'before HRID: '+c);
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
for(const c of always) assert.equal(allowed(c),true,c);
for(const c of ['IRBEGIN 4097 0 48','IRBEGIN -1 0 48','IRBEGIN 04 0 48','IRBEGIN 4 0 44','IRBEGIN 4 20001 48','IRBEGIN 4 -60001 48','IRBEGIN 4 0',
                'ISAVE 8 x','ISAVE 0','ISAVE 0 '+'x'.repeat(24),'ISAVE -1 x','ILOAD 8','ILOAD -1','IDEL 8','IDEL','IREAD 8','IREAD 0 01',
                'IRB 0 00','IREND 00000000','FXIR 0 0','LDB 0 00']) assert.equal(allowed(c),false,c);
const say=(c,lines)=>HyperRigMini.observeReply(c,lines,false,'usb-cdc');
say('IRBEGIN 4 0 48',['OK IRBEGIN 4']);
for(const c of ['IRB 0 0011223344556677','IRB 6 0011','IREND 1234abcd']) assert.equal(allowed(c),true,c);
for(const c of ['LDB 0 00','LDEND 1234abcd','IRB 7 0011','IRB 8 00','IRB 0 001','IRB 0 00AA','IRB 0','IREND 1234ABCD','IREND 123','IRB 0 '+'00'.repeat(96)]) assert.equal(allowed(c),false,c);
say('IREND 1234abcd',['IR ok 4 samples gain 0 mdB fs 48']);
assert.equal(allowed('IRB 0 00'),false,'the upload is closed');
say('IRBEGIN 4 0 48',['OK IRBEGIN 4']); say('IRBEGIN 0 0 48',['OK IRBEGIN 0']); assert.equal(allowed('IRB 0 00'),false,'dropped');
say('FXS',['FX Q0 id=3 ir on=1 p=0,0,0,21,0,0,0 ticks=1 irlen=1024/4076','FX Q1 id=4 gate on=1 p=0,0,0,0,0,0,0 ticks=1','FXS amp=1 on=1','FXS peak=1 ticks skipped=0']);
for(const c of ['FXIR 3 0','FXIR 3 7','FXIR 3 -1']) assert.equal(allowed(c),true,c);
for(const c of ['FXIR 3 8','FXIR 4 0','FXIR 5 0','FXIR 3 -2','FXIR 3']) assert.equal(allowed(c),false,c);
assert.equal(allowed('ISAVE 0 x','ble-nus'),false,'not over Bluetooth');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 ffffffffffffffff banks=3']);
for(const c of always) assert.equal(allowed(c),false,'another build: '+c);
''', self.payload())

    def test_captures(self):
        '''One upload at a time; fifteen slots; trims; the engine stopped and started around a load.'''
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
const always=['LDBEGIN 4892','LDBEGIN 0','LDBEGIN 8192','CSAVE 0 My amp','CSAVE 14 JCM','CLOAD 0','CLOAD 14','CDEL 9','CREAD 0','CREAD 14 4800','CTRIM live 1.5',
              'CTRIM live 0 123','CTRIM live 0.0 -','CTRIM 14 -12.0','CTRIM 3 12.0 400','CTRIM live 0 -200','AUDIO OFF','AUDIO A2L'];
for(const c of always) assert.equal(allowed(c),false,'before HRID: '+c);
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
for(const c of always) assert.equal(allowed(c),true,c);
for(const c of ['LDBEGIN 8193','LDBEGIN -1','LDBEGIN 01','LDBEGIN','CSAVE 15 x','CSAVE 0','CSAVE 0 '+'x'.repeat(24),'CLOAD 15','CLOAD -1','CDEL 15','CREAD 15',
                'CTRIM live 12.5','CTRIM live 0.3','CTRIM 15 0','CTRIM live 0 401','CTRIM live 0 -201','CTRIM live','AUDIO','AUDIO ON','AUDIO 2','LDB 0 00','LDEND 00000000','IRB 0 00']) assert.equal(allowed(c),false,c);
const say=(c,lines)=>HyperRigMini.observeReply(c,lines,false,'usb-cdc');
say('LDBEGIN 8',['OK LDBEGIN 8']);
for(const c of ['LDB 0 0011223344556677','LDB 7 00','LDEND 1234abcd']) assert.equal(allowed(c),true,c);
for(const c of ['LDB 7 0011','LDB 8 00','IRB 0 00','IREND 1234abcd','LDB 0 0']) assert.equal(allowed(c),false,c);
say('LDEND 1234abcd',["LOAD rc=0 name='A2' layers=23 channels=3 audio=0 engine=A2L ms=0"]);
assert.equal(allowed('LDB 0 00'),false,'the upload is closed');
say('LDBEGIN 8',['OK LDBEGIN 8']); say('IRBEGIN 4 0 48',['OK IRBEGIN 4']);
assert.equal(allowed('LDB 0 00'),false,'one upload at a time'); assert.equal(allowed('IRB 0 00'),true);
say('LDBEGIN 4',['ERR LDBEGIN out of memory']); say('LDBEGIN 4',['OK LDBEGIN 5']); assert.equal(allowed('LDB 0 00'),false,'another answer');
assert.equal(allowed('CSAVE 0 x','ble-nus'),false,'not over Bluetooth');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 ffffffffffffffff banks=3']);
for(const c of always) assert.equal(allowed(c),false,'another build: '+c);
''', self.payload())

    def test_the_settings_for_every_preset(self):
        '''The global EQ, the high-pass, the limiter, tails, the glide and the whine: once the pedal has said them, within the firmware's limits. Calibration listens.'''
        node(HEAD + r'''
const right='HRID 1 0.2.0-dev.1 0123456789abcdef banks=3';
const say=(c,lines,late)=>HyperRigMini.observeReply(c,lines,!!late,'usb-cdc');
const told={GEQ:'GEQ 0 -3 12 0 0',HPF:'HPF hz=55',LIM:'LIM on=1 thr=-3 rel=100 lat=48 samples=1520',SPILL:'SPILL 1 tails=2',GLIDE:'GLIDE ms=42 blocks=16 snap=1',
            SPUR:'SPUR 1 learned=900 blocks slow=2 pattern_rms=77 (Q30)'};
const good={GEQ:['GEQ 0 0','GEQ 0 12','GEQ 4 -12','GEQ 2 -1'],HPF:['HPF 0','HPF 20','HPF 55','HPF 120'],LIM:['LIM 0 0 10','LIM 1 -200 2000','LIM 1 -3 100'],SPILL:['SPILL 0','SPILL 1'],
            GLIDE:['GLIDE 0 0','GLIDE 42 1','GLIDE 170 1'],SPUR:['SPUR 0','SPUR 1']};
const all=Object.values(good).flat(), words=Object.keys(good);
HyperRigMini.acceptPong(input.pong,'usb-cdc');
for(const c of [...all,'CALIB start','CALIB stop']) assert.equal(allowed(c),false,'before HRID: '+c);
for(const c of words) assert.equal(allowed(c),true,'the question: '+c);
HyperRigMini.acceptBuild([right]);
for(const c of all) assert.equal(allowed(c),false,'before the pedal has said it: '+c);
for(const c of ['CALIB start','CALIB stop']) assert.equal(allowed(c),true,c);
for(const w of words) { say(w,[told[w]]); for(const x of words) for(const c of good[x]) assert.equal(allowed(c),words.indexOf(x)<=words.indexOf(w),c+' after '+w); }
for(const c of ['GEQ 5 0','GEQ -1 0','GEQ 0 13','GEQ 0 -13','GEQ 0','GEQ 0 +1','GEQ 0 01','GEQ 0 -0','GEQ 0 1.5','GEQ 0 1 2','GEQ 0  1','GEQ flat','HPF 5','HPF 19','HPF 21','HPF 121','HPF 125',
                'HPF -20','HPF 055','HPF off','LIM','LIM 1','LIM 1 -3','LIM 2 -3 100','LIM 1 1 100','LIM 1 -201 100','LIM 1 -3 9','LIM 1 -3 2001','LIM 1 -0 100','LIM 1 -3 100 1','LIM 1 -0.3 100','SPILL 2','SPILL on',
                'SPUR 2','SPUR -1','GLIDE 42','GLIDE 171 1','GLIDE 42 2','GLIDE -1 1','CALIB','CALIB status','CALIB sens','CALIB sens 12.0','CALIB 1','CALIB start 1','NOISE 1000','NOISE','REC 1 128','INJ 1'])
  if(!words.includes(c)) assert.equal(allowed(c),false,c);
for(const c of all) assert.equal(allowed(c,'ble-nus'),false,'not over Bluetooth: '+c);
// an answer that is not one: not known until the pedal says it again; a refusal changes nothing
for(const bad of [['GEQ 0 0 0 0'],['GEQ 0 0 0 0 x'],['GEQ 0 0 0 0 0','GEQ 0 0 0 0 0'],[]]) {
  say('GEQ 0 3',bad); assert.equal(allowed('GEQ 0 1'),false,JSON.stringify(bad)); assert.equal(allowed('HPF 80'),true); say('GEQ',[told.GEQ]); assert.equal(allowed('GEQ 0 1'),true); }
say('LIM 1 1 100',['ERR LIM usage']); assert.equal(allowed('LIM 1 -3 100'),true);
say('GEQ 0 3',['GEQ 0 -3 12 0 0']); assert.equal(allowed('GEQ 0 3'),true,'the pedal did not take it: asked again');
HyperRigMini.resetIdentity(); HyperRigMini.acceptPong(input.pong,'usb-cdc'); HyperRigMini.acceptBuild([right]);
for(const c of all) assert.equal(allowed(c),false,'after a new connection: '+c);
for(const w of words) say(w,[told[w]]);
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 ffffffffffffffff banks=3']);
for(const c of [...all,'CALIB start']) assert.equal(allowed(c),false,'another build: '+c);
''', self.payload())

    def test_a_refused_block_does_not_refuse_the_next_one(self):
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
const say=(c,lines,late)=>HyperRigMini.observeReply(c,lines,!!late,'usb-cdc');
const chain=()=>{ say('FXT',['FXT 1 gate cost=1','FXT  0 thr -90..0 (-70)','FXT 7 ir cost=1','FXT  0 mix 0..100 (100)','FXT end']);
  say('FXS',['FX Q0 id=3 gate on=1 p=0,0,0,0,0,0,0 ticks=1','FXS amp=1 on=1','FXS peak=1 ticks skipped=0']); };
chain(); assert.equal(allowed('FXA Q 99 ir'),true);
for(const [c,e] of [['FXA Q 99 ir','ERR FXA ir: no IR loaded (tankg_load_ir.py)'],['FXA Q 99 gate','ERR FXA not enough CPU'],['FXE 3 1','ERR FXE not enough CPU'],
                    ['FXM 3 P 0','ERR FXM usage'],['FXIR 3 0','ERR FXIR empty or invalid slot (-1)'],['FXP 3 0 -10','ERR FXP x']]) {
  say(c,[e]); assert.equal(allowed('FXA Q 99 ir'),true,'after '+e); assert.equal(allowed('FXR 3'),true,'after '+e); }
for(const [c,lines,late] of [['FXA Q 99 ir',['ERR FXA not enough CPU'],true],['FXA Q 99 ir',['ERR something else']],['FXA Q 99 ir',[]],['FXA Q 99 ir',null],
                             ['FXA Q 99 ir',['FXA id=9 ir','ERR FXA x']],['FXE 3 1',['ERR FXA x']]]) {
  chain(); say(c,lines,late); assert.equal(allowed('FXA Q 99 ir'),false,'not known any more: '+c+' '+lines+' '+late); }
''', self.payload())

    def test_a_block_in_the_place_of_another(self):
        '''For the preset and the block that the pedal reported, of a type that it has and that is another.'''
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc');
const say=(c,lines,late)=>HyperRigMini.observeReply(c,lines,!!late,'usb-cdc');
const chain=()=>{ say('FXT',['FXT 1 gate cost=1','FXT  0 thr -90..0 (-70)','FXT 2 boost cost=1','FXT  0 gain -12..24 (6)','FXT end']);
  say('PLIST',["PRE 0 1 -1 -1 'One' t=q1 s=1","PRE 4 1 -1 -1 'Two' t=q1 s=1",'PLIST end current=4']);
  say('FXS',['FX P0 id=3 gate on=1 p=0,0,0,0,0,0,0 ticks=1 l=2','FX Q0 id=5 boost on=1 p=0,0,0,0,0,0,0 ticks=1','FXS amp=1 on=1','FXS peak=1 ticks skipped=0']); };
chain(); assert.equal(allowed('FXC 4 3 gate boost'),false,'before HRID');
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 0123456789abcdef banks=3']);
for(const c of ['FXC 4 3 gate boost','FXC 4 5 boost gate']) assert.equal(allowed(c),true,c);
for(const c of ['FXC 0 3 gate boost','FXC -1 3 gate boost','FXC 4 3 boost gate','FXC 4 3 gate gate','FXC 4 3 gate laser','FXC 4 4 gate boost','FXC 4 16 gate boost','FXC 4 03 gate boost',
                'FXC 04 3 gate boost','FXC 32 3 gate boost','FXC 4 3 gate','FXC 4 3 gate boost x','FXC 4 3 gate boost ','FXC 3 gate boost','FXC']) assert.equal(allowed(c),false,c);
assert.equal(allowed('FXC 4 3 gate boost','ble-nus'),false,'not over Bluetooth');
assert.equal(HyperRigMini.preflight(['FXC 4 3 gate boost','FXE 3 0'],'usb-cdc').allowed,false,'the old block is gone');
// the new block is where the old one was; its id is its own
say('FXC 4 3 gate boost',['FXC id=0 boost','FX cpu=1/2 ticks (0%) mem_fx=0 B']);
for(const c of ['FXE 0 1','FXP 0 0 24','FXC 4 0 boost gate','FXR 0']) assert.equal(allowed(c),true,c);
for(const c of ['FXE 3 1','FXC 4 3 gate boost','FXP 0 0 25']) assert.equal(allowed(c),false,c);
say('FXC 4 0 boost gate',['FXC id=0 gate','FX cpu=1/2 ticks (0%) mem_fx=0 B']);
assert.equal(allowed('FXC 4 0 gate boost'),true,'in its own slot, when there is no other');
// refused: everything is as it was; but not when the pedal has another preset, or when it did not answer
for(const e of ['not enough CPU','out of memory (max 12 kB)','no IR loaded','unknown effect']) { say('FXC 4 0 gate boost',['ERR FXC '+e]); assert.equal(allowed('FXC 4 0 gate boost'),true,e); }
for(const [lines,late] of [[['ERR FXC another preset']],[['ERR FXC another block']],[[],true],[['FXC id=1 gate','FX cpu=1/2']],[['FXC id=5 boost','FX cpu=1/2']],[['FXC id=1 boost'],true],[['FX cpu=1/2']]]) {
  chain(); assert.equal(allowed('FXC 4 3 gate boost'),true); say('FXC 4 3 gate boost',lines,late);
  for(const c of ['FXC 4 3 gate boost','FXE 5 0','FXR 5']) assert.equal(allowed(c),false,'not known any more: '+lines+' '+late+' '+c); }
// a footswitch: the preset in LVL
chain(); say('LVL',['LVL in=-240 out=-253 m=2 g=0/0 b=1200 s=0 a=1 c=5 p=0 tu=0 lim=0']);
for(const c of ['FXC 4 3 gate boost','FXC 0 3 gate boost']) assert.equal(allowed(c),false,c);
// a chain without a preset
say('PNEW',['PNEW ok']); say('FXS',['FX Q0 id=0 gate on=1 p=0,0,0,0,0,0,0 ticks=1','FXS amp=1 on=1','FXS peak=1 ticks skipped=0']);
assert.equal(allowed('FXC -1 0 gate boost'),true); assert.equal(allowed('FXC 4 0 gate boost'),false);
HyperRigMini.acceptBuild(['HRID 1 0.2.0-dev.1 ffffffffffffffff banks=3']);
assert.equal(allowed('FXC -1 0 gate boost'),false,'another build');
''', self.payload())
        page = self.files['editor/web/' + editor.PAGE_FILE].decode('utf-8')
        self.assertIn('Replace with…', page)
        self.assertNotIn('Replace is not enabled', page)
        self.assertNotIn('FXC', editor.files_of({**AREA, 'product': None})['editor/web/mini-profile.js'].decode('utf-8'))

    def test_the_bar_is_readable(self):
        ui = self.files['editor/web/mini-ui.js'].decode('utf-8')
        self.assertIn('HyperRig 0.2.0-dev.1 \u00b7 Test version: not everything has been tried on the pedal yet', ui)
        self.assertNotIn('not qualified', ui)
        self.assertIn(editor.PRODUCT_REVISION, ui)
        ui = editor.files_of({**AREA, 'product': {**self.PRODUCT, 'version': '0.2.0'}})['editor/web/mini-ui.js'].decode('utf-8')
        self.assertIn('"HyperRig 0.2.0 \u00b7 " +', ui)
        self.assertNotIn('Test version', ui)
        policy = self.files['editor/web/mini-profile.js'].decode('utf-8')
        self.assertIn('not available in this version of the editor yet', policy)
        self.assertNotIn('mutations are not validated', policy)

    def test_an_editor_of_another_source_build_does_not_ask_for_a_product(self):
        plain = json.loads(editor.files_of(AREA)['editor/profile.json'])
        self.assertNotIn('product', plain['development'])
        node(HEAD + r'''
HyperRigMini.acceptPong(input.pong,'usb-cdc'); assert.equal(allowed('BPM 1200'),true); assert.equal(allowed('KNOB off'),false);
for(const c of ['IRBEGIN 4 0 48','ISAVE 0 x','ILOAD 0','IDEL 0','IREAD 0','LDBEGIN 4','CSAVE 0 x','CLOAD 0','CDEL 0','CREAD 0','CTRIM live 0','AUDIO OFF'])
  assert.equal(allowed(c),false,c);
''', {**self.payload(), 'profile': plain})

    def test_it_names_its_build_and_claims_no_more(self):
        self.assertEqual(self.profile['development']['product'], self.PRODUCT)
        self.assertEqual(self.profile['development']['revision'], editor.PRODUCT_REVISION)
        self.assertIs(self.profile['hardware_verified'], False)
        self.assertIn('0.2.0-dev.1', self.page)
        self.assertNotIn('MINI source build', self.page)
        self.assertNotIn('TANK MINI', self.page)
        self.assertIn('0123456789abcdef', self.files['editor/DERIVATION.txt'].decode('utf-8'))

    def test_the_bundle_of_a_product_checks(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build') as temp:
            out = Path(temp) / 'bundle'
            with mock.patch.object(editor, 'area_of', return_value=self.area):
                editor.build(out, 'ignored')
            self.assertEqual(editor.check(out)['families'], editor.FAMILIES + editor.ADDED + editor.PRODUCT_ADDED)


if __name__ == '__main__':
    unittest.main()
