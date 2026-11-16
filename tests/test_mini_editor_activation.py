"""Offline fake-CDP tests; never start a browser or access serial/GPIO."""
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

from tools import activate_mini_editor_ui as tool

URL = 'http://127.0.0.1:1234/tankmini.html?saved_reload_continuation=1'


class Clock:
    def __init__(self): self.value = 0
    def __call__(self): return self.value
    def sleep(self, seconds): self.value += seconds


class FakeCDP:
    def __init__(self, *, coach=True, covered=False, trusted=True, lose_release=False):
        self.state = dict(url=URL, visibility='hidden', focused=False, coach=coach,
            connected=False, connecting=False, serialOpen=False,
            guard=dict(requests=0, opens=0, mutations=0, stopped=False, fatal=None,
                       requestEnabled=True, appInstalled=True))
        self.covered, self.trusted, self.lose_release = covered, trusted, lose_release
        self.calls, self.clicks, self.installed, self.removed = [], [], False, False
        self.current = None

    def evaluate(self, expression):
        if expression == tool.STATE: return copy.deepcopy(self.state)
        if expression == tool.INSTALL_OBSERVER:
            if self.installed: raise ValueError('already installed')
            self.installed = True; return True
        if expression == '__miniTourOperator.clicks': return copy.deepcopy(self.clicks)
        if expression == '__miniTourOperator.remove()': self.removed = True; return None
        if 'scrollIntoView' in expression: return None
        for selector in (tool.SKIP, tool.CONNECT):
            if expression == tool.target_script(selector):
                self.current = selector
                return dict(x=10 if selector == tool.SKIP else 100, y=30, width=60, height=30,
                            okay=not self.covered, hit='BUTTON' if not self.covered else 'DIV')
        raise AssertionError(expression)

    def call(self, method, params=None):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'Input.dispatchMouseEvent' and params['type'] == 'mouseReleased':
            if self.lose_release: raise ConnectionError('lost CDP reply; outcome unknown')
            self.clicks.append(dict(selector=self.current, trusted=self.trusted, utc='2026-11-16T00:00:00Z'))
            if self.trusted:
                if self.current == tool.SKIP: self.state['coach'] = False
                else: self.state['guard']['requests'] = 1; self.state['connecting'] = True
        return {}

    def screenshot(self, path):
        self.calls.append(('Page.captureScreenshot', None))
        return {'path': str(path), 'sha256': 'synthetic-offline-no-file'}


class ActivationTests(unittest.TestCase):
    def activate(self, cdp):
        clock = Clock(); published = []
        result = tool.activate(cdp, {'url': URL}, Path('build/offline-unit-only'),
            clock=clock, sleep=clock.sleep, publish=lambda value: published.append(copy.deepcopy(value)))
        return result, published

    def test_two_trusted_ui_clicks_with_screenshot_and_verified_absent_tour(self):
        cdp = FakeCDP(); result, reports = self.activate(cdp)
        self.assertEqual(result['result'], 'request_observed')
        self.assertEqual([x['selector'] for x in result['clicks']], [tool.SKIP, tool.CONNECT])
        self.assertEqual(result['after']['guard']['requests'], 1)
        self.assertEqual(result['after']['guard']['opens'], 0)
        self.assertEqual(result['direct_protocol_commands'], [])
        self.assertFalse(result['connection_verified']); self.assertTrue(cdp.removed)
        names = [name for name, _ in cdp.calls]
        self.assertEqual(names.count('Page.captureScreenshot'), 2)
        self.assertLess(names.index('Page.captureScreenshot'), names.index('Input.dispatchMouseEvent'))
        self.assertTrue(reports[0]['actions'][0]['dispatch_intent'])
        self.assertNotIn('observed_click', reports[0]['actions'][0])

    def test_no_tour_requires_only_one_connect_click(self):
        result, _ = self.activate(FakeCDP(coach=False))
        self.assertEqual(result['result'], 'request_observed')
        self.assertTrue(result['tour_already_absent'])
        self.assertEqual([x['selector'] for x in result['clicks']], [tool.CONNECT])

    def test_covered_hit_test_never_clicks_even_with_hidden_visibility(self):
        cdp = FakeCDP(covered=True); result, _ = self.activate(cdp)
        self.assertEqual(result['result'], 'fail')
        self.assertIn('hit-test', result['error'])
        self.assertFalse(any(name == 'Input.dispatchMouseEvent' for name, _ in cdp.calls))

    def test_untrusted_event_and_lost_cdp_response_never_repeat_click(self):
        for options in ({'trusted': False}, {'lose_release': True}):
            with self.subTest(options=options):
                cdp = FakeCDP(**options); result, _ = self.activate(cdp)
                self.assertEqual(result['result'], 'fail')
                self.assertEqual(len(result['actions']), 1)
                self.assertEqual(sum(name == 'Input.dispatchMouseEvent' for name, _ in cdp.calls), 2)

    def test_existing_request_open_connecting_or_mutation_blocks_all_ui_input(self):
        for key in ('requests', 'opens', 'mutations', 'connecting', 'connected', 'serialOpen'):
            with self.subTest(key=key):
                cdp = FakeCDP()
                if key in cdp.state['guard']: cdp.state['guard'][key] = 1
                else: cdp.state[key] = True
                result, _ = self.activate(cdp)
                self.assertEqual(result['result'], 'fail'); self.assertEqual(cdp.calls, [])

    def test_real_closed_report_rejected_before_cdp(self):
        with self.assertRaisesRegex(ValueError, 'active frozen'):
            tool.prepare(tool.ROOT/'build/mini-saved-reload-ui-03/report.json')

    def test_active_report_pin_checks_are_file_only(self):
        path = tool.ROOT/'build/unit-only-active-report.json'
        report = {'kind': 'mini-browser-saved-reload-continuation', 'result': 'running',
            'phase': 'awaiting_exact_UIA_selection', 'origin': 'http://127.0.0.1:1234',
            'CDP_http': 'http://127.0.0.1:1235', 'source_sha256': dict(tool.PINS)}
        original_read = tool.read_shared_bytes
        def read(p): return json.dumps(report).encode() if Path(p) == path else original_read(p)
        with patch.object(tool, 'read_shared_bytes', side_effect=read):
            self.assertEqual(tool.prepare(path)['url'], URL)
            report['source_sha256'][next(iter(tool.PINS))] = '0'*64
            with self.assertRaisesRegex(ValueError, 'pin differs'): tool.prepare(path)

    def test_default_does_not_prepare_or_access_browser(self):
        with (patch.object(tool, 'prepare', side_effect=AssertionError('read')),
              patch.object(tool, 'CDP', side_effect=AssertionError('browser')),
              patch.object(tool, 'urlopen', side_effect=AssertionError('network'))):
            self.assertEqual(tool.main([]), 0)

    def test_actual_original_initial_S_without_connecting_survives_json(self):
        html = (tool.ROOT/'build/hyperrig-mini-ui-v2/app/web/tankmini.html').read_text('utf-8')
        initial = re.search(r'const S = \{.*?\};', html, re.S).group(0)
        script = r"""const vm=require('node:vm'),fs=require('node:fs');
          const input=JSON.parse(fs.readFileSync(0,'utf8'));
          const context=vm.createContext({location:{href:input.url},
            document:{visibilityState:'hidden',hasFocus:()=>false,querySelector:()=>null},
            SerialTransport:{isOpen:()=>false},__miniSavedReloadGuard:{state:input.guard}});
          vm.runInContext(input.initial,context);
          const missing=vm.runInContext("!Object.hasOwn(S,'connecting')",context);
          const before=vm.runInContext(input.expression,context);
          vm.runInContext('S.connecting=true',context);
          const after=vm.runInContext(input.expression,context);
          console.log(JSON.stringify({missing,before,after}));"""
        value = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True,
            input=json.dumps({'url': URL, 'guard': FakeCDP().state['guard'],
                              'initial': initial, 'expression': tool.STATE}))
        result = json.loads(value.stdout)
        self.assertTrue(result['missing'], 'fixture must retain the real initially absent property')
        self.assertIs(result['before']['connecting'], False)
        self.assertIs(result['before']['connected'], False)
        tool.idle(result['before'], URL)
        self.assertIs(result['after']['connecting'], True)
        with self.assertRaisesRegex(ValueError, 'disconnected and idle'):
            tool.idle(result['after'], URL)


if __name__ == '__main__': unittest.main()
