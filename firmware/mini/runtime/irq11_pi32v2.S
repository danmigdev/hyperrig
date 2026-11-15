/* MINI stock IRQ11 (0x01c0374a) saves PSR/RETS/RETI and r0..r5.
 * Save every GPR here, so interrupted code never relies on the C callee's
 * register selection. The verifier compares the vendor compiler's interrupt
 * attribute output and audits the known ISR call graph. Hidden hardware loop
 * state, interrupt delivery and mode switching still need target validation.
 * This wrapper has no nesting/RTOS context-switch policy. */
.section .ramtext.mini_runtime_irq,"ax",@progbits
.global hyperrig_mini_irq11_entry
.type hyperrig_mini_irq11_entry,@function
hyperrig_mini_irq11_entry:
    [--sp] = {psr, rets, reti}
    [--sp] = {r15-r0}
    call hyperrig_mini_irq11_dispatch
    {r15-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    csync
    rti
.size hyperrig_mini_irq11_entry, .-hyperrig_mini_irq11_entry
