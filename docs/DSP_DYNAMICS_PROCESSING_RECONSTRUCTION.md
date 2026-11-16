# Dynamics sample processing reconstruction

This milestone reconstructs the complete fixed-block dynamics sample processor,
its state reset and clone, and both direct callers. The existing recovered
configuration and startup bodies now feed these original sample instructions and
their meter updates on carried state. This is an offline instruction comparison;
it is not a hardware, audio, timing or complete audio-task validation.

The input remains the pinned UltraRig M5.71 application, SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The decoded application must equal the unpacked original before any comparison.
The original artifacts, existing reconstruction modules and earlier evidence are
unchanged. The new C is a reconstruction, not recovered original source.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
See [the retained license](../third_party/ultrarig/LICENSE.md).

## Complete native scope

| Entry | Start | End, exclusive | Bytes | Instructions |
| --- | --- | --- | ---: | ---: |
| First-bank reset | `0x01c11b00` | `0x01c11bfa` | 250 | 67 |
| First-bank caller | `0x01c11bfa` | `0x01c11c66` | 108 | 32 |
| Clone first bank to second | `0x01c11c66` | `0x01c11c7e` | 24 | 6 |
| Conditional first-bank and unconditional second-bank caller | `0x01c11c7e` | `0x01c11d06` | 136 | 39 |
| Fixed-block numerical processor | `0x01c1a636` | `0x01c1ab40` | 1,290 | 371 |

The clone executes the complete existing word-copy dependency
`0x01c1a14c..0x01c1a182`, 54 bytes and 24 instructions, with its actual argument
of 61 words. It is recorded separately as a reused dependency. The numerical
processor has no callees. All 515 instructions in the five new bodies are
exercised by the C/original comparisons.

| Entry | Original-region SHA-256 |
| --- | --- |
| Reset | `06aaab535d1f536ff21824e9b3387a1fca0b5360d597d204ea8e9f75bd2b70c6` |
| First-bank caller | `73cedf03d263f328f97b5fea8f1ffcae573dd4315e11b0d79b040a6b3b9cf7ae` |
| Clone | `1b66a13ca85daccd2893198ce0e0aed748bc36cc27cfe40810bbb9514e49b2a2` |
| Second-bank caller | `f6d24221858055fad8aaaa416652a5b5b0ee1541b88ccdc90e69e8dfb6df03c6` |
| Numerical processor | `21884e5a6804c58ac57b96dbbdbca03cf3ca14dd337ae8e209dca13b7ecbe4e7` |
| Reused word copy | `eaaa450e908ade4708dd2b43a50e0aa0de48351a19d37080dfa7ae8ef525e4eb` |

## Memory and borrowed interface

The new [header](../firmware/include/hyperrig/hyperrig_dsp_dynamics_processing.h)
exposes direct borrowed pointers to the existing 68-byte configuration and
640-byte control regions, plus a 500-byte state region at `0x01c1f820`.
The first state occupies 244 bytes; the second starts 256 bytes later at
`0x01c1f920`. The twelve intervening bytes are preserved. The API does not copy
shared runtime state into a hidden object, which permits the enclosing task to
provide views of its original-address memory directly.

Each 244-byte state contains:

| Offset | Bytes | Meaning established by instructions |
| ---: | ---: | --- |
| 0 | 192 | 48 retained sample words |
| 192 | 32 | Eight gain words indexed modulo eight |
| 224 | 4 | Current gain word |
| 228 | 4 | Wrapping group counter |
| 232 | 4 | Nonzero selects the full processing path |
| 236 | 4 | Number of samples handled by gain multiplication this call |
| 240 | 4 | Signed minimum of gain endpoints this call |

The working buffer is exactly 176 signed words, or 704 bytes. The caller places
128 input words at indices 48 through 175. The processor overwrites indices 0
through 47 with retained history, produces 128 output words at indices 0 through
127, and retains input indices 128 through 175 as the next 48 history words.
Those final 48 working words are not modified. This is a sample-layout fact;
no physical latency or sample rate is inferred.

The API admits every raw integer state, sample, threshold and release word.
The original callers also admit every scale bit pattern in this reconstruction.
Division by zero returns zero according to the pinned ISA semantics; it is not
evaluated as undefined C division. The enclosing audio-task call sites supply a
scale of at least 256, which is a subset of the tested domain. Pointers, sizes
and buffer disjointness remain explicit caller contracts. New status returns
are 0 or -1 and do not claim a native return-register contract for void entries.

## Numerical and state behavior

The processor first copies history and initializes this call's affected count
to zero and minimum gain to `0x01000000`. If state word 232 is zero, it scans
all 128 inputs while retaining their last 48 words. If neither signed positive
peak nor unsigned negated negative peak exceeds the threshold, it advances the
counter by eight and returns. This shortcut preserves arbitrary existing gain
and ring words, even when they do not equal unity.

The full path handles eight groups of sixteen samples. Each group measures the
sixteen inputs 48 words ahead of the output being changed. A threshold crossing
computes the low word of `(uint64(threshold) << 24) / peak`, installs it in the
next gain slot and lowers the preceding three slots with signed minima. The
backward increments use the original multiply by 21845 and arithmetic shift by
16. The current gain approaches unity using the configured release word,
arithmetic shift by 20 and minimum increment one. A signed minimum with the
selected ring entry supplies the target.

The comparisons deliberately preserve details that an idealized limiter could
change:

- Negating `INT_MIN` produces unsigned magnitude `0x80000000`, so its peak is
  not lost or clamped to `INT_MAX`.
- The release gate compares current gain to unity as unsigned; later minima
  compare signed words.
- The multiplication shortcut is literally `(current & target) == 0x01000000`,
  not a pair of equality tests.
- The wrapped target-minus-current difference is arithmetically shifted by
  four. Each sample uses the current gain before the gain increment.
- Signed 32-by-32 products are arithmetically shifted by 24 and only their low
  word is retained. There is no added clipping or rounding.
- Gain, counters, deltas and meter accumulation retain native 32-bit wrapping.

The original reset clears only first-bank history, sets its eight slots and
current gain to unity, and clears its index and active words. It preserves the
first bank's two meter words, the gap and the whole second bank. The clone then
copies all 244 first-bank bytes, including those preserved meter words.

## Configuration, callers and meters

The first-bank caller caches its scale at control offset 108. On a cache miss,
it divides the unsigned configured threshold shifted left by sixteen by scale,
then inspects only the low quotient word. A nonzero high byte of that low word
selects `0x07fffff8`; otherwise the low word shifted left by three is cached at
control offset 116. A cache hit preserves and uses the existing cached threshold.
The processor receives that word and the configured release word at
configuration offset 56.

After a first-bank call, a nonzero affected count is added to control offset
112. Configuration offset 60 receives the signed minimum of its previous value
and the bank's minimum gain. The second caller runs the first bank only on a
scale change, then always runs the second bank on the same working buffer.
The second bank does not update the shared meters. The original meter getter
returns the accumulated count and optionally resets only the shared minimum
word when that output is requested.

Integration cases execute the original guarded startup and mathematical
configuration bodies, then reset, clone, repeated single/dual calls and meter
reads on carried memory. They compare all twelve runtime regions, all 176
working words and all optional outputs. The sequence is explicit in the
verifier; the enclosing native audio task is not claimed as executed here.
The optional parameter-notification body at `0x0201a9ea` remains a separate
capture-gain dependency outside this module.

## Independent execution and provenance

The new instruction model subclasses the unchanged audio-path model, loads
the five complete bodies and word-copy dependency, and executes original
instructions for every numerical operation. There are no scripted numerical,
configuration, copy or startup services. It adds signed maximum, register XOR
and positive bounded REP execution. REP uses original byte-sized body boundaries
and counts its register down to zero, retaining the pinned ISA's documented
semantics. Unknown instructions, escaping memory and unbalanced frames fail.

The source manifest comes from maintained source lists, independent of earlier
ignored build reports. MINI validation requires the reviewed v4 image SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
All 36 loaded code regions, both coefficient tables, dynamics reset-copy bytes
and the inherited static audio-caller windows are compared locally against the
original. This binds the compared implementation to that image; it does not
establish hardware operation.

Run the standalone builder with a new directory:

```text
python tools/build_dsp_dynamics_processing.py --output build/reverse-dsp-dynamics-processing-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder creates a UBSan host library, seven freestanding pi32v2 r3 objects,
an exact-allocation ASan/UBSan harness, focused native instruction tests, and the
C/original comparison report. All generated artifacts stay outside Git.

## Recorded validation

Final evidence is `build/reverse-dsp-dynamics-processing-02`. The partial
`-01` directory is preserved. All 515 new instructions are visited; combined
loaded coverage is 1,079 of 1,800 instructions. Unvisited instructions are in
reused regions, not omitted instructions in the five new bodies.

| Evidence | Result |
| --- | ---: |
| C/original comparisons | 756 |
| Reset / clone / kernel comparisons | 16 / 16 / 414 |
| Single / dual caller comparisons | 129 / 129 |
| Configure / getter / meter / startup comparisons | 4 / 4 / 40 / 4 |
| Actual dynamics numerical calls | 694 |
| Actual 61-word copies | 16 |
| Complete mathematical coefficient-producer calls | 16 |
| Working sample words checked | 118,272 |
| Carried calls | 248 |
| Maximum instruction packets per compared entry | 4,078 |
| Focused tests / invalid-API checks | 16 / 21 |
| Exact-allocation ASan/UBSan cases | 324 |
| Source hashes / generated artifact hashes audited | 59 / 11 |

All seven target objects compile without warnings. The six reused target
objects are byte-identical to audio-path build `-01`, whose source and artifact
hashes remain unchanged. The new target object is 2,244 bytes.

An independent source review compared the complete kernel and callers against
the original instructions, including the raw integer domain, delayed history,
gain skip condition, reset preservation and dual-bank meter ordering. It found
no concrete mismatch. That review did not repeat the test suite or access hardware.

| Output | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_dsp_dynamics_processing.c` | `6862930a484b89fcb4a03403585cb7a83ead4cb794b74c9de9d125cf5655c0b9` |
| `verification.json` | `c9983b720c585734751b1abeec773975de8d5f8e83b8f696a974cc9828462e89` |
| `hyperrig_dsp_dynamics_processing.pi32v2.o` | `0dd29292e62b1c0a09daecfe0432ff170823e387fa5325b29a4fa29d4c72ef8c` |
| `sanitizers.json` | `84d1328c3c7d47ea5080f1545a7b8c5d9dfe7be0cfda843b498dd5e1a150595f` |
| `build-manifest.json` | `15a614415eafd655ab9346ec5e8ebc75635fd8b5d8880ec65caa3fb2ab2d7f0b` |

The deterministic compared output/state stream has SHA-256
`6b6966a44c582398e0a18eace1d453cb970f39fc0aa9c858d9a4b914a05f1e37`.
