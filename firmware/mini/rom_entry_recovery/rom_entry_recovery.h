#ifndef HYPERRIG_ROM_ENTRY_RECOVERY_H
#define HYPERRIG_ROM_ENTRY_RECOVERY_H
#include <stdint.h>

typedef int (*hyperrig_rom_entry_send)(const void *, uint32_t);
typedef int (*hyperrig_rom_entry_handler)(const uint8_t *, uint8_t *);
typedef struct {
    hyperrig_rom_entry_send send;
    int (*receive)(void *, uint32_t);
    hyperrig_rom_entry_handler *handler_slot;
} hyperrig_rom_entry_services;
typedef struct {
    uint32_t (*read)(uint32_t address);
    uint32_t (*check)(void);
    void (*reset)(void);
} hyperrig_rom_entry_hardware;

enum { HYK1_RECORD_BYTES = 256, HYK1_STACK_BYTES = 4096, HYK1_KEY_MASK = 0x409 };
/* All commands: CBW USBC, IN, LUN0, CDB length16; unused CDB bytes FF.
 * FC74 identity16: op2,HYK1,version1,capabilities7,baseBE32,spanBE16,recordBE16.
 * FC75 snapshot: no args; passive MMIO reads, arms one check if DIR inputs.
 * FC76 check: sequenceBE32,recordCRCBE32; only after a successful snapshot.
 * FC75/76 reply16: op2,HYK1,sequenceBE32,statusBE32,phase,check_armed.
 * FD77 record256: sequenceBE32. Exposes the completed record without MMIO.
 * FC81 reset: sequenceBE32,recordCRCBE32,ASCII ROM!,then two FF bytes.
 * Requires FD77 exposure and intact stack guards; one reset attempt per load.
 * This token prevents stale/accidental calls; it is NOT authentication.
 * No reply is promised by FC81; independently establish fresh ROM enumeration.
 * Entry, identity, snapshot, check and their errors NEVER invoke reset.
 *
 * Record LE32 except ASCII: 0 HYK1,4 version1,8 base,12 buildtag,16 seq,
 * 20 phase(0 snapshot,1 check,2 unexpected reset return),24 signed status,
 * 28 check_result(0/1/2,FFFFFFFF absent/invalid),32 mask409,36 observed_stack,
 * 40 guards_ok,44 GPIO_config_equal(excludes IN),48 before_IN&409,
 * 52 after_IN&409,56 check_invoked,60 reset_attempted,
 * 64..99 PORTA before;100..135 PORTA after (OUT,IN,DIR,DIE,PU,PD,HD0,HD,DIEH),
 * 136..183 clocks before;184..231 clocks after (12 addresses in probe.c),
 * 232 clocks_equal,236 consumed_sequence(0 for snapshot),240..247 zero,
 * 248 CRC32[0:248],252 DONE.
 * Status precedence: -7 guards,-6 GPIO changed,-8 clocks changed,
 * -9 unexpected reset return,-10 invalid check result,-3 config error,0.
 * Host dispatch tests substitute the two ASM effects; target bytes are audited
 * separately. Neither model is an execution on the MINI.
 */
extern uint8_t hyperrig_rom_entry_record[HYK1_RECORD_BYTES];
int hyperrig_rom_entry_initialize(const hyperrig_rom_entry_services *, uint32_t,
                                 const hyperrig_rom_entry_hardware *);
int hyperrig_rom_entry_dispatch(const uint8_t *, uint8_t *);
#endif
