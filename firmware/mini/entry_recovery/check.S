/* MINI evidence: PA10/PA0/PA3 inputs, active low; PORTA 0x50000.
 * Only input direction, digital input, pull-up and pull-down are touched.
 * Delay counts are instruction counts, not measured milliseconds.
 * Caller owns these GPIO bits and provides an ordinary word-aligned stack.
 * This is a callable component, not a ROM USB plugin entry point. */
.section .text.hyperrig_mini_entry_recovery_check,"ax",@progbits
.global hyperrig_mini_entry_recovery_check
.type hyperrig_mini_entry_recovery_check,@function
hyperrig_mini_entry_recovery_check:
    [--sp] = {r9-r4}
    r4 = 0x00050000
    r5 = 0x00000409
    r6 = [r4+8]
    r7 = [r4+12]
    r8 = [r4+16]
    r9 = [r4+20]
    r6 &= r5
    r7 &= r5
    r8 &= r5
    r9 &= r5
    /* A restore must never turn a selected line back into a driven output.
     * The inherited state must already be input; otherwise report an error
     * before any GPIO write. Cold SPL entry still needs qualification. */
    if (r6 != r5) goto .Lbad_initial_direction

    /* Input direction first: never drive a pressed switch from this code. */
    r0 = [r4+8]
    r0 |= r5
    [r4+8] = r0
    r0 = [r4+12]
    r0 |= r5
    [r4+12] = r0
    r2 = ~r5
    r0 = [r4+20]
    r0 &= r2
    [r4+20] = r0
    r0 = [r4+16]
    r0 |= r5
    [r4+16] = r0
    csync

    r1 = 2
    r0 = [r4+8]
    r0 &= r5
    if (r0 != r5) goto .Lrestore
    r0 = [r4+12]
    r0 &= r5
    if (r0 != r5) goto .Lrestore
    r0 = [r4+16]
    r0 &= r5
    if (r0 != r5) goto .Lrestore
    r0 = [r4+20]
    r0 &= r5
    if (r0 != 0) goto .Lrestore

    r2 = 100000
.Lsettle:
    nop
    r2 += -1
    if (r2 != 0) goto .Lsettle

    r3 = 32
    r1 = 0
.Lsample:
    r0 = [r4+4]
    r0 &= r5
    if (r0 != 0) goto .Lrestore
    r2 = 100000
.Lhold:
    nop
    r2 += -1
    if (r2 != 0) goto .Lhold
    r3 += -1
    if (r3 != 0) goto .Lsample
    r1 = 1

.Lrestore:
    /* Restore only these three bits, preserving current unrelated bits.
     * Restore direction last. OUT, DIEH, drive strength and mux are untouched. */
    r2 = ~r5
    r0 = [r4+20]
    r0 &= r2
    r0 |= r9
    [r4+20] = r0
    r0 = [r4+16]
    r0 &= r2
    r0 |= r8
    [r4+16] = r0
    r0 = [r4+12]
    r0 &= r2
    r0 |= r7
    [r4+12] = r0
    r0 = [r4+8]
    r0 &= r2
    r0 |= r6
    [r4+8] = r0
    csync
    r0 = r1
    {r9-r4} = [sp++]
    rts
.Lbad_initial_direction:
    r0 = 2
    {r9-r4} = [sp++]
    rts
.size hyperrig_mini_entry_recovery_check, .-hyperrig_mini_entry_recovery_check
