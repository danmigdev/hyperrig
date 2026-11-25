; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_journal: 1 function, 0x0200a622..0x0200a72e

; capture_journal_rewrite: 0x0200a622..0x0200a72e, module capture-journal (rewrite)
.type capture_journal_rewrite,@function
capture_journal_rewrite:
    [--sp] = {rets, r15-r4}
    sp += -40
    r8 = r3
    r9 = r2
    r6 = r1
    r15 = r0
    r7 = 1
    r0 = 1
    if (r15 >= 782336) {
    r0 = 0
    }
    r2 = r6 + r15
    r1 = 1
    if (r2 <= 1044480) {
    r1 = 0
    }
    r12 = r0 | r1
    r0 = r6 | r15
    r1 = 4095
    if ((r0 & r1) == 0) {
    r7 = 0
    }
    r11 = [sp+92]  ; @ld.w.sp.l
    r0 = r11 + 4135
    r5 = r0 >> 12
    r4 = r5 << 12
    r14 = -1
    call storage_platform_clock  ; @call.xl
    r10 = r0
    if (r4 > r6) goto L0200a686
    r0 = r7 | r12
    if (r0 != 0) goto L0200a686
    call storage_coordination_wait_ready
    r0 = r15
    r1 = r5
    call capture_journal_erase
    if (r0 == 0) goto L0200a6a2
L0200a686:
    r0 = r10
    call preset_loader_elapsed
    r2 = uextra(r14, p:0, l:8)
    r2 <= insert(r0, p:8, l:24)
    r0 = 18
    r1 = r15
    call storage_coordination_notify
    r0 = r14
    sp += 40
    {pc, r15-r4} = [sp++]
L0200a6a2:
    if (r11 == 0) goto L0200a6b8
    r0 = r15 + 40
    r1 = r8
    r2 = r11
    call capture_journal_write
    r14 = -3
    if (r0 != 0) goto L0200a686
L0200a6b8:
    r2 = 40
    r0 = r15
    r1 = r9
    call capture_journal_write
    r14 = -3
    if (r0 != 0) goto L0200a686
    r0 = sp + 0
    r2 = 40
    r1 = r15
    call storage_control_raw_read
    ifs (r0 < 0) goto L0200a686
    r0 = sp + 0
    r2 = 40
    r1 = r9
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0200a686
    r12 = r15 + 40
    r9 = L01c24420
    r6 = r11
    r5 = 0
L0200a6f2:
    if (r5 >= r11) goto L0200a72a
    r1 = r12 + r5
    r13 = r6
    if (r6 >= 256) {  ; @if.ge.ri.s12
    r13 = 256
    }
    r0 = r9
    r2 = r13
    call storage_control_raw_read
    ifs (r0 < 0) goto L0200a686
    r1 = r8 + r5
    r0 = r9
    r2 = r13
    call capture_journal_compare  ; @call.xl
    r6 = r6 + -256
    r5 = r5 + 256
    if (r0 == 0) goto L0200a6f2
    goto L0200a686
L0200a72a:
    r14 = 0
    goto L0200a686
