; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; scene_application: 1 function, 0x02014366..0x020143ae

; scene_application_select: 0x02014366..0x020143ae, module scene-application (select), selection (scene)
; HyperRig MINI, product option: eight scenes.
.type scene_application_select,@function
scene_application_select:
    [--sp] = {rets, r6-r4}
    r4 = r0
.if MINI_PRODUCT
    if (r4 > 7) goto L020143ac
.else
    if (r4 > 3) goto L020143ac
.endif
.if MINI_PRODUCT
    r0 = r4 * 0x104
    r6 = hyperrig_scene_base  ; @li.u32
    r0 += r6  ; @add.rr
    r6 = L01c26890
.else
    r0 = r4 * 0x104
    r6 = L01c26890
    r0 += r6  ; @add.rr
.endif
    r1 = 11936
    r0 = b[r0+r1] (u)
    if (r0 == 0) goto L020143ac
    call storage_platform_clock  ; @call.xl
    r5 = r0
    r0 = r4
    call scene_application_apply
    r1 = 740
    r1 = b[r6+r1] (u)
    if (r1 != 0) goto L020143ac
    r1 = r5
    call scene_application_report
    r2 = r0
    r0 = 8
    r1 = r4
    call storage_coordination_notify
L020143ac:
    {pc, r6-r4} = [sp++]
