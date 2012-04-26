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
#undef assert
#define assert(x) {if (!(x)) *(char*)0 = 0;}
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
        err_occurred = 0;
        return ftl_new(T, Np);
    }
    void put_blk(struct segment *blk) {
        err_occurred = 0;
        do_put_blk(self, blk);
    }
    struct segment *get_blk(void) {
        err_occurred = 0;
        return do_get_blk(self);
    }
    struct segment *find_blk(int lba) {
        err_occurred = 0;
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].block;
    }
    int find_page(int lba) {
        err_occurred = 0;
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].page_num;
    }
    struct pool *frontier(int lba) {
        err_occurred = 0;
        return self->get_input_pool(self, lba);
    }
    void run(struct getaddr *addrs, int count) {
        err_occurred = 0;
        do_ftl_run(self, addrs, count);
    }
    ~ftl() {
        err_occurred = 0;
        ftl_del(self);
    }
}

%exception {
    $action
    if (err_occurred)
        return NULL;
}

struct pool {
    struct segment *frontier;
    int i, pages_valid, pages_invalid, length;
    struct pool *next_pool;
    double rate;
};
%extend pool {
    pool(struct ftl *ftl, char *type, int Np) {
        err_occurred = 0;
        if (!strcmp(type, "lru"))
            return lru_pool_new(ftl, Np);
        if (!strcmp(type, "greedy"))
            return greedy_pool_new(ftl, Np);
        return NULL;
    }
    struct segment *next_segment(struct segment *s) {
        err_occurred = 0;
        return self->next_segment(self, s);
    }
    void add_segment(struct segment *blk) {
        err_occurred = 0;
        self->addseg(self, blk);
    }
    struct segment *remove_segment(void) {
        err_occurred = 0;
        return self->getseg(self);
    }
    struct segment *tail_segment(void) {
        err_occurred = 0;
        return self->tail_segment(self);
    }
    double tail_util(void) {
        err_occurred = 0;
        return self->tail_utilization(self);
    }
    void write(int lba) {
        err_occurred = 0;
        self->write(self->ftl, self, lba);
    }
    ~pool() {
        err_occurred = 0;
        self->del(self);
    }
}

void srand(int seed);
int rand(void);
double ewma_rate;
