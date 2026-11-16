/* Reconstructed UltraRig M5.71 native capture parser, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_PARSER_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_PARSER_H
#define HYPERRIG_CAPTURE_PARSER_H
#include <stdint.h>

/* Original address tokens map to writable arena storage. Mapping must be pure,
 * consistent, and valid throughout the call. Context, ledger, source, IO and
 * mapped arena storage must be disjoint. No concurrent mutations are supported.
 * A zero arena token makes an allocation query; it still changes context and
 * ledger exactly as the original parser does. */
typedef uint8_t *(*hyperrig_capture_parser_map)(void *opaque, uint32_t address, uint32_t size);
typedef struct {
    hyperrig_capture_parser_map map;
    void *opaque;
} hyperrig_capture_parser_io;

/* Execute the complete 0x02031c64 parser and its 0x01c127de read64 dependency.
 * Context is the original 228-byte layout; ledger is {arena_token,used,capacity}.
 * Configuration supplies the original word at 0x01c1fa18 without assigning
 * a physical meaning. Preserve its uint32 value, including UINT32_MAX.
 * Original results are 0/-1/-2/-3/-4. Partial context, ledger and arena writes
 * survive errors; capacity exhaustion records null pointers and advances used,
 * so a zero parser result does not prove the arena was sufficient.
 * New -200 rejects invalid API arguments; -201 rejects an unmapped allocation
 * before its host access. Source contains exactly length initialized bytes.
 * Original arithmetic wraps uint32; generated pointers remain integer tokens.
 * This does not initialize/reset history or execute capture audio. */
int hyperrig_capture_parser(uint8_t context[228], uint32_t ledger[3],
    const uint8_t *source, uint32_t length, uint32_t configuration,
    const hyperrig_capture_parser_io *io);
#endif
