; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_command: 2 functions, 0x0200a5e2..0x0200a622

; capture_command_gain_clamp: 0x0200a5e2..0x0200a5f6, module capture-command (gain_clamp)
.type capture_command_gain_clamp,@function
capture_command_gain_clamp:
    r2 = r0
    ifs (r0 >= 24) {  ; @ifs.ge.ri.s12
    r2 = 24
    }
    r1 = -24
    ifs (r0 >= -24) {
    r1 = r2
    }
    r0 = r1
    rts

; capture_command_pack: 0x0200a5f6..0x0200a622, module capture-command (pack)
.type capture_command_pack,@function
capture_command_pack:
    [--sp] = {rets, r4}
    r3 = r2
    r4 = r1
    call capture_command_gain_clamp
    r0 = r0.b0 (u)
    if (r4 == 0) goto L0200a620
    ifs (r3 <= -200) {
    r3 = -200
    }
    ifs (r3 >= 400) {  ; @ifs.ge.ri.s12
    r3 = 400
    }
    r1 = r3 << 8
    r2 = 16776960
    r1 &= r2
    r0 |= r1
    r0 |= 16777216
L0200a620:
    {pc, r4} = [sp++]
