/* Presets of others on Patchstorage (patchstorage.js), against a simulated service. Run: node app/desktop/test_patchstorage.js */
"use strict";
const assert = require("node:assert");
const share = require("./patchstorage.js");

const PLATFORM = 9001;
const preset = JSON.stringify({ format: "hyperrig-preset", version: 1, presets: [{ meta: { name: "x" }, sound: { chain: [] } }] });
const record = (id, more) => ({ id, url: `https://patchstorage.com/preset-${id}/`, created_at: "2026-11-01T10:00:00+00:00", updated_at: "2026-11-02T10:00:00+00:00", title: "A &#8220;tone&#8221; &amp; more", excerpt: "Short &hellip; <b>bold</b>",
  content: "<p>First.</p><p>Second<br>line</p><script>alert(1)</script>", download_count: 3, like_count: 1, author: { id: 1, slug: "maker", name: "The Maker" }, license: { id: 1, name: "Creative Commons Attribution 4.0", slug: "cc-by-4-0", custom_license_text: "" },
  platform: { id: PLATFORM, name: "HyperRig", slug: "hyperrig" }, files: [{ id: 70 + id, url: "https://evil.example/x.json", filesize: 900, filename: "x.hyperrig.json" }, { id: 71 + id, filesize: 10, filename: "setup.exe" }, { id: 72 + id, filesize: 9e9, filename: "big.json" }], ...more });
const reply = (body, { status = 200, headers = {} } = {}) => {
  const raw = Buffer.isBuffer(body) ? body : Buffer.from(typeof body === "string" ? body : JSON.stringify(body));
  const h = new Map(Object.entries({ "content-type": "application/json", ...headers }).map(([k, v]) => [k.toLowerCase(), String(v)]));
  return { status, ok: status >= 200 && status < 300, headers: { get: k => h.get(k.toLowerCase()) ?? null }, arrayBuffer: async () => raw, body: null };
};
function service(answers) {
  const asked = [];
  const fetch = async (address, options) => { asked.push([address, options]); const f = answers[new URL(address).pathname] || answers["*"]; if (!f) return reply({}, { status: 404 }); const r = typeof f === "function" ? await f(new URL(address), options) : f; if (r instanceof Error) throw r; return r; };
  return { asked, fetch };
}
const refuses = async (what, code) => { try { await what; } catch (e) { assert.ok(e instanceof share.ShareError, String(e.stack)); assert.strictEqual(e.code, code, e.message); assert.ok(e.message.length > 10 && !/undefined|\[object/.test(e.message)); return; } assert.fail("not refused: " + code); };

(async () => {
  // a place on Patchstorage, or nothing
  for (const platform of [undefined, null, 0, -1, "9001", 1.5, NaN]) assert.throws(() => share.connect({ platform, fetch: async () => {} }), e => e.code === "platform");

  // looking: one page of one platform, plain words, and only what the page needs
  let s = service({ "/api/beta/patches": reply([record(1), record(2, { platform: { id: 5 } }), record(3, { platform: null }), { id: "x" }, null, record(4, { title: "", author: null, url: "javascript:alert(1)", excerpt: 5 })], { headers: { "X-WP-Total": 41, "X-WP-TotalPages": 3 } }) });
  let api = share.connect({ platform: PLATFORM, fetch: s.fetch });
  const got = await api.search("crunch\u0007 & <b>", 2);
  const url = new URL(s.asked[0][0]);
  assert.strictEqual(url.origin + url.pathname, "https://patchstorage.com/api/beta/patches");
  assert.deepStrictEqual([url.searchParams.get("platforms[]"), url.searchParams.get("per_page"), url.searchParams.get("page"), url.searchParams.get("search")], ["9001", "20", "2", "crunch &"]);
  assert.deepStrictEqual(Object.keys(s.asked[0][1].headers).sort(), ["accept", "user-agent"]);
  assert.deepStrictEqual([s.asked[0][1].method, s.asked[0][1].redirect, s.asked[0][1].credentials, s.asked[0][1].body], ["GET", "manual", "omit", undefined]);
  assert.deepStrictEqual([got.page, got.pages, got.total, got.list.map(x => x.id)], [2, 3, 41, [1, 4]]);
  assert.deepStrictEqual(got.list[0], { id: 1, title: "A \u201ctone\u201d & more", creator: "The Maker", about: "Short &hellip; bold", day: "2026-11-02", downloads: 3, likes: 1, address: "https://patchstorage.com/preset-1/" });
  assert.deepStrictEqual([got.list[1].title, got.list[1].creator, got.list[1].about, got.list[1].address], ["Untitled", "unknown", "5", "https://patchstorage.com/"]);
  await api.search("", "x");
  assert.strictEqual(new URL(s.asked[1][0]).searchParams.get("page"), "1");
  assert.strictEqual(new URL(s.asked[1][0]).searchParams.has("search"), false);
  // the order: the newest first unless the most downloaded or the most liked are asked for; nothing else reaches the service
  const orders = [];
  for (const order of [undefined, "new", "downloads", "likes", "title", "toString", "__proto__", "download_count", 3]) {
    await api.search("lead", 1, order);
    const p = new URL(s.asked.at(-1)[0]).searchParams;
    orders.push(p.get("orderby") + " " + p.get("order"));
  }
  assert.deepStrictEqual(orders, ["date desc", "date desc", "download_count desc", "like_count desc", "date desc", "date desc", "date desc", "date desc", "date desc"]);
  assert.deepStrictEqual(url.searchParams.get("orderby") + " " + url.searchParams.get("order"), "date desc");

  // a patch and its file: only of the one that was looked at, only presets, and the address is made here
  s = service({ "/api/beta/patches/7": reply(record(7)), "/api/beta/patches/8": reply(record(8, { license: null })), "/api/beta/patches/9": reply(record(1)), "/api/beta/patches/10": reply(record(10, { platform: { id: 4 } })),
    "/api/beta/patches/7/files/77/download/": reply(preset), "/api/beta/patches/8/files/78/download/": reply('{"format":"other"}') });
  api = share.connect({ platform: PLATFORM, fetch: s.fetch });
  await refuses(api.file(7, 77), "gone");
  const p = await api.patch("7");
  assert.deepStrictEqual([p.license, p.about, p.files], ["Creative Commons Attribution 4.0", "First.\nSecond\nline", [{ id: 77, name: "x.hyperrig.json", size: 900 }]]);
  assert.strictEqual((await api.file(7, 77)).toString(), preset);
  assert.strictEqual(s.asked.at(-1)[0], "https://patchstorage.com/api/beta/patches/7/files/77/download/");
  assert.ok(!s.asked.some(a => /evil/.test(a[0])));
  for (const [id, fid] of [[7, 78], [7, 79], [8, 77], ["7/../8", 77], [7, "77?x"], [null, null]]) await refuses(api.file(id, fid), "gone");
  assert.match((await api.patch(8)).license, /not given/);
  await refuses(api.file(7, 77), "gone");
  await refuses(api.file(8, 78), "file");
  for (const id of ["9", 10]) await refuses(api.patch(id), "answer");
  for (const id of ["", null, "../x", -3, "7 8", true]) { const n = s.asked.length; await refuses(api.patch(id), "gone"); assert.strictEqual(s.asked.length, n, String(id)); }
  await refuses(api.patch(11), "gone");

  // redirects stay there; what is too large or something else is refused
  const hop = to => share.connect({ platform: PLATFORM, fetch: service({ "/api/beta/patches": (u, o) => reply("", { status: 302, headers: { location: to } }) }).fetch });
  for (const to of ["https://evil.example/", "http://patchstorage.com/x", "https://u:p" + "@patchstorage.com/x", "file:///c:/x", "https://patchstorage.com:8443/", "", "/api/beta/patches"]) await refuses(hop(to).search("", 1), "service");
  const moved = service({ "/api/beta/patches": reply("", { status: 301, headers: { location: "/api/beta/patches/" } }), "/api/beta/patches/": reply([]) });
  assert.deepStrictEqual((await share.connect({ platform: PLATFORM, fetch: moved.fetch }).search("", 1)).list, []);
  const once = r => share.connect({ platform: PLATFORM, fetch: async () => { if (r instanceof Error) throw r; return r; } });
  await refuses(once(reply("<html>")).search("", 1), "answer");
  await refuses(once(reply({ code: 1 })).search("", 1), "answer");
  await refuses(once(reply("[]", { headers: { "content-length": 3 * 1024 * 1024 } })).search("", 1), "size");
  await refuses(once(reply(Buffer.alloc(3 * 1024 * 1024, 32))).search("", 1), "size");
  await refuses(once(reply("", { status: 429 })).search("", 1), "limit");
  await refuses(once(reply("", { status: 500 })).search("", 1), "service");
  await refuses(once(reply("", { status: 404 })).search("", 1), "gone");
  await refuses(once(new Error("offline")).search("", 1), "network");
  // an answer without its length stops at the limit
  let sent = 0;
  const endless = { status: 200, ok: true, headers: { get: () => null }, body: { getReader: () => ({ read: async () => { sent += 65536; return { done: false, value: new Uint8Array(65536) }; }, cancel: async () => {} }) } };
  await refuses(once(endless).search("", 1), "size");
  assert.ok(sent < 3 * 1024 * 1024);

  // one question at a time
  let go;
  const slow = share.connect({ platform: PLATFORM, fetch: () => new Promise(r => { go = () => r(reply([])); }) }), first = slow.search("", 1);
  await refuses(slow.patch(7), "busy");
  go();
  await first;

  // plain text
  for (const [from, to] of [["a<script>x</script>b", "a b"], ["&lt;b&gt;", "<b>"], ["&amp;lt;", "&lt;"], ["&#0;&#xD800;&#x110000;x", "x"], ["a\r\n\tb", "a b"], [null, ""], [{}, ""], [["x"], ""], ["x".repeat(500), "x".repeat(10)]]) assert.strictEqual(share.text(from, 10), to, String(from));
  console.log("all tests passed");
})().catch(e => { console.error(e); process.exit(1); });
