/* node app/desktop/test_rules.js */
"use strict";
const assert = require("node:assert/strict");
const rules = require("./rules.js");

// Ports: only the pedal, however the system describes it.
for (const port of [{ vendorId: "19530", productId: "20821" }, { vendor_id: 0x4c4a, product_id: 0x5155 }, { usbVendorId: 0x4c4a, usbProductId: 0x5155 },
  { vendorId: "19530", deviceInstanceId: "USB\\VID_4C4A&PID_5155&MI_00\\7&1" }, { deviceInstanceId: "USB\\VID_4C4A&PID_5155\\1" }, { device_instance_id: "usb#vid_4c4a&pid_5155#1" },
  { vendorId: "13908" }, { vendorId: 13908, productId: 20821 }, { vendor_id: 0x3654 }, { usbVendorId: 0x3654 },
  { deviceInstanceId: "USB\\VID_3654&PID_5155&MI_00\\7&1" }, { device_instance_id: "usb\\vid_3654&pid_5155\\1" }])
  assert.equal(rules.isPedal(port), true, JSON.stringify(port));
for (const port of [null, undefined, 5, "13908", {}, { vendorId: "19530" }, { vendorId: "" }, { vendorId: 0 }, { portName: "COM3", displayName: "VID_3654" },
  { vendorId: "19530", productId: "51029" }, { vendorId: "19530", productId: "32855" }, { vendorId: "19530", productId: "18514" }, { vendorId: "19530", productId: "16725" },
  { deviceInstanceId: "USB\\VID_4C4A&PID_8057\\1" }, { deviceInstanceId: "USB\\VID_4C4A&PID_C755&MI_03\\1" }, { deviceInstanceId: "USB\\VID_4C4A&PID_51550\\1" }, { deviceInstanceId: "USB\\VID_4C4A\\1" }, { deviceInstanceId: "USB\\VID_36541&PID_1\\1" }, { vendorId: 1, deviceInstanceId: "USB\\VID_3654&PID_5155\\1" }])
  assert.equal(rules.isPedal(port), false, JSON.stringify(port));
assert.deepEqual(rules.pedals([{ vendorId: "13908", portId: "a" }, { vendorId: "1", portId: "b" }, { vendorId: "19530", productId: "20821", portId: "c" }]).map(p => p.portId), ["a", "c"]);
assert.deepEqual(rules.pedals(null), []);
assert.equal(rules.portLabel({ portName: "COM7" }), "COM7");

// Bluetooth: only a device that says the pedal's name, and only for the editor's page.
for (const device of [{ deviceName: "HyperRig 68F0", deviceId: "F0:68:00:00:00:01" }, { deviceName: "HyperRig 0000", deviceId: "x" }])
  assert.equal(rules.isAirPedal(device), true, JSON.stringify(device));
for (const device of [null, undefined, "HyperRig 68F0", {}, { deviceName: "HyperRig 68F0" }, { deviceName: "HyperRig 68F0", deviceId: "" }, { deviceName: "HyperRig 68f0", deviceId: "a" },
  { deviceName: "HyperRig", deviceId: "a" }, { deviceName: "HyperRig 68F01", deviceId: "a" }, { deviceName: " HyperRig 68F0", deviceId: "a" }, { deviceName: "TANK MINI_BLE", deviceId: "a" },
  { deviceName: "Unknown or Unsupported Device (F0:68:00:00:00:01)", deviceId: "a" }, { deviceName: 5, deviceId: "a" }])
  assert.equal(rules.isAirPedal(device), false, JSON.stringify(device));
assert.deepEqual(rules.airPedals([{ deviceName: "Headphones", deviceId: "a" }, { deviceName: "HyperRig 68F0", deviceId: "b" }, { deviceName: "HyperRig 1234", deviceId: "c" }]).map(d => d.deviceId), ["b", "c"]);
assert.deepEqual(rules.airPedals(undefined), []);
for (const address of ["hyperrig://editor/tank-mini.html", "hyperrig://editor/tank-mini.html?first=1", "hyperrig://editor/"]) assert.equal(rules.isEditor(address), true, address);
for (const address of ["hyperrig://installer/index.html", "https://example.com/tank-mini.html", "hyperrig://other/tank-mini.html", "about:blank", "", null]) assert.equal(rules.isEditor(address), false, String(address));

// Files: the editor's own, nothing outside its folder.
assert.equal(rules.fileOf("hyperrig://editor/"), "web/tank-mini.html");
assert.equal(rules.fileOf("hyperrig://editor/tank-mini.html?x=1#demo"), "web/tank-mini.html");
assert.equal(rules.fileOf("hyperrig://editor/nam2chip.js"), "web/nam2chip.js");
for (const address of ["hyperrig://editor/..%2fmanifest.json", "hyperrig://editor/%2fetc/x/../..%2f..", "hyperrig://editor/a%5cb", "hyperrig://other/tank-mini.html",
  "https://editor/tank-mini.html", "file:///C:/Windows/win.ini", "hyperrig://editor/a b", "nonsense", "hyperrig://editor/%", "hyperrig://editor/a//b"])
  assert.equal(rules.fileOf(address), null, address);
// The address is normalised first, and only the files of the bundle are ever answered: these are none of them.
assert.equal(rules.fileOf("hyperrig://editor/../manifest.json"), "web/manifest.json");
assert.equal(rules.fileOf("hyperrig://editor/%2e%2e/%2e%2e/main.js"), "web/main.js");

// Loading and opening.
for (const address of [rules.START, "hyperrig://editor/log", "blob:hyperrig://editor/1234", "data:image/png;base64,AA==", "devtools://devtools/x"])
  assert.equal(rules.mayLoad(address), true, address);
for (const address of ["https://github.com/danmigdev/hyperrig", "http://127.0.0.1:8765/", "blob:https://example.com/1", "file:///C:/x", "ws://127.0.0.1/", "chrome://gpu"])
  assert.equal(rules.mayLoad(address), false, address);
for (const address of ["https://github.com/danmigdev/hyperrig", "https://github.com/danmigdev/hyperrig/issues/new/choose", "https://github.com/danmigdev/hyperrig#readme"])
  assert.equal(rules.mayOpen(address), true, address);
for (const address of ["https://github.com/danmigdev/hyperrig-evil", "https://github.com/other/x", "http://github.com/danmigdev/hyperrig", "https://github.com.evil.com/danmigdev/hyperrig",
  "file:///C:/Windows/System32/calc.exe", "javascript:alert(1)", "ms-settings:", ""])
  assert.equal(rules.mayOpen(address), false, address);

for (const address of ["https://www.tone3000.com", "https://www.tone3000.com/tones/77", "https://patchstorage.com/", "https://patchstorage.com/upload-a-patch/"]) assert.equal(rules.mayOpen(address), true, address);
for (const address of ["https://patchstorage.com.evil.example/", "http://patchstorage.com/", "https://patchstorage.com@evil.example/", "https://patchstorage.community/", "https://www.tone3000.com.evil.example/", "http://www.tone3000.com/", "https://tone3000.com@evil.example/"]) assert.equal(rules.mayOpen(address), false, address);
for (const address of ["https://www.tone3000.com/x", "https://images.example/p.png", "data:image/png;base64,AA", "blob:https://www.tone3000.com/1"]) assert.equal(rules.mayVisit(address), true, address);
for (const address of ["http://www.tone3000.com/", "http://localhost:3001/callback", "file:///C:/x", "hyperrig://editor/", "chrome://gpu", "ms-settings:"]) assert.equal(rules.mayVisit(address), false, address);
assert.equal(rules.mayVisit("http://127.0.0.1:5000/x", "http://127.0.0.1:5000"), true); assert.equal(rules.mayVisit("http://127.0.0.1:50001/x", "http://127.0.0.1:5000"), false);

// The installer's page: its own place, MIDI and the pedal's port, and nothing of the editor's.
assert.equal(rules.fileOf("hyperrig://installer/"), "installer/index.html");
assert.equal(rules.fileOf("hyperrig://installer/firmware/image.bin"), "installer/firmware/image.bin");
for (const address of ["hyperrig://installer/..%2fmanifest.json", "hyperrig://installer/a%5cb", "hyperrig://constructor/x", "hyperrig://installer.evil/x"]) assert.equal(rules.fileOf(address), null, address);
assert.equal(rules.fileOf("hyperrig://installer/../web/tank-mini.html"), "installer/web/tank-mini.html");
assert.equal(rules.originOf("hyperrig://installer/index.html?x=1"), rules.INSTALLER); assert.equal(rules.originOf("hyperrig://editor/x"), rules.ORIGIN);
assert.equal(rules.originOf("https://example.com/x"), "https://example.com"); assert.equal(rules.originOf("nonsense"), "");
assert.equal(rules.isInstaller(rules.INSTALL), true); assert.equal(rules.isInstaller(rules.START), false);
for (const permission of ["midi", "midiSysex", "serial", "clipboard-sanitized-write", "screen-wake-lock"]) assert.equal(rules.mayUse(permission, rules.INSTALLER + "/"), true, permission);
for (const permission of ["media", "geolocation", "notifications", "usb", "hid", "clipboard-read", "openExternal", "fullscreen", "fileSystem", "unknown"])
  assert.equal(rules.mayUse(permission, rules.INSTALLER, { fileAccessType: "readable", isDirectory: false }), false, permission);
assert.match(rules.INSTALLER_POLICY, /script-src 'self';/);
assert.doesNotMatch(rules.INSTALLER_POLICY, /https?:|\*|unsafe-eval|script-src[^;]*unsafe/);

// Permissions: the editor's page only, and only what it uses.
for (const permission of ["serial", "clipboard-sanitized-write", "screen-wake-lock", "fullscreen"]) {
  assert.equal(rules.mayUse(permission, rules.ORIGIN), true, permission);
  assert.equal(rules.mayUse(permission, rules.ORIGIN + "/"), true, permission);
  assert.equal(rules.mayUse(permission, "https://example.com"), false, permission);
  assert.equal(rules.mayUse(permission, ""), false, permission);
}
for (const permission of ["media", "geolocation", "notifications", "usb", "hid", "midi", "midiSysex", "clipboard-read", "openExternal", "pointerLock", "unknown"])
  assert.equal(rules.mayUse(permission, rules.ORIGIN), false, permission);
assert.equal(rules.mayUse("fileSystem", rules.ORIGIN, { fileAccessType: "readable", isDirectory: false }), true);
for (const details of [undefined, { fileAccessType: "writable", isDirectory: false }, { fileAccessType: "readable", isDirectory: true }])
  assert.equal(rules.mayUse("fileSystem", rules.ORIGIN, details), false);

// The policy of the page: nothing from outside.
assert.match(rules.POLICY, /default-src 'none'/);
assert.doesNotMatch(rules.POLICY, /https?:|\*/);

// The window's place.
const screens = [{ x: 0, y: 0, width: 1920, height: 1040 }];
assert.deepEqual(rules.placeOf({ x: 10, y: 10, width: 900, height: 700, maximized: true }, screens), { x: 10, y: 10, width: 900, height: 700 });
for (const saved of [null, {}, { x: 5000, y: 0, width: 900, height: 700 }, { x: 0, y: -900, width: 900, height: 700 }, { x: 0, y: 0, width: 10, height: 10 }, { x: "0", y: 0, width: 900, height: 700 }])
  assert.deepEqual(rules.placeOf(saved, screens), { width: 1280, height: 860 }, JSON.stringify(saved));

// The size of everything.
assert.equal(rules.fits(1360, 900), 1); assert.equal(rules.fits(2077, 1196), 1.35); assert.equal(rules.fits(3840, 1560), 1.75);
assert.equal(rules.fits(700, 500), 0.8); assert.equal(rules.fits(9000, 9000), 2.5);
assert.deepEqual(rules.zoomOf(null, 2720, 1800), { auto: true, factor: 2 });
for (const bad of [{}, { auto: true }, { factor: 9 }, { factor: 0.1 }, { factor: "2" }, { factor: NaN }]) assert.equal(rules.zoomOf(bad, 1360, 900).auto, true, JSON.stringify(bad));
assert.deepEqual(rules.zoomOf({ factor: 1.6 }, 1920, 1080), { auto: false, factor: 1.6 });
assert.ok(rules.zoomOf({ factor: 3 }, 1360, 900).factor <= 1360 / 820 + 0.001, "a size of a larger window is brought down");
let z = { auto: true };
z = rules.zoomBy(z, "in", 1920, 1080); assert.deepEqual(z, { auto: false, factor: 1.25 });          // it fitted at 1.2
z = rules.zoomBy(z, "in", 1920, 1080); assert.equal(z.factor, 1.4);
z = rules.zoomBy(z, "out", 1920, 1080); assert.equal(z.factor, 1.25);
for (let i = 0; i < 30; i++) z = rules.zoomBy(z, "in", 1920, 1080);
assert.equal(z.factor, 2.25); assert.equal(rules.zoomShown(z, 1920, 1080).in, false); assert.equal(rules.zoomShown(z, 1920, 1080).out, true);
for (let i = 0; i < 30; i++) z = rules.zoomBy(z, "out", 1920, 1080);
assert.equal(z.factor, 0.6); assert.equal(rules.zoomShown(z, 1920, 1080).out, false);
assert.deepEqual(rules.zoomBy(z, "auto", 1920, 1080), { auto: true });
assert.deepEqual(rules.zoomBy(z, "other", 1920, 1080), z); assert.deepEqual(rules.zoomBy(z, null, 1920, 1080), z);
assert.deepEqual(rules.zoomShown({ auto: true }, 1360, 900), { percent: 100, auto: true, in: true, out: true });

// Files to save: what the editor's page made, and a name without a path.
for (const good of ["blob:hyperrig://editor/0f8fad5b-d9cb-469f-a165-70867728950e"]) assert.equal(rules.maySave(good), true, good);
for (const bad of ["blob:hyperrig://installer/0f8fad5b", "blob:https://example.com/0f8fad5b", "https://example.com/x.json", "hyperrig://editor/nam2chip.js", "file:///C:/x", "data:text/plain,x",
  "blob:hyperrig://editor.evil/0f8fad5b", "blob:hyperrig://editor/../x", "", null]) assert.equal(rules.maySave(bad), false, String(bad));
for (const [name, kept] of [["Preset 1A.hyperrig.json", "Preset 1A.hyperrig.json"], ["..\\..\\evil.json", "evil.json"], ["a/b/c.json", "c.json"], ["a<b>:c?.json", "abc.json"], ["", "HyperRig.json"], ["...", "HyperRig.json"],
  [null, "HyperRig.json"]]) assert.equal(rules.saveName(name), kept, String(name));

// The log: the page's rows, nothing else.
assert.deepEqual(rules.logRows('[{"a":1},{"b":"\\n"}]'), ['{"a":1}', '{"b":"\\n"}']);
for (const text of ["", "not json", "{}", "5", null, "[1,2]", "x".repeat(2 * 1024 * 1024)]) assert.deepEqual(rules.logRows(text), []);

assert.equal(rules.typeOf("web/tank-mini.html"), "text/html; charset=utf-8");
assert.equal(rules.typeOf("web/unknown.bin"), "application/octet-stream");
console.log("rules: all tests passed");
