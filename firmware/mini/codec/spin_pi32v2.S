/* Same loop body as MINI stock 0x020069F0: nop, increment, conditional back
 * edge. Callback ABI r0=user (unused), r1=positive iteration count. Function
 * calls/MMIO/GPIO and cache state add overhead; this does not calibrate us. */
.text
.global hyperrig_mini_codec_spin_pi32v2
.type hyperrig_mini_codec_spin_pi32v2,@function
hyperrig_mini_codec_spin_pi32v2:
    r1 = -r1
    goto .Lcodec_delay_test
.Lcodec_delay_loop:
    nop
    r1 += 1
.Lcodec_delay_test:
    if (r1 != 0) goto .Lcodec_delay_loop
    rts
.size hyperrig_mini_codec_spin_pi32v2, .-hyperrig_mini_codec_spin_pi32v2
