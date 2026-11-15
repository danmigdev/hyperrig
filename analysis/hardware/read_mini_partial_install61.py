"""Run the unchanged sixth inspection with its existing user-site dependencies.

The administrative broker uses isolated Python. The historical prepare() imports
rtmidi installed in this user's site directory. Adding that directory explicitly
does not execute site customization or .pth files, and does not open MIDI ports.
The original inspection, its source pins and its output paths remain unchanged.
"""
from pathlib import Path
import runpy
import site
import sys

sys.path.append(site.getusersitepackages())
runpy.run_path(str(Path(__file__).with_name('read_mini_partial_install6.py')), run_name='__main__')
