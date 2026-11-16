/* Reconstructed UltraRig M5.71 application dependencies, not original sources.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/PRESET_ASSETS_RECONSTRUCTION.md. */
#ifndef HYPERRIG_PRESET_ASSETS_H
#define HYPERRIG_PRESET_ASSETS_H

#include "hyperrig_preset_storage.h"

/* Probe J then I headers at the same wrapped slot address. Format is cleared
 * first and set to 1 only on J acceptance. Return 0/1; new -1 rejects invalid
 * API before calls/writes. Rejected/partial header reads remain visible. */
int hyperrig_asset_header(uint32_t slot, uint8_t header[40], uint32_t maximum,
                          uint32_t *format, const hyperrig_storage_io *io);

/* This sentinel/length test selects an extended identity, not a CRC check. */
int hyperrig_asset_extended(uint32_t marker, uint32_t size);
/* New status API: 0 writes the selected word; -1 rejects invalid pointers. */
int hyperrig_asset_identity(uint32_t marker, uint32_t size, const uint8_t tail[4],
                            uint32_t *result);

/* Original status 0 on success, -1 on trailer-read failure (output unchanged).
 * New -2 rejects invalid API. The header is read again after a successful read;
 * synchronous callback changes are therefore observed. No payload CRC check.
 * Slot/length/address arithmetic preserves uint32 wrapping, including signed
 * slot >=8 selection. The physical reader supplies range/error behavior. */
int hyperrig_asset_resolve(uint32_t slot, const uint8_t header[40], uint32_t *result,
                           const hyperrig_storage_io *io);

/* Pure dependencies of original application 0x020092fa. Mode is 1 when the
 * high bit of working[1347] is clear. Layout clears and fills 16 placement and
 * 12 branch bytes, handling legacy versions <=3. Return -1 for null pointers;
 * otherwise mode returns 0/1 and layout returns the new status 0. */
int hyperrig_asset_mode(const uint8_t working[1490]);
int hyperrig_asset_layout(const uint8_t working[1490], uint8_t placement[16],
                          uint8_t branches[12]);
/* Descriptor is 16 bytes: byte 0 present, byte 1 kind, words at 4/8/12.
 * Kind is compared as a full uint32 argument against byte 1. Return 0/1,
 * or new -1 for a null descriptor. */
int hyperrig_asset_matches(const uint8_t descriptor[16], uint32_t first,
                           uint32_t second, uint32_t third, uint32_t kind);
/* Boolean test of state word 416; no deeper ownership meaning is assigned. */
int hyperrig_asset_state416(const uint8_t state[1860]);
/* Interpret input as signed int32, clamp to [400,3000], return unsigned word. */
uint32_t hyperrig_asset_clamp(uint32_t value);

/* Buffers must be large enough and nonoverlapping. Read callbacks are borrowed
 * synchronously; no retained pointers, re-entry or interrupt concurrency.
 * These dependencies do not implement live DSP application or persistence. */
#endif
