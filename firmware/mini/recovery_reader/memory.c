#include <stddef.h>

/* Local implementation for compiler-generated structure copies. ROM entry
 * supplies no libc ABI; do not resolve helpers to guessed ROM addresses. */
void *memcpy(void *destination, const void *source, size_t bytes)
{
    unsigned char *out = destination;
    const unsigned char *in = source;
    size_t i;
    for (i = 0; i < bytes; ++i) out[i] = in[i];
    return destination;
}
