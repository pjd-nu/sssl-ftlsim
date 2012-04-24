/*
 * file:        ftlsim.c
 * description: Simple, fast multi-pool FTL simulator
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

#include <stdio.h>
#include <stdlib.h>
//#include <assert.h>
#include <Python.h>

#include "ftlsim.h"

#define assert(x) {if (!(x)) *(char*)0 = 0;}

static void list_add(struct segment *b, struct segment *list)
{
    b->next = list;
    b->prev = list->prev;
    list->prev->next = b;
    list->prev = b;
}

static void list_rm(struct segment *b)
{
    b->prev->next = b->next;
    b->next->prev = b->prev;
    b->next = b->prev = b;
}

static int list_empty(struct segment *b)
{
    return b->next == b;
}

static struct segment *list_pop(struct segment *list)
{
    struct segment *b = list->next;
    list_rm(b);
    return b;
}

struct segment *segment_new(int Np)
{
    int i;
    struct segment *fb = calloc(sizeof(*fb), 1);
    fb->magic = 0x5E65e65e;
    fb->Np = Np;
    fb->lba = calloc(Np * sizeof(int), 1);
    for (i = 0; i < Np; i++)
        fb->lba[i] = -1;
    fb->lbas = (void*)fb->lba;

    return fb;
}

void segment_del(struct segment *fb)
{
    fb->magic = 0;
    free(fb->lbas);
    free(fb);
}

void do_segment_write(struct segment *self, int page, int lba)
{
    assert(page < self->Np && page >= 0 && self->lba[page] == -1);
    self->lba[page] = lba;
    self->pool->ftl->map[lba].block = self;
    self->pool->ftl->map[lba].page_num = page;
    self->n_valid++;
}

void do_segment_overwrite(struct segment *self, int page, int lba)
{
    assert(page < self->Np && page >= 0 && self->lba[page] == lba);
    self->lba[page] = -1;
    self->n_valid--;
    if (self->pool && self->in_pool) {
        self->pool->pages_valid--;
        self->pool->pages_invalid++;

        if (self->pool->bins) {
            list_rm(self);
            list_add(self, &self->pool->bins[self->n_valid]);
            if (self->n_valid < self->pool->min_valid)
                self->pool->min_valid = self->n_valid;
        }
        
        /* minor inaccuracy here - we don't count over-writes while
         * still on the write frontier. 
         */
        for (; self->pool->last_write < self->pool->ftl->write_seq; self->pool->last_write++)
            self->pool->rate *= ewma_rate;
        self->pool->rate += (1-ewma_rate);
    }
}

struct ftl *ftl_new(int T, int Np)
{
    struct ftl *ftl = calloc(sizeof(*ftl), 1);
    ftl->magic = 0xFff77711;
    ftl->T = T;
    ftl->Np = Np;
    ftl->map = calloc(sizeof(*ftl->map)*T*Np, 1);

    return ftl;
}

void ftl_del(struct ftl *ftl)
{
    struct segment *b;
    ftl->magic = 0;
    while ((b = do_get_blk(ftl)) != NULL)
        segment_del(b);
    free(ftl->map);
    free(ftl);
}

void do_put_blk(struct ftl *self, struct segment *blk)
{
    blk->next = self->free_list;
    self->free_list = blk;
    self->nfree++;
}

struct segment *do_get_blk(struct ftl *self)
{
    struct segment *val = self->free_list;
    if (val != NULL) {
        self->free_list = val->next;
        self->nfree--;
    }
    return val;
}

static void check_new_segment(struct ftl *ftl, struct pool *pool)
{
    assert(pool->i <= pool->Np);
    if (pool->i >= pool->Np) {
        struct segment *b = do_get_blk(ftl);
        pool->addseg(pool, b);
    }
}

void do_ftl_run(struct ftl *ftl, struct getaddr *addrs, int count)
{
    int i, j;
    for (i = 0; i < count; i++) {
        int lba = addrs->getaddr(addrs);
        if (lba == -1)
            return;
        assert(lba >= 0 && lba < ftl->T * ftl->Np);
        struct pool *pool = ftl->get_input_pool(ftl, lba);
        if (pool == NULL)
            return;
        ftl->ext_writes++;
        ftl->write_seq++;

        pool->write(ftl, pool, lba);
        check_new_segment(ftl, pool);

        while (ftl->nfree < ftl->minfree) {
            pool = ftl->get_pool_to_clean(ftl);
            struct segment *b = pool->getseg(pool);
            struct pool *next = pool->next_pool;
            if (pool == NULL)
                return;

            for (j = 0; j < b->Np; j++)
                if (b->lba[j] != -1) {
                    next->write(ftl, next, b->lba[j]);
                    check_new_segment(ftl, next);
                }
            do_put_blk(ftl, b);
        }

#if 0 /* only works for LRU */
        for (j = 0; j < ftl->npools; j++) {
            int nv = 0, ni = 0;
            struct segment *s;
            for (s = ftl->pools[j]->frontier; s != NULL; s = s->next)
                if (s->in_pool) {
                    nv += s->n_valid;
                    ni += (s->Np - s->n_valid);
                }
            assert(nv == ftl->pools[j]->pages_valid);
            assert(ni == ftl->pools[j]->pages_invalid);
        }
#endif
    }
}

/* cleaning - grab the tail of the pool. the caller of this function
 * is responsible for copying the remaining valid pages.
 */
struct segment *lru_pool_getseg(struct pool *pool)
{
    assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);
    assert(pool->tail != NULL && pool->tail != pool->frontier);
    struct segment *val = pool->tail;
    assert(val->in_pool);
    assert(val->pool == pool);
    
    pool->tail = val->prev;
    if (pool->tail != NULL)
        pool->tail->next = NULL;
    val->in_pool = 0;

    pool->pages_valid -= val->n_valid;
    pool->pages_invalid -= (pool->Np - val->n_valid);
    assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);

    val->pool = NULL;
    
    return val;
}

double lru_tail_utilization(struct pool *pool)
{
    if (pool->tail == NULL || pool->tail == pool->frontier)
        return 1.0;
    return (double)pool->tail->n_valid / (double)pool->tail->Np;
}

/* After the current write frontier fills, call this function to move
 * it to the pool and provide a new write frontier.
 */
void lru_pool_addseg(struct pool *pool, struct segment *fb)
{
    assert(pool->frontier == NULL || pool->i == pool->Np);
    assert(fb->in_pool == 0);

    fb->pool = pool;

    pool->i = 0;                /* page pointer for new block */

    fb->prev = NULL;            /* link onto head of dbl linked list */
    fb->next = pool->frontier;
    if (pool->frontier != NULL) {
        pool->frontier->in_pool = 1; /* old frontier is now in pool */
        pool->frontier->prev = fb;
        pool->pages_valid += pool->frontier->n_valid;
        pool->pages_invalid += (pool->Np - pool->frontier->n_valid);
        assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);
    }
    pool->frontier = fb;

    if (pool->tail == NULL)     /* handle initial case */
        pool->tail = fb;
    
}

void lru_pool_del(struct pool *pool)
{
    pool->magic = 0;
    free(pool);
}
double ewma_rate = 0.95;

static void lru_int_write(struct ftl *ftl, struct pool *pool, int lba)
{
    assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);
    ftl->int_writes++;
    struct segment *b = ftl->map[lba].block;
    int page = ftl->map[lba].page_num;
    if (b != NULL) 
        do_segment_overwrite(b, page, lba);
    do_segment_write(pool->frontier, pool->i++, lba);
    assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);
}

struct segment *lru_next_seg(struct pool *pool, struct segment *prev)
{
    if (prev == NULL)
        prev = pool->frontier;
    return prev->next;
}

struct pool *lru_pool_new(struct ftl *ftl, int Np)
{
    struct pool *val = calloc(sizeof(*val), 1);
    val->magic = 0x60016001;
    
    val->ftl = ftl;
    val->Np = Np;

    int i = ftl->npools++;
    ftl->pools[i] = val;

    val->addseg = lru_pool_addseg;
    val->getseg = lru_pool_getseg;
    val->write = lru_int_write;
    val->del = lru_pool_del;
    val->tail_utilization = lru_tail_utilization;
    val->next_segment = lru_next_seg;
    
    return val;
}

static int greedy_tail_n_valid(struct pool *pool)
{
    int i;
    for (i = pool->min_valid; i < pool->Np; i++)
        if (!list_empty(&pool->bins[i]))
            break;
    pool->min_valid = i;
    return i;
}

static double greedy_tail_utilization(struct pool *pool)
{
    return (double)greedy_tail_n_valid(pool) / (double)pool->Np;
}

static struct segment *greedy_pool_getseg(struct pool *pool)
{
    int i = greedy_tail_n_valid(pool);
    assert(i < pool->Np);
    struct segment *b = list_pop(&pool->bins[i]);
    b->in_pool = 0;

    pool->pages_valid -= b->n_valid;
    pool->pages_invalid -= (pool->Np - b->n_valid);
    assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);
    b->pool = NULL;
    return b;
}

static void greedy_pool_addseg(struct pool *pool, struct segment *fb)
{
    assert(pool->frontier == NULL || pool->i == pool->Np);
    assert(fb->in_pool == 0);

    pool->i = 0;                /* page pointer for new block */

    struct segment *blk = pool->frontier;
    if (blk != NULL) {
        pool->frontier->in_pool = 1; /* old frontier is now in pool */
        pool->pages_valid += pool->frontier->n_valid;
        pool->pages_invalid += (pool->Np - pool->frontier->n_valid);
        assert(pool->pages_valid >= 0 && pool->pages_invalid >= 0);

        list_add(blk, &pool->bins[blk->n_valid]);
        if (blk->n_valid < pool->min_valid)
            pool->min_valid = blk->n_valid;
    }

    pool->frontier = fb;
    fb->pool = pool;
}

static void greedy_int_write(struct ftl *ftl, struct pool *pool, int lba)
{
    ftl->int_writes++;
    struct segment *b = ftl->map[lba].block;
    int page = ftl->map[lba].page_num;
    if (b != NULL) {
        do_segment_overwrite(b, page, lba);
    }
    
    do_segment_write(pool->frontier, pool->i++, lba);
}

static void greedy_pool_del(struct pool *pool)
{
    pool->magic = 0;
    free(pool->bins);
    free(pool);
}

struct segment *greedy_next_seg(struct pool *pool, struct segment *prev)
{
    if (prev == NULL)
        prev = &pool->bins[0];
    if (prev->next == &pool->bins[pool->Np])
        return NULL;
    if (prev->lba == NULL) {    /* it's a bin */
        if (list_empty(prev))
            return greedy_next_seg(pool, prev+1);
        else
            return prev->next;
    }
    if (prev->next->lba == NULL)
        return greedy_next_seg(pool, prev->next+1);
    return prev->next;
}

struct pool *greedy_pool_new(struct ftl *ftl, int Np)
{
    struct pool *pool = calloc(sizeof(*pool), 1);
    pool->magic = 0x60016002;
    pool->ftl = ftl;
    pool->Np = Np;

    int i = ftl->npools++;
    ftl->pools[i] = pool;

    pool->bins = calloc((Np+1) * sizeof(*pool->bins), 1);
    for (i = 0; i <= Np; i++)
        pool->bins[i].next = pool->bins[i].prev = &pool->bins[i];
    
    pool->addseg = greedy_pool_addseg;
    pool->getseg = greedy_pool_getseg;
    pool->write = greedy_int_write;
    pool->del = greedy_pool_del;
    pool->tail_utilization = greedy_tail_utilization;
    pool->next_segment = greedy_next_seg;
    
    return pool;
}

static struct pool *do_select_first(struct ftl* ftl, int lba)
{
    return ftl->pools[0];
}

static struct pool *do_select_top_down(struct ftl* ftl, int lba)
{
    return NULL;
}

struct pool *pool_retval;
void return_pool(struct pool *pool)
{
    pool_retval = pool;
}

static struct pool *python_select_1_arg(struct ftl *ftl, int lba)
{
    PyObject *args = Py_BuildValue("(i)", lba);
    PyObject *result = PyEval_CallObject(ftl->get_input_pool_arg, args);
    if (PyErr_Occurred()) 
        PyErr_Print();
    if (result != NULL) {
        Py_DECREF(result);
    }
    Py_DECREF(args);
    return pool_retval;
}

write_selector_t write_select_first = do_select_first;
write_selector_t write_select_top_down = do_select_top_down;
write_selector_t write_select_python = python_select_1_arg;

static struct pool *do_clean_select_first(struct ftl *ftl)
{
    return ftl->pools[0];
}
clean_selector_t clean_select_first = do_clean_select_first;

static struct pool *python_select_no_arg(struct ftl *ftl)
{
    PyObject *args = Py_BuildValue("()");
    PyObject *result = PyEval_CallObject(ftl->get_pool_to_clean_arg, args);
    if (PyErr_Occurred()) 
        PyErr_Print();
    if (result != NULL) {
        Py_DECREF(result);
    }
    return pool_retval;
}

clean_selector_t clean_select_python = python_select_no_arg;
