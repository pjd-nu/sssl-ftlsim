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
    struct getaddr *generator;
    struct lru_private *private_data;
};

struct lru *lru_new(int T, int U, int Np);
void lru_del(struct lru*);

struct greedy {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    int target_free;
    struct getaddr *generator;
    struct greedy_private *private_data;
};

struct greedy *greedy_new(int T, int U, int Np);
void greedy_del(struct greedy *g);

