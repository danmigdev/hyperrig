const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');

async function test(invalidState = false) {
  const listeners = {}, requests = [];
  const addListener = async (name, fn) => { listeners[name] = fn; return {remove: async () => { delete listeners[name]; }}; };
  const plugins = {
    App: {addListener},
    Browser: {addListener, close: async () => {}, open: async ({url}) => {
      const q = new URL(url).searchParams;
      assert.equal(q.get('code_challenge_method'), 'S256');
      assert.equal(q.get('architecture'), '2');
      setImmediate(() => listeners.appUrlOpen({url: 'com.hyperrig.editor://tone3000/callback?code=code&tone_id=1&state=' + (invalidState ? 'bad' : q.get('state'))}));
    }},
    CapacitorHttp: {request: async o => {
      requests.push(o);
      assert.equal(o.disableRedirects, true);
      if (o.url.endsWith('/oauth/token')) return {status: 200, data: {access_token: 'private'}, headers: {}};
      if (o.url.includes('/api/v1/tones/1')) return {status: 200, data: {id: 1, title: 'Tone', user: {username: 'Creator'}, images: ['https://cdn.example/picture']}, headers: {}};
      if (o.url.includes('/api/v1/models?')) return {status: 200, data: {data: [{id: 2, name: 'Model', model_url: 'https://www.tone3000.com/model', architecture_version: 2}]}, headers: {}};
      if (o.url === 'https://www.tone3000.com/model') return {status: 302, headers: {Location: 'https://cdn.example/model'}};
      if (o.url === 'https://cdn.example/picture') {
        assert.equal(o.headers.authorization, undefined);
        return {status: 200, data: btoa('image'), headers: {'content-type': 'image/png'}};
      }
      if (o.url === 'https://cdn.example/model') {
        assert.equal(o.headers.authorization, undefined, 'token must not reach another domain');
        return {status: 200, data: {architecture: 'A2'}, headers: {'content-type': 'application/json'}};
      }
      throw new Error('Unexpected request');
    }}
  };
  const location = new URL('https://localhost/tank-mini.html');
  const window = {Capacitor: {Plugins: plugins}, fetch: async () => new Response('other')};
  const context = {window, location, URL, URLSearchParams, Response, Blob, TextEncoder, TextDecoder, Uint8Array, crypto: webcrypto, btoa, atob,
    setTimeout, clearTimeout, HYPERRIG_TONE3000_KEY: 't3k_pub_example123'};
  vm.runInNewContext(fs.readFileSync(__dirname + '/tone3000-mobile.js', 'utf8'), context);
  assert.equal((await (await window.fetch('tone3000/status')).json()).available, true);
  const selected = await (await window.fetch('tone3000/select?kind=capture', {method: 'POST'})).json();
  if (invalidState) {
    assert.match(selected.error.message, /state/);
    assert.equal(requests.length, 0);
    return;
  }
  assert.equal(selected.tone.creator, 'Creator');
  assert.equal(selected.tone.picture, true);
  assert.equal(selected.models[0].id, 2);
  const response = await window.fetch('tone3000/model?id=2', {method: 'POST'});
  assert.equal(response.status, 200);
  assert.equal((await response.json()).architecture, 'A2');
  await window.fetch('tone3000/signout', {method: 'POST'});
  assert.equal((await (await window.fetch('tone3000/status')).json()).signedIn, false);
}
test().then(() => test(true)).catch(e => { console.error(e); process.exitCode = 1; });
