; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_audio_path: 1 function, 0x01c19d36..0x01c19ede

; dsp_audio_path_ramp: 0x01c19d36..0x01c19ede, module dsp-audio-path (ramp), dsp-transition-notification (audio_ramp)
.type dsp_audio_path_ramp,@function
dsp_audio_path_ramp:
    [--sp] = {r9-r4}
    r9 = r1
    r1 = r2
    r2 = r3
    r3 = r9 & 0x1
    if (r3 == 0) goto L01c19d5c
    r3 = [r0+0]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r5_r4 >>>= 16
    r8 = r4 >>> 31
    if (r5 != r8) goto L01c19e44
L01c19d58:
    [r0+0] = r4
    r0 = r0 + 4
L01c19d5c:
    r9 = r9 >> 1
    if (r9 == 0) goto L01c19e40
    r3 = r9 & 0x3
    r9 = r9 + 3
    r9 = r9 >> 2
    if (r3 == 0) goto L01c19d8a
    r3 += -1
    if (r3 == 0) goto L01c19d86
    r3 += -1
    if (r3 == 0) goto L01c19d82
    r3 += -1
    goto L01c19d7e
L01c19d7e:
    r0 += -8
    goto L01c19db6
L01c19d82:
    r0 += -16
    goto L01c19de2
L01c19d86:
    r0 += -24
    goto L01c19e0e
L01c19d8a:
    r3 = [r0+0]
    r8 = [r0+4]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r1 = r1 + r2
    r7_r6 = r8 * r1 (s)
    r5_r4 >>>= 16
    r7_r6 >>>= 16
    r3 = r4 >>> 31
    r8 = r6 >>> 31
    if (r5 != r3) goto L01c19e56
L01c19dae:
    [r0+0] = r4
    if (r7 != r8) goto L01c19e66
L01c19db4:
    [r0+4] = r6
L01c19db6:
    r3 = [r0+8]
    r8 = [r0+12]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r1 = r1 + r2
    r7_r6 = r8 * r1 (s)
    r5_r4 >>>= 16
    r7_r6 >>>= 16
    r3 = r4 >>> 31
    r8 = r6 >>> 31
    if (r5 != r3) goto L01c19e78
L01c19dda:
    [r0+8] = r4
    if (r7 != r8) goto L01c19e88
L01c19de0:
    [r0+12] = r6
L01c19de2:
    r3 = [r0+16]
    r8 = [r0+20]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r1 = r1 + r2
    r7_r6 = r8 * r1 (s)
    r5_r4 >>>= 16
    r7_r6 >>>= 16
    r3 = r4 >>> 31
    r8 = r6 >>> 31
    if (r5 != r3) goto L01c19e9a
L01c19e06:
    [r0+16] = r4
    if (r7 != r8) goto L01c19eaa
L01c19e0c:
    [r0+20] = r6
L01c19e0e:
    r3 = [r0+24]
    r8 = [r0+28]
    r1 = r1 + r2
    r5_r4 = r3 * r1 (s)
    r1 = r1 + r2
    r7_r6 = r8 * r1 (s)
    r5_r4 >>>= 16
    r7_r6 >>>= 16
    r3 = r4 >>> 31
    r8 = r6 >>> 31
    if (r5 != r3) goto L01c19ebc
L01c19e32:
    [r0+24] = r4
    if (r7 != r8) goto L01c19ecc
L01c19e38:
    [r0+28] = r6
    r0 += 32
    if (--r9 != 0) goto L01c19d8a
L01c19e40:
    {r9-r4} = [sp++]
    rts
L01c19e44:
    r8 = r5 >> 31
    r8 += r8
    r5 = 2147483647
    r8 += r5
    r4 = r8
    goto L01c19d58
L01c19e56:
    r3 = r5 >> 31
    r3 = r3 + r3
    r5 = 2147483647
    r3 = r3 + r5
    r4 = r3
    goto L01c19dae
L01c19e66:
    r8 = r7 >> 31
    r8 += r8
    r7 = 2147483647
    r8 += r7
    r6 = r8
    goto L01c19db4
L01c19e78:
    r3 = r5 >> 31
    r3 = r3 + r3
    r5 = 2147483647
    r3 = r3 + r5
    r4 = r3
    goto L01c19dda
L01c19e88:
    r8 = r7 >> 31
    r8 += r8
    r7 = 2147483647
    r8 += r7
    r6 = r8
    goto L01c19de0
L01c19e9a:
    r3 = r5 >> 31
    r3 = r3 + r3
    r5 = 2147483647
    r3 = r3 + r5
    r4 = r3
    goto L01c19e06
L01c19eaa:
    r8 = r7 >> 31
    r8 += r8
    r7 = 2147483647
    r8 += r7
    r6 = r8
    goto L01c19e0c
L01c19ebc:
    r3 = r5 >> 31
    r3 = r3 + r3
    r5 = 2147483647
    r3 = r3 + r5
    r4 = r3
    goto L01c19e32
L01c19ecc:
    r8 = r7 >> 31
    r8 += r8
    r7 = 2147483647
    r8 += r7
    r6 = r8
    goto L01c19e38
