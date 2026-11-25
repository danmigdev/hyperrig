/* A cab IR that was just uploaded (IREND) is heard at once, as one that is loaded from a slot (ILOAD): the cab blocks that play the loaded IR are made
 * again from it. The application makes them again only for ILOAD of another slot, for another length and for a new block: until then a block that was
 * there went on with the IR before, also after ISAVE. The same steps as in ILOAD (ir_installation_load); a block with an IR of its own keeps it.
 * HyperRig code; the names of the application are those of firmware/ultrarig. No hardware test of this code has been made. */
#include <stdint.h>

enum { CHAINS = 2, BLOCKS = 10, CAB = 7 };

extern void audio_pause_pause_audio(void), audio_pause_resume_audio(void);
extern unsigned preset_application_chain_read(unsigned chain, uint8_t *order);
extern unsigned preset_application_effect_type(unsigned block);
extern int ir_effect_lifecycle_owns(unsigned block);
extern int ir_effect_lifecycle_refresh(unsigned block);

void hyperrig_ir_heard(void)
{
    uint8_t order[BLOCKS];
    unsigned chain, i, count;
    audio_pause_pause_audio();
    for (chain = 0; chain < CHAINS; ++chain) {
        count = preset_application_chain_read(chain, order);
        for (i = 0; i < count; ++i)
            if (preset_application_effect_type(order[i]) == CAB && !ir_effect_lifecycle_owns(order[i]))
                ir_effect_lifecycle_refresh(order[i]);
    }
    audio_pause_resume_audio();
}
