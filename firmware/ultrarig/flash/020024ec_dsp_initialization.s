; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_initialization: 1 function, 0x020024ec..0x020025ca

; dsp_initialization_startup: 0x020024ec..0x020025ca, module dsp-initialization (startup), dsp-transition-notification (initialization_startup)
.type dsp_initialization_startup,@function
dsp_initialization_startup:
    [--sp] = rets
    r0 = L01c2249c
    r1 = b[r0+0] (u)
    if (r1 != 0) goto L020025c8
    r1 = 1
    b[r0+0] = r1
    call dsp_audio_path_input  ; @call.xl
    r1 = r0
    r0 = 48077
    call dsp_initialization_initialize  ; @call.xl
    r0 = 1
    r1 = -3
    r2 = 100
    call dsp_dynamics_configure  ; @call.xl
    r0 = pool_callbacks_pool_take
    r1 = pool_callbacks_pool_give
    call dsp_initialization_bind  ; @call.xl
    r0 = L01c343c4
    r1 = pool_callbacks_event_report
    [r0+0] = r1
    r0 = L01c34458
    r1 = dispatch_helpers_audio_hold
    [r0+0] = r1
    r0 = L01c34194
    r1 = effect_enable_clear
    [r0+0] = r1
    r0 = L01c3446c
    r1 = dsp_transition_notification_notify
    [r0+0] = r1
    r0 = L01c343d4
    r1 = flash_helpers_largest_free
    [r0+0] = r1
    r0 = L01c34434
    r1 = flash_helpers_set_limit
    [r0+0] = r1
    r0 = L01c34198
    r1 = storage_platform_clock
    [r0+0] = r1
    r0 = L01c343d0
    r1 = flash_helpers_second_call
    [r0+0] = r1
    r0 = L01c341c0
    r1 = ram_callbacks_wait_job
    [r0+0] = r1
    r0 = L01c341a0
    r1 = ram_callbacks_job_busy
    [r0+0] = r1
    r0 = L01c3444c
    r1 = audio_pause_queue_drained
    [r0+0] = r1
L020025c8:
    pc = [sp++]
