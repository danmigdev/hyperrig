; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_application: 5 functions, 0x02006f14..0x02007008

; preset_application_header: 0x02006f14..0x02006f3a, module preset-application (header), preset-storage (header)
.type preset_application_header,@function
preset_application_header:
    [--sp] = {rets, r6-r4}
    r5_r4 = r3_r2
    r6 = r1
    r2 = 40
    r1 = r5
    call storage_control_read
    r1 = r0
    r0 = 0
    if (r1 != 0) goto L02006f38
    r1 = [r5+0]
    if (r1 != r6) goto L02006f38
    r1 = [r5+4]
    r0 = 1
    if (r1 > r4) {
    r0 = 0
    }
L02006f38:
    {pc, r6-r4} = [sp++]

; preset_application_asset_header: 0x02006f3a..0x02006f70, module preset-application (asset_header), preset-assets (header)
.type preset_application_asset_header,@function
preset_application_asset_header:
    [--sp] = {rets, r7-r4}
    r4 = r3
    [r4+0] = 0x0
    r6 = r2
    r5 = r1
    r0 = r0 << 13
    r7 = r0 + 0xEF000
    r1 = 1246186324
    r0 = r7
    r3 = r5
    call preset_application_header
    if (r0 == 0) goto L02006f60
    r0 = 1
    [r4+0] = r0
    {pc, r7-r4} = [sp++]
L02006f60:
    r1 = 1229409108
    r0 = r7
    r2 = r6
    r3 = r5
    call preset_application_header
    {pc, r7-r4} = [sp++]

; preset_application_asset_extended: 0x02006f70..0x02006f8e, module preset-application (asset_extended), preset-assets (extended)
.type preset_application_asset_extended,@function
preset_application_asset_extended:
    [--sp] = {rets, r4}
    r2 = 1
    r4 = 558161692
    r3 = 1
    if (r0 != r4) {
    r3 = 0
    }
    if (r1 <= 7) {  ; @if.le.ri.s12
    r2 = 0
    }
    r0 = r3 & r2
    {pc, r4} = [sp++]

; preset_application_asset_identity: 0x02006f8e..0x02006fb0, module preset-application (asset_identity), preset-assets (identity)
.type preset_application_asset_identity,@function
preset_application_asset_identity:
    [--sp] = {rets, r5, r4}
    r5 = r2
    r4 = r0
    call preset_application_asset_extended
    if (r0 == 0) goto L02006fac
    r0 = b[r5+1] (u)
    r4 = b[r5+0] (u)
    r4 <= insert(r0, p:8, l:8)  #
    r1 = b[r5+2] (u)
    r4 <= insert(r1, p:16, l:8)  #
    r2 = b[r5+3] (u)
    r4 <= insert(r2, p:24, l:8)
L02006fac:
    r0 = r4
    {pc, r5, r4} = [sp++]

; preset_application_asset_resolve: 0x02006fb0..0x02007008, module preset-application (asset_resolve), preset-assets (resolve)
.type preset_application_asset_resolve,@function
preset_application_asset_resolve:
    [--sp] = {rets, r7-r4}
    sp += -4
    r5 = r1
    r1 = 0
    r4 = r2  #
    [sp] = r1
    r6 = r0  #
    r1 = [r5+4]
    r7 = [r5+8]
    r0 = r7
    call preset_application_asset_extended
    if (r0 == 0) goto L02006ffa
    r0 = 0xDF000
    ifs (r6 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r6 += r0  ; @add.rr
    r0 = 0xCF000
    }
    r2 = r6 << 13
    r0 += r2  ; @add.rr
    r0 = r0 | 0x28
    r0 += r1  ; @add.rr
    r0 += -4
    r1 = sp + 0
    r2 = 4
    call storage_control_read
    r1 = r0
    r0 = -1
    if (r1 != 0) goto L02007004
    r1 = [r5+4]
    r7 = [r5+8]
L02006ffa:
    r2 = sp + 0
    r0 = r7
    call preset_application_asset_identity
    [r4+0] = r0
    r0 = 0
L02007004:
    sp += 4
    {pc, r7-r4} = [sp++]
