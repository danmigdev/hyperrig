/* The numbers of loudness.c. Made by tools/make_loudness_tables.py, which says where they come from: do not edit by hand. */
#define SHELF_B1 -1.75379527f
#define SHELF_B2 0.780956491f
#define SHELF_A1 -1.69114511f
#define SHELF_A2 0.732843059f
#define HIGH_A1 -1.99006336f
#define HIGH_A2 0.990088072f
#define ENERGY 5.23333099e-16f
enum { PAIRS = 6 };
TABLE static const int16_t halfband[PAIRS] = { 20763, -6352, 3191, -1714, 873, -377 };
