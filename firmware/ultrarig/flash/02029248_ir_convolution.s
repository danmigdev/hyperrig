; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_convolution: 4 functions, 0x02029248..0x0202930e

; ir_convolution_installation_budget: 0x02029248..0x02029268, module ir-convolution (installation_budget), ir-installation (budget), ir-processing (installation_budget)
.type ir_convolution_installation_budget,@function
ir_convolution_installation_budget:
    ifs (r0 < 1) {
    r0 = 0
    rts
    }
    r0 = r0 * 0x30
    r0 += 64
    r1 = r0 >> 7
    r0 = 1
    if (r1 == 0) goto L0202925e
    r0 = r1
L0202925e:
    if (r0 >= 32) {
    r0 = 32
    }
    r0 = r0 << 7
    rts

; ir_convolution_installation_convert: 0x02029268..0x0202928a, module ir-convolution (installation_convert), ir-installation (convert), ir-processing (installation_convert)
.type ir_convolution_installation_convert,@function
ir_convolution_installation_convert:
    [--sp] = {rets, r4}
    r3 = 1
    r4 = 1
    if (r2 != 0) goto L02029272
    r4 = r2
L02029272:
    if (r1 != 0) goto L02029276
    r3 = r1
L02029276:
    if (r3 == r4) goto L02029288
    if (r2 == 0) goto L02029282
    r0 = r0 << 1
    r0 = r0 + 18
    {pc, r4} = [sp++]
L02029282:
    r0 = r0 + 1
    r0 = r0 >> 1
    r0 = r0 + 9
L02029288:
    {pc, r4} = [sp++]

; ir_convolution_installation_limit: 0x0202928a..0x020292ee, module ir-convolution (installation_limit), ir-installation (limit), ir-processing (installation_limit)
.type ir_convolution_installation_limit,@function
ir_convolution_installation_limit:
    [--sp] = {rets, r6-r4}
    r4 = r3
    r3 = r1
    r6 = r0
    if (r4 == 0) goto L020292a0
    r0 = 1
    if (r2 == 0) goto L0202929a
    r0 = 0
L0202929a:
    r5 = r6 << r0
    goto L020292a8
L020292a0:
    r0 = r6 + 1
    r5 = r0 >> 1
    if (r2 != 0) goto L020292a8
    r5 = r6
L020292a8:
    r0 = [sp+16]
    if (r5 >= 4096) {
    r5 = 4096
    }
    call ir_convolution_installation_budget
    if (r0 == 0) goto L020292c2
    r1 = 1
    if (r4 == 0) goto L020292bc
    r1 = 0
L020292bc:
    r0 >>= r1
    r5 = umin(r5, r0)
L020292c2:
    if (r3 == 0) goto L020292c8
    if (r3 < r6) goto L020292cc
L020292c8:
    r0 = r5
    {pc, r6-r4} = [sp++]
L020292cc:
    r6 = 128
    if (r4 != 0) goto L020292d2
    r6 = 64
L020292d2:
    r0 = r3
    r1 = r2
    r2 = r4
    call ir_convolution_installation_convert
    r0 = r0 + r6
    r0 += -1
    r1 = 7
    if (r4 != 0) goto L020292e4
    r1 = 6
L020292e4:
    r0 >>= r1
    r0 *= r6
    r5 = umin(r0, r5)
    goto L020292c8

; ir_convolution_installation_effective: 0x020292ee..0x0202930e, module ir-convolution (installation_effective), ir-installation (effective), ir-processing (installation_effective)
.type ir_convolution_installation_effective,@function
ir_convolution_installation_effective:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = L01c32df0
    r5 = r0  #
    r2 = [r4+4]
    r3 = [r4+16]
    r4 = [r4+0]
    r0 = r4  #
    [sp] = r1
    r1 = r3
    r3 = r5
    call ir_convolution_installation_limit
    sp += 4
    {pc, r5, r4} = [sp++]
