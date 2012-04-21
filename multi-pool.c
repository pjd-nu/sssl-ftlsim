/*
 * file:        runsim_pool.c
 * description: Simple, fast multi-pool FTL simulator
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <Python.h>

#include "newsim.h"

struct flash_block *flash_block_new(int Np)
{
    int i;
    struct flash_block *fb = calloc(sizeof(*fb), 1);
    fb->Np = Np;
    fb->lba = calloc(Np * sizeof(int), 1);
    for (i = 0; i < Np; i++)
        fb->lba[i] = -1;
    fb->lbas = (void*)fb->lba;

    return fb;
}

void flash_block_del(struct flash_block *fb)
{
    free(fb->lbas);
    free(fb);
}

void do_flash_block_write(struct flash_block *self, int page, int lba)
{
    assert(page < self->Np && page >= 0 && self->lba[page] == -1);
    self->lba[page] = lba;
    self->pool->map->map[lba].block = self;
    self->pool->map->map[lba].page_num = page;
    self->n_valid++;
}

void do_flash_block_overwrite(struct flash_block *self, int page, int lba)
{
    assert(page < self->Np && page >= 0 && self->lba[page] == lba);
    self->lba[page] = -1;
    self->n_valid--;
    if (self->pool)
        self->pool->pages_valid--;
}

struct rmap *rmap_new(int T, int Np)
{
    struct rmap *rmap = calloc(sizeof(*rmap), 1);
    rmap->T = T;
    rmap->Np = Np;
    rmap->map = calloc(sizeof(*rmap->map)*T*Np, 1);

    return rmap;
}

void rmap_del(struct rmap *rmap)
{
    struct flash_block *b;
    while ((b = do_get_blk(rmap)) != NULL)
        flash_block_del(b);
    free(rmap->map);
    free(rmap);
}

void do_put_blk(struct rmap *self, struct flash_block *blk)
{
    blk->next = self->free_list;
    self->free_list = blk;
    self->nfree++;
}

struct flash_block *do_get_blk(struct rmap *self)
{
    struct flash_block *val = self->free_list;
    if (val != NULL) {
        self->free_list = val->next;
        self->nfree--;
    }
    return val;
}

void do_rmap_run(struct rmap *rmap, struct getaddr *addrs, int count)
{
    int i, j;
    for (i = 0; i < count; i++) {
        int lba = addrs->getaddr(addrs);
        if (lba == -1)
            return;
        struct pool *pool = rmap->get_input_pool(rmap, lba);
        if (pool == NULL)
            return;
        rmap->ext_writes++;
        rmap->write_seq++;
        for (; pool->last_write < rmap->write_seq; pool->last_write++)
            pool->rate *= ewma_rate;
        pool->rate += (1-ewma_rate);
        
        pool->write(rmap, pool, lba);
        while (rmap->nfree < rmap->minfree) {
            pool = rmap->get_pool_to_clean(rmap);
            struct flash_block *b = pool->getseg(pool);
            struct pool *next = pool->next_pool;
            if (pool == NULL)
                return;
            for (j = 0; j < b->Np; j++)
                if (b->lba[j] != -1) 
                    next->write(rmap, next, b->lba[j]);
            do_put_blk(rmap, b);
        }
    }
}

/* cleaning - grab the tail of the pool. the caller of this function
 * is responsible for copying the remaining valid pages.
 */
struct flash_block *lru_pool_getseg(struct pool *pool)
{
    assert(pool->tail != NULL);
    struct flash_block *val = pool->tail;
    pool->tail = val->prev;
    pool->tail->next = NULL;
    val->in_pool = 0;

    pool->pages_valid -= val->n_valid;
    pool->pages_invalid -= (pool->Np - val->n_valid);

    val->pool = NULL;
    
    return val;
}

double lru_tail_utilization(struct pool *pool)
{
    if (pool->tail == NULL)
        return 0.0;
    return (double)pool->tail->n_valid / (double)pool->tail->Np;
}

/* After the current write frontier fills, call this function to move
 * it to the pool and provide a new write frontier.
 */
void lru_pool_addseg(struct pool *pool, struct flash_block *fb)
{
    assert(pool->i == pool->Np);
    assert(fb->n_valid == 0 && fb->in_pool == 0);

    pool->i = 0;                /* page pointer for new block */

    fb->prev = NULL;            /* link onto head of dbl linked list */
    fb->next = pool->frontier;
    if (pool->frontier != NULL) {
        pool->frontier->in_pool = 1; /* old frontier is now in pool */
        pool->frontier->prev = fb;
        pool->pages_valid += pool->frontier->n_valid;
        pool->pages_invalid += (pool->Np - pool->frontier->n_valid);
    }
    pool->frontier = fb;

    if (pool->tail == NULL)     /* handle initial case */
        pool->tail = fb;
    
    fb->pool = pool;
}

void lru_pool_del(struct pool *pool)
{
    free(pool);
}
double ewma_rate = 0.95;

static void lru_int_write(struct rmap *rmap, struct pool *pool, int lba)
{
    rmap->int_writes++;
    struct flash_block *b = rmap->map[lba].block;
    int page = rmap->map[lba].page_num;
    if (b != NULL) 
        do_flash_block_overwrite(b, page, lba);
    do_flash_block_write(pool->frontier, pool->i++, lba);
    if (pool->i >= pool->Np) {
        b = do_get_blk(rmap);
        lru_pool_addseg(pool, b);
    }
}

struct pool *lru_pool_new(struct rmap *map, int Np)
{
    struct pool *val = calloc(sizeof(*val), 1);
    val->map = map;
    val->Np = Np;

    int i = map->npools++;
    map->pools[i] = val;

    val->addseg = lru_pool_addseg;
    val->getseg = lru_pool_getseg;
    val->write = lru_int_write;
    val->del = lru_pool_del;
    val->tail_utilization = lru_tail_utilization;
    
    return val;
}

static void list_add(struct flash_block *b, struct flash_block *list)
{
    b->next = list;
    b->prev = list->prev;
    list->prev->next = b;
    list->prev = b;
}

static void list_rm(struct flash_block *b)
{
    b->prev->next = b->next;
    b->next->prev = b->prev;
    b->next = b->prev = b;
}

static int list_empty(struct flash_block *b)
{
    return b->next == b;
}

static struct flash_block *list_pop(struct flash_block *list)
{
    struct flash_block *b = list->next;
    list_rm(b);
    return b;
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

static struct flash_block *greedy_pool_getseg(struct pool *pool)
{
    int i = greedy_tail_n_valid(pool);
    assert(i < pool->Np);
    struct flash_block *b = list_pop(&pool->bins[i]);
    b->in_pool = 0;

    pool->pages_valid -= b->n_valid;
    pool->pages_invalid -= (pool->Np - b->n_valid);
    b->pool = NULL;
    return b;
}

static void greedy_pool_addseg(struct pool *pool, struct flash_block *fb)
{
    assert(pool->i == pool->Np);
    assert(fb->n_valid == 0 && fb->in_pool == 0);

    pool->i = 0;                /* page pointer for new block */

    struct flash_block *blk = pool->frontier;
    if (blk != NULL) {
        pool->frontier->in_pool = 1; /* old frontier is now in pool */
        pool->pages_valid += pool->frontier->n_valid;
        pool->pages_invalid += (pool->Np - pool->frontier->n_valid);

        list_add(blk, &pool->bins[blk->n_valid]);
        if (blk->n_valid < pool->min_valid)
            pool->min_valid = blk->n_valid;
    }

    pool->frontier = fb;
    fb->pool = pool;
}

static void greedy_int_write(struct rmap *rmap, struct pool *pool, int lba)
{
    rmap->int_writes++;
    struct flash_block *b = rmap->map[lba].block;
    int page = rmap->map[lba].page_num;
    if (b != NULL) {
        do_flash_block_overwrite(b, page, lba);
        if (b->in_pool) {
            list_rm(b);
            list_add(b, &b->pool->bins[b->n_valid]);
            if (b->n_valid < b->pool->min_valid)
                b->pool->min_valid = b->n_valid;
        }
    }
    
    do_flash_block_write(pool->frontier, pool->i++, lba);
    if (pool->i >= pool->Np) {
        b = do_get_blk(rmap);
        greedy_pool_addseg(pool, b);
    }
}

static void greedy_pool_del(struct pool *pool)
{
    free(pool->bins);
    free(pool);
}

struct pool *greedy_pool_new(struct rmap *map, int Np)
{
    struct pool *pool = calloc(sizeof(*pool), 1);
    pool->map = map;
    pool->Np = Np;

    int i = map->npools++;
    map->pools[i] = pool;

    pool->bins = calloc((Np+1) * sizeof(*pool->bins), 1);
    for (i = 0; i <= Np; i++)
        pool->bins[i].next = pool->bins[i].prev = &pool->bins[i];
    
    pool->addseg = greedy_pool_addseg;
    pool->getseg = greedy_pool_getseg;
    pool->write = greedy_int_write;
    pool->del = greedy_pool_del;
    pool->tail_utilization = greedy_tail_utilization;
    
    return pool;
}

static struct pool *do_select_first(struct rmap* map, int lba)
{
    return map->pools[0];
}

static struct pool *do_select_top_down(struct rmap* map, int lba)
{
    return NULL;
}

struct pool *pool_retval;
void return_pool(struct pool *pool)
{
    pool_retval = pool;
}

static struct pool *python_select_1_arg(struct rmap *map, int lba)
{
    PyObject *args = Py_BuildValue("(i)", lba);
    PyObject *result = PyEval_CallObject(map->get_input_pool_arg, args);
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

static struct pool *do_clean_select_first(struct rmap *map)
{
    return map->pools[0];
}
clean_selector_t clean_select_first = do_clean_select_first;

static struct pool *python_select_no_arg(struct rmap *map)
{
    PyObject *args = Py_BuildValue("()");
    PyObject *result = PyEval_CallObject(map->get_pool_to_clean_arg, args);
    if (PyErr_Occurred()) 
        PyErr_Print();
    if (result != NULL) {
        Py_DECREF(result);
    }
    return pool_retval;
}

clean_selector_t clean_select_python = python_select_no_arg;
