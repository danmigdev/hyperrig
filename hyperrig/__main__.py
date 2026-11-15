import argparse
import json
from pathlib import Path
import sys
import wave


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hyperrig", description="Firmware research and read-only Tank Mini tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    analysis = sub.add_parser("analyze", help="verify and extract the downloaded firmware artifacts")
    analysis.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sub.add_parser("ports", help="list MIDI ports, without opening them")
    sub.add_parser("port-status", help="show established Mini compatibility facts and remaining port work")
    for command in ("identify", "backup"):
        item = sub.add_parser(command, help="read the Tank Mini identity" if command == "identify" else "read the preset bank twice")
        item.add_argument("--input", type=int, required=True, help="MIDI input index from ports")
        item.add_argument("--output", type=int, required=True, help="MIDI output index from ports")
        if command == "backup":
            item.add_argument("--directory", type=Path, required=True, help="new output directory")
    frame = sub.add_parser("decode-sysex", help="decode a hex SysEx frame offline")
    frame.add_argument("hex")
    bank = sub.add_parser("inspect-presets", help="decode a 1942-byte Tank Mini preset bank offline")
    bank.add_argument("path", type=Path)
    render = sub.add_parser("render-a2l", help="offline float reference; not the firmware's fixed-point DSP")
    render.add_argument("capture", type=Path)
    render.add_argument("input_wav", type=Path, help="mono PCM16 at 48000 Hz")
    render.add_argument("output_wav", type=Path, help="new output file")
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            from .analyze import analyze
            result = analyze(args.root.resolve())
            print(f"Verified {len(result['ultrarig'])} UltraRig images and {result['tank_mini']['version_in_binary']}.")
            print(f"Evidence: {args.root.resolve() / 'analysis/summary.json'}")
            return 0
        if args.command == "render-a2l":
            from .a2l_reference import render_wave
            result = render_wave(args.capture, args.input_wav, args.output_wav)
        elif args.command == "port-status":
            from .porting import status
            result = status(Path(__file__).resolve().parents[1])
        elif args.command == "decode-sysex":
            from .mini import Frame
            f = Frame.decode(bytes.fromhex(args.hex))
            result = {"command": f.command, "body_hex": f.body.hex(), "body_ascii": f.body.decode("ascii", errors="replace")}
        elif args.command == "inspect-presets":
            from .mini import decode_table
            result = [p.to_dict() for p in decode_table(args.path.read_bytes())]
        elif args.command == "ports":
            from .device import ports
            result = ports()
        else:
            from .device import ReadOnlyMini
            with ReadOnlyMini(args.input, args.output) as device:
                result = {"identity": device.identity}
                if args.command == "backup":
                    result = device.backup(args.directory)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, wave.Error) as exc:
        print(f"HyperRig: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
