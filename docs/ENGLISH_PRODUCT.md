# English HyperRig product

The maintained HyperRig interface and documentation use English. Project
destinations are centralized in `app/project.json`:

- Repository: https://github.com/danmigdev/hyperrig
- Issue form: https://github.com/danmigdev/hyperrig/issues/new/choose
- Releases: https://github.com/danmigdev/hyperrig/releases

The editor removes donation controls, payment-click tracking, the old report
upload service and its embedded public service key, the language selector,
the first-run language prompt, and automatic online update checks. Both normal
reporting and the independent startup-error screen open HyperRig's GitHub issue
form. No issue is submitted automatically. The editor's local diagnostic log
remains available.

The product builder derives a new bundle from the sealed MINI FX editor.
It edits parsed presentation boundaries and checks that comment removal does
not change JavaScript semantics. Independent tests compare the parsed USB
transport, Bluetooth transport, and command dispatcher before and after all
changes. The command-policy helper, FX guard, converter, firmware hash, and
qualified command families are preserved. The serial-open timeout adapter is
regenerated for the same method after comment removal; its only behavioral
change remains the previously tested 5-to-30-second host timeout.

Historical bundles, raw reports, third-party licenses, required notices, and
upstream input artifacts retain their original bytes. Original comments,
protocol field names, captured user text, and frozen test inputs may therefore
contain other languages. They are not product translations or new project
prose. The current UI sources are English; historical source versions remain
available in Git and selected source snapshots.

`tools/check_project_language.py` checks maintained Markdown for recurring
Italian prose. It is a focused regression guard, not proof that an arbitrary
string is English. Editor tests separately verify that a Spanish browser locale
and a saved Spanish preference still produce English UI.

The migration does not flash firmware, operate the MINI, change the Raspberry
Pi MIDI hub, or reclassify previous physical tests as tests of the new UI.
The existing connected editor session can be closed normally; the next launch
through the HyperRig launcher uses the English bundle.
