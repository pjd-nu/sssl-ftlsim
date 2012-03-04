/*
 * file:        runsim.h
 * description: Generic FTL simulator interface for fast FTL simulator
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

/* note that the abstract runsim structure is defined in ftlsim.h 
 */
struct lru {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    struct lru_private *private_data;
};

struct lru *lru_new(int T, int U, int Np);
void lru_del(struct lru*);

struct greedy {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    int target_free;
    struct greedy_private *private_data;
};

struct greedy *greedy_new(int T, int U, int Np);
void greedy_del(struct greedy *g);

struct greedylru {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    int target_free, lru_max;
    struct greedylru_private *private_data;
};

struct greedylru *greedylru_new(int T, int U, int Np);
void greedylru_del(struct greedylru *g);

void runsim_stats_exit(struct runsim *sim, int n_valid, int blknum);
void runsim_stats_enter(struct runsim *sim, int blknum);
void runsim_stats_write(struct runsim *sim, int addr, int blknum, int pg);
