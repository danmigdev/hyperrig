; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 3 functions, 0x02000604..0x02000730

; phase3_p3_debug_enter_critical: 0x02000604..0x02000616, module phase3-p3 (debug_enter_critical)
.type phase3_p3_debug_enter_critical,@function
phase3_p3_debug_enter_critical:
    r0 = 32432704
    r1 = [r0+0]
    if ((r1 & 0x1) == 0) {
    [r0+0] = 0xE7
    }
    rts

; phase3_p3_debug_exit_critical: 0x02000616..0x02000628, module phase3-p3 (debug_exit_critical)
.type phase3_p3_debug_exit_critical,@function
phase3_p3_debug_exit_critical:
    r0 = 32432704
    r1 = [r0+0]
    if ((r1 & 0x1) != 0) {
    [r0+0] = 0xE7
    }
    rts

; phase3_p3_debug_init: 0x02000628..0x02000730, module phase3-p3 (debug_init)
.type phase3_p3_debug_init,@function
phase3_p3_debug_init:
    [--sp] = {rets, r8-r4}
    r7 = cnum
    r2 = sdk_exception_irq_handler
    r0 = 1
    r1 = 7
    r3 = 255
    call storage_platform_register
    r0 = 0x13400
    [r0+0] = 0x6D
    r2 = L0201b164
    r0 = 28
    r1 = 7
    r3 = 0
    r4 = 0
    call storage_platform_register
    r5 = 32436432
    r0 = r7 << 9
    r2 = r5
    [++r2=r0] = r4
    r1 = r5 + -208
    r8 = r0 + r1
    call phase3_p3_debug_enter_critical
    r0 = r5 + -3720
    r6 = r0 + 4232
    if (r7 == 0) goto L020006c8
    r3 = -1
    r5 = r0 + 312  #
    [r0+0] = r3
; HyperRig MINI v4, patch mini_appended_flash_pc_limit: Extend the shared flash execution range through the exact appended app/guard end. Preserve the original RAM-copy source, RAM execution range and all debug enables.
.if TARGET_MINI
    r1 = hyperrig_mini_append_end  ; @li.u32
.else
    r1 = ultrarig_flash_text_end
.endif
    [r5+0] = r1
    r1 = ultrarig_flash_start
    [r5+4] = r1
    [r0+0] = r3
; HyperRig MINI, product option: the code that the product has in the RAM is after the application's own.
.if MINI_PRODUCT
    r0 = ultrarig_ram_code_end  ; @li.u32
.else
    r0 = L01c1f088
.endif
    [r5+8] = r0
    r0 = ultrarig_ram_start
    [r5+12] = r0
    call phase3_p3_debug_exit_critical
    [r6+0] &= 0xFFFFFFF7
    r0 = L01c363b8
    [r6+12] = r0
    r0 = L01c373b8
    [r6+8] = r0
    [r6+20] = r4
    [r6+16] = r3
    [r6+0] |= 0x8
    r0 = [r6+20]
    r0 = [r6+16]
    r0 = [r6+12]
    r0 = [r6+8]
    goto L02000722
L020006c8:
    r1 = 263224
    r1 = r1 + 6088  #
    [r1+0] = r4
    r7 = r0 + 248  #
    [r1+0] = r4
    [r7+4] = r4
    [r7+0] = r4
    [r7+8] = r4
    [r7+12] = r4
    [r7+16] = r4
    [r7+20] = r4
    [r7+24] = r4
    r3 = -1
    [r0+0] = r3
    [r5+4] = r3
    [r6+4] = r3
    call phase3_p3_debug_exit_critical
    call phase3_p3_debug_enter_critical
    [r7+0] |= 0x3F0000
    [r7+0] |= 0x30
    call phase3_p3_debug_exit_critical
    [r5+0] &= 0xFFFFFFF7
    r0 = L01c350b8
    [r5+12] = r0
    r0 = L01c360b8
    [r5+8] = r0
    [r5+20] = r4
    [r5+16] = r3
    [r5+0] |= 0x8
    r0 = [r5+20]
    r0 = [r5+16]
    r0 = [r5+12]
    r0 = [r5+8]
L02000722:
    [r2+0] |= 0x104
    r0 = r8 + 448
    [r0+0] |= 0x1
    {pc, r8-r4} = [sp++]
