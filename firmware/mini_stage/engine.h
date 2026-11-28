/* The HyperRig loader of the TANK-MINI: what it does with the flash, and the messages that ask for it.
 *
 * A host reads the flash, shows with BEGIN that it has all of it, opens the application (its header sector is erased, so
 * that from then on a loss of power leads back to this loader), sends the sectors that change, the header sector last, and
 * lets the loader check the whole flash. Only whole sectors of two windows are ever written: the application and the user
 * area. The application's window ends at 0x82000, or where BEGIN says, up to the pedal's VM (a TANK-MINI with M-VAVE's 011 has
 * its application partition up to 0x95000). The boot area, the stored loader, the radio data and the last sector are never written, nor are the flash's
 * protection bits. A whole application is not opened unless the bootloader would come back to a HyperRig loader without
 * it; an older update record that would be found first can be made void. This file does no I/O of its own; README.md has
 * the protocol. */
#ifndef HYPERRIG_STAGE_ENGINE_H
#define HYPERRIG_STAGE_ENGINE_H
#include <stddef.h>
#include <stdint.h>

#define HRS_CAPACITY UINT32_C(0x100000)
#define HRS_SECTOR 4096u
#define HRS_PAGE 256u
#define HRS_APP UINT32_C(0x4000)
#define HRS_APP_END UINT32_C(0x82000)          /* the application's window, unless BEGIN widens it; old loaders have only this one */
#define HRS_APP_END_MAX UINT32_C(0xa0000)      /* the widest: no TANK-MINI's VM starts higher */
#define HRS_VM_END UINT32_C(0xbe000)           /* where every TANK-MINI's VM ends, and its radio data begin */
#define HRS_USER UINT32_C(0xbf000)
#define HRS_USER_END UINT32_C(0xff000)
#define HRS_JEDEC UINT32_C(0xeb6014)
#define HRS_CHUNK 1024u                       /* the most data bytes in one message */
#define HRS_HEAD 8u
#define HRS_FRAME (HRS_HEAD + 16u + HRS_CHUNK + 4u)
#define HRS_MAX_SECTORS 220u                  /* 156 of the widest application and 64 of the user area */
#define HRS_MAGIC UINT32_C(0x214d5241)        /* "ARM!" */
#define HRS_BUILD_TEXT 16u
#define HRS_RECORD 80u                        /* the bootloader's update record ... */
#define HRS_RECORD_MARK 0x5441u               /* ... with this in it */
#define HRS_LOADER_AT UINT32_C(0x01c0a800)    /* where the bootloader puts a stored loader */
#define HRS_LOADER_MAX UINT32_C(0x5b1c)
#define HRS_LOADER_CRC 0x4852u                /* the CRC-16 of every HyperRig loader; its builder sees to that */

/* Commands; a reply has HRS_REPLY added. */
enum { HRS_HELLO = 0x01, HRS_READ = 0x02, HRS_CRC = 0x03, HRS_BEGIN = 0x10, HRS_DATA = 0x11, HRS_WRITE = 0x12, HRS_OPEN = 0x13,
       HRS_FINISH = 0x14, HRS_RETIRE = 0x15, HRS_LEAVE = 0x20, HRS_REPLY = 0x80 };
enum { HRS_READY, HRS_ARMED, HRS_OPENED, HRS_DONE, HRS_FAILED };            /* phases */
enum { HRS_WINDOW_APP = 1, HRS_WINDOW_USER = 2 };                           /* of BEGIN */
enum { HRS_STAY, HRS_START_APP, HRS_DOWNLOAD, HRS_RESTART };                /* of LEAVE */
/* Errors up to HRS_LAST_NOTE changed nothing and leave the session usable; the rest end it (HRS_FAILED). */
enum { HRS_OK, HRS_E_FRAME, HRS_E_RANGE, HRS_E_STATE, HRS_E_CRC, HRS_E_BACKUP, HRS_E_PREIMAGE, HRS_E_NO_APP,
       HRS_E_NO_RETURN, HRS_LAST_NOTE = HRS_E_NO_RETURN,
       HRS_E_IO, HRS_E_JEDEC, HRS_E_PROTECTED, HRS_E_BUSY, HRS_E_WEL, HRS_E_TIMEOUT, HRS_E_READBACK };

/* Every call returns 0 only when its bounded transaction ended with the flash deselected. */
typedef struct {
    void *user;
    int (*status)(void *, uint8_t *sr1, uint8_t *sr2);
    int (*read)(void *, uint32_t address, uint8_t *, unsigned length);      /* up to a sector */
    int (*write_enable)(void *);
    int (*erase4k)(void *, uint32_t address);
    int (*program256)(void *, uint32_t address, const uint8_t *);
    void (*poll_delay)(void *);
    void (*idle)(void *);                                                   /* between sectors of a long job */
    unsigned wip_poll_limit;
} hrs_nor;
typedef struct {
    uint32_t jedec;
    uint16_t key;                             /* the chip's key, 0 when it was not read */
    uint8_t fast, app_valid;                  /* fast reads passed their check; the bootloader found an application */
    char build[HRS_BUILD_TEXT];
} hrs_unit;

int hrs_writable(uint32_t address, uint32_t length);
/* hrs_writable, and the one page RETIRE is at; what the flash driver asks. */
int hrs_permits(uint32_t address, uint32_t length);
uint32_t hrs_crc32(const uint8_t *data, unsigned length);
void hrs_start(const hrs_nor *nor, const hrs_unit *unit);
/* One whole message; the reply goes to out (HRS_FRAME bytes) and its length is returned, 0 for none. The same message
 * again gets the same reply and is not carried out a second time. */
uint32_t hrs_message(const uint8_t *in, uint32_t length, uint8_t *out);
/* What an answered LEAVE asked for; HRS_STAY when there was none. */
unsigned hrs_leaving(void);
/* Nothing was erased or written: the application is as it was. */
int hrs_untouched(void);
#endif
