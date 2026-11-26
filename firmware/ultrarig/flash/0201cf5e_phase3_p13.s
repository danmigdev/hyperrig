; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p13: 15 functions, 0x0201cf5e..0x0201d056

; phase3_p13_cxx_zero_a: 0x0201cf5e..0x0201cf62, module phase3-p13 (cxx_zero_a)
.type phase3_p13_cxx_zero_a,@function
phase3_p13_cxx_zero_a:
    r0 = 0
    rts

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; phase3_p13_cxx_zero_b: 0x0201cf62..0x0201cf66, module phase3-p13 (cxx_zero_b)
.type phase3_p13_cxx_zero_b,@function
phase3_p13_cxx_zero_b:
    r0 = 0
    rts

; phase3_p13_cxx_zero_c: 0x0201cf66..0x0201cf6a, module phase3-p13 (cxx_zero_c)
.type phase3_p13_cxx_zero_c,@function
phase3_p13_cxx_zero_c:
    r0 = 0
    rts

; phase3_p13_cxx_zero_d: 0x0201cf6a..0x0201cf6e, module phase3-p13 (cxx_zero_d)
.type phase3_p13_cxx_zero_d,@function
phase3_p13_cxx_zero_d:
    r0 = 0
    rts

; phase3_p13_cxx_zero_e: 0x0201cf6e..0x0201cf72, module phase3-p13 (cxx_zero_e)
.type phase3_p13_cxx_zero_e,@function
phase3_p13_cxx_zero_e:
    r0 = 0
    rts

; phase3_p13_cxx_zero_f: 0x0201cf72..0x0201cf76, module phase3-p13 (cxx_zero_f)
.type phase3_p13_cxx_zero_f,@function
phase3_p13_cxx_zero_f:
    r0 = 0
    rts

; phase3_p13_operator_new: 0x0201cf76..0x0201cf8c, module phase3-p13 (operator_new)
.type phase3_p13_operator_new,@function
phase3_p13_operator_new:
    [--sp] = rets
    r1 = r0
    r0 = 1
    if (r1 == 0) goto L0201cf80
    r0 = r1
L0201cf80:
    call L0203c15c  ; @call.xl
    if (r0 == 0) goto L0201cf8a
    pc = [sp++]
L0201cf8a:
    goto L0201cf8a

; phase3_p13_operator_new_array: 0x0201cf8c..0x0201cf92, module phase3-p13 (operator_new_array)
.type phase3_p13_operator_new_array,@function
phase3_p13_operator_new_array:
    [--sp] = rets
    call phase3_p13_operator_new
    pc = [sp++]

; phase3_p13_operator_delete: 0x0201cf92..0x0201cf9c, module phase3-p13 (operator_delete)
.type phase3_p13_operator_delete,@function
phase3_p13_operator_delete:
    [--sp] = rets
    call L0203d218  ; @call.xl
    pc = [sp++]

; phase3_p13_operator_delete_array: 0x0201cf9c..0x0201cfa2, module phase3-p13 (operator_delete_array)
.type phase3_p13_operator_delete_array,@function
phase3_p13_operator_delete_array:
    [--sp] = rets
    call phase3_p13_operator_delete
    pc = [sp++]
.endif

; phase3_p13_fseek: 0x0201cfa2..0x0201cff8, module phase3-p13 (fseek)
.type phase3_p13_fseek,@function
phase3_p13_fseek:
    [--sp] = {rets, r7-r4}
    r5 = r2
    r7 = r1
    r4 = r0
    r6 = -1
    if (r4 == 0) goto L0201cff4
    r0 = [r4+0]
    if (r0 == 0) goto L0201cff4
    r0 += 84
    call L02040614  ; @call.xl
    r1 = [r4+0]
    r2 = b[r1+164] (u)
    if (r2 == 0) goto L0201cfda
    r6 = -19
    if (r0 != 0) goto L0201cff4
    r0 = [r1+8]
    r3 = [r0+40]
    if (r3 == 0) goto L0201cfe8
    r0 = r4
    r1 = r7
    r2 = r5
    call r3
    r6 = r0  #
    r1 = [r4+0]
    goto L0201cfea
L0201cfda:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    r6 = -19
    goto L0201cff4
L0201cfe8:
    r6 = 0
L0201cfea:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
L0201cff4:
    r0 = r6
    {pc, r7-r4} = [sp++]

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; phase3_p13_fseeko: 0x0201cff8..0x0201cffe, module phase3-p13 (fseeko)
.type phase3_p13_fseeko,@function
phase3_p13_fseeko:
    [--sp] = rets
    call phase3_p13_fseek
    pc = [sp++]

; phase3_p13_ftell: 0x0201cffe..0x0201d04c, module phase3-p13 (ftell)
.type phase3_p13_ftell,@function
phase3_p13_ftell:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = -1
    if (r4 == 0) goto L0201d048
    r0 = [r4+0]
    if (r0 == 0) goto L0201d048
    r0 += 84
    call L02040614  ; @call.xl
    r1 = [r4+0]
    r2 = b[r1+164] (u)
    if (r2 == 0) goto L0201d02e
    r5 = -19
    if (r0 != 0) goto L0201d048
    r0 = [r1+8]
    r2 = [r0+52]
    if (r2 == 0) goto L0201d03c
    r0 = r4
    call r2
    r5 = r0  #
    r1 = [r4+0]
    goto L0201d03e
L0201d02e:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    r5 = -19
    goto L0201d048
L0201d03c:
    r5 = 0
L0201d03e:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
L0201d048:
    r0 = r5
    {pc, r5, r4} = [sp++]

; phase3_p13_ftello: 0x0201d04c..0x0201d052, module phase3-p13 (ftello)
.type phase3_p13_ftello,@function
phase3_p13_ftello:
    [--sp] = rets
    call phase3_p13_ftell
    pc = [sp++]

; phase3_p13_cxx_zero_g: 0x0201d052..0x0201d056, module phase3-p13 (cxx_zero_g)
.type phase3_p13_cxx_zero_g,@function
phase3_p13_cxx_zero_g:
    r0 = 0
    rts
.endif
