const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const page = fs.readFileSync('app/android/www/tank-mini.html', 'utf8');
const profile = JSON.parse(page.match(/globalThis\.HYPERRIG_MINI_BUILD=(\{.*?\});<\/script>/)[1]);
const policy = fs.readFileSync('app/android/www/mini-profile.js', 'utf8');
for (const file of ['app/mini/mini-dev-rules.js', 'app/android/www/mini-dev-rules.js']) {
  const rules = fs.readFileSync(file, 'utf8');
  for (const transport of ['usb-cdc', 'ble-nus']) {
    const ctx = vm.createContext({ HYPERRIG_MINI_BUILD: JSON.parse(JSON.stringify(profile)) });
    vm.runInContext(rules, ctx);
    vm.runInContext(policy, ctx);
    const api = ctx.HyperRigMini;
    const allowed = command => api.commandPolicy(command, transport).allowed;
    assert.equal(api.acceptPong('PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11', transport).ok, true);
    const { version, build_id } = profile.development.product;
    api.acceptBuild([`HRID 1 ${version} ${build_id} banks=3`]);
    assert.equal(allowed('PCOLOR ff0000'), true);
    assert.equal(allowed('PCOLOR ff0000 save'), false, 'save requires a known preset');
    api.observeReply('PLIST', ["PRE 0 1 -1 -1 'Test' t=q1 s=1", 'PLIST end current=0'], false, transport);
    for (const command of ['PCOLOR ff0000 save', 'PCOLOR none save', 'PCOLOR ff0000', 'PCOLOR none'])
      assert.equal(allowed(command), true, `${file} ${transport}: ${command}`);
    for (const command of ['PCOLOR ff0000 save x', 'PCOLOR red save', 'PCOLOR FF0000 save', 'PCOLOR ff0000  save'])
      assert.equal(allowed(command), false, command);
    api.observeReply('LVL', ['LVL in=-240 out=-253 g=0/0 b=1200 p=-1'], false, transport);
    assert.equal(allowed('PCOLOR ff0000 save'), false, 'do not save when no preset is loaded');
    api.acceptBuild(['HRID 1 0.5.0 ffffffffffffffff banks=3']);
    assert.equal(allowed('PCOLOR ff0000 save'), false, 'another firmware build stays read-only');
  }
}
