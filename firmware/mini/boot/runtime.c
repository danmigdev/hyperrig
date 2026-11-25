/* Minimal freestanding routines for compiler-generated structure copies. */
#include <stddef.h>
void *memcpy(void *destination, const void *source, size_t bytes)
{
    unsigned char *d = (unsigned char *)destination;
    const unsigned char *s = (const unsigned char *)source;
    size_t i;
    for (i = 0; i < bytes; ++i) d[i] = s[i];
    return destination;
}
void *memset(void *destination, int value, size_t bytes)
{
    unsigned char *d = (unsigned char *)destination;
    size_t i;
    for (i = 0; i < bytes; ++i) d[i] = (unsigned char)value;
    return destination;
}
