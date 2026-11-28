const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const page = fs.readFileSync(__dirname + '/www/tank-mini.html', 'utf8');
const source = page.slice(page.indexOf('let lvlTicking = false;'), page.indexOf('\nasync function pollLvl()'));
assert.ok(source.startsWith('let lvlTicking = false;'));
let polls = 0;
const now = Date.now();
const S = { connected: true, lvlSub: true, lvlSubOk: true, lvlPushT: now, lvlFullT: now - 3000 };
const context = { S, DEMO: false, Pedal: { busy: 0 }, pageHidden: () => false, drag: false, tuOpen: false,
  LVL_PUSH_STALE: 3000, LVL_REARM_MS: 5000, ED: {}, pollLvl: async () => { polls++; } };
vm.runInNewContext(source + '\nglobalThis.run = lvlTick;', context);

(async () => {
  await context.run();
  assert.equal(polls, 1, 'a fresh meter stream must not prevent a full state refresh');
  S.lvlFullT = Date.now();
  await context.run();
  assert.equal(polls, 1, 'avoid unnecessary polling immediately after a full update');
})().catch(e => { console.error(e); process.exitCode = 1; });
