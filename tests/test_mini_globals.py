"""The settings for every preset: the rules and the simulated pedal of the page check, without the firmware (tools/check_mini_globals.py compares both with it)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'upstream/pi32v2-isa/tools/llvm/sim.py').is_file():
    pytest.skip('no simulator here', allow_module_level=True)
sys.path.insert(0, str(ROOT / 'tools'))
import check_mini_globals as globals_check  # noqa: E402

QUESTIONS = [(w, a) for w, a in zip(globals_check.WORDS, globals_check.DEFAULTS) if w != 'CALIB sens']


def test_the_rules_permit_what_the_firmware_takes_and_nothing_else():
    lines = globals_check.corpus()
    got = globals_check.permitted([x for x, _ in lines] + globals_check.SPELLINGS, QUESTIONS)
    assert got['after'] == [want for _, want in lines] + [False] * len(globals_check.SPELLINGS)
    assert got['before'] == [] and got['other'] == []
    assert sum(want for _, want in lines) > 300


def test_a_word_the_pedal_has_not_said_is_not_permitted():
    lines = [x for x, want in globals_check.corpus() if want]
    for word, _ in QUESTIONS:
        got = globals_check.permitted(lines, [q for q in QUESTIONS if q[0] != word])['after']
        assert got == [x.split(' ')[0] != word for x in lines], word


def test_the_simulated_pedal_takes_them_as_they_are_written():
    assert [x[0] for x in globals_check.simulated(list(globals_check.WORDS))] == globals_check.DEFAULTS
    lines, geq = globals_check.corpus(), [0] * 5
    for (line, want), answer in zip(lines, globals_check.simulated([x for x, _ in lines])):
        assert globals_check.taken(line, answer, geq) == want, (line, answer)
        if answer[0].startswith('GEQ '):
            geq = [int(x) for x in answer[0].split()[1:]]


@pytest.mark.parametrize('loud, gain, said', [(-200, 0, 'suggest=+2.0 trim=0.0'), (-120, 0, 'suggest=-6.0 trim=0.0'), (-120, 4, 'suggest=-10.0 trim=0.0'), (0, 0, 'suggest=-12.0 clamped=1 trim=0.0'),
                                              (-599, 0, 'suggest=+12.0 clamped=1 trim=0.0'), (-600, 0, 'suggest=none trim=0.0'), (-999, 0, 'suggest=none trim=0.0')])
def test_the_suggestion_of_the_calibration(loud, gain, said):
    line = globals_check.node(globals_check.simulated_globals.GLOBALS + 'const g = makeGlobals(), live = {gain: %d, trim: 0, level: null, slot: -1, audio: 2}; globalAnswer(g, live, "CALIB", ["start"]);'
                              'console.log(JSON.stringify(calibWindow(g, live, %d, %d)));' % (gain, loud, loud), None)
    assert line.startswith('CALIB running=1 win=1 peak=') and f' target=-18.0 {said} slot=-1' in line
