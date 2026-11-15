/* HYW1 application-only NOR writer. Initial target build has mutation gate0.
 * Host tests explicitly enable mutations only against an in-memory NOR. */
#ifndef HYPERRIG_MINI_APP_WRITER_H
#define HYPERRIG_MINI_APP_WRITER_H
#include <stdint.h>
#include <stddef.h>

#define HYW_START UINT32_C(0x4000)
#define HYW_END UINT32_C(0x82000)
#define HYW_SECTOR 4096u
#define HYW_PAGE 256u
#define HYW_RX 260u
#define HYW_RECORD 128u
enum { HYW_IDLE, HYW_READY, HYW_ARMED, HYW_ERASED, HYW_STAGED, HYW_VERIFIED, HYW_FAILED };
enum { HYW_OK, HYW_FRAME, HYW_RANGE, HYW_STATE, HYW_JEDEC, HYW_PROTECTED,
       HYW_BUSY, HYW_WEL, HYW_IO, HYW_TIMEOUT, HYW_CRC, HYW_PREIMAGE,
       HYW_READBACK, HYW_RECEIVE, HYW_GUARD, HYW_TRANSPORT, HYW_LOCKED, HYW_STACK };

typedef int (*hyw_handler)(const uint8_t *,uint8_t *);
typedef struct {
    int (*send)(const void *,uint32_t);
    int (*receive)(void *,uint32_t);
    hyw_handler *handler_slot;
} hyw_services;

/* HAL calls return0 only after their bounded transaction completes and CS is
 * deasserted. The HAL cannot unlock NOR or expose arbitrary opcodes. */
typedef struct {
    void *user;
    int (*initialize)(void *,uint32_t *jedec);
    int (*status)(void *,uint8_t *sr1,uint8_t *sr2);
    int (*read)(void *,uint32_t address,uint8_t *,unsigned length);
    int (*write_enable)(void *);
    int (*erase4k)(void *,uint32_t address);
    int (*program256)(void *,uint32_t address,const uint8_t *);
    void (*poll_delay)(void *);
    unsigned wip_poll_limit;
} hyw_nor;

typedef struct {
    void *user;
    uint32_t (*read32)(void *,uintptr_t);
    void (*write32)(void *,uintptr_t,uint32_t);
    void (*sync)(void *);
    void (*settle)(void *,unsigned);
    unsigned byte_poll_limit;
} hyw_pio_io;
typedef struct {
    hyw_pio_io io;
    uint32_t sys_div,clk_con2;
    unsigned failed,initialized;
} hyw_pio;

extern const uint32_t hyperrig_writer_mutations_enabled;
extern uint8_t hyperrig_writer_record[HYW_RECORD];
int hyw_range(uint32_t address,uint32_t length);
uint32_t hyw_crc32(const uint8_t *,unsigned);
void hyw_pio_bind(hyw_pio *,const hyw_pio_io *,hyw_nor *,unsigned wip_poll_limit);
int hyperrig_writer_initialize(const hyw_services *,const hyw_nor *,uint32_t base);
int hyperrig_writer_dispatch(const uint8_t *,uint8_t *);
#endif
