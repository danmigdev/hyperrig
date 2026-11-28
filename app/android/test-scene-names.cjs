const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const page = fs.readFileSync(__dirname + '/www/tank-mini.html', 'utf8');
const source = page.slice(page.indexOf('async function loadSnapNames()'), page.indexOf('\nconst snapLabel'));
assert.ok(source.startsWith('async function loadSnapNames()'));
const state = { snaps: [1, 1], snapNames: ['Old A', 'Old B'] };
let lines;
const context = { S: state, DEMO: false, Pedal: { cmd: async () => lines }, doneBy: () => () => true };
vm.runInNewContext(source + '\nglobalThis.run = loadSnapNames;', context);

(async () => {
  lines = ["SNAPNAME 0 'Clean'", 'SNAPNAME end'];
  await context.run();
  assert.deepEqual(Array.from(state.snapNames), ['Clean', '']);
  lines = ['SNAPNAME end'];
  await context.run();
  assert.deepEqual(Array.from(state.snapNames), ['', '']);
  state.snapNames = ['Keep', 'these'];
  lines = [];
  await context.run();
  assert.deepEqual(Array.from(state.snapNames), ['Keep', 'these']);
})().catch(e => { console.error(e); process.exitCode = 1; });
