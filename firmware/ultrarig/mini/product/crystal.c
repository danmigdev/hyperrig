/* The two capacitors of the crystal, which set the frequency of the radio. The radio's start asks for them (wifi_get_xosc) and puts
 * them into JL_ANA->WLA_CON12. JieLi's SDK answers with the product's own values, the first two bytes of the RF block of the
 * configuration file (item CFG_WIFI_RF_CFG_ID, 655, a RF_PARAM_CONFIG: apps/common/config/user_cfg.c and
 * include_lib/utils/syscfg/syscfg_id.h of fw-AC79_AIoT_SDK), unless a calibration is stored (item 106). The application answered
 * with what the register holds after a reset, 3 and 3, and never read that block: the TANK-MINI's file says 11 and 11. With 3 the
 * radio was off its frequency: a phone still connected, a computer's adapter was not heard at all. Tried on one pedal with one
 * adapter: no answer to it from 0 to 4, every time from 7 to 14. On that pedal the read gives the 31 bytes of the block. */
#include <stdint.h>

enum { RF_BLOCK = 655, RF_BYTES = 31, MOST = 15 };

int L02024a78(unsigned item, void *to, unsigned bytes);       /* the SDK's syscfg_read: the bytes read, or less than 1 */

/* xosc: the two values the application took from the register; replaced by the file's when it has them. */
void hyperrig_crystal(uint8_t *xosc)
{
    uint8_t rf[RF_BYTES];
    if (L02024a78(RF_BLOCK, rf, RF_BYTES) < 2 || rf[0] > MOST || rf[1] > MOST)
        return;
    xosc[0] = rf[0];
    xosc[1] = rf[1];
}
