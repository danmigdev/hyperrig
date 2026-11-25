/* The MIDI function of the USB port, beside the serial port of the editor. A part of midi.c: one unit is a good deal smaller than two.
 *
 * The application's USB device is JieLi's, with a list of up to eight functions (L01c26890 + 3376): the first is the serial port, on
 * endpoint 2 and the interfaces 0 and 1, and stays as it is. This is the second, when it is wanted: an audio control and a MIDI
 * streaming interface, as the class of USB-MIDI 1.0 has them, on endpoint 1, which is free. No computer needs a driver for it.
 *
 * In: the interrupt puts packets into a short row, and the main task takes them from there. When the row is full a packet stays in
 * the controller and the computer waits; nothing is lost, and a flood costs no more than the row in each turn.
 * Out: one packet in each turn, when the one before has left. Nothing waits for a computer that does not read.
 *
 * The USB port is the only way of the editor and of an update. So:
 * - without the setting nothing of this is in the descriptors, and they are the same bytes as ever;
 * - turned on from the console it is a trial: the link is restarted with it, and when the editor has not come back after TRIAL_MS,
 *   the link is restarted without it and the setting is off again;
 * - a computer that reads the description and does not take it within REFUSED_MS gets the link without it, until the cable was out.
 *
 * The descriptors are those of firmware/mini_stage/usb_midi.c (MIT, m-bootloader, Copyright (c) 2026 Julius Vitkauskas) with an
 * interface association before them. */

enum { USB = 0, ENDPOINT = 1, IN = 0x80, PACKET = 64, ROW = 8, FIRST = 2 };
enum { TRIAL_MS = 45000, REFUSED_MS = 15000, OUT_MS = 3000, ANSWER_TURNS = 20 };
enum { S_PRESENT = 1, S_CONFIGURED = 3, S_FUNCTIONS = 3376 };
enum { PORT_OFF, PORT_WAITING, PORT_ON, PORT_REFUSED };
enum { TX_CSR1 = 17, RX_CSR1 = 20, RX_COUNT1 = 22 };      /* registers of the controller, reached through the SIE window, by endpoint */
enum { READY = 1, FLUSH_RX = 0x10, KEEP_RX = 0x9b, STALL = 3, ACKNOWLEDGE = 0 };
#define CON0 (*(volatile uint32_t *)0x11800)
#define EP1_COUNT (*(volatile uint32_t *)0x1180c)
#define EP1_OFF (1u << 20)

extern volatile uint32_t L01c1fc4c[2];                    /* how deep each core is in the lock of the two */
extern void storage_coordination_irq_enter(void);         /* these three are in the RAM: too far for a call from the flash */
extern void storage_coordination_irq_leave(void);
extern uint32_t storage_platform_clock(void);
extern void L02005cb8(unsigned endpoint);                 /* usb_write_index */
extern unsigned L02001b94(unsigned reg);                  /* musb_read */
extern void L02005d1c(unsigned usb, unsigned endpoint, unsigned value);       /* usb_write_rxcsr */
extern void L02006af8(unsigned usb, unsigned endpoint, unsigned value);       /* usb_write_txcsr */
extern void sdk_usb_set_dma_taddr(unsigned usb, unsigned endpoint, const void *buffer);
extern void phase3_p4_usb_g_ep_config(unsigned usb, unsigned endpoint, unsigned interrupt, void *buffer);
extern void L0201c442(unsigned usb, unsigned endpoint, void (*handler)(void));
extern unsigned L0201c202(unsigned usb, unsigned interface, unsigned (*hook)(uint8_t *device, const uint8_t *request));
extern unsigned L0201c220(unsigned usb, unsigned interface, void (*hook)(void));
extern void L0201ba8a(uint8_t *device, const uint8_t *request, const void *data, unsigned size);      /* usb_set_data_payload */
extern void phase3_p4_usb_set_setup_phase(uint8_t *device, unsigned phase);
extern int phase3_p4_cdc_ready(void);
extern int link_and_print_link_pause(void);
extern void link_and_print_link_resume(int paused);
void hyperrig_usb_functions(void);

static const uint8_t function[100] = {
    8, 11, FIRST, 2, 1, 1, 0, 0,                   /* two interfaces that belong together */
    9, 4, FIRST, 0, 0, 1, 1, 0, 0,                 /* audio control */
    9, 0x24, 1, 0x00, 0x01, 9, 0, 1, FIRST + 1,
    9, 4, FIRST + 1, 0, 2, 1, 3, 0, 0,             /* MIDI streaming */
    7, 0x24, 1, 0x00, 0x01, 65, 0,
    6, 0x24, 2, 1, 1, 0,                           /* jacks */
    6, 0x24, 2, 2, 2, 0,
    9, 0x24, 3, 1, 3, 1, 2, 1, 0,
    9, 0x24, 3, 2, 4, 1, 1, 1, 0,
    9, 5, ENDPOINT, 2, PACKET, 0, 0, 0, 0,
    5, 0x25, 1, 1, 1,
    9, 5, IN | ENDPOINT, 2, PACKET, 0, 0, 0, 0,
    5, 0x25, 1, 1, 3
};

/* The controller writes past a full packet when receiving, so this one has room to spare. */
static uint8_t received[PACKET + 4] __attribute__((aligned(4)));
static uint8_t sending[PACKET] __attribute__((aligned(4)));

static struct {
    volatile uint32_t in, out;                            /* packets put into the row, and taken out of it */
    struct { uint32_t clock; uint8_t events[PACKET]; } packet[ROW];
} row;

static struct {
    uint32_t since, gone;                                 /* when this connection began; when the cable was last in */
    volatile uint8_t offered, fresh, described;           /* in the descriptors; a new connection; how often they were asked for */
    uint8_t wanted, refused, trial, restart, taken;
} port;

static void (*const volatile interrupts_off)(void) = storage_coordination_irq_enter;
static void (*const volatile interrupts_back)(void) = storage_coordination_irq_leave;
static uint32_t (*const volatile clock_now)(void) = storage_platform_clock;

static __attribute__((noinline)) void enter(void)
{
    uint32_t core;
    interrupts_off();
    __asm__ volatile("%0 = cnum" : "=r"(core));
    if (!L01c1fc4c[core]++)
        __asm__ volatile("lockset" ::: "memory");
    __asm__ volatile("csync" ::: "memory");
    L02005cb8(ENDPOINT);
}

static __attribute__((noinline)) void leave(void)
{
    uint32_t core;
    __asm__ volatile("csync" ::: "memory");
    __asm__ volatile("%0 = cnum" : "=r"(core));
    if (!--L01c1fc4c[core])
        __asm__ volatile("lockclr" ::: "memory");
    interrupts_back();
}

/* The packet in the controller, if there is one, into the row, if there is room. In the interrupt, and once in a turn for one that waited. */
static void take(void)
{
    unsigned csr, n, i;
    enter();
    csr = L02001b94(RX_CSR1);
    if (csr & READY && row.in - row.out < ROW) {
        uint8_t *to = row.packet[row.in % ROW].events;
        n = L02001b94(RX_COUNT1);
        __asm__ volatile("ssync" ::: "memory");
        for (i = 0; i < PACKET; ++i)
            to[i] = i < n ? received[i] : 0;              /* an event of nothing */
        row.packet[row.in % ROW].clock = clock_now();
        __asm__ volatile("csync" ::: "memory");
        ++row.in;
        L02005d1c(USB, ENDPOINT, (csr & KEEP_RX) | FLUSH_RX);
    }
    leave();
}

/* A reset of the bus: in the interrupt. */
static void bus_reset(void)
{
    phase3_p4_usb_g_ep_config(USB, IN | ENDPOINT, 0, sending);
    phase3_p4_usb_g_ep_config(USB, ENDPOINT, 1, received);
    L0201c442(USB, ENDPOINT, take);
    CON0 &= ~EP1_OFF;
}

/* What is asked of the two interfaces: they have one setting each, and nothing else. In the interrupt. */
static unsigned asked(uint8_t *device, const uint8_t *request)
{
    static const uint8_t zero[2];
    if (request[0] == 0x81 && !(request[1] & ~10))
        L0201ba8a(device, request, zero, 2);              /* the state, or which setting: as many bytes as are asked for */
    else
        phase3_p4_usb_set_setup_phase(device, request[0] == 0x01 && request[1] == 11 && !request[2] ? ACKNOWLEDGE : STALL);
    return 0;
}

/* Writes the function's descriptors, as the application's list asks: their length, and the first free interface moved on. In the interrupt. */
static unsigned describe(unsigned usb, uint8_t *to, unsigned *interface)
{
    unsigned i;
    for (i = 0; i < sizeof function; ++i)
        to[i] = function[i];
    L0201c202(usb, FIRST, asked);
    L0201c202(usb, FIRST + 1, asked);
    L0201c220(usb, FIRST, bus_reset);
    *interface += 2;
    port.described = port.described << 1 | 1;             /* 1 at the start of the device, more when a computer asks */
    return sizeof function;
}

/* The USB device starts, with the serial port in its list: the MIDI port after it, when it is wanted. */
void hyperrig_usb_functions(void)
{
    port.offered = port.wanted && !port.refused;
    port.described = 0;
    port.fresh = 1;
    if (port.offered)
        *(unsigned (*volatile *)(unsigned, uint8_t *, unsigned *))(L01c26890 + S_FUNCTIONS + 4) = describe;
}

/* From the console: the answer leaves before the port closes. */
static void port_ask(unsigned wanted)
{
    port.refused = 0;
    port.wanted = wanted;
    port.trial = wanted > port.offered;
    port.restart = wanted != port.offered ? ANSWER_TURNS : 0;
}

static unsigned state(void)
{
    return port.refused ? PORT_REFUSED : !port.offered ? PORT_OFF : L01c26890[S_CONFIGURED] ? PORT_ON : PORT_WAITING;
}

/* Once in each turn of the control scan, in the main task. S_CONFIGURED is set with S_PRESENT only. */
static void port_turn(uint32_t now)
{
    unsigned configured = L01c26890[S_CONFIGURED];
    if (port.fresh) {
        port.fresh = port.taken = 0;
        port.since = now;
    }
    if (L01c26890[S_PRESENT])
        port.gone = now;
    else {
        port.since = now;
        if (now - port.gone >= OUT_MS)
            port.refused = 0;                             /* the cable was out: the next connection is a new one */
    }
    if (port.restart) {
        if (--port.restart)
            return;
    } else {
        if (!port.offered)
            return;
        port.taken |= configured;
        if (configured && phase3_p4_cdc_ready())
            port.trial = 0;                               /* the editor is there, over the link that has it */
        if (now - port.since < (port.trial ? TRIAL_MS : REFUSED_MS) || (!port.trial && (port.taken || port.described < 2)))
            return;
        port.refused = 1;
        if (port.trial)
            port.trial = port.wanted = 0;
    }
    link_and_print_link_resume(link_and_print_link_pause());
}

/* Sends what is in the buffer. */
static void transmit(unsigned bytes)
{
    enter();
    sdk_usb_set_dma_taddr(USB, ENDPOINT, sending);
    EP1_COUNT = bytes;
    __asm__ volatile("csync" ::: "memory");
    L02006af8(USB, ENDPOINT, READY);
    leave();
}

/* The packet before has left. */
static unsigned is_free(void)
{
    unsigned csr;
    enter();
    csr = L02001b94(TX_CSR1);
    leave();
    return !(csr & READY);
}
