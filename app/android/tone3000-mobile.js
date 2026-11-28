/* Android transport for the editor's TONE3000 interface. Tokens are kept in memory. */
(() => {
  'use strict';
  const service = 'https://www.tone3000.com';
  const callback = 'com.hyperrig.editor://tone3000/callback';
  const key = globalThis.HYPERRIG_TONE3000_KEY;
  const native = window.Capacitor?.Plugins;
  if (!/^t3k_pub_[A-Za-z0-9_-]{6,200}$/.test(key || '') || !native?.CapacitorHttp || !native?.Browser || !native?.App) return;
  const originalFetch = window.fetch.bind(window);
  let token = null, models = new Map(), pictures = new Map(), pictureUrl = null, busy = false;
  globalThis.hyperrigTonePicture = () => pictureUrl;
  const encoder = new TextEncoder();
  const json = (value, status = 200) => new Response(JSON.stringify(value), {status, headers: {'content-type': 'application/json'}});
  const b64url = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const random = n => b64url(crypto.getRandomValues(new Uint8Array(n)));
  const own = url => url.protocol === 'https:' && !url.username && !url.password && !url.port && (url.hostname === 'tone3000.com' || url.hostname.endsWith('.tone3000.com'));
  const whole = v => Number.isSafeInteger(Number(v)) && Number(v) > 0 ? Number(v) : null;
  const clean = (v, max) => String(v ?? '').replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
  const fail = text => { throw new Error(text); };
  const header = (headers, name) => Object.entries(headers || {}).find(([k]) => k.toLowerCase() === name)?.[1] || '';

  async function request(address, options = {}) {
    let url = new URL(address), headers = {...options.headers};
    for (let i = 0; i < 5; i++) {
      if (url.protocol !== 'https:' || url.username || url.password || url.port) fail('Invalid download address.');
      if (!own(url)) delete headers.authorization;
      const r = await native.CapacitorHttp.request({url: url.href, method: options.method || 'GET', headers,
        data: options.data, responseType: options.binary ? 'arraybuffer' : 'json', disableRedirects: true, connectTimeout: 30000, readTimeout: 60000});
      if (![301, 302, 303, 307, 308].includes(r.status)) return r;
      if (options.method && options.method !== 'GET') fail('Unexpected redirect.');
      const location = header(r.headers, 'location');
      if (!location) fail('Missing redirect address.');
      url = new URL(location, url);
    }
    fail('Too many redirects.');
  }
  async function api(path) {
    if (!token) fail('Sign in to TONE3000 again.');
    const r = await request(service + '/api/v1' + path, {headers: {authorization: 'Bearer ' + token}});
    if (r.status < 200 || r.status >= 300 || !r.data || typeof r.data !== 'object') fail('TONE3000 did not accept the request.');
    return r.data;
  }
  async function authorize(kind) {
    const verifier = random(48), state = random(24);
    const challenge = b64url(new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(verifier))));
    const q = new URLSearchParams({client_id: key, redirect_uri: callback, response_type: 'code', code_challenge: challenge,
      code_challenge_method: 'S256', state, prompt: 'select_tone', format: kind === 'capture' ? 'nam' : 'ir'});
    if (kind === 'capture') q.set('architecture', '2');
    const result = await new Promise(async (resolve, reject) => {
      let listener, closed, timer, done = false;
      const finish = async (value, error) => {
        if (done) return; done = true; clearTimeout(timer);
        try { await listener?.remove(); } catch (_) {}
        try { await closed?.remove(); } catch (_) {}
        try { await native.Browser.close(); } catch (_) {}
        if (error) reject(error); else resolve(value);
      };
      try {
        listener = await native.App.addListener('appUrlOpen', e => {
          let u; try { u = new URL(e.url); } catch (_) { return; }
          if (u.protocol !== 'com.hyperrig.editor:' || u.host !== 'tone3000' || u.pathname !== '/callback') return;
          if (u.searchParams.get('state') !== state) return finish(null, new Error('Invalid TONE3000 authorization state.'));
          if (u.searchParams.get('canceled') === 'true') return finish(null);
          const id = whole(u.searchParams.get('tone_id')), code = u.searchParams.get('code');
          if (!code || !id || u.searchParams.has('error')) return finish(null, new Error('TONE3000 authorization was not completed.'));
          finish({id, code});
        });
        closed = await native.Browser.addListener('browserFinished', () => { timer = setTimeout(() => finish(null), 1200); });
        await native.Browser.open({url: service + '/api/v1/oauth/authorize?' + q});
      } catch (e) { finish(null, e); }
    });
    if (!result) return null;
    const data = new URLSearchParams({grant_type: 'authorization_code', code: result.code, code_verifier: verifier, redirect_uri: callback, client_id: key}).toString();
    const r = await request(service + '/api/v1/oauth/token', {method: 'POST', headers: {'content-type': 'application/x-www-form-urlencoded'}, data});
    if (r.status !== 200 || typeof r.data?.access_token !== 'string' || !r.data.access_token) fail('TONE3000 sign-in failed.');
    token = r.data.access_token;
    return result.id;
  }
  async function select(kind) {
    if (!['capture', 'ir'].includes(kind)) fail('Unknown tone type.');
    if (busy) fail('TONE3000 is already open.');
    busy = true;
    try {
      const id = await authorize(kind);
      if (!id) return {canceled: true};
      const suffix = kind === 'capture' ? '?architecture=2' : '';
      const raw = await api('/tones/' + id + suffix);
      const result = await api('/models?tone_id=' + id + '&page=1&page_size=100' + (kind === 'capture' ? '&architecture=2' : ''));
      const list = Array.isArray(result) ? result : result.data;
      if (!Array.isArray(list) || whole(raw.id) !== id) fail('Invalid TONE3000 response.');
      const user = raw.user || {}, image = Array.isArray(raw.images) ? raw.images.find(s => typeof s === 'string' && s.startsWith('https://')) : null;
      const tone = {id, title: clean(raw.title, 120) || 'Untitled', creator: clean(user.username || user.display_name, 80) || 'unknown',
        gear: clean(raw.gear, 40), license: clean(raw.license, 40), description: clean(raw.description, 600),
        makes: Array.isArray(raw.makes) ? raw.makes.slice(0, 6).map(m => clean(m?.name ?? m, 60)).filter(Boolean) : [],
        address: typeof raw.url === 'string' && raw.url.startsWith(service + '/') ? raw.url : service + '/tones/' + id, picture: false};
      models = new Map(); pictures = new Map();
      if (pictureUrl) URL.revokeObjectURL(pictureUrl);
      pictureUrl = null;
      if (image) {
        pictures.set(id, image);
        try {
          const picture = await binary(image, false, 3 * 1024 * 1024);
          if (['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/avif'].includes(picture.type)) {
            pictureUrl = URL.createObjectURL(new Blob([picture.data], {type: picture.type}));
            tone.picture = true;
          }
        } catch (_) {}
      }
      for (const m of list) {
        if (!whole(m?.id) || typeof m.model_url !== 'string') continue;
        if (kind === 'capture' ? String(m.architecture_version) !== '2' : m.architecture_version != null && m.architecture_version !== '') continue;
        let url; try { url = new URL(m.model_url); } catch (_) { continue; }
        if (!own(url)) continue;
        models.set(whole(m.id), {id: whole(m.id), name: clean(m.name, 120) || 'Model ' + m.id, size: clean(m.size, 20), url: url.href, kind});
      }
      if (!models.size) fail('This tone has no compatible model.');
      return {tone, models: [...models.values()].map(({id, name, size}) => ({id, name, size}))};
    } finally { busy = false; }
  }
  const bytes = data => {
    if (typeof data === 'object') return encoder.encode(JSON.stringify(data));
    const s = atob(data), out = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  };
  async function binary(url, authorized, limit) {
    if (authorized && !own(new URL(url))) fail('Invalid model address.');
    const r = await request(url, {binary: true, headers: authorized ? {authorization: 'Bearer ' + token} : {}});
    if (r.status < 200 || r.status >= 300) fail('The file could not be fetched.');
    const data = bytes(r.data);
    if (data.length > limit) fail('The file is too large.');
    return {data, type: String(header(r.headers, 'content-type')).split(';')[0].toLowerCase()};
  }
  async function answer(path, query) {
    if (path === 'status') return json({available: true, signedIn: !!token});
    if (path === 'signout') { token = null; models.clear(); pictures.clear(); if (pictureUrl) URL.revokeObjectURL(pictureUrl); pictureUrl = null; return json({signedIn: false}); }
    if (path === 'select') return json(await select(query.get('kind')));
    if (path === 'picture') {
      const url = pictures.get(whole(query.get('id'))); if (!url) return new Response('', {status: 404});
      const r = await binary(url, false, 3 * 1024 * 1024);
      if (!['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/avif'].includes(r.type)) fail('Invalid image.');
      return new Response(r.data, {headers: {'content-type': r.type}});
    }
    if (path === 'model') {
      const m = models.get(whole(query.get('id'))); if (!m || !token) fail('Choose the tone again.');
      const r = await binary(m.url, true, (m.kind === 'ir' ? 24 : 8) * 1024 * 1024);
      if (m.kind === 'ir') { if (r.data.length < 44 || new TextDecoder().decode(r.data.slice(0, 4)) !== 'RIFF' || new TextDecoder().decode(r.data.slice(8, 12)) !== 'WAVE') fail('Invalid WAV file.'); }
      else { let j; try { j = JSON.parse(new TextDecoder().decode(r.data)); } catch (_) {} if (!j?.architecture) fail('Invalid NAM file.'); }
      const name = (m.name.replace(/[\\/:*?"<>|]/g, ' ').trim().slice(0, 60) || 'TONE3000') + (m.kind === 'ir' ? '.wav' : '.nam');
      return new Response(r.data, {headers: {'content-type': 'application/octet-stream', 'x-file-name': encodeURIComponent(name)}});
    }
    return new Response('', {status: 404});
  }
  window.fetch = async (input, options) => {
    const u = new URL(typeof input === 'string' || input instanceof URL ? input : input.url, location.href);
    if (u.origin !== location.origin || !u.pathname.startsWith('/tone3000/')) return originalFetch(input, options);
    try { return await answer(u.pathname.slice('/tone3000/'.length), u.searchParams); }
    catch (e) { return json({error: {message: clean(e?.message || 'TONE3000 error', 200)}}, u.pathname.endsWith('/select') ? 200 : 502); }
  };
})();
