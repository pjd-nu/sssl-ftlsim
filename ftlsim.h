/*
 * file:        ftlsim.h
 * description: Generic FTL simulator interface for fast FTL simulator
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

#include <Python.h>

struct int_array {          /* kludge for indexed arrays */
    int val;
};

struct segment {
    struct segment *next, *prev;
    int  Np;
    int *lba;            /* lba[0..Np-1] = LBA / -1 */
    struct int_array *lbas;     /* alias for python indexed access */
    int  in_pool;        /* false if we're still the write frontier */
    int  n_valid;
    struct pool *pool;
};

struct segment *segment_new(int Np);
void segment_del(struct segment *b);
void do_segment_write(struct segment *self, int page, int lba);
void do_segment_overwrite(struct segment *self, int page, int lba);

struct ftl;                    /* forward declaration */
typedef struct pool *(*write_selector_t)(struct ftl*, int lba);
extern write_selector_t write_select_first;
extern write_selector_t write_select_top_down;
extern write_selector_t write_select_python;
//PyObject *write_select_python_f;

typedef struct pool *(*clean_selector_t)(struct ftl*);
extern clean_selector_t clean_select_first;
extern clean_selector_t clean_select_python;
extern void return_pool(struct pool *);

struct ftl {
    struct segment *free_list;
    struct {
        struct segment *block;
        int    page_num;
    } *map;
    int T, Np;
    int int_writes, ext_writes;
    int nfree, minfree;
    int npools;
    struct pool *pools[10];
    write_selector_t get_input_pool;
    PyObject *get_input_pool_arg;
    clean_selector_t get_pool_to_clean;
    PyObject *get_pool_to_clean_arg;
    int write_seq;
};

struct getaddr;                 /* forward declaration */
struct ftl *ftl_new(int T, int Np);
void ftl_del(struct ftl*);
void do_put_blk(struct ftl *self, struct segment *blk);
struct segment *do_get_blk(struct ftl *self);
void do_ftl_run(struct ftl *ftl, struct getaddr *addrs, int count);

struct getaddr {
    int (*getaddr)(void *self);
    void (*del)(void *self);
    void *private_data;
};

struct pool {
    struct ftl *ftl;
    struct segment *frontier, *tail;
    int Np, int_writes, ext_writes, i;
    int pages_valid, pages_invalid;
    void (*addseg)(struct pool *self, struct segment *blk);
    struct segment * (*getseg)(struct pool *self);
    void (*write)(struct ftl*, struct pool*, int);
    void (*run)(struct pool*, struct getaddr*, int);
    void (*del)(struct pool*);
    double (*tail_utilization)(struct pool*);
    struct pool *next_pool;
    int last_write;
    double rate;
    struct segment *bins; /* for greedy - [i] has 'i' valid pages */
    int min_valid;
};

extern double ewma_rate;
struct pool *lru_pool_new(struct ftl *, int Np);
struct pool *greedy_pool_new(struct ftl *, int Np);
