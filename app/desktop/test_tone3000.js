/* node app/desktop/test_tone3000.js: against a simulated TONE3000, no request leaves this computer. */
"use strict";
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const t3k = require("./tone3000.js");

const KEY = "t3k_pub_test0123";
const NAM = Buffer.from(JSON.stringify({ architecture: "SlimmableContainer", config: {}, weights: [] }));
const WAV = Buffer.concat([Buffer.from("RIFF\x24\x00\x00\x00WAVEfmt ", "latin1"), Buffer.alloc(60)]);
const hash = v => crypto.createHash("sha256").update(v).digest("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

/* The service: what it was asked, and answers that can be spoiled one at a time. */
function simulated() {
  const s = { asked: [], codes: new Map(), refresh: new Map([["r0", true]]), access: new Set(["a0"]), count: 0, spoil: {}, models: null };
  const reply = (status, body, headers = {}) => ({ status, ok: status >= 200 && status < 300, headers: { get: k => headers[k.toLowerCase()] ?? null },
    arrayBuffer: async () => { const raw = Buffer.isBuffer(body) ? body : Buffer.from(typeof body === "string" ? body : JSON.stringify(body)); return raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.length); } });
  s.reply = reply;
  s.tone = { id: 77, title: "Plexi \u0007Crunch", user: { username: "amp.maker" }, gear: "amp-cab", format: "nam", license: "cc-by", description: "Loud", images: ["https://images.example/p.png"], makes: [{ name: "Marshall" }], url: "https://www.tone3000.com/tones/77" };
  s.list = [{ id: 1, name: "Clean", size: "standard", architecture_version: "2", model_url: t3k.SERVICE + "/api/v1/models/1/download" },
    { id: 2, name: "Crunch", size: "lite", architecture_version: 2, model_url: t3k.SERVICE + "/api/v1/models/2/download" },
    { id: 3, name: "Old", size: "standard", architecture_version: "1", model_url: t3k.SERVICE + "/api/v1/models/3/download" }];
  s.fetch = async (address, options = {}) => {
    const url = new URL(address), headers = options.headers || {};
    s.asked.push({ address, method: options.method || "GET", authorization: headers.authorization || null, body: options.body || "" });
    if (s.spoil.network) throw new TypeError("fetch failed");
    if (url.pathname === "/api/v1/oauth/token") {
      if (s.spoil.token) return s.spoil.token;
      const q = new URLSearchParams(options.body);
      assert.equal(q.get("client_id"), KEY); assert.equal(q.get("client_secret"), null);
      if (q.get("grant_type") === "authorization_code") {
        const want = s.codes.get(q.get("code"));
        if (!want || want !== hash(q.get("code_verifier")) || q.get("redirect_uri") !== t3k.REDIRECT) return reply(400, { error: "invalid_grant" });
        s.codes.delete(q.get("code"));
      } else if (!s.refresh.delete(q.get("refresh_token"))) return reply(400, { error: "invalid_grant" });
      const n = ++s.count;
      s.access.add("a" + n); s.refresh.set("r" + n, true);
      return reply(200, { access_token: "a" + n, refresh_token: "r" + n, token_type: "bearer", expires_in: 3600, scope: "read" });
    }
    if (url.hostname === "images.example") return s.spoil.picture || reply(200, Buffer.from("png"), { "content-type": "image/png" });
    if (!s.access.has((headers.authorization || "").replace("Bearer ", ""))) return reply(401, { error: "unauthorized" });
    if (s.spoil.api) return s.spoil.api;
    if (url.pathname === "/api/v1/tones/77") return reply(200, s.tone);
    if (url.pathname === "/api/v1/models") return reply(200, { data: s.list, page: 1, page_size: 100, total: s.list.length, total_pages: 1 });
    if (/^\/api\/v1\/models\/\d+\/download$/.test(url.pathname)) return s.spoil.file || reply(200, s.file || NAM);
    return reply(404, {});
  };
  return s;
}
function keeper(first) { let v = first || null; return { load: () => v && { ...v }, save: x => { v = { ...x }; }, clear: () => { v = null; } }; }
const refused = async (code, f) => { await assert.rejects(f, e => e instanceof t3k.ToneError && e.code === code ? true : assert.fail(`${e.code || e.name}: ${e.message}, expected ${code}`)); };

(async () => {
  // A request and the address of the sign-in page.
  const request = t3k.newRequest("capture"), other = t3k.newRequest("ir");
  assert.notEqual(request.verifier, other.verifier); assert.notEqual(request.state, other.state);
  assert.match(request.verifier, /^[A-Za-z0-9_-]{64}$/); assert.equal(request.challenge, hash(request.verifier));
  assert.throws(() => t3k.newRequest("preset"));
  const q = new URL(t3k.authorizeUrl(t3k.SERVICE, KEY, request)).searchParams;
  assert.deepEqual([...q.keys()].sort(), ["architecture", "client_id", "code_challenge", "code_challenge_method", "format", "menubar", "prompt", "redirect_uri", "response_type", "state"]);
  assert.deepEqual([q.get("prompt"), q.get("format"), q.get("architecture"), q.get("response_type"), q.get("code_challenge_method"), q.get("redirect_uri")], ["select_tone", "nam", "2", "code", "S256", t3k.REDIRECT]);
  assert.ok(!t3k.authorizeUrl(t3k.SERVICE, KEY, request).includes(request.verifier), "the verifier stays here");
  const qi = new URL(t3k.authorizeUrl(t3k.SERVICE, KEY, other, "me@example.com")).searchParams;
  assert.deepEqual([qi.get("format"), qi.get("architecture"), qi.get("login_hint")], ["ir", null, "me@example.com"]);

  // What comes back.
  const back = fields => t3k.readCallback(t3k.REDIRECT + "?" + new URLSearchParams(fields), request);
  assert.deepEqual(back({ code: "c", state: request.state, tone_id: "77" }), { code: "c", toneId: 77 });
  assert.deepEqual(back({ state: request.state, canceled: "true" }), { canceled: true, code: null });
  assert.deepEqual(back({ state: request.state, canceled: "true", code: "c" }), { canceled: true, code: "c" });
  assert.deepEqual(back({ canceled: "true" }), { canceled: true, code: null });
  assert.deepEqual(back({ state: request.state, error: "access_denied" }), { error: "access_denied" });
  for (const fields of [{ code: "c", tone_id: "77" }, { code: "c", state: other.state, tone_id: "77" }, { code: "c", state: request.state + "x", tone_id: "77" }, { canceled: "true", state: other.state, code: "c" }])
    assert.deepEqual(back(fields), { error: "state" }, JSON.stringify(fields));
  for (const fields of [{ code: "c", state: request.state }, { state: request.state, tone_id: "77" }, { code: "c", state: request.state, tone_id: "x" }, { code: "c", state: request.state, tone_id: "-1" }])
    assert.deepEqual(back(fields), { error: "incomplete" }, JSON.stringify(fields));
  for (const address of ["https://www.tone3000.com/callback?code=c", "http://localhost:3002/callback?code=c", "http://localhost:3001/other", "https://localhost:3001/callback", "nonsense", "",
    "http://localhost.evil.example:3001/callback", "http://x@localhost:3001/callback", "http://127.0.0.1:3001/callback", "hyperrig://editor/callback"])
    assert.equal(t3k.readCallback(address, request), null, address);

  // The key: the publishable one only.
  assert.equal(t3k.isPublishable(KEY), true);
  for (const key of ["", null, undefined, "t3k_cs_secret0123456789", "t3k_pub_", "t3k_pub_a b c d e f", " t3k_pub_test0123", "pk_live_0123456789", 5]) {
    assert.equal(t3k.isPublishable(key), false, String(key));
    assert.throws(() => t3k.connect({ clientId: key, fetch: () => assert.fail("asked"), store: keeper() }), e => e.code === "key");
  }

  // Signing in, choosing, downloading: one model, with the token to TONE3000 only.
  let s = simulated(), store = keeper(), c = t3k.connect({ clientId: KEY, fetch: s.fetch, store });
  assert.equal(c.signedIn(), false);
  await refused("signin", () => c.chosen("capture", 77));
  assert.equal(s.asked.length, 0, "nothing is asked before the person signs in");
  s.codes.set("code1", request.challenge);
  await c.exchange("code1", request);
  assert.equal(c.signedIn(), true);
  const chosen = await c.chosen("capture", 77);
  assert.deepEqual(chosen.tone, { id: 77, title: "Plexi  Crunch", creator: "amp.maker", gear: "amp-cab", format: "nam", license: "cc-by", description: "Loud", makes: ["Marshall"], picture: true, address: "https://www.tone3000.com/tones/77" });
  assert.deepEqual(chosen.models, [{ id: 1, name: "Clean", size: "standard" }, { id: 2, name: "Crunch", size: "lite" }], "architecture 2 only, and no address");
  const file = await c.model(2);
  assert.deepEqual([file.name, file.type, file.raw.equals(NAM)], ["Plexi Crunch Crunch.nam", "application/json", true]);
  assert.equal(s.asked.filter(a => a.address.includes("/download")).length, 1, "the one that was asked for");
  const picture = await c.picture(77);
  assert.deepEqual([picture.type, picture.raw.toString()], ["image/png", "png"]);
  for (const a of s.asked) if (a.authorization) assert.ok(a.address.startsWith(t3k.SERVICE + "/"), a.address);
  assert.equal(s.asked.find(a => a.address.includes("images.example")).authorization, null);
  for (const id of [3, 9, "x", null]) await refused("gone", () => c.model(id));
  await refused("gone", () => c.picture(78));

  // A code is used once, and only with its verifier.
  await refused("signin", () => c.exchange("code1", request));
  s.codes.set("code2", request.challenge);
  await refused("signin", () => c.exchange("code2", other));
  assert.equal(c.signedIn(), true, "a failed exchange keeps the sign-in there was");

  // Tokens: refreshed before they end, once for several requests, and again when one is refused.
  let time = 1000000;
  s = simulated(); store = keeper({ access: "a0", refresh: "r0", until: time + 3600000 });
  c = t3k.connect({ clientId: KEY, fetch: s.fetch, store, now: () => time });
  await c.chosen("capture", 77);
  assert.equal(s.count, 0);
  time += 3600000 - 30000;
  await Promise.all([c.chosen("capture", 77), c.chosen("capture", 77)]);
  assert.equal(s.count, 1, "one refresh"); assert.equal(store.load().refresh, "r1", "the new refresh token is kept");
  s.access.clear(); s.access.add("later"); s.refresh.set("r1", true);
  await c.chosen("capture", 77);
  assert.equal(s.count, 2, "refused once, refreshed, and done");
  s.access.clear(); s.refresh.clear();
  await refused("signin", () => c.chosen("capture", 77));
  assert.equal(c.signedIn(), false, "a refresh that is refused signs out");

  // Impulse responses.
  s = simulated(); store = keeper({ access: "a0", refresh: "r0", until: Date.now() + 3600000 }); c = t3k.connect({ clientId: KEY, fetch: s.fetch, store });
  s.tone.format = "ir"; s.file = WAV;
  s.list = [{ id: 5, name: "V30", size: "", architecture_version: null, model_url: t3k.SERVICE + "/api/v1/models/5/download" }, { id: 6, name: "amp", architecture_version: "2", model_url: t3k.SERVICE + "/x" }];
  assert.deepEqual((await c.chosen("ir", 77)).models, [{ id: 5, name: "V30", size: "" }]);
  const ir = await c.model(5);
  assert.deepEqual([ir.name, ir.type], ["Plexi Crunch.wav", "audio/wav"]);
  s.file = NAM; await refused("file", () => c.model(5));

  // What can go wrong.
  const broken = async (spoil, code, kind = "capture", setup = () => {}) => {
    const x = simulated(), k = keeper({ access: "a0", refresh: "r0", until: Date.now() + 3600000 });
    Object.assign(x.spoil, spoil(x)); setup(x);
    await refused(code, () => t3k.connect({ clientId: KEY, fetch: x.fetch, store: k }).chosen(kind, 77));
    return k;
  };
  await broken(() => ({ network: true }), "network");
  await broken(x => ({ api: x.reply(403, {}) }), "gone");
  await broken(x => ({ api: x.reply(404, {}) }), "gone");
  await broken(x => ({ api: x.reply(429, {}) }), "limit");
  await broken(x => ({ api: x.reply(500, {}) }), "service");
  await broken(x => ({ api: x.reply(200, "<html>") }), "answer");
  await broken(x => ({ api: x.reply(200, []) }), "answer");
  await broken(x => ({ api: x.reply(200, {}, { "content-length": "999999999" }) }), "size");
  await broken(() => ({}), "none", "capture", x => { x.list = x.list.slice(2); });
  await broken(() => ({}), "none", "ir");
  for (const [bad, code] of [[{ access_token: "" }, "answer"], [{}, "answer"], [{ access_token: "x", token_type: "mac" }, "answer"]]) {
    const x = simulated(); x.codes.set("k", request.challenge); x.spoil.token = x.reply(200, bad);
    await refused(code, () => t3k.connect({ clientId: KEY, fetch: x.fetch, store: keeper() }).exchange("k", request));
  }
  // A model kept elsewhere never gets the token; a file that is too large or not a capture is refused.
  for (const address of ["https://evil.example/m.nam", "http://www.tone3000.com/m", "https://tone3000.com.evil.example/m", "https://user@www.tone3000.com/m", "https://nottone3000.com/m", "file:///C:/x"]) {
    const x = simulated(), k = keeper({ access: "a0", refresh: "r0", until: Date.now() + 3600000 }), d = t3k.connect({ clientId: KEY, fetch: x.fetch, store: k });
    x.list = [{ id: 1, name: "m", architecture_version: "2", model_url: address }];
    await d.chosen("capture", 77);
    await refused("address", () => d.model(1));
    assert.ok(!x.asked.some(a => a.address === address), address);
  }
  for (const [file, code] of [[Buffer.from("not json"), "file"], [Buffer.from("{}"), "file"], [Buffer.alloc(9 * 1024 * 1024, 32), "size"]]) {
    const x = simulated(), k = keeper({ access: "a0", refresh: "r0", until: Date.now() + 3600000 }), d = t3k.connect({ clientId: KEY, fetch: x.fetch, store: k });
    x.file = file;
    await d.chosen("capture", 77);
    await refused(code, () => d.model(1));
  }
  for (const bad of [["text/html", Buffer.from("x")], ["image/svg+xml", Buffer.from("<svg/>")]]) {
    const x = simulated(), k = keeper({ access: "a0", refresh: "r0", until: Date.now() + 3600000 }), d = t3k.connect({ clientId: KEY, fetch: x.fetch, store: k });
    x.spoil.picture = x.reply(200, bad[1], { "content-type": bad[0] });
    await d.chosen("capture", 77);
    await refused("file", () => d.picture(77));
  }
  // A file that is kept elsewhere is fetched from there without the token; a redirect to anything but https is not followed.
  for (const [to, good] of [["https://files.example/m.nam", true], ["http://files.example/m.nam", false], ["file:///C:/x", false], ["https://u" + ":p@files.example/m", false], ["", false]]) {
    const x = simulated(), k = keeper({ access: "a0", refresh: "r0", until: Date.now() + 3600000 }), inner = x.fetch;
    x.spoil.file = x.reply(302, "", { location: to });
    const d = t3k.connect({ clientId: KEY, store: k, fetch: async (address, options) => { assert.equal(options.redirect, "manual");
      if (address.startsWith("https://files.example/")) { x.asked.push({ address, authorization: (options.headers || {}).authorization || null }); return x.reply(200, NAM); } return inner(address, options); } });
    await d.chosen("capture", 77);
    if (good) { assert.ok((await d.model(1)).raw.equals(NAM)); assert.equal(x.asked.find(a => a.address.startsWith("https://files.example/")).authorization, null); }
    else { await refused("service", () => d.model(1)); assert.ok(!x.asked.some(a => a.address.includes("files.example"))); }
  }
  // Names that could be paths become plain ones; signing out leaves nothing.
  for (const name of ["..\\..\\evil/<x>?.nam", "a/b.nam", "C:\\x.nam"]) assert.match(t3k.fileOf("capture", name, NAM).name, /^[^\\/:*?"<>|]+\.nam$/);
  assert.equal(t3k.fileOf("capture", "", NAM).name, "TONE3000.nam");
  assert.ok(t3k.fileOf("ir", "x".repeat(500), WAV).name.length <= 64);
  c.signOut();
  assert.equal(c.signedIn(), false); await refused("gone", () => c.model(5));
  console.log("tone3000: all tests passed");
})().catch(e => { console.error(e); process.exit(1); });
