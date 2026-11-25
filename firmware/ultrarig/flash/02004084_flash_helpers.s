; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 1 function, 0x02004084..0x020040f8

; flash_helpers_firmware_version: 0x02004084..0x020040f8, module flash-helpers (firmware_version)
.type flash_helpers_firmware_version,@function
flash_helpers_firmware_version:
    [--sp] = {rets, r7-r4}
    r3 = L0203678e  ; "tankg_fw M5.71 rel ble"
L0200408c:
    r2 = r3
    r3 = b[r2+0] (u)
    if (r3 == 77) goto L0200409a
    if (r3 == 0) goto L020040f6
    r3 = r2 + 1
    goto L0200408c
L0200409a:
    r5 = b[r2+1] (u)
    r3 = r5 + -48
    r4 = r3.b0 (u)
    r3 = r2 + 1
    if (r4 > 9) goto L0200408c
    r3 = 0
    goto L020040ba
L020040ac:
    r4 = r5.b0 (s)  #
    r5 = b[r2+2] (u)
    r3 = r3 * 0xA
    r3 += r4  ; @add.rr
    r3 += -48
    r2 += 1  ; @add.ri.u5
L020040ba:
    r4 = r5 + -48
    r4 = r4.b0 (u)
    if (r4 <= 9) goto L020040ac
    r4 = 0
    if (r5 != 46) goto L020040e6
    r5 = 2
    goto L020040d8
L020040ce:
    r4 = r4 * 0xA
    r4 += r6  ; @add.rr
    r4 += -48
    r5 += 1  ; @add.ri.u5
L020040d8:
    r6 = b[r2+r5] (s)
    r7 = r6 + -48
    r7 = r7.b0 (u)
    if (r7 <= 9) goto L020040ce
L020040e6:
    r2 = r3 + -1
    if (r2 > 14) goto L020040f6
    if (r4 <= 255) {  ; @if.le.ri.s12
    b[r0+0] = r3
    b[r1+0] = r4
    }
L020040f6:
    {pc, r7-r4} = [sp++]
