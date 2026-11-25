; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_pause: 6 functions, 0x02003898..0x02003a4e

; audio_pause_crc32: 0x02003898..0x020038cc, module audio-pause (crc32)
.type audio_pause_crc32,@function
audio_pause_crc32:
    [--sp] = {rets, r6-r4}
    r2 = 0
    r3 = -1
    r4 = 3988292384
    goto L020038c4
L020038a6:
    r5 = b[r0+r2] (u)
    r3 ^= r5
    r5 = 8
    goto L020038c0
L020038b0:
    r6 = r3 & 0x1
    r6 = 0x0 - r6
    r6 &= r4
    r3 = r3 >> 1
    r3 ^= r6
    r5 += -1
L020038c0:
    if (r5 != 0) goto L020038b0
    r2 += 1  ; @add.ri.u5
L020038c4:
    if (r2 != r1) goto L020038a6
    r0 = ~r3
    {pc, r6-r4} = [sp++]

; audio_pause_breadcrumb: 0x020038cc..0x020038fa, module audio-pause (breadcrumb)
.type audio_pause_breadcrumb,@function
audio_pause_breadcrumb:
    [--sp] = {rets, r6-r4}
    r4 = 29883708
    r5 = [r4+156]
    r5 = r5 >> 20
    r6 = 3708
    if (r5 == r6) goto L020038f8
    if (r0 == 0) goto L020038f4
    r0 = r0 << 16
    r0 |= r1  #
    [r4+4] = r3
    r1 = r2 << 8
    r0 |= r1
    r0 = r0 | 0xFA000000
    goto L020038f6
L020038f4:
    r0 = 0
L020038f6:
    [r4+0] = r0
L020038f8:
    {pc, r6-r4} = [sp++]

; audio_pause_pause_audio: 0x020038fa..0x020039e0, module audio-pause (pause_audio)
.type audio_pause_pause_audio,@function
audio_pause_pause_audio:
    [--sp] = {rets, r6-r4}
    call dsp_initialization_startup
    r5 = L01c26890
    r0 = 1
    b[r5+20] = r0
    r0 = [r5+280]
    if (r0 != 2) goto L020039d8
    r0 = 4
    call storage_control_activity
    r0 = 48
    r1 = 0
    r3_r2 = 0
    call audio_pause_breadcrumb
    call storage_platform_clock  ; @call.xl
    r4 = r0
    call preset_application_rate
    r6 = r0 << 2
    goto L02003942
L02003932:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r4
    if (r0 >= r6) goto L02003948
    call storage_coordination_poll_forward
L02003942:
    r0 = b[r5+21] (u)
    if (r0 == 0) goto L02003932
L02003948:
    r6 = r5 + 472
    call storage_platform_clock  ; @call.xl
    [r6+0] += 1  ; @rmw.add.s12
    r1 = b[r5+21] (u)
    r0 = r0 - r4
    if (r1 != 0) goto L02003966
    r1 = r5 + 476
    [r1+0] += 1  ; @rmw.add.s12
L02003966:
    r1 = [r5+480]
    if (r0 > r1) {
    [r5+480] = r0
    }
    r4 = 0
    goto L02003986
L02003976:
    r0 = b[r5+21] (u)
    if (r0 != 0) goto L0200398a
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L02003986:
    ifs (r4 <= 19) goto L02003976
L0200398a:
    r0 = b[r5+21] (u)
    if (r0 != 0) goto L02003998
    r0 = r5 + 388
    [r0+0] += 1  ; @rmw.add.s12
L02003998:
    r0 = b[r5+21] (u)
    if (r0 == 0) goto L020039a4
    call ir_processing_wait  ; @call.xl
L020039a4:
    r0 = 49
    r1 = 0
    r2 = 0
    r3 = r4
    call audio_pause_breadcrumb
    r4 = 1
    goto L020039c0
L020039b2:
    ifs (r4 > 49) goto L020039ca
    r0 = 1
    call L0203feb8  ; @call.xl
    r4 += 1  ; @add.ri.u5
L020039c0:
    call audio_pause_queue_drained  ; @call.xl
    if (r0 == 0) goto L020039b2
    goto L020039d2
L020039ca:
    r0 = r5 + 484
    [r0+0] += 1  ; @rmw.add.s12
L020039d2:
    r0 = 0
    call storage_control_activity
L020039d8:
    call audio_pause_drop_idle_queued  ; @call.xl
    {pc, r6-r4} = [sp++]

; audio_pause_resume_audio: 0x020039e0..0x02003a00, module audio-pause (resume_audio)
.type audio_pause_resume_audio,@function
audio_pause_resume_audio:
    [--sp] = rets
    r0 = L01c26890
    r1 = 0
    [r0+328] = r1
    r0 += 16  ; @add.ri.u5
    b[r0+3] = r1
    b[r0+4] = r1
    r3_r2 = 0  #
    b[r0+5] = r1
    r0 = 0
    call audio_pause_breadcrumb
    pc = [sp++]

; audio_pause_set_auxiliary: 0x02003a00..0x02003a3e, module audio-pause (set_auxiliary)
.type audio_pause_set_auxiliary,@function
audio_pause_set_auxiliary:
    [--sp] = {rets, r4}
    r1 = 1
    if (r0 != 0) goto L02003a08
    r1 = r0
L02003a08:
    r2 = L01c1f180
    b[r2+4] = r1
    r1 = L01c26890
    if (r0 != 0) goto L02003a2e
    r0 = 0
    r2 = 9752
    r3 = 0
    goto L02003a2a
L02003a22:
    r4 = r1 + r2
    [r4+r3<<2] = r0
    r3 += 1  ; @add.ri.u5
L02003a2a:
    if (r3 != 128) goto L02003a22
L02003a2e:
    r0 = 10264
    r0 += r1  ; @add.rr
    r2 = 0
    r3 = 0
    d[r0+0] = r3_r2
    {pc, r4} = [sp++]

; audio_pause_set_selector: 0x02003a3e..0x02003a4e, module audio-pause (set_selector)
.type audio_pause_set_selector,@function
audio_pause_set_selector:
    if (r0 <= 2) {  ; @if.le.ri.s12
    r1 = L01c26890
    b[r1+74] = r0
    }
    rts
