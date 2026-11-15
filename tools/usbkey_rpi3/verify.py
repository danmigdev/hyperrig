"""Build and exercise USB_KEY exclusively with virtual or fake GPIO lines.

Uses the existing Linux C compiler (WSL Ubuntu on Windows). It never invokes
--execute, reads no GPIO device and installs nothing. The resulting executable
is for this compiler's architecture; an x86_64 result is not a Pi3 binary.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build/mini-usbkey-rpi3"
REPORT = ROOT / "research/mini-usbkey-rpi3.json"
SPEC = ROOT / "upstream/m-bootloader/docs/SPEC.md"
SPEC_COMMIT = "3ac7651a019fa44daba061b05654278496477b64"
SPEC_SHA256 = "d86ae060b1db368a8aba421e21903b3b9c7517943bcf2667ee170a5a96a2863c"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], *, expected: int = 0) -> subprocess.CompletedProcess[str]:
    if "--execute" in args:
        raise ValueError("Verifier must never execute GPIO operations")
    command = (["wsl.exe", "--distribution", "Ubuntu", "--exec"] if os.name == "nt" else []) + args
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", timeout=90)
    if result.returncode != expected:
        raise RuntimeError(f"{command!r}: expected {expected}, got {result.returncode}\n"
                           f"{result.stdout}\n{result.stderr}")
    return result


def main() -> None:
    if digest(SPEC) != SPEC_SHA256:
        raise ValueError("Pinned USB_KEY reference changed; review before regenerating report")
    BUILD.mkdir(parents=True, exist_ok=True)
    compiler = run(["cc", "--version"]).stdout.splitlines()[0]
    machine = run(["cc", "-dumpmachine"]).stdout.strip()
    source = "tools/usbkey_rpi3/usbkey.c"
    binary = "build/mini-usbkey-rpi3/usbkey-rpi3"
    test = "build/mini-usbkey-rpi3/test-usbkey"
    run(["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", source, "-o", binary])
    run(["cc", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
         "tools/usbkey_rpi3/test_usbkey.c", "-o", test])
    unit = json.loads(run([f"./{test}"]).stdout)
    assert unit["result"] == "PASS" and unit["GPIO_access"] is False

    # This path deliberately cannot be a GPIO device. Default mode must ignore
    # it and never open it; the same binary's simulation is checked below.
    simulation = json.loads(run([f"./{binary}", "--chip", "/THIS_IS_NOT_A_GPIO_DEVICE"]).stdout)
    assert simulation["mode"] == "simulation" and simulation["result"] == "ack_candidate"
    assert simulation["frames"] == 1 and simulation["mini_verified"] is False
    assert simulation["ROM_identity_verified"] is False
    assert simulation["release_cleanup_ok"]
    assert simulation["half_hold_ns"] == {"min": 10000, "max": 10000}
    (BUILD / "simulation.json").write_text(json.dumps(simulation, indent=2)+"\n", encoding="utf-8")

    for bad in ["0", "60001", "invalid", "-1"]:
        run([f"./{binary}", "--timeout-ms", bad], expected=1)
    run([f"./{binary}", "--unknown"], expected=1)
    run([f"./{binary}", "--help"])
    # A fresh isolated directory belongs solely to this verifier. The tool must
    # preserve an existing log and write a new JSON log without GPIO operations.
    with tempfile.TemporaryDirectory(prefix="cli-", dir=BUILD) as temporary:
        directory = Path(temporary)
        existing = directory / "existing.json"
        existing.write_bytes(b"DO NOT REPLACE\n")
        relative_existing = existing.relative_to(ROOT).as_posix()
        run([f"./{binary}", "--log", relative_existing], expected=1)
        assert existing.read_bytes() == b"DO NOT REPLACE\n"
        new = directory / "new.json"
        run([f"./{binary}", "--log", new.relative_to(ROOT).as_posix()])
        assert json.loads(new.read_text())["mode"] == "simulation"

    # A bounded, real host-clock benchmark with fake lines. TIMEOUT is intended:
    # this mode generates frames for the entire requested measurement window.
    timing = json.loads(run([f"./{binary}", "--timing-only", "--timeout-ms", "100"], expected=2).stdout)
    assert timing["mode"] == "timing-only" and timing["result"] == "timeout"
    assert timing["frames"] and timing["release_cleanup_ok"]
    (BUILD / "timing-only.json").write_text(json.dumps(timing, indent=2)+"\n", encoding="utf-8")

    report = {
        "schema": 1,
        "status": "offline_checks_passed_hardware_unverified",
        "device_access": False,
        "GPIO_executed": False,
        "NVM_access": False,
        "ARM_target_compilation": machine.startswith(("arm", "aarch64")),
        "Raspberry_Pi_3_build_and_run_verified": False,
        "Raspberry_Pi_3_GPIO_tested": False,
        "MINI_USB_KEY_recovery_verified": False,
        "sources": {
            "m_bootloader_SPEC": {
                "path": SPEC.relative_to(ROOT).as_posix(), "commit": SPEC_COMMIT,
                "sha256": digest(SPEC), "section": "4.3",
                "url": f"https://github.com/jvitkauskas/m-bootloader/blob/{SPEC_COMMIT}/docs/SPEC.md",
                "hardware_evidence_scope": "Pico plus SMK-37 Pro only; no Pi3 or MINI proof",
            },
            "protocol": "https://kagaimiq.github.io/jielie/isp/usb/usb-key.html",
            "gpio_v2": "https://www.kernel.org/doc/html/latest/userspace-api/gpio/chardev.html",
            "open_drain_emulation": "https://docs.kernel.org/driver-api/gpio/driver.html#gpio-electrical-configuration",
            "Raspberry_Pi_pinout": "https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#pin-layout",
            "Raspberry_Pi_GPIO_whitepaper": "https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-006553-WP-2-A%20history%20of%20GPIO%20usage%20on%20Raspberry%20Pi%20devices,%20and%20current%20best%20practices.pdf",
        },
        "source_files": {p.relative_to(ROOT).as_posix(): digest(p)
                         for p in sorted((ROOT / "tools/usbkey_rpi3").glob("*")) if p.is_file()},
        "host_validation": {
            "compiler": compiler, "machine": machine,
            "asan_ubsan": unit, "strict_compilation": "-Wall -Wextra -Werror",
            "CLI_cases": 9,
            "default_fake_device_path_succeeded": True,
            "existing_log_preserved": True,
            "binary_sha256": digest(ROOT / binary),
            "simulation_log_sha256": digest(BUILD / "simulation.json"),
        },
        "host_timing_fake_lines": {
            "window_ms": 100, "frames": timing["frames"],
            "max_wait_lateness_ns": timing["max_wait_lateness_ns"],
            "half_hold_ns": timing["half_hold_ns"],
            "max_software_operation_ns": timing["max_gpio_call_ns"],
            "log": "build/mini-usbkey-rpi3/timing-only.json",
            "log_sha256": digest(BUILD / "timing-only.json"),
            "actual_GPIO_ioctl_or_edge_measurement": False,
        },
        "protocol": {
            "word": "0x16EF", "order": "MSB-first", "clock": "D+ rising", "data": "D-",
            "minimum_requested_half_ns": 10000, "minimum_frame_gap_ns": 150000,
            "maximum_requested_runtime_ms": 60000, "default_requested_runtime_ms": 20000,
            "ACK_policy_not_ROM_spec": {"minimum_low_ns": 500000, "maximum_low_ns": 3000000,
                                        "maximum_sample_gap_ns": 100000},
            "ACK_requires": ["both released lines seen HIGH", "at least one complete frame sent",
                             "both LOW while both outputs released", "finite low pulse ends",
                             "no excessive gap between ACK samples"],
        },
        "wiring_experimental": {
            "DP": {"BCM": 17, "physical_header": 11},
            "DM": {"BCM": 27, "physical_header": 13},
            "ground_physical_header": 6, "pullup_supply_physical_header": 1,
            "pullups_ohms_each": 2200, "pullup_supply_volts": 3.3,
            "VBUS_connected": False, "PC_USB_simultaneously_connected": False,
            "target_power": "own battery", "Pi_power": "own supply",
        },
        "open_gates": [
            "Compile and validate GPIO v2 support on the actual Pi3/kernel",
            "Confirm actual GPIO ioctl latency and electrical waveforms on that Pi3",
            "Verify MINI cold-boot USB_KEY window, battery power and connector path",
            "Confirm candidate ACK by subsequent independent WL82 ROM USB enumeration",
            "Demonstrate recovery with stock intact before relying on it for a replacement app",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "cases": unit["cases"], "CLI_cases": 9,
                      "machine": machine, "GPIO_access": False,
                      "report": REPORT.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
