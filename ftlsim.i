/*
 * file:        ftlsim.i
 * description: SWIG interface for multiple FTL simulation engines
 *
 * Peter Desnoyers, Northeastern University, 2012
 *
 * Copyright 2012 Peter Desnoyers
 * This file is part of ftlsim.
 * ftlsim is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version. 
 *
 * ftlsim is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details. 
 * You should have received a copy of the GNU General Public License
 * along with ftlsim. If not, see http://www.gnu.org/licenses/. 
 */

%module ftlsim

%{
#define SWIG_FILE_WITH_INIT
#include "ftlsim.h"
#undef assert
#define assert(x) {if (!(x)) *(volatile char*)0 = 0;}
%}

int total_writes;

struct segment {
    int  n_valid;
    int  blkno, elem;
    int  in_pool;
    int  erasures;
    struct pool *pool;
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
    void write_ftl(struct ftl *ftl, int page, int lba) {
        do_segment_write_ftl(self, ftl, page, lba);
    }
    void overwrite(int page, int lba) {
        do_segment_overwrite(self, page, lba);
    }
    int page(int _page) {
        return self->lba[_page];
    }
    void erase(void) {
        do_segment_erase(self);
    }
}

struct segment *get_segment(int n);

typedef struct pool *(*write_selector_t)(struct ftl*, int lba);
write_selector_t write_select_first;
write_selector_t write_select_top_down;
write_selector_t write_select_python;

typedef struct pool *(*clean_selector_t)(struct ftl*);
clean_selector_t clean_select_first;
clean_selector_t clean_select_python;
typedef struct segment *(*segment_selector_t)(struct ftl*);
segment_selector_t segment_select_python;

void return_pool(struct pool *);
void return_segment(struct segment *);

struct ftl {
    int int_writes, ext_writes;
    int nfree, minfree, maxfree;
    write_selector_t get_input_pool;
    PyObject *get_input_pool_arg;
    PyObject *get_next_pool_arg;
    clean_selector_t get_pool_to_clean;
    PyObject *get_pool_to_clean_arg;
    segment_selector_t get_segment_to_clean;
    PyObject *get_segment_to_clean_arg;
};

%extend ftl {
    ftl(int T, int Np) {
        err_occurred = 0;
        struct ftl *_f = ftl_new(T, Np);
        _f->get_input_pool = write_select_first;
        _f->get_pool_to_clean = clean_select_first;
        return _f;
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
    void write(int lba) {
        err_occurred = 0;
        do_ftl_write(self, lba);
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

struct bins {
};
%extend bins {
    bins(int n) {
	return do_bins_new(n);
    }
    ~bins() {
	do_bins_delete(self);
    }
    void insert(struct segment *s, int i) {
	do_bins_insert(self, s, i);
    }
    void remove(struct segment *s) {
	do_bins_remove(s);
    }
    struct segment *tail(int i) {
	return do_bins_tail(self, i);
    }
    int is_empty(int i) {
	return do_bins_empty(self, i);
    }
}


struct pool {
    struct segment *frontier;
    int i, pages_valid, pages_invalid, length;
    int invalidations, msr;
    struct pool *next_pool;
    double rate;
    PyObject *write_callback;
    PyObject *to_pool_callback;
};
%extend pool {
    pool(struct ftl *ftl, char *type, int Np) {
        err_occurred = 0;
        struct pool *p = NULL;
        if (!strcmp(type, "lru"))
            p = lru_pool_new(ftl, Np);
        if (!strcmp(type, "greedy"))
            p = greedy_pool_new(ftl, Np);
        if (!strcmp(type, "null"))
            p = null_pool_new(ftl, Np);
        if (p != NULL)
            p->next_pool = p;
        return p;
    }
    struct segment *next_segment(struct segment *s) {
        err_occurred = 0;
        return self->next_segment(self, s);
    }
    void add_segment(struct segment *blk) {
        err_occurred = 0;
        self->addseg(self, blk);
    }
    void insert_segment(struct segment *blk) {
        err_occurred = 0;
        self->insertseg(self, blk);
    }
    struct segment *get_segment(void) {
        err_occurred = 0;
        return self->getseg(self);
    }
    void *remove_segment(struct segment *seg) {
        err_occurred = 0;
        self->remove(self, seg);
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
