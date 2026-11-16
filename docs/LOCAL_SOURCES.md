# Local copies and HyperRig modifications

The requirement to retain the UltraRig firmware and apps is recorded in
[HYPERRIG_GOAL.md](HYPERRIG_GOAL.md). The following command verifies the
originals' hashes and inventories the material actually present, without
downloading or running installers:

```powershell
python -B -X utf8 tools/inventory_local_sources.py
```

The result is [local-source-inventory.json](../research/local-source-inventory.json).
The originals remain separate from HyperRig outputs, with their version,
provenance and SHA-256. Extraction directories and binaries are local and
ignored by Git; the information needed to obtain them again is retained in
the repository.

| Material | Local path | How it can be modified |
|---|---|---|
| Original G/B firmware, v1/v2 and app packages | `artifacts/alpha11/` | Unchanged reference copies |
| Original editor and converter | `recovered/ultrarig-original/web/` | Readable distributed HTML/JavaScript |
| Original Android assets | `recovered/android/assets/` | HTML/JavaScript and Capacitor configuration |
| Extracted Windows installer | `recovered/installer/` | Python 3.12 bytecode, constants and disassembly |
| G/B decompilation | `recovered/ghidra/tank-{g,b}-v{1,2}/` | Inferred C pseudocode and function map |
| Reconstructed A2 DSP | `firmware/src/`, `firmware/include/` | Compilable C, compared against the original kernels |
| Full MINI port | `firmware/mini/audio_port/`, `tools/audit_mini_*_port.py`, `tools/audit_mini_boot_contract.py` | C shim and checked patches to the original bytes |
| MINI editor | `app/mini/`, `tools/build_mini_app.py` | Profile and adaptations of the original code |
| Rebuilding G/B copies | `hyperrig/branding.py`, `tools/rebrand.py` | HyperRig firmware, installer and APK rebuilds |

The full MINI firmware contains the UltraRig G application, with the board
patches listed by the composer. The stock MINI application is not used as
a container for the DSP. Stock samples are used to reconstruct the board
and to restore it.

We have not recovered a complete, rebuildable original UltraRig C project.
Part of it has been reconstructed in C; the rest can be modified through
assembly, pseudocode and checked binary patches. Likewise, the installer
bytecode is not equivalent to its original Python files. The inventory
makes these distinctions explicit without claiming a level of completeness
that the recovered material has not reached. Licenses and attribution remain
unchanged, as described in [PROVENANCE.md](PROVENANCE.md).
