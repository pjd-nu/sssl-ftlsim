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

struct int_array {          /* kludge for indexed arrays */
    int val;
};

struct flash_block {
    struct flash_block *next, *prev;
    int  Np;
    int *lba;            /* lba[0..Np-1] = LBA / -1 */
    struct int_array *lbas;     /* alias for python indexed access */
    int  in_pool;        /* false if we're still the write frontier */
    int  n_valid;
    struct lru_pool *pool;
};

struct flash_block *flash_block_new(int Np);
void flash_block_del(struct flash_block *b);

struct rmap {
    struct flash_block *free_list;
    struct {
        struct flash_block *block;
        int    page_num;
    } *map;
    int T, Np;
    int int_writes, ext_writes;
};

struct rmap *rmap_new(int T, int Np);
void rmap_del(struct rmap*);

struct lru_pool {
    struct runsim handle;
    struct rmap *map;
    struct flash_block *frontier, *tail;
    int Np, int_writes, ext_writes, i;
    int pages_valid, pages_invalid;
    
};

struct lru_pool *lru_pool_new(struct rmap *map, int Np);
void lru_pool_del(struct lru_pool*);
void lru_pool_addseg(struct lru_pool*, struct flash_block *);
struct flash_block *lru_pool_getseg(struct lru_pool*);

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

struct fast {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    struct fast_private *private_data;
};

struct fast *fast_new(int T, int U, int Np);
void fast_del(struct fast *f);

void runsim_stats_exit(struct runsim *sim, int n_valid, int blknum);
void runsim_stats_enter(struct runsim *sim, int blknum);
void runsim_stats_write(struct runsim *sim, int addr, int blknum, int pg);
