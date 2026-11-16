/* Reconstructed UltraRig M5.71 capture installation, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/CAPTURE_CONTAINER_RECONSTRUCTION.md. */
#ifndef HYPERRIG_CAPTURE_CONTAINER_H
#define HYPERRIG_CAPTURE_CONTAINER_H
#include "hyperrig_capture_loader.h"

enum {
    HYPERRIG_CAPTURE_READER = 0x0201acd8,
    HYPERRIG_CAPTURE_EMBEDDED = 0x02033c8c,
    HYPERRIG_CAPTURE_ALLOCATE = 0x0203c15c,
    HYPERRIG_CAPTURE_FREE = 0x0203d218,
    HYPERRIG_CAPTURE_GATE = 0x02002d06,
    HYPERRIG_CAPTURE_MODE = 0x020051fc,
    HYPERRIG_CAPTURE_PRIORITY_GET = 0x02040850,
    HYPERRIG_CAPTURE_PRIORITY_SET = 0x020408d6,
    HYPERRIG_CAPTURE_PROBE = 0x01c04a7a,
    HYPERRIG_CAPTURE_COMPACT = 0x020083d6,
    HYPERRIG_CAPTURE_PREPARE = 0x020025ca,
    HYPERRIG_CAPTURE_PROCESS_LOAD = 0x01c04a8e,
    HYPERRIG_CAPTURE_CAPABILITIES = 0x01c04bac,
    HYPERRIG_CAPTURE_CLEANUP = 0x02002634
};

typedef struct {
    hyperrig_preset_storage storage;
    uint8_t kind_word[4]; /* Original state+4120, an opaque probe result. */
} hyperrig_capture_container_runtime;

typedef uint32_t (*hyperrig_capture_container_service)(void *opaque,
    uint32_t service, uint32_t a, uint32_t b, uint32_t c, uint32_t d);
/* Pure host mapping of original uint32 address tokens, not a firmware service.
 * Return NULL for an unmapped/insufficient range. Mappings must be consistent,
 * disjoint from runtime/request storage, and valid until the operation returns.
 * Embedded bytes are read-only. Successful allocations map at least the exact
 * aligned allocation request. A free callback observes ownership; it must not
 * destroy buffers still reachable under this API's synchronous test contract. */
typedef uint8_t *(*hyperrig_capture_container_map)(void *opaque, uint32_t address,
    uint32_t size, uint32_t writable);
typedef struct {
    hyperrig_capture_container_service call;
    hyperrig_storage_read read;
    hyperrig_capture_container_map map;
    hyperrig_capture_metadata metadata;
    void *opaque;
} hyperrig_capture_container_io;

/* Recover the actual 0x0201acd8 reader: record/CRC, size/header identity checks,
 * then extended identity validation/update. Maximum record payload is 8152.
 * New -200 rejects invalid API; -201 rejects a payload beyond capacity or a
 * failed address mapping before that memory access. Other statuses are original.
 * Request contains 17 initialized bytes as defined by the capture loader. */
int hyperrig_capture_container_read(uint32_t destination, uint32_t capacity,
    uint8_t request[17], const hyperrig_capture_container_io *io);

/* Original container orchestration. Size accepts 1..8192. Loader must be zero
 * or HYPERRIG_CAPTURE_READER; that callback executes internally. The source,
 * context, allocation and cached pointers are opaque uint32 address tokens.
 * Probe, compaction, preparation, DSP load, capability query, cleanup, mode,
 * priority and allocator bodies remain external. Capability output pointers
 * refer to unused private stack bytes, so the service exposes no semantic args.
 * Callbacks may mutate runtime and mapped writable bytes synchronously; no
 * re-entry, concurrency, retained private pointers or IO-structure mutation.
 * New invalid-API/mapping statuses are -200/-201. Firmware status passes through. */
int hyperrig_capture_container_install(hyperrig_capture_container_runtime *runtime,
    uint32_t source, uint32_t size, uint32_t loader, uint8_t request[17],
    const hyperrig_capture_container_io *io);

/* Connect the unchanged slot loader to this installer and reader. Metadata
 * lookup remains the supplied callback; no flash writing or real allocation. */
int hyperrig_capture_container_slot(hyperrig_capture_container_runtime *runtime,
    uint32_t slot, const hyperrig_capture_container_io *io);
#endif
