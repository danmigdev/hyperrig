; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 3 functions, 0x0201b4bc..0x0201b60a

; phase3_p13_iic_ioctl: 0x0201b4bc..0x0201b5b4, module phase3-p13 (iic_ioctl)
.type phase3_p13_iic_ioctl,@function
phase3_p13_iic_ioctl:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = r2
    r3 = 0
    r2 = 2147399419
    r2 += r1  #  ; @add.rr.p
    [sp] = r3
    if (r2 <= 4) goto L0201b502
    r3 = r1 - 0x4900
    r2 = -22
    if (r3 > 11) goto L0201b516
    r1 = L01c25434
    tbb [r3]
phase3_p13_case_table_0201b4e4:
    .byte (L0201b4f0 - phase3_p13_case_table_0201b4e4) / 2, (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2, (L0201b532 - phase3_p13_case_table_0201b4e4) / 2, (L0201b53a - phase3_p13_case_table_0201b4e4) / 2, (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2, (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2, (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2, (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2
    .byte (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2, (L0201b5ae - phase3_p13_case_table_0201b4e4) / 2, (L0201b544 - phase3_p13_case_table_0201b4e4) / 2, (L0201b548 - phase3_p13_case_table_0201b4e4) / 2
L0201b4f0:
    r0 = [r0+12]
    r0 = [r0+20]
    r1 = h[r0+0] (u)
    r1 &= 4294967287
    h[r0+0] = r1
    r1 = h[r0+0] (u)
    r1 |= 32
    h[r0+0] = r1
    goto L0201b5ac
L0201b502:
    tbb [r2]
phase3_p13_case_table_0201b504:
    .byte (L0201b50a - phase3_p13_case_table_0201b504) / 2, (L0201b54e - phase3_p13_case_table_0201b504) / 2, (L0201b55a - phase3_p13_case_table_0201b504) / 2, (L0201b50a - phase3_p13_case_table_0201b504) / 2, (L0201b58a - phase3_p13_case_table_0201b504) / 2
    .byte 0x00  ; alignment
L0201b50a:
    r0 = [r0+12]
    r1 = sp + 0
    call L0201b330
    if (r4 != 0) goto L0201b594
    goto L0201b5ac
L0201b516:
    r3 = 1073826052
    if (r1 == r3) goto L0201b598
    r3 += -3
    if (r1 == r3) goto L0201b5a2
    if (r1 != 4) goto L0201b5ae
    r0 = [r0+12]
    r0 = [r0+20]
    b[r0+8] = r4
    goto L0201b5ac
L0201b532:
    r0 = [r0+12]
    call L0201b362
    goto L0201b5ac
L0201b53a:
    r1 = r4.b0 (u)  #
    r0 = [r0+12]
    call L0201b42c
    goto L0201b5aa
L0201b544:
    r0 = 1
    goto L0201b54a
L0201b548:
    r0 = 0
L0201b54a:
    b[r1+0] = r0
    goto L0201b5ac
L0201b54e:
    r0 = [r0+12]
    r1 = sp + 0
    call L0201b384
    if (r4 != 0) goto L0201b594
    goto L0201b5ac
L0201b55a:
    r5 = [r0+12]
    r0 = [r5+20]
    r1 = h[r0+0] (u)
    r1 |= 8
    h[r0+0] = r1
    r1 = h[r0+0] (u)
    r1 |= 64
    h[r0+0] = r1
    r1 = 255
    b[r0+4] = r1
    csync
    nop
    r0 = [r5+20]
    r1 = h[r0+0] (u)
    r1 |= 4
    r0 = r5  #
    h[r0+0] = r1
    call L0201b2ce
    [sp] = r0
    r0 = [r5+20]
    r0 = b[r0+4] (u)
    if (r4 != 0) goto L0201b594
    goto L0201b5ac
L0201b58a:
    r0 = [r0+12]
    r1 = sp + 0
    call L0201b2f8
    if (r4 == 0) goto L0201b5ac
L0201b594:
    b[r4+0] = r0
    goto L0201b5ac
L0201b598:
    r1 = r4.b0 (u)  #
    r0 = [r0+12]
    call L0201b44a
    goto L0201b5aa
L0201b5a2:
    r1 = r4.b0 (u)  #
    r0 = [r0+12]
    call L0201b408
L0201b5aa:
    [sp] = r0
L0201b5ac:
    r2 = [sp]
L0201b5ae:
    r0 = r2
    sp += 4
    {pc, r5, r4} = [sp++]

; phase3_p13_iic_close: 0x0201b5b4..0x0201b606, module phase3-p13 (iic_close)
.type phase3_p13_iic_close,@function
phase3_p13_iic_close:
    [--sp] = {rets, r4}
    r4 = [r0+12]
    r0 = r4
    call L0201b18a
    r4 = r0  #
    r1 = [r4+20]
    r0 = 0
    h[r1+0] = r0
    r0 = b[r4+0] (u)
    call L02004ad6
    r0 = b[r4+0] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r4+0] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = b[r4+0] (u)
    r1 = 0
    call phase3_p5_gpio_set_die
    r0 = b[r4+1] (u)
    call L02004ad6
    r0 = b[r4+1] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_down
    r0 = b[r4+1] (u)
    r1 = 0
    call phase3_p5_gpio_set_pull_up
    r0 = b[r4+1] (u)
    r1 = 0
    call phase3_p5_gpio_set_die
    r0 = 0
    {pc, r4} = [sp++]

; phase3_p13_adc_scan_idle_query: 0x0201b606..0x0201b60a, module phase3-p13 (adc_scan_idle_query)
.type phase3_p13_adc_scan_idle_query,@function
phase3_p13_adc_scan_idle_query:
    r0 = 1
    rts
