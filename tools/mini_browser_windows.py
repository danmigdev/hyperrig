"""Process-local Windows chooser configuration; no browser or device I/O."""
from __future__ import annotations

import os
from pathlib import Path
import sys

from tools.launch_mini_desktop_readonly import browser_arguments as frozen_browser_arguments
from tools.verify_mini_browser import browser_path as frozen_browser_path

FEATURE = 'SerialUsbDisplayNameWin'
REVISION = '0985600c06a688b9c669e74afde7dacd5aaed047'
SOURCE_ROOT = 'https://raw.githubusercontent.com/chromium/chromium/' + REVISION + '/'


def browser_path():
    """Use the installed Edge on Windows; no launch, download or profile access."""
    if sys.platform != 'win32':
        return frozen_browser_path()
    roots = (os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'),
             os.environ.get('PROGRAMFILES', 'C:/Program Files'))
    for root in roots:
        candidate = Path(root)/'Microsoft/Edge/Application/msedge.exe'
        if candidate.is_file():
            return candidate
    raise FileNotFoundError('Existing Microsoft Edge required on Windows; nothing is installed automatically')


def configure_arguments(arguments, *, windows):
    """Retain every argument; merge one Windows feature into the existing switch."""
    result = list(arguments)
    if windows:
        positions = [i for i, value in enumerate(result) if value.startswith('--disable-features=')]
        if len(positions) != 1:
            raise ValueError('one existing disable-features switch required')
        index = positions[0]
        features = result[index].split('=', 1)[1].split(',')
        if FEATURE not in features:
            features.append(FEATURE)
        result[index] = '--disable-features=' + ','.join(features)
    return result


def browser_arguments(executable, profile):
    return configure_arguments(frozen_browser_arguments(executable, profile), windows=sys.platform == 'win32')


def description(arguments):
    switches = [value for value in arguments if value.startswith('--disable-features=')]
    disabled = len(switches) == 1 and FEATURE in switches[0].split('=', 1)[1].split(',')
    return {'kind': 'windows-serial-chooser-display-name-v1', 'platform': sys.platform,
            'browser_preference': 'installed Microsoft Edge on Windows; frozen chooser on other platforms',
            'browser_executable': arguments[0],
            'feature': FEATURE, 'disabled_for_this_process': disabled,
            'reason': 'Avoid synchronous USB hub descriptor reads for chooser display names; use cached device properties.',
            'source_revision': REVISION,
            'source_urls': [SOURCE_ROOT + 'services/device/public/cpp/device_features.cc',
                            SOURCE_ROOT + 'services/device/serial/serial_device_enumerator_win.cc'],
            'permissions_changed': False, 'protocol_changed': False,
            'system_configuration_changed': False, 'causality_proven': False}
