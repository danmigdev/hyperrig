/* The bootloader calls the first byte of the loader with r0 = its context and r1 = the end of the stored stream. The loader
 * never returns: it takes stacks of its own and goes on in C, with both arguments. */
.section .entry,"ax",@progbits
.global stage_entry
.type stage_entry,@function
stage_entry:
    cli
    r2 = __exception_stack_top
    ssp = r2
    r2 = __main_stack_top
    sp = r2
    goto stage_main
.size stage_entry, .-stage_entry
