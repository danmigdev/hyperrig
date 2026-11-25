; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 3 functions, 0x02001e7e..0x0200205a

; phase3_p5_user_setup_filter_install: 0x02001e7e..0x02001e9c, module phase3-p5 (user_setup_filter_install)
.type phase3_p5_user_setup_filter_install,@function
phase3_p5_user_setup_filter_install:
    r1 = b[r0+25] (u)
    r2 = L01c26f08
    r1 = r1 & 0xFFFFFF01
    r1 = [r2+r1<<2]
    if (r1 == 0) goto L02001e9a
    r1 = phase3_p4_user_setup_filter
    [r0+12] = r1
L02001e9a:
    rts

; phase3_p5_usb_device_mode: 0x02001e9c..0x0200204a, module phase3-p5 (usb_device_mode)
.type phase3_p5_usb_device_mode,@function
phase3_p5_usb_device_mode:
    [--sp] = {rets, r7-r4}
    r5 = L01c26890
    if (r0 == 0) goto L02002000
    r1 = r5 + 3376
    r4 = 0
    rep 8 {
    [r1++=4] = r4
    }
    r6 = L01c37c28
    if ((r0 & 16) == 0) goto L02001f1c
    r0 = 844
    r1 = phase3_p4_cdc_desc_config
    [r5+r0<<2] = r1
; HyperRig MINI, product option: the MIDI port after the serial port, when it is wanted (mini/product/midi.c).
.if MINI_PRODUCT
    call hyperrig_usb_functions  ; @call.xl
.endif
    r7 = 412
    r0 = [r5+r7<<2]
    if (r0 != 0) goto L02001f1c
    r0 = L01c37ee8
    r1 = r0 + 4
    r2 = 0
    rep 28 {
    [r1++=4] = r2
    }
    [r5+r7<<2] = r0
    r1 = L01c37fd0
    r1 = r0 + 104  #
    [r0+0] = r1
    b[r1+4] = r2
    r3 = 7
    b[r1+3] = r3
    r3 = 8
    b[r1+2] = r3
    b[r1+1] = r2
    b[r1+5] = r2
    b[r1+6] = r2
    b[r1+7] = r3
    r0 += 24  ; @add.ri.u5
    call L0203fb92  ; @call.xl
    r0 = [r5+r7<<2]
    r1 = r6 + 224
    r1 = r6 + 92  #
    [r0+8] = r1
    [r0+4] = r1
L02001f1c:
    r0 = r5 + 2560
    r1 = r0 + 40
    r2 = r0 + 120
    r3 = r0 + 80
    rep 5 {
    [r0++=4] = r4
    }
    rep 5 {
    [r1++=4] = r4
    }
    rep 5 {
    [r2++=4] = r4
    }
    rep 5 {
    [r3++=4] = r4
    }
    r7 = 381
    r4 = [r5+r7<<2]
    if (r4 != 0) goto L02001f5e
    r4 = L01c37490
    r1 = 0
    r2 = 1944
    r0 = r4
    call effect_enable_memset  ; @call.xl
    [r5+r7<<2] = r4
L02001f5e:
    r0 = r4 + 768
    call phase3_p5_usb_var_init
    r0 = r4 + 872
    r1 = r4
    call phase3_p5_usb_setup_init
    r0 = 0
    call L02001a08
    r0 = 0
    call phase3_p5_usb_write_power
    call phase3_p5_usb_slave_init
    r0 = r7 + 29
    r2 = [r5+r0<<2]
    if (r2 != 0) goto L02001f8e
    [r5+r0<<2] = r6
    r2 = r6
L02001f8e:
    r1_r0 = 0
    call sdk_usb_set_dma_raddr
    r4 = r5 + 1640
    r2 = [r4+0]
    r0 = 0
    r1 = 1
    call sdk_usb_set_dma_raddr
    r2 = [r4+0]
    r0 = 0
    r1 = 2
    call sdk_usb_set_dma_raddr
    r2 = [r4+0]
    r0 = 0
    r1 = 3
    call sdk_usb_set_dma_raddr
    r2 = [r4+0]
    r0 = 0
    r1 = 4
    call sdk_usb_set_dma_raddr
    r0 = 0
    r1 = 5
    call L02001b40
    r0 = 0
    r1 = -1
    call L02001bca
    r0 = 0
    r1 = -1
    call L02001c58
    r1_r0 = 0
    call L02001d7a
    r1_r0 = 0
    call L02001df6
    r2 = L0201c0be
    r0 = 9
    r1 = 3
    r3 = 0
    call storage_platform_register
    r0 = 0
    call L02001e72
    call phase3_p5_user_setup_filter_install
    {pc, r7-r4} = [sp++]
L02002000:
    r0 = 412
    r0 = [r5+r0<<2]
    if (r0 == 0) goto L02002024
    r1 = [r0+8]
    if (r1 == 0) goto L02002012
    [r0+8] = 0x0
L02002012:
    r1 = [r0+4]
    if (r1 == 0) goto L0200201a
    [r0+4] = 0x0
L0200201a:
    r0 = 412
    r1 = 0
    [r5+r0<<2] = r1
L02002024:
    r0 = 0
    r4 = 0
    call L02001916
    r0 = 0
    call phase3_p5_usb_var_init
    r1_r0 = 0
    call phase3_p5_usb_setup_init
    r0 = 381
    [r5+r0<<2] = r4
    r0 = 15
    call L0203feb8  ; @call.xl
    {pc, r7-r4} = [sp++]

; phase3_p5_cdc_set_wakeup_handler: 0x0200204a..0x0200205a, module phase3-p5 (cdc_set_wakeup_handler)
.type phase3_p5_cdc_set_wakeup_handler,@function
phase3_p5_cdc_set_wakeup_handler:
    r2 = L01c26f00
    r0 = [r2+r0<<2]
    if (r0 == 0) goto L02002058
    [r0+20] = r1
L02002058:
    rts
