; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 1 function, 0x0200cca0..0x0200ccfa

; footswitch_events_adc_read: 0x0200cca0..0x0200ccfa, module footswitch-events (adc_read)
.type footswitch_events_adc_read,@function
footswitch_events_adc_read:
    [--sp] = {rets, r5, r4}
    r4 = 71936
    r4 = r0  #
    r5 = [r4+0]
    r0 = 0
    if ((r5 & 16384) != 0) goto L0200ccf8
    r0 = r4 << 8
    r1 = r1 << 12
    r1 |= r0
    r4 = r1 | 0xE
    r0 = 78080
    r4 = r1 | 0x1E  #
    [r0+0] = r4
    r1 = r1 | 0x5E  #
    [r0+0] = r4
    [r0+0] = r1
    r1 = 0
L0200ccd2:
    r4 = [r0+0]
    if (r1 >= r2) goto L0200cce0
    r4 = r4.b0 (s)
    r1 += 1  ; @add.ri.u5
    ifs (r4 > -1) goto L0200ccd2
L0200cce0:
    r1 = [r0+0]
    r4 = 1023  #
    r2 = [r0+4]
    r2 &= r4
    [r3+0] = r2
    [r0+0] = 0x40
    [r0+0] = 0x0
    r0 = uextra(r1, p:7, l:1)
L0200ccf8:
    {pc, r5, r4} = [sp++]
