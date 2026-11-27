/* HyperRig's part of the Bluetooth link.
 *
 * Which words. The application lets a line that came over Bluetooth by when its word is in one of its two lists: the words
 * that only read, for anyone who is connected, and the words that change something, for a phone that is paired or a computer
 * that showed the pedal's key (AUTH). Any other word is answered "usb only", and so was every word of HyperRig's own: an
 * editor over Bluetooth could not even ask which build it talks to (HRID). They are sorted here as the application sorts its
 * own: a word by itself that only reads, always; a word with something after it, with the key. The words of the trials,
 * STAGE and what the application keeps to the cable stay with the cable.
 *
 * A link that nobody ends. A computer may keep the link after its program has disconnected and closed (a Windows computer
 * did). The pedal then does not advertise, and nothing can connect to it, that computer included. So the pedal
 * ends a link on which no line has come for SILENT milliseconds (an editor asks all the time, and says PING when it has
 * nothing to ask), and at once when the editor says HRBYE, which it does before it disconnects.
 *
 * The minute for letting a device in. After A and B were held, the pedal gives its key or pairs for one minute, and its lights
 * pulse blue for as long. The application ends the minute when it has given a key; a computer that had the key already, or a
 * phone that was paired before, left the lights blue for the whole minute though it was in. The minute ends here as soon as
 * the link that came is one the pedal takes changes from: the lights go back to what they show, and nobody else is let in for
 * what was left of it. A device that is in can still open the minute for another one: only becoming one that is in ends it. */
#include <stdint.h>

enum { SILENT = 90000, LINK = 82, MINUTE = 1532 };        /* a hidden page's timers may run once a minute */

extern uint8_t L01c26890[];                               /* the application's state: the link's handle at LINK (0 without a link), */
                                                          /* and at MINUTE whether the minute for letting a device in is running */
void console_helpers_ble_drop(unsigned handle);           /* ends the link, as the application does when Bluetooth is turned off */
int console_helpers_key_window(void);                     /* whether the pedal takes changes from the link: it showed the key, or is paired */

static struct {
    uint32_t heard;                                       /* when the last line came, or when the link was first seen */
    uint16_t link;
    uint8_t fresh, bye, in;                               /* in: the link was one the pedal takes changes from, at the last turn */
} air;

/* 0 the line does not begin with the word; 1 it is the word by itself; 2 the word, a space and more. */
static int word_is(const char *line, const char *word)
{
    while (*word && *line == *word)
        ++line, ++word;
    if (*word)
        return 0;
    return !*line ? 1 : *line == ' ' ? 2 : 0;
}

static int one_of(const char *line, const char *words, int how)      /* words: each ends with a zero, the list with another */
{
    while (*words) {
        if (word_is(line, words) == how)
            return 1;
        while (*words++)
            ;
    }
    return 0;
}

/* A line came over Bluetooth whose word the application does not have in its lists. 0: it is not one of these either, and the
 * answer stays "usb only"; 1: with the key only; 2: always. */
int hyperrig_air(const char *line)
{
    if (one_of(line, "HRID\0HRST\0HRBYE\0AMPK\0MIDI\0KNOB\0HRLV\0SNAPCAP\0", 1))
        return 2;
    if (one_of(line, "MIDI\0KNOB\0HRLV\0FXC\0SNAPCAP\0", 2))
        return 1;
    return 0;
}

/* A whole line came over Bluetooth, whatever becomes of it. */
void hyperrig_air_heard(void)
{
    air.fresh = 1;
}

/* HRBYE: the editor is about to disconnect. The link is ended in the next turn, after the answer. */
void hyperrig_air_bye(void)
{
    air.bye = 1;
}

/* Once in each turn of the control scan; now in milliseconds. */
void hyperrig_air_turn(uint32_t now)
{
    unsigned link = L01c26890[LINK] | (unsigned)L01c26890[LINK + 1] << 8, in;
    if (!link) {
        air.link = 0;
        air.fresh = air.bye = air.in = 0;
        return;
    }
    if (link != air.link)
        air.in = 0;
    in = console_helpers_key_window() != 0;
    if (in && !air.in)
        L01c26890[MINUTE] = 0;                            /* it has just become a device that is in: the minute is over */
    air.in = (uint8_t)in;
    if (link != air.link || air.fresh) {
        air.link = (uint16_t)link;
        air.heard = now;
        air.fresh = 0;
    }
    if (air.bye || now - air.heard >= SILENT) {
        air.bye = 0;
        air.heard = now;                                  /* and again after as long, should the link not end */
        console_helpers_ble_drop(link);
    }
}
