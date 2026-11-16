/* Reconstructed UltraRig M5.71 capture command, not original source code.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_COMMAND_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_COMMAND_H
#define HYPERRIG_CAPTURE_COMMAND_H
#include "hyperrig_capture_journal.h"
#include "hyperrig_capture_loader.h"

typedef struct {
    hyperrig_capture_journal_runtime journal;
    uint32_t error_word; /* Decimal conversion's original errno location. */
} hyperrig_capture_command_runtime;
enum {
    HYPERRIG_CAPTURE_COMMAND_ALLOCATE = 0x0203c15c,
    HYPERRIG_CAPTURE_COMMAND_FREE = 0x0203d218,
    HYPERRIG_CAPTURE_COMMAND_PRINT = 0x02007010,
    HYPERRIG_CAPTURE_COMMAND_REPORT = 0x0200a768
};
/* The synthetic allocator returns NULL or an independent writable allocation
 * of at least size bytes, borrowed until the exactly matching free call. */
typedef uint8_t *(*hyperrig_capture_command_allocate)(void *opaque, uint32_t size);
typedef void (*hyperrig_capture_command_free)(void *opaque, uint8_t *allocation);
/* Original argument words, never host addresses. PRINT receives a format token
 * followed by zero, one or two arguments. REPORT receives ten words: mode token,
 * slot, trim steps, auxiliary-present, auxiliary value, saved, show-journal,
 * journal cursor, journal capacity, rewrite flag. Signed fields use uint32 bits.
 * Formatting, transport and the report helper body remain external. */
typedef uint32_t (*hyperrig_capture_command_text)(void *opaque, uint32_t service,
    const uint32_t *words, uint32_t count);
typedef struct {
    hyperrig_capture_journal_io journal;
    hyperrig_capture_command_allocate allocate;
    hyperrig_capture_command_free release;
    hyperrig_capture_command_text text;
} hyperrig_capture_command_io;

/* Standalone parser helpers require disjoint buffers and a NUL terminator
 * within size (1..256).
 * Invalid API returns new -200 without writes. Tenths returns original 0/1 and
 * preserves output on rejection. Decimal returns 0 and produces the base-ten
 * value and end offset; overflow saturates and writes 34 to error_word.
 * Decimal uses the pinned C-locale character classification, not host locale. */
int hyperrig_capture_command_tenths(const uint8_t *text, uint32_t size, uint32_t *output);
int hyperrig_capture_command_decimal(const uint8_t *text, uint32_t size,
    uint32_t *output, uint32_t *end, uint32_t *error_word);
uint32_t hyperrig_capture_command_pack(uint32_t gain, uint32_t present, uint32_t auxiliary);

/* Complete original command 0x0200a888..0x0200ad06. Input is the argument tail
 * after CTRIM, not a complete wire command. Return 0 with the original terminal
 * text-service return word, or new -200 for invalid API before calls/writes.
 * New -201 frees an allocation and stops before an oversized reload payload
 * read; original firmware has no such bound. Output is preserved on this guard.
 * All storage/allocation/text callbacks are synthetic. They may synchronously
 * mutate only caller-owned runtime, preserving its sizes. Input, IO, private
 * stack data and program sources are immutable to callbacks; a read may write
 * only its destination. No overlapping buffers, retained pointers, re-entry,
 * concurrent mutation, physical writes or actual text transport are provided. */
int hyperrig_capture_command_execute(hyperrig_capture_command_runtime *runtime,
    const uint8_t *text, uint32_t size, uint32_t *output, const hyperrig_capture_command_io *io);
#endif
