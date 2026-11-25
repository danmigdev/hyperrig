/* The numbers of harmonizer.c. Made by tools/make_harmonizer_tables.py, which says where they come from: do not edit by hand. */
enum { SCALES = 11, FIXED = 9, REFERENCE = 56899, UP = 69433, DOWN = 61858, LOUDER = 36766, SOFTER = 29205, STILL = 128,
       NEARLY = 38, QUIET = 450, RISE = 4, DEEP = 26, SURE = 13, KEEP = 64, CHANGE = 115, ONCE = 28,
       DOUBT = 8, PATIENCE = 18, HELD = 80, EARLY = 12, DUCK = 81, CHORD = 162, LOUDNESS = 80 };

/* a bit for each note of a scale */
static const uint16_t scales[SCALES] = {
    /* major */ 0xab5,
    /* minor */ 0x5ad,
    /* dorian */ 0x6ad,
    /* phrygian */ 0x5ab,
    /* lydian */ 0xad5,
    /* mixolydian */ 0x6b5,
    /* locrian */ 0x56b,
    /* harmonic minor */ 0x9ad,
    /* melodic minor */ 0xaad,
    /* fixed, major */ 0xab5,
    /* fixed, minor */ 0x5ad
};
TABLE static const int16_t quarter[24] = { 4, 8, -21, -117, -280, -402, -258, 418, 1748, 3550, 5317, 6417, 6417, 5317, 3550, 1748, 418, -258, -402, -280, -117, -21, 8, 4 };
