"""Explicit-port, read-only MIDI identification and preset backup."""

import json
from pathlib import Path
import queue
import time

from .jieli import sha256
from .mini import Frame, READ_WINDOWS, decode_table, read_request, validate_readonly


def _rtmidi():
    try:
        import rtmidi
    except ImportError as exc:
        raise RuntimeError('MIDI support is optional: install with python -m pip install -e ".[midi]"') from exc
    return rtmidi


def ports() -> dict:
    api = _rtmidi()
    return {"inputs": api.MidiIn().get_ports(), "outputs": api.MidiOut().get_ports()}


class ReadOnlyMini:
    def __init__(self, input_port: int, output_port: int):
        self.input_port, self.output_port = input_port, output_port
        self.messages = queue.Queue()
        self.identity = None

    def __enter__(self):
        api = _rtmidi()
        self.midi_in, self.midi_out = api.MidiIn(), api.MidiOut()
        inputs, outputs = self.midi_in.get_ports(), self.midi_out.get_ports()
        if not 0 <= self.input_port < len(inputs) or not 0 <= self.output_port < len(outputs):
            raise ValueError("MIDI port index outside available ports")
        self.midi_in.ignore_types(sysex=False, timing=True, active_sense=True)
        self.midi_in.set_callback(lambda event, _: self.messages.put(bytes(event[0])))
        try:
            self.midi_in.open_port(self.input_port)
            self.midi_out.open_port(self.output_port)
            reply = self.exchange(Frame(0x11))
            name = reply.body.split(b"\0", 1)[0].decode("ascii")
            if not name.startswith("TANK MINI_") or not name[len("TANK MINI_"):].isdigit():
                raise ValueError(f"selected device identifies as {name!r}, not a Tank Mini")
            self.identity = name
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        self.midi_in.close_port()
        self.midi_out.close_port()

    def exchange(self, frame: Frame, timeout: float = 2.0) -> Frame:
        validate_readonly(frame)
        if frame.command != 0x11 and self.identity is None:
            raise ValueError("identify the Tank Mini before reading")
        while not self.messages.empty():
            try:
                self.messages.get_nowait()
            except queue.Empty:
                break
        self.midi_out.send_message(list(frame.encode()))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                wire = self.messages.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty:
                break
            if not wire.startswith(b"\xf0"):
                continue
            reply = Frame.decode(wire)
            if reply.command == 0 and reply.body != b"\0":
                raise ValueError(f"device rejected the request: {reply.body.hex()}")
            if reply.command == frame.command:
                if frame.command == 0x23:
                    length = int.from_bytes(frame.body[5:8], "little")
                    if reply.body[:8] != frame.body or len(reply.body) != 8 + length:
                        raise ValueError("read reply does not match requested address/length")
                return reply
        raise TimeoutError("no valid MIDI reply before timeout")

    def read(self, window: str) -> bytes:
        size = READ_WINDOWS[window][2]
        data = bytearray()
        # Conservative reads; every response is checked against the requested range.
        for offset in range(0, size, 128):
            reply = self.exchange(read_request(window, offset, min(128, size - offset)))
            data.extend(reply.body[8:])
        return bytes(data)

    def backup(self, destination: Path) -> dict:
        # Two equal reads establish a stable preset snapshot. This is NOT a NOR dump.
        a, b = self.read("presets"), self.read("presets")
        if a != b:
            raise ValueError("preset bank changed between reads; retry with the pedal idle")
        presets = decode_table(a)
        destination.mkdir(parents=True, exist_ok=False)
        (destination / "presets.bin").write_bytes(a)
        info = {"identity": self.identity, "scope": "preset bank, not a full flash/recovery backup",
                "bytes": len(a), "sha256": sha256(a), "equal_reads": 2,
                "presets": [p.to_dict() for p in presets]}
        (destination / "presets.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
        return info
