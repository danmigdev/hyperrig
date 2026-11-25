; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage_preparation: 3 functions, 0x020077aa..0x02007976

; preset_storage_preparation_record_copy: 0x020077aa..0x020077ec, module preset-storage-preparation (record_copy)
.type preset_storage_preparation_record_copy,@function
preset_storage_preparation_record_copy:
    [--sp] = {rets, r6-r4}
    sp += -40
    r5 = r1
    r6 = r0
    r1 = sp + 0
    r2 = 40
    call preset_storage_preparation_read_forward
    r4 = -2
    if (r0 != 0) goto L020077e6
    r0 = [sp]
    r1 = 1363626836
    r4 = 0
    if (r0 != r1) goto L020077e6
    r0 = [sp+4]
    if (r0 > 1880) goto L020077e6
    r4 = r0 + 40
    r0 = r6
    r1 = r5
    r2 = r4
    call preset_storage_preparation_read_forward
    if (r0 == 0) goto L020077e6
    r4 = -2
L020077e6:
    r0 = r4
    sp += 40
    {pc, r6-r4} = [sp++]

; preset_storage_preparation_preset_write: 0x020077ec..0x02007966, module preset-storage-preparation (preset_write)
; HyperRig MINI, product option: what is stored in place of the working preset, or a refusal before the flash is touched.
.type preset_storage_preparation_preset_write,@function
preset_storage_preparation_preset_write:
    [--sp] = {rets, r14-r4}
    sp += -4
    r9 = r3
    r4 = r2
    r5 = r1
.if MINI_PRODUCT
    r10 = r0
    if (r4 == 0) goto Lhr_payload_known
    r0 = r4
    call hyperrig_payload  ; @call.xl
    r4 = r0
    r7 = -90
    if (r4 == 0) goto L02007960
Lhr_payload_known:
    call preset_storage_preparation_prepare
.else
    r10 = r0
    call preset_storage_preparation_prepare
.endif
    r0 = 3840
    call L0203c15c  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L02007872
    call storage_platform_clock  ; @call.xl
    r8 = r0
    if (r5 == 0) goto L02007878
    if (r4 != 0) goto L02007878
    r7 = -1
    if (r10 > 31) goto L0200793c
    r0 = r10
    call preset_storage_address
    r4 = r0
    r0 = r10 ^ 0x1
    call preset_storage_address
    r7 = r0
    if (r4 == 0) goto L02007906
    r11 = r10 & 0x1
    r0 = 0x0 - r11
    r0 = r0 & 0x780
    r9 = r6 + r0
    r0 = r4
    r1 = r9
    call preset_storage_preparation_record_copy
    r4 = r0
    ifs (r4 <= 0) goto L02007908
    r0 = r5 + 16
    r1 = r11 ^ 0x1
    r2 = r9 + 16
    rep 24 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r0 = 0x0 - r1
    r0 = r0 & 0x780
    r5 = r6 + r0
    if (r7 == 0) goto L0200791c
    r0 = r7
    r1 = r5
    call preset_storage_preparation_record_copy
    r7 = r0
    ifs (r7 >= 0) goto L0200791e
    goto L0200793c
L02007872:
    r7 = -100
    goto L02007960
L02007878:
    r7 = -1
    if (r10 > 31) goto L0200793c
    if (r5 == 0) goto L02007896
    r0 = r9 + 40
    if (r0 > 1920) goto L0200793c
    r0 = [r5+0]
    r1 = 1363626836
    if (r0 != r1) goto L0200793c
L02007896:
    r14 = r10 & 0x1
    r0 = r14 ^ 0x1
    r0 = 0x0 - r0
    r0 = r0 & 0x780
    r11 = r6 + r0
    r0 = r10 ^ 0x1
    call preset_storage_address
    r13 = 0
    r7 = 0
    if (r0 == 0) goto L020078c4
    r1 = r11
    call preset_storage_preparation_record_copy
    r7 = r0
    ifs (r7 < 0) goto L0200793c
L020078c4:
    r0 = 0x0 - r14
    r0 = r0 & 0x780
    r12 = r6 + r0
    if (r5 == 0) goto L020078f4
    r2 = 40
    r0 = r12
    r1 = r5
    call effect_parameter_support_memmove  ; @call.xl
    if (r9 != 0) {  ; @if.ne.ri.s12
    r0 = r12 + 40
    r1 = r4
    r2 = r9
    call effect_parameter_support_memmove  ; @call.xl
    }
    r13 = r9 + 40
L020078f4:
    r0 = r10 >> 1
    if (r14 != 0) goto L02007910
    r1 = r12  #
    [sp] = r7
    r2 = r13
    r3 = r11
    goto L02007936
L02007906:
    r4 = 0
L02007908:
    if (r4 != 0) goto L0200790c
    r4 = -1
L0200790c:
    r7 = r4
    goto L0200793c
L02007910:
    [sp] = r13  ; @st.w.sp.l
    r1 = r11
    r2 = r7
    r3 = r12
    goto L02007936
L0200791c:
    r7 = 0
L0200791e:
    r0 = r10 >> 1
    if (r11 != 0) goto L0200792e
    r1 = r9  #
    [sp] = r7
    r3_r2 = r5_r4
    goto L02007936
L0200792e:
    r1 = r5  #
    [sp] = r4
    r2 = r7
    r3 = r9
L02007936:
    call preset_storage_preparation_replace_pair
    r7 = r0
L0200793c:
    r0 = r6
    call L0203d218  ; @call.xl
    r0 = r10
    call preset_storage_address
    r4 = r0
    r0 = r8
    call preset_loader_elapsed
    r2 = r7.b0 (u)
    r2 <= insert(r0, p:8, l:24)
    r0 = 18
    r1 = r4
    call storage_coordination_notify
L02007960:
    r0 = r7
    sp += 4
    {pc, r14-r4} = [sp++]

; preset_storage_preparation_invalidate: 0x02007966..0x02007976, module preset-storage-preparation (invalidate)
.type preset_storage_preparation_invalidate,@function
preset_storage_preparation_invalidate:
    if (r0 <= 31) {  ; @if.le.ri.s12
    r1 = L01c26b54
    [r1+0] &= ~(1 << r0)
    }
    rts
