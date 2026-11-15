.section .capture,"a",@progbits
.balign 4
.global hyperrig_probe_capture
.global hyperrig_probe_capture_end
hyperrig_probe_capture:
.incbin "analysis/firmware/m571_g_app/embedded-0.a2l"
hyperrig_probe_capture_end:
