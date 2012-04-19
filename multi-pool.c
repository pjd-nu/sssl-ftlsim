/*
 * file:        runsim_pool.c
 * description: Simple, fast multi-pool FTL simulator
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
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
    /* assumes you've already freed the free list */
    free(rmap->map);
    free(rmap);
}

struct lru_pool *lru_pool_new(struct rmap *map, int Np)
{
    struct lru_pool *val = calloc(sizeof(*val), 1);
    val->map = map;
    val->Np = Np;

    /* whoops - need to initialize handle... */
    return val;
}

void lru_pool_del(struct lru_pool *pool)
{
    free(pool);
}

/* cleaning - grab the tail of the pool. the caller of this function
 * is responsible for copying the remaining valid pages.
 */
struct flash_block *lru_pool_getseg(struct lru_pool *pool)
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

/* After the current write frontier fills, call this function to move
 * it to the pool and provide a new write frontier.
 */
void lru_pool_addseg(struct lru_pool *pool, struct flash_block *fb)
{
    assert(pool->i == pool->Np);
    assert(fb->n_valid == 0 && fb->in_pool == 0);

    pool->i = 0;                /* page pointer for new block */

    fb->prev = NULL;            /* link onto head of dbl linked list */
    fb->next = pool->frontier;
    if (pool->frontier != NULL) {
        pool->frontier->in_pool = 1; /* old frontier is now in pool */
        pool->frontier->prev = fb;
    }
    pool->frontier = fb;

    if (pool->tail == NULL)     /* handle initial case */
        pool->tail = fb;
    
    /* 'pages_invalid' is actually free+invalid - i.e. total space - valid pages.
     */
    pool->pages_invalid += pool->Np;

    fb->pool = pool;
}

