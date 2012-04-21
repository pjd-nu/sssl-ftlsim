/*
 * file:        ftlsim.i
 * description: SWIG interface for multiple FTL simulation engines
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

%module ftlsim

%{
#define SWIG_FILE_WITH_INIT
#include "ftlsim.h"
%}

struct int_array {          /* kludge for indexed arrays */
    int val;
};

%extend int_array {
    struct int_array *__getitem__(int i) {
        return self + i;
    }
 }

struct segment {
    int  n_valid;
    struct int_array *lbas;
};

%extend segment {
    segment(int Np) {
        return segment_new(Np);
    }
    ~segment() {
        segment_del(self);
    }
    void write(int page, int lba) {
        do_segment_write(self, page, lba);
    }
    void overwrite(int page, int lba) {
        do_segment_overwrite(self, page, lba);
    }
}
    
typedef struct pool *(*write_selector_t)(struct ftl*, int lba);
write_selector_t write_select_first;
write_selector_t write_select_top_down;
write_selector_t write_select_python;

typedef struct pool *(*clean_selector_t)(struct ftl*);
clean_selector_t clean_select_first;
clean_selector_t clean_select_python;
void return_pool(struct pool *);

struct ftl {
    int int_writes, ext_writes;
    int nfree, minfree;
    write_selector_t get_input_pool;
    PyObject *get_input_pool_arg;
    clean_selector_t get_pool_to_clean;
    PyObject *get_pool_to_clean_arg;
};

%extend ftl {
    ftl(int T, int Np) {
        return ftl_new(T, Np);
    }
    void put_blk(struct segment *blk) {
        do_put_blk(self, blk);
    }
    struct segment *get_blk(void) {
        return do_get_blk(self);
    }
    struct segment *find_blk(int lba) {
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].block;
    }
    int find_page(int lba) {
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].page_num;
    }
    struct pool *frontier(int lba) {
        return self->get_input_pool(self, lba);
    }
    void run(struct getaddr *addrs, int count) {
        do_ftl_run(self, addrs, count);
    }
    ~ftl() {
        ftl_del(self);
    }
}

struct pool {
    struct segment *frontier;
    int i, pages_valid, pages_invalid;
    struct pool *next_pool;
    double rate;
};
%extend pool {
    pool(struct ftl *ftl, char *type, int Np) {
        if (!strcmp(type, "lru"))
            return lru_pool_new(ftl, Np);
        if (!strcmp(type, "greedy"))
            return greedy_pool_new(ftl, Np);
        return NULL;
    }
    void add_segment(struct segment *blk) {
        self->addseg(self, blk);
    }
    struct segment *remove_segment(void) {
        return self->getseg(self);
    }
    void write(int lba) {
        self->write(self->ftl, self, lba);
    }
    ~pool() {
        self->del(self);
    }
}

void srand(int seed);
int rand(void);
double ewma_rate;
