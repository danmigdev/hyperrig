; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_audio_path: 2 functions, 0x01c01058..0x01c010e4

; dsp_audio_path_cached: 0x01c01058..0x01c010a6, module dsp-audio-path (cached), dsp-transition-notification (audio_cached)
.type dsp_audio_path_cached,@function
dsp_audio_path_cached:
    [--sp] = {rets, r4}
    r0 = L01c1f180
    r1 = [r0+44]
    r0 = L01c26890
    r2 = [r0+504]
    if (r2 == r1) goto L01c010a0
    r2 = 1000000
    r3_r2 = r1 * r2 (u)
    r4 = 6
    r3_r2 = r3_r2 / r4 (u)
    r3_r2 <<= 7
    r4 = 48077
    r3_r2 = r3_r2 / r4 (u)
    r2 = r2 * 0x61
    r3 = 100
    r2 = r2 / r3 (u)
    [r0+508] = r2
    [r0+504] = r1
L01c010a0:
    r0 = [r0+508]
    {pc, r4} = [sp++]

; dsp_audio_path_input: 0x01c010a6..0x01c010e4, module dsp-audio-path (input), dsp-transition-notification (audio_input)
.type dsp_audio_path_input,@function
dsp_audio_path_input:
    [--sp] = rets
    call dsp_audio_path_cached
    r1 = L01c1f180
    r1 = r0  #
    r2 = [r1+52]
    r0 = r1 - r2
    if (r1 <= r2) {
    r0 = 0
    }
    r2 = 154951
    if (r1 < r2) goto L01c010e2
    r1 = r1 * 0x32
    r2 = 4287219796
    r1 += r2  ; @add.rr
    r2 = 100
    r2 = r1 / r2 (u)
    r1 = r0 - r2
    if (r0 <= r2) {
    r1 = 0
    }
    r0 = r1
L01c010e2:
    pc = [sp++]
