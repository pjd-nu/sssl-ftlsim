/*
 * file:        newsim.i
 * description: SWIG interface for multiple FTL simulation engines
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

%module newsim

%{
#define SWIG_FILE_WITH_INIT
#include "newsim.h"
%}

struct int_array {          /* kludge for indexed arrays */
    int val;
};

%extend int_array {
    struct int_array *__getitem__(int i) {
        return self + i;
    }
 }

struct flash_block {
    int  n_valid;
    struct int_array *lbas;
};

%extend flash_block {
    flash_block(int Np) {
        return flash_block_new(Np);
    }
    ~flash_block() {
        flash_block_del(self);
    }
    void write(int page, int lba) {
        do_flash_block_write(self, page, lba);
    }
    void overwrite(int page, int lba) {
        do_flash_block_overwrite(self, page, lba);
    }
}
    
typedef struct pool *(*write_selector_t)(struct rmap* map, int lba);
write_selector_t write_select_first;
write_selector_t write_select_top_down;
write_selector_t write_select_python;

typedef struct pool *(*clean_selector_t)(struct rmap* map);
clean_selector_t clean_select_first;
clean_selector_t clean_select_python;
void return_pool(struct pool *);

struct rmap {
    int int_writes, ext_writes;
    int nfree, minfree;
    write_selector_t get_input_pool;
    PyObject *get_input_pool_arg;
    clean_selector_t get_pool_to_clean;
    PyObject *get_pool_to_clean_arg;
};

%extend rmap {
    rmap(int T, int Np) {
        return rmap_new(T, Np);
    }
    void xx(void) {
        printf("111\n");
        printf("%p\n", self->get_input_pool_arg);
        void *x = self->get_input_pool(self, 1);
        printf("%p\n", x);
    }
    struct flash_block *find_blk(int lba) {
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].block;
    }
    void put_blk(struct flash_block *blk) {
        do_put_blk(self, blk);
    }
    struct flash_block *get_blk(void) {
        return do_get_blk(self);
    }
    int find_page(int lba) {
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].page_num;
    }
    struct pool *frontier(int lba) {
        return self->get_input_pool(self, lba);
    }
    void run(struct getaddr *addrs, int count) {
        do_rmap_run(self, addrs, count);
    }
    ~rmap() {
        rmap_del(self);
    }
}

struct pool {
    struct flash_block *frontier;
    int i, pages_valid, pages_invalid;
    struct pool *next_pool;
    double rate;
};
%extend pool {
    pool(struct rmap *map, char *type, int Np) {
        if (!strcmp(type, "lru"))
            return lru_pool_new(map, Np);
        if (!strcmp(type, "greedy"))
            return greedy_pool_new(map, Np);
        return NULL;
    }
    void add_block(struct flash_block *blk) {
        self->addseg(self, blk);
    }
    struct flash_block *remove_block(void) {
        return self->getseg(self);
    }
    void write(int lba) {
        self->write(self->map, self, lba);
    }
    ~pool() {
        self->del(self);
    }
}

void srand(int seed);
int rand(void);
double ewma_rate;
