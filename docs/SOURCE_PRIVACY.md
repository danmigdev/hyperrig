# Source privacy

Personal workstation launch scripts and the original receive-stress report are
excluded from Git. The report's public derivative is
`research/mini-receive-stress-hardware-public.json`; it identifies the removed
field and the SHA256 of the private original. Historical evidence and source
pins continue to describe the unchanged private originals.

Run `python tools/audit_source_privacy.py` before publishing source changes.
The scanner reports file locations and finding types without printing matched
values. It checks tracked files and new files that are not ignored by Git.
It is a pattern check, not proof that every possible credential format is absent.

Use repository-relative paths or environment-based discovery for local files.
Keep device dumps, presets, credentials, keys and generated artifacts outside Git.
Public project URLs and required third-party attribution remain source metadata.

After a history cleanup, start from the rewritten branch. Merging old history
can restore removed objects. Private local recovery copies must never be pushed.
