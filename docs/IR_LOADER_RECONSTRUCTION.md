# Reconstructed IR loading and ownership

The subsequent [IR installation reconstruction](IR_INSTALLATION_RECONSTRUCTION.md)
executes direct/deferred installation, gain/trimming, length selection and the
stored-read callback through these ownership paths. The evidence below remains
the earlier loader milestone; full convolution construction is still separate.

Five original functions now have portable C reconstructions covering IR reuse,
record reading/CRC checks, buffer attachment, pending-slot refresh and ownership
queries. They execute the previous [asset-header and descriptor helpers](PRESET_ASSETS_RECONSTRUCTION.md)
and [record/CRC and selection dependencies](PRESET_STORAGE_RECONSTRUCTION.md).
Allocation, freeing, DSP installation, effect refresh, locking and physical reads
remain explicit services. No IR convolution or complete preset application is
claimed by this component.

Sources: [`hyperrig_ir_loader.c`](../firmware/src/hyperrig_ir_loader.c) and
[`hyperrig_ir_loader.h`](../firmware/include/hyperrig/hyperrig_ir_loader.h).
The original Required Notice and license are retained. Earlier sources, reports,
original inputs and firmware images remain unchanged.

## Pinned functions

The original G v2 M5.71 application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x02008972..0x020089c4` | Install and transfer buffer ownership | `30cadae9cbfc0d8215f1994e722a28dcb6baab1c087acd5beffdcb5ff03c8ac5` |
| `0x020089c4..0x020089da` | Pending-slot query | `d8297c0e892a91701659099a04f98487622eab37e5e1cba21c77805fb67ee972` |
| `0x020089da..0x020089f2` | Size/metadata/handle query | `e99734e4532060a7162e977f02900ab768560918985b9a1deb1d3e428dd7ceb3` |
| `0x020089f2..0x02008a62` | Refresh through slot/identity service | `7045ae78e424a5169c604d85f1ae1ba7053800f52f9941ede6dddd25226edb18` |
| `0x02008a62..0x02008c28` | IR reuse and replacement loader | `94198f114567001d7cc469dfd3209dbc43d95f82de5291ea0a0990e619eb061a` |

All five regions and twenty-five asset/storage/selection dependency regions
match the reviewed MINI v4 image byte-for-byte. Its SHA256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This is an image binding, not target execution.

## Loader sequence

The loader calls the priority service with one, then probes the J/I header with
maximum payload length 8152. Header rejection restores priority with zero and
returns **-1**, without allocation, activity or notification calls.

Reuse is accepted when the current IR byte at global offset 10 equals the full
slot argument, or when the descriptor at state offset 1796 matches the header
identity, length, metadata and format. This path restores priority, writes the
selected slot byte, identity at state word 744 and descriptor, sets global byte
19 to 255, emits `notify(20, slot | 0x600, 0)`, and returns zero. It does not
allocate, install a payload or invoke the requested post-load refresh.

Replacement proceeds as follows:

1. Allocate the initially accepted length. A zero handle restores priority and
   returns **-100**; activity has not started.
2. Set activity to six. Re-read the selected format's header, then its payload,
   and calculate/compare CRC using the original record/CRC instruction bodies.
   Address arithmetic preserves uint32 wrapping. CRC processing polls between
   256-byte chunks, including when the IR exceeds the older 1490-byte preset API.
3. Restore priority. A record failure frees the new handle, emits
   `notify(20, slot | 0x100, error)`, sets activity to zero and returns the record
   error: **-1** header rejection, **-2** payload read failure, or **-3** CRC mismatch.
   Partial payload writes remain in the modeled allocation.
4. On record success, emit `notify(20, slot | 0x100, 0)` and attach the new buffer
   with a count of `length >> 1`, header word 12 and the probed format. Odd lengths
   are not rejected here; division by two alone does not establish a complete
   sample-format contract.
5. Lock, read each chain's effect order into a local snapshot, and examine its
   effect slots. Present effects of type seven call the ownership predicate;
   those returning zero receive the effect-refresh call. Duplicates are retained.
   Unlock after both chains.
6. Commit the slot byte, state word 744 and descriptor, with global byte 19 set
   to 255. If requested, run pending-slot refresh. Set activity to zero and return
   zero.

The install callback's result and effect-refresh callback results are not tested
by these callers. A successful loader return therefore establishes completion
of this orchestration, not successful live audio processing. Callback changes to
mapped state are observed at subsequent original read points; they are not rolled
back on failure. Physical persistence is not part of this path.

## Ownership fields and attachment

The following offsets are relative to original state base `0x01c26890`:

| Offset | Observed role |
| --- | --- |
| 152 | Count supplied to the install service |
| 156 | Header metadata supplied to the install service |
| 160 | Presence byte |
| 164 | Live buffer handle/pointer word |
| 168 | Boolean nonzero-format word |
| 172 | Pending slot plus one, or zero after attachment |
| 176 | Identity retained after slot refresh |
| 744 | Current IR identity |
| 1796..1811 | Present/format/identity/length/metadata descriptor |

Attachment captures the previous handle before calling lock, install and unlock.
Only afterward does it commit the new handle, count, metadata, presence, boolean
format and zero pending slot. It then frees the captured previous handle if it
was nonzero and differs from the new handle. It never re-reads that previous
handle after a callback. The multi-register store at `0x020089a0` uses ascending
register order without changing its base, as documented in the pinned ISA's
`stm.post1` entry and hardware evidence.

The pending query returns word 172 only when presence is nonzero and the live
handle is zero. The other query writes count and metadata and returns the live
handle only when presence is nonzero.

## Pending-slot refresh

Refresh captures global slot byte 10 and unconditionally writes callback identifier
`0x0201ad4c` to original word `0x01c3441c`, including on early exits. It exits for
slot 255, an existing nonzero pending slot, or absence of a present live handle.

Otherwise it captures identity word 744, calls lock, then
`install_slot(slot + 1, identity)`, then unlock. A nonzero install-slot result
leaves ownership fields unchanged by this caller. On zero, it re-reads and frees
the current live handle, clears that word, and writes the captured slot plus one
and identity to words 172/176. This re-read differs from attachment's captured
old handle. The callback identifier's implementation remains external.

## Portable API and limits

`hyperrig_ir_runtime` embeds the unchanged storage/selection runtime and adds the
four-byte callback word. Service calls carry four uint32 arguments. Original
pointer words are opaque tokens, never native host pointers. A caller-owned
buffer supplies the new allocation's bytes; its backing must remain alive after
ownership transfer. The instruction verifier maps one fresh allocation at
`0x32000000`; other saved handles are opaque service arguments.

The C loader requires a backing capacity of at least 8152, nonoverlapping buffers,
valid callbacks and chain counts at most ten. Invalid API calls return the new
status **-200** before side effects. Pure queries and original void helpers expose
new status returns; incidental original register returns are not semantic results.

The first header determines the allocation request, but record reading fetches a
second header. The equivalence domain requires later payload lengths to remain
within that original request and the backing capacity. The C implementation adds
**-201** when a later length exceeds either bound, before reading/checking bytes
outside it. Prior calls remain; the error path restores priority, frees the new
handle, notifies and resets activity. This guard is new API behavior, not claimed
original protection. The instruction verifier rejects such executions as outside
its allocated-memory domain.

Read callbacks may leave a prefix on failure. Service callbacks may synchronously
mutate mapped runtime within the stated bounds. Re-entry, concurrent mutation,
retained read pointers and changes to private stack/header storage are excluded.
The allocator, free, lock, install, effect services and physical read wrapper are
scripted boundaries; their internal allocation, synchronization and DSP behavior
have not been reconstructed here.

## Verification

The completed run passed **541 C-versus-instruction comparisons**:

| Operation | Comparisons |
| --- | ---: |
| Pending query / metadata query | 48 / 48 |
| Attach | 40 |
| Refresh | 204 |
| Full load/reuse/failure paths | 201 |

Comparisons check semantic results, all prior mapped state, the callback word,
all 8152 allocation bytes, and ordered read/service arguments with state at each
boundary. Private header/stack bytes are not compared as persistent state.
The corpus includes both formats, zero/odd/maximum payload sizes, CRC and partial
read failures, duplicate effect slots, allocator failure, reuse, callback results
and **46 mutating-service cases** within the total.

All **229 new instructions** were visited. The run visited **377 of 1,321 combined
instructions**; prior reports retain their own coverage. Fourteen focused
instruction tests, 17 invalid-API checks and one C allocation-growth guard check
passed. The host library builds with warnings as errors and UBSan. All six
dependency objects compile for pi32v2 r3; the new object is **3,112 bytes**,
which is not linked firmware size, RAM usage or a latency measurement.
No hardware/audio/durable-write test was performed.

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_ir_loader.py --output build/reverse-ir-loader-new
```

Optionally pass `--mini-image` with the reviewed MINI v4 application inside the
workspace. The builder refuses an existing directory. The completed local run
is `build/reverse-ir-loader-02`, containing the host library, six target objects,
source-hashed verification report and artifact manifest. Generated files remain
outside Git.

## Next boundary: capture loading

Capture loader `0x020087cc..0x02008972`, SHA256
`dacef25e4d770e3071c0c3b4db040a08ef17124838de91904f2489908ab965cb`,
has been traced statically but is not executed by this component. It uses the
capture header/extended-identity helpers, a descriptor at state 1780, preparation
and fallback helpers, and installation through `0x02008586` with callback
`0x0201acd8`. Its rollback restores words at state 696/700/704 and clears descriptor
presence on an installation error. Recover those preparation/installation contracts
next, before connecting both loaders to complete preset application.

The parallel [five-section DSP chain](BIQUAD_CHAIN_RECONSTRUCTION.md) now executes
its two filter variants internally. Coefficient generation and IR convolution
remain separate numerical components on the [roadmap](REVERSE_ROADMAP.md).

The subsequent [capture loader milestone](CAPTURE_LOADER_RECONSTRUCTION.md) now
executes the capture caller, gain metadata and signature helpers. Installation
through `0x02008586` and the metadata journal remain external. The IR results
above retain their original scope and evidence.
