# Editor tour during the reload test

`tools/activate_mini_editor_ui.py` is an operator utility for the already frozen
`probe_mini_browser_saved_reload.py` test. It does not modify the probe, guard,
qualifier, or their reports.

With `--execute`, it selects only the exact local page attested by the active
report, brings the window forward, and saves screenshots. It waits for three
stable hit-tests on the Skip button, performs a real CDP click, and verifies
that `.coach` disappears. It then clicks Connect once, only with
`requests=opens=mutations=0`, a closed port, and a state that is neither connected
nor connecting. It verifies the trusted click and chooser request. It does not
select the device, send serial commands, or certify a connection. Any subsequent
selection remains the operator's responsibility, and the original probe flow
remains active.

```powershell
python tools/activate_mini_editor_ui.py --check-only --report build/mini-saved-reload-ui-NN/report.json
python tools/activate_mini_editor_ui.py --execute --report build/mini-saved-reload-ui-NN/report.json --output build/mini-tour-operation-NN
```

A new output is required; there is no automatic repetition after an uncertain
click. The default reads no input and does not open a browser. Automated tests
use only simulated CDP. Visibility and focus are observations: none of their
properties is falsified. This procedure addresses click interception by the
tour; by itself, it neither resolves nor diagnoses a subsequent empty device
chooser or the USB nonresponse also observed by the COM client.
