"""Offline argument configuration tests; no process or device is opened."""
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import mini_browser_windows as configuration


class BrowserWindowsTests(unittest.TestCase):
    def test_windows_changes_only_existing_feature_switch(self):
        original = configuration.frozen_browser_arguments(Path('chrome.exe'), Path('isolated-profile'))
        expected = [value + ',SerialUsbDisplayNameWin' if value.startswith('--disable-features=') else value
                    for value in original]
        with patch.object(configuration.sys, 'platform', 'win32'):
            actual = configuration.browser_arguments(Path('chrome.exe'), Path('isolated-profile'))
            note = configuration.description(actual)
        self.assertEqual(actual, expected)
        self.assertEqual(sum(value.startswith('--disable-features=') for value in actual), 1)
        self.assertEqual(configuration.configure_arguments(actual, windows=True), actual)
        self.assertTrue(note['disabled_for_this_process'])
        self.assertFalse(note['permissions_changed'] or note['protocol_changed'] or note['system_configuration_changed'])
        self.assertIn(configuration.REVISION, note['source_urls'][0])

    def test_other_platforms_keep_frozen_arguments(self):
        original = configuration.frozen_browser_arguments('chrome', 'isolated-profile')
        with patch.object(configuration.sys, 'platform', 'linux'):
            actual = configuration.browser_arguments('chrome', 'isolated-profile')
            note = configuration.description(actual)
        self.assertEqual(actual, original)
        self.assertFalse(note['disabled_for_this_process'])

    def test_rejects_ambiguous_windows_switches_without_mutating_input(self):
        for arguments in (['chrome'], ['chrome', '--disable-features=A', '--disable-features=B']):
            original = arguments.copy()
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                configuration.configure_arguments(arguments, windows=True)
            self.assertEqual(arguments, original)


if __name__ == '__main__':
    unittest.main()
