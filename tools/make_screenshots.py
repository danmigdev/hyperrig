"""The picture of the editor in README.md (docs/images/editor.png), made again for a release.

The editor of a bundle runs in a browser with the simulated pedal of tools/check_mini_dev_editor.py, as in that check: three presets
with names, scenes and a chain, the first one playing and its delay chosen. Offline; no device is opened. The picture is of the
page and of a simulated pedal, not of a pedal. The installer's picture (docs/images/installer.png) is the one that
tools/check_desktop_installer.py takes of the pedal that is ready for HyperRig (2-ready.png).

Usage, from the repository root:
    python -B tools/make_screenshots.py --bundle build/release-parts/editor --output build/screenshots
The picture is OUTPUT/editor.png; it goes to docs/images/ by hand, after a look.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
import check_mini_dev_editor as check  # noqa: E402

# The presets, as a player might have them: name, scenes, the chain before the amp (P) and after it (Q).
PRESETS = [
    ('Glass', ['Verse', 'Chorus', 'Solo', 'Ambient'], ['gate', 'comp'], ['ir', 'chorus', 'delay', 'plate']),
    ('Edge', ['Rhythm', 'Lead', 'Clean'], ['gate', 'ts9'], ['ir', 'delay', 'spring']),
    ('Twelve', ['Intro', 'Full'], ['comp'], ['ir', 'chorus', 'hybrid']),
]
QUIET = 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'


def defaults(identity):
    """{type: its seven parameters at their defaults}, from the lines the simulated pedal answers FXT with."""
    out, cur = {}, None
    for line in check.answers(identity)['FXT']:
        m = re.match(r'^FXT (\d+) (\S+) cost=', line)
        if m:
            cur = out[m.group(2)] = [0] * 7
            continue
        m = re.match(r'^FXT\s+(\d+) (\S+) -?\d+\.\.-?\d+ \((-?\d+)\)$', line)
        if m and cur is not None and int(m.group(1)) < 7:
            cur[int(m.group(1))] = int(m.group(3))
    return out


def make(bundle, output):
    output = Path(output).resolve()
    check.require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    output.mkdir(parents=True)
    product = json.loads((Path(bundle) / 'editor/profile.json').read_bytes())['development'].get('product')
    identity = f"HRID 1 {product['version']} {product['build_id']} banks=3" if product else None
    page = check.Page(bundle, output, identity)
    cdp = page.cdp
    try:
        page.wait('window.__urOk === true && !!document.getElementById("miniPortStatus")', 'the page')
        # The presets are put into the simulated pedal before the page connects, as a pedal that has them: the editor changes only what
        # the pedal reported, and reads all of it when it connects. Each block with the defaults the pedal lists for its type.
        cdp.evaluate('''(() => {
          const P = __pedal, defaults = %s, presets = %s, eight = a => [...a, ...Array(8).fill("")].slice(0, 8);
          presets.forEach(([name, scenes, pre, post], n) => {
            let id = 0; const block = type => ({id: id++, type, on: 1, p: defaults[type].slice()});
            Object.assign(P, {chain: {P: pre.map(block), Q: post.map(block)}, ampx: 1, amp: 1, bpm: 1200, scene: 0,
                              scenes: eight(scenes.map(() => "1")).map(x => x || "0").join(""), names: eight(scenes)});
            P.presets[n] = name; P.store[n] = P.keep();
          });
          P.load(0);
        })()''' % (json.dumps(defaults(identity)), json.dumps(PRESETS)))
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        cdp.evaluate('void connect()')
        page.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer', 'the connection', 60)
        page.wait(QUIET + ' && curPreset === 0', 'the first preset', 30)
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        stored = len(PRESETS)
        cdp.evaluate('document.querySelectorAll(".toast, .toasts > *, #toasts > *").forEach(e => e.remove())')
        delay = cdp.evaluate('(() => { const e = [...document.querySelectorAll("[data-id]")].find(x => /delay/i.test(x.innerText || "")); '
                             'return e ? e.getAttribute("data-id") : null; })()')
        check.require(delay is not None, 'no delay block on the page')
        cdp.click(f'[data-id="{delay}"]')
        page.wait(QUIET, 'a quiet page')
        time.sleep(1.5)
        cdp.evaluate('document.querySelectorAll(".toast, .toasts > *, #toasts > *").forEach(e => e.remove())')
        shot = cdp.screenshot(output / 'editor.png')['path']
        errors = cdp.evaluate('__errors')
        check.require(not errors, f'page errors: {errors}')
        print(json.dumps({'kind': 'hyperrig-screenshots', 'editor': str(shot), 'presets': stored, 'device_io': False}, indent=1))
    finally:
        page.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    make(args.bundle, args.output)


if __name__ == '__main__':
    main()
