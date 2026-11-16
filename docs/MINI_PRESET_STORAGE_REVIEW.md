# Persistence of G presets adapted to MINI

Static review of the audio v2 candidate, performed on 15 November 2026.
The examined `PSAVE`, `SNAPSAVE`, and `PDEL` paths use the preset journal
in the USR area, with addresses allowed by the original G NOR check.
No geometry mismatch was found that would direct these three commands into
OTA, BTIF, or the final unit-data sector.

Reducing VM from 64 to 16 KiB does not, by itself, establish this.
There is also a post-update migration branch, conditional on boot type
`0x5A02`. Both this condition and the protections in its final helpers were
checked. The first syscfg backend is also BTIF-based: it must not be described
as a simple RAM cache.

This review executes no code on the pedal. At its completion, neither a G boot
nor a physical HyperRig save has yet been verified.
The [first-attempt report](../analysis/hardware/mini-first-install-run.json)
reports `RomCommandError`, `installed_image_verified=false`,
`full_NOR_verified=false`, and `automatic_reset=false`. Earlier ROM-plugin
tests do not replace persistence testing in the G application.

## Image and sources examined

| Input | SHA256 |
|---|---|
| `build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin` | `3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff` |
| `artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin` | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Decoded G area | `2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334` |
| Full backup `artifacts/my-mini-flash/20261115-paced-resume/flash-a.bin` | `72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180` |

Instructions come from
[G flash.asm](../analysis/firmware/m571_g_app/flash.asm), compared against
original and candidate bytes, not just constant searches in a linear disassembly.
The geometry is the one actually decoded from the candidate's JLFS directory.
The patch is `VM_PATCH` in
[audit_mini_ultrarig_port.py](../tools/audit_mini_ultrarig_port.py).
Offsets in the following table are physical NOR addresses; `0x020xxxxx`
addresses cited in the text are application CPU addresses.
All ranges are half-open: the final endpoint is excluded.

| Object | Physical range |
|---|---|
| MINI JLFS VM descriptor | `[0x82000,0xBE000)` |
| Two VM banks after clamping | `[0x82000,0x84000)`, `[0x84000,0x86000)` |
| OTA area to preserve, including metadata | `[0xB7000,0xBD000)` |
| MINI BTIF | `[0xBE000,0xBF000)` |
| MINI USR | `[0xBF000,0xFF000)` |
| Final unit-data sector | `[0xFF000,0x100000)` |
| Sectors usable by the preset journal | `[0xBF000,0xCF000)`, `[0xDD000,0xDF000)` |

The VM descriptor deliberately remains larger than actual VM: it includes the
area where stock stores the updater. It must not be interpreted as permission
to use the entire range for runtime records.

## Paths of the three commands

| Command | Relevant G chain |
|---|---|
| `PSAVE` | Dispatcher `0x0200B834`, branch `0x0200BA86`, call to `0x020077EC` from `0x0200BAC0` |
| `SNAPSAVE` | Branch `0x0200BB78`; RAM scene capture `0x0200A256`; with a valid current preset, `0x0200A312` calls `0x020077EC` from `0x0200A36C` |
| `PDEL` | Branch `0x0200C06E`; call to `0x020077EC` from `0x0200C084` with an empty record |

`PSAVE` and `PDEL` accept preset indices 0..31. `SNAPSAVE` accepts scene
indices 0..3; persistence uses the current preset, validated again within 0..31
by `0x0200A312`. A scene captured only in RAM without a valid current preset
does not demonstrate a NOR save.

Common writer `0x020077EC` also preserves the neighbouring preset in the same
pair and calls `0x02003040` from `0x02007936`. The latter validates the pair
index 0..15 and two lengths no greater than 1920 bytes. Rotation uses 18 physical
sectors. Mapper `0x020026BA` returns:

```text
index 0..15: 0xBF000 + index * 0x1000
index 16:    0xDD000
index 17:    0xDE000
```

Resolver `0x0200777A` adds either 0 or `0x800` to the base for the sector's
two halves. Metadata extends through the marker at sector+4092, staying within
4096 bytes. Startup scan `0x020031D4` traverses the same 18 sectors;
it rejects pair identifiers above 15 at `0x020032A2`. The remaining G dimensions
in this journal therefore match MINI USR without going through the VM descriptor.

The writer can rotate and rewrite a sector that also contains the neighbouring
preset. Application testing must therefore compare preserved logical content,
rather than assume that only the selected slot's page changes.

## Final erase and program checks

USR erase `0x02002D9E` requires a base of at least `0xBF000`, alignment of
4096, and an end no greater than `0xFF000`. USR program `0x02002F16` checks
base and end against the same range and divides writes at 256-byte page boundaries.

A second check, already present in original G and not introduced by the port,
is `0x02002994`. For the bounded values in the examined paths, it allows:

```c
base >= 0xBF000 && length <= 0x40000 && base + length <= 0xFF000
```

Erase wrapper `0x02002B80` calls it with 4096 bytes for opcode 200,
65536 for opcode 201, and 256 for opcode 204. Program wrapper
`0x02002EF2` calls it before NOR callee `0x02002E6A`. Rejection records
the address through `0x020029B0` and returns `-1`.

This establishes the boundary for the reconstructed calls, with valid bases
and lengths and no overflow. It is not formal verification of arbitrary
pointers, every NOR entrypoint, or all firmware updaters. Lower-level callees
still exist: the check must be followed through the actual chain, not attributed
indiscriminately to every flash operation.

## VM: geometry and persistence limits

`0x020221E4` looks up the JLFS name `vm` and derives the base from the directory;
it does not retain the previous G base as a constant. In initialisation
`0x02020664`, the patch at `0x0202067E` changes the clamp from `0x10000`
to `0x4000`:

```text
before: 20 e9 80 0b 60 e0 80 0b
after:  20 e9 80 0c 60 e0 80 0c
```

In the NOR branch, `0x02020732..0x02020742` produces two `0x2000`-byte
descriptors at bases `0x82000` and `0x84000`. Writer `0x02020A5A` checks
the offset and remaining bank space, while `0x02020376` derives the erase count
from its size. This geometry does not encroach on OTA, BTIF, or unit data.

There is, however, a further distinction: these VM helpers use `0x020201A2`
for erase and `0x020201CE` for program, reaching `0x02002B80` and
`0x02002EF2`, respectively. VM bases lie below `0xBF000`, so the original G
check rejects these requests. `0x020201A2` ignores the ioctl outcome and
returns 1; path `0x02020A5A` can also advance RAM state without propagating
program errors at `0x02020BBE/0x02020BCE`. A positive syscfg result must
therefore not be treated as proof of VM persistence. This behaviour already
existed in the examined G; the three preset commands use the separate USR journal
and allowed addresses. The review proposes no new blocking mechanism.

## OTA branch and boot type in our sequence

VM initialisation calls `0x02020210` from `0x0202074E`. The first check,
`0x02020100`, returns true only when `h[0x01C21CB4] == 0x5A02`;
otherwise, it returns at `0x02020350` before scanning OTA records.

If the type is `0x5A02`, the code looks for a valid record in the JLFS VM
extension or searches backward through flash; it verifies the type, marker
`0x5441`, header CRC, and name `LOADER.BIN`. The backup contains the loader
at `0xB7000` and the 80-byte record at `0xBCF00`, documented in
[MINI_BOOT_CONTRACT.md](MINI_BOOT_CONTRACT.md). That path calculates requests
to copy into VM, erase the loader at `0x0202033E`, and rewrite the record at
`0x0202034C`.

These are **requests**, not evidence of successful changes: both final helpers
pass through check `0x02002994`. VM addresses, `0xB7000`, and `0xBCF00`
are below `0xBF000` and are rejected. The clamp alone would not have prevented
these address calculations; the complete chain excludes writes through the
examined helpers. A working OTA migration for adapted G has not been qualified.

G boot parser `0x020017F6`, called from entry at `0x02000216`, calculates
the CRC over 78 bytes at `0x01C7FD8A`. If the CRC is nonzero and matches
the halfword at `0x01C7FD88`, it loads the type from `0x01C7FD8C`;
otherwise it uses `0x5A00`. After saving the type at `0x01C21CB4`, it clears
80 bytes `[0x01C7FD88,0x01C7FDD8)`.

Our software ROM-entry sequence uses the 16-byte marker `usb_update_mode\0`
at `0x01C7FD80`. It is present in stock MINI routine
`0x01C02362..0x01C02372` and reproduced in
[entry_recovery/reset.S](../firmware/mini/entry_recovery/reset.S).
The return plugin [rom_reset/startup.S](../firmware/mini/rom_reset/startup.S)
clears **only the first word**, not all 16 bytes. The halfword at
`0x01C7FD8C` therefore remains `0x646F`. For this marker, regardless of the
tail CRC result, the parser returns `0x5A00` or `0x646F`, never `0x5A02`.

This exclusion applies to the marker written by the known sequence and retained
until normal entry. It is neither a recent physical read of retention memory
nor a property of every reset. SPL copies the 80 bytes to RAM and clears
`h[0x01C7FD82]` in fragments `0x01C04DEC` and `0x01C04E66`; this is not
equivalent to clearing the type at `0x01C7FD8C`. A real update can write
`0x5A02`: stock MINI does so at `0x0206DA62..0x0206DA78`.
This review does not generalise the sequence to cold boot, an intervening
updater, or a partial application taking a different SPL branch.

## BTIF: format checking, not a promise of immutability

The syscfg table at `0x020558F4` uses initialiser `0x0201FEA4`, reader
`0x0201FF2A`, and writer `0x0201FFD2` as its first backend.
`0x0201FD6C` opens the name `mnt/sdfile/app/btif`, a string at `0x0203660C`.
The table at `0x02033B40` contains ID102/104/110/111, each with a 6-byte
payload. The backend verifies length and low8 CRC; it is not merely a volatile cache.

On the pinned backup, without publishing payload values:

| Record | Offset | G check result |
|---|---:|---|
| ID102 | `0xBE000` | Correct ID and length, valid low8 CRC |
| ID104 | `0xBE00A` | Empty header `0xFFFFFFFF` |
| ID110 | `0xBE014` | Empty header `0xFFFFFFFF` |
| ID111 | `0xBE01E` | Empty header `0xFFFFFFFF` |

Initialisation skips repair for valid or empty records. None of the four
therefore activates repair branch `0x0201FEE4..0x0201FF04` on the examined
backup. That branch attempts an erase through `0x0201FE92` and
`0x02002B80`, also subject to the address check described above.
The third backend, which reads cfg_tool and the BTIF+512 table, instead has a
null write pointer in its table; the backup's zero-length BTIF+512 fallback
is rejected at `0x0201FB26`.

No format mismatch requiring BTIF erasure at candidate startup was found with
these data. Normal runtime use of the application's own configuration or
bonding records must be distinguished from an improper write into another
partition. The installer's `preserved_regions` attests preservation during
installation, before app boot; it does not promise that all runtime data remain
immutable throughout the application's lifetime.

## Repeatable verification without building or hardware

25 fragments were compared, including the dispatcher, journal, guard, VM,
boot parser, and tables. All match original G, with only the intended VM-constant
replacement in these ranges. JLFS headers/CRCs, the four BTIF records,
18 allowed preset sectors, and six out-of-area requests rejected by the
arithmetic bounds model were also checked. The model is not ISA execution.

The following PowerShell command repeats the comparisons; it reads only the
declared local artifacts and does not display unit payloads:

```powershell
@'
from pathlib import Path
import hashlib, struct
from hyperrig.jieli import crc16, unpack_app
from tools.audit_mini_ultrarig_port import VM_PATCH

def load(path, digest):
    data = Path(path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, path
    return data

image = load('build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin',
    '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff')
original = load('artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin',
    '2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059')
backup = load('artifacts/my-mini-flash/20261115-paced-resume/flash-a.bin',
    '72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180')
candidate, entries, _ = unpack_app(image)
expected, _, _ = unpack_app(original)
expected = bytearray(expected)
at = VM_PATCH.address - 0x02000000
assert expected[at:at+8] == VM_PATCH.before
expected[at:at+8] = VM_PATCH.after
spans = [(0x026BA,0x026D6),(0x02D9E,0x02E08),(0x02F16,0x02FF6),
 (0x03040,0x031BE),(0x031D4,0x03388),(0x0777A,0x07966),
 (0x0A312,0x0A37E),(0x0B834,0x0C28C),(0x20100,0x20354),
 (0x20376,0x20450),(0x20664,0x20750),(0x20A5A,0x20C50),
 (0x221E4,0x2225E),(0x017F6,0x0182E),(0x01776,0x017F6),
 (0x02994,0x029B0),(0x02B80,0x02BCC),(0x1FAAA,0x1FB6C),
 (0x1FD6C,0x200EA),(0x33B40,0x33B54),(0x3660C,0x3661E),
 (0x558F4,0x55948),(0x02EF2,0x02F16),(0x1F2BA,0x1F2DA),
 (0x35F74,0x35F8C)]
for begin, end in spans:
    assert candidate[begin:end] == expected[begin:end], hex(begin)
geometry = {e.name:(e.offset,e.size) for e in entries
            if e.name in ('VM','BTIF','USR')}
assert geometry == {'VM':(0x82000,0x3C000),'BTIF':(0xBE000,0x1000),
                    'USR':(0xBF000,0x40000)}
for i, record_id in enumerate((102,104,110,111)):
    at = 0xBE000 + 10*i
    header = struct.unpack_from('<I', backup, at)[0]
    assert header == 0xFFFFFFFF or (header >> 20 == 6 and
        ((header >> 8) & 4095) == record_id and
        (crc16(backup[at+4:at+10]) & 255) == (header & 255))
def permitted(base, length):
    return base >= 0xBF000 and length <= 0x40000 and base+length <= 0xFF000
sectors = [0xBF000+i*4096 for i in range(16)] + [0xDD000,0xDE000]
assert all(permitted(base,4096) for base in sectors)
for base, length in [(0x82000,4096),(0x84000,4096),(0xB7000,4096),
                     (0xBCF00,80),(0xBE000,4096),(0xFF000,1)]:
    assert not permitted(base,length)
assert int.from_bytes(b'usb_update_mode\0'[12:14],'little') == 0x646F
print('PASS: 25 fragments, geometry, BTIF, bounds and marker; offline only')
'@ | python -B -X utf8 -
```

Valid addresses, command success, and persistence after reload are different
forms of evidence. The application cycle prepared in
[MINI_APP_MUTATION.md](MINI_APP_MUTATION.md) must still verify saving, reloading,
scenes, and restoration on running G firmware. No result from this review
alone enables a USB or BLE capability.
