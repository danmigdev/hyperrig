"use strict";
// Parse the actual shipped scripts; execute only the pure identity/write policy.
const fs = require("node:fs"), vm = require("node:vm"), assert = require("node:assert/strict");
const data = JSON.parse(fs.readFileSync(0, "utf8"));
const context = vm.createContext({HYPERRIG_MINI_BUILD: data.profile});
for (const source of data.scripts) new vm.Script(source);
vm.runInContext(data.policy, context);
const policy = context.HyperRigMini;
const pong = "PONG " + data.profile.firmware_version + " Nov 12 2026 16:04:11";
for (const transport of ["usb-cdc", "ble-nus"]) {
  for (const wrong of ["TANK MINI_009", "PONG tankg_fw M5.71 rel ble", "PONG tankb_fw M5.71 rel ble"])
    assert.equal(policy.acceptPong(wrong, transport).ok, false);
  assert.equal(policy.acceptPong(pong, transport).ok, true);
  assert.equal(policy.commandPolicy("PLIST", transport).allowed, true);
  assert.equal(policy.fullWriteEnabled(), false);
  assert.equal(policy.familyWriteEnabled(transport), transport === "usb-cdc");
  for (const command of ["PDEL 0", "FSPRESS 0", "LDBEGIN 8", "IRBEGIN 256 0 48000", "UBOOT"])
    assert.equal(policy.commandPolicy(command, transport).allowed, false, command);
  if (transport === "ble-nus") {
    for (const command of ["GAIN 0 0", "PLOAD 0", "PSAVE 31 Scratch", "SNAPSAVE 0", "FXA P 0 gate", "FXP 1 0 51", "FXE 1 0", "FXR 1", "SNAP 0"])
      assert.equal(policy.commandPolicy(command, transport).allowed, false, command);
  }
}
assert.equal(data.profile.capabilities.panel, false);
console.log("Editor scripts parse; identity boundaries, USB scope and BLE mutation blocks pass (offline).");
