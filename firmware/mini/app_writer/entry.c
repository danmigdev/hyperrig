#include "writer.h"
extern uint8_t __slot_start[];
static hyw_pio controller;
static hyw_nor nor;
static uint32_t read32(void *u,uintptr_t a){(void)u;return *(volatile uint32_t *)a;}
static void write32(void *u,uintptr_t a,uint32_t v){(void)u;*(volatile uint32_t *)a=v;}
static void synchronize(void *u){(void)u;__asm__ volatile("csync" ::: "memory");}
static void settle(void *u,unsigned n){(void)u;while(n--)__asm__ volatile("nop" ::: "memory");}
static const hyw_pio_io io={0,read32,write32,synchronize,settle,32768};

__attribute__((section(".entry"),used))
int hyperrig_writer_entry(const hyw_services *services)
{
    /* Values observed by HYRX on this MINI. A mismatch returns before any
     * SPI initialization. No extra ROM address is read or dereferenced. */
    if(!services||(uintptr_t)services->send!=UINT32_C(0x01e008e4)||
       (uintptr_t)services->receive!=UINT32_C(0x01e0089a)||
       (uintptr_t)services->handler_slot!=UINT32_C(0x01c01264))return -1;
    hyw_pio_bind(&controller,&io,&nor,65536);
    return hyperrig_writer_initialize(services,&nor,(uint32_t)(uintptr_t)__slot_start);
}
