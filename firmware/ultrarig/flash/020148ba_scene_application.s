; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; scene_application: 1 function, 0x020148ba..0x02014952

; scene_application_flush: 0x020148ba..0x02014952, module scene-application (flush), selection (scene_flush)
; HyperRig MINI, product option: eight scenes.
.type scene_application_flush,@function
scene_application_flush:
    [--sp] = {rets, r8-r4}
    r6 = L01c26890
    r1 = [r6+956]
    r0 = 0
    [r6+956] = r0
    if (r1 == 0) goto L02014950
    r2 = r1 >>> 31
    r2 |= 1
    ifs (r2 <= 0) {  ; @ifs.le.ri.s12
.if MINI_PRODUCT
    r0 = 7
.else
    r0 = 3
.endif
    }
    r8 = abs(r1)
    r1 = L01c1f180
    r7 = [r1+88]
.if MINI_PRODUCT
    r2 += 8  ; @add.ri.u5
.else
    r2 += 4  ; @add.ri.u5
.endif
    r4 = -1
    r3 = 11936
.if MINI_PRODUCT
    r5 = 8
.else
    r5 = 4
.endif
    goto L02014920
L020148f2:
    r1 = 0
L020148f4:
    r4 = r0
    ifs (r7 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r2 + r7
    r7 = r4 / r5 (s)
.if MINI_PRODUCT
    r7 = r7 << 3
.else
    r7 = r7 << 2
.endif
    r4 = r4 - r7
    }
.if MINI_PRODUCT
    r7 = r4 * 0x104
    r3 = hyperrig_scene_base  ; @li.u32
    r7 += r3  ; @add.rr
    r3 = 11936
    r7 = b[r7+r3] (u)
.else
    r7 = r4 * 0x104
    r7 += r6  ; @add.rr
    r7 = b[r7+r3] (u)
.endif
    if (r7 != 0) goto L0201491a
    r1 += 1  ; @add.ri.u5
    r7 = r4
.if MINI_PRODUCT
    ifs (r1 < 8) goto L020148f4
.else
    ifs (r1 < 4) goto L020148f4
.endif
    {pc, r8-r4} = [sp++]
L0201491a:
    r8 = r8 + -1
    r7 = r4
L02014920:
    ifs (r8 >= 1) goto L020148f2
    ifs (r4 < 0) goto L02014950
    call storage_platform_clock  ; @call.xl
    r5 = r0
    r0 = r4
    call scene_application_apply
    r1 = 740
    r1 = b[r6+r1] (u)
    if (r1 != 0) goto L02014950
    r1 = r5
    call scene_application_report
    r2 = r0
    r0 = 8
    r1 = r4
    call storage_coordination_notify
L02014950:
    {pc, r8-r4} = [sp++]
