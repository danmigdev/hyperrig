# Code and artifact provenance

HyperRig is the local research repository chosen by the user. It is not an
UltraRig release, is not affiliated with M-VAVE, and does not claim authorship
of the recovered code.

| Source | Material used | Local handling |
|---|---|---|
| [UltraRig](https://github.com/manuaguirre9/ultrarig) | Firmware, installer, editor, NAM converter | Originals in `artifacts/`, extractions in `recovered/`; LICENSE/NOTICE preserved |
| [M-VAVE downloads](https://www.m-vave.com/download) | TANK MINI 009 update | Official sample, pinned hash; binaries excluded from Git |
| [jl-misctools](https://github.com/kagaimiq/jl-misctools) | ENC/SFC/JLFS reference | MIT repository preserved in `upstream/`; HyperRig parser reconstructed and checked against samples |
| [pi32v2-isa](https://github.com/jvitkauskas/pi32v2-isa) | Disassembler and ISA table | MIT-0 code, CC0 table/documentation; used by the local tool |
| [ghidra-jieli](https://github.com/virtualabs/ghidra-jieli) | Ghidra processor specification | Apache-2.0; copy in the local Ghidra distribution |
| [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | Decompiler | Distribution 12.2 verified against the GitHub digest |
| [tankmini-linux](https://github.com/viniciusapl97/tankmini-linux) | Protocol documentation and captured vectors | MIT; reference for the new Python implementation |
| [m-bootloader](https://github.com/jvitkauskas/m-bootloader) | AC791N/ROM specification, P33 and cache registers | MIT; SoC reference only, no FM1/SMK37 binary used on MINI |
| [m-flasher](https://github.com/jvitkauskas/m-flasher) | ROM CDBs and USB-client reference | Pinned commit; no loader for other boards uploaded to MINI |
| [AC79 SDK mirror](https://github.com/amitv87/fw-AC79_AIoT_SDK) | Reference headers and LICENSE, `iis.h` and `cpu.a` for the I2S selector | Official Gitee source could not be resolved from the local network; mirror, commit, and hashes recorded |
| [JieLi toolchain](https://jl-update.oss-cn-shenzhen.aliyuncs.com/jieli-linux-toolchains-20260730.1.tar.xz) | pi32v2 Clang, linker, and objdump | Used locally as tools through WSL; archive verified and ignored by Git |
| [Apktool](https://github.com/iBotPeaches/Apktool) | Resource/Smali decoding and APK reconstruction | Version 3.0.3 verified against the release digest |
| [Uber APK Signer](https://github.com/patrickfav/uber-apk-signer) | APK alignment, signing, and verification | Version 1.3.0 verified against the published checksum; local development key |

Recovered UltraRig code retains PolyForm Noncommercial 1.0.0 and the component
licenses declared in the package. The repository's new name does not change
those terms. Derived pseudocode and assembly are not presented as a new
independent implementation or as original sources.

The A2L1 parser and numerical model `hyperrig/a2l_reference.py` are reconstructed
from the converter distributed with UltraRig. For these files, the Required
Notice and PolyForm Noncommercial 1.0.0 are preserved in
`third_party/ultrarig/LICENSE.md`, together with the original `NOTICE.md`.
The Float64 reference is not presented as an exact copy of the pedal's integer DSP.

Files `firmware/src/hyperrig_dot.c`, `hyperrig_head.c`, and their headers are
also reconstructions derived from UltraRig firmware; they retain the same
Required Notice and license. The local interpreter executes three regions
of the original sample without redistributing the firmware. The new C
structure and function names are not attributed to the original author.

Renamed copies in `build/hyperrig/` preserve the originals' LICENSE, NOTICE,
and THIRD_PARTY_LICENSES in full, including as APK assets. The Android signature
is identified as HyperRig Local Development. Originals remain separate for
evidence verification; see [REBRANDING.md](REBRANDING.md).

Repository coordinates, commits, URLs, and SHA-256 values are in
`research/sources.lock.json` and `research/input-manifest.json`. The `upstream/`
directory also preserves cloned projects' LICENSE files. No recovered binary
or source has been published remotely.
