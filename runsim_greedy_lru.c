/*
 * file:        runsim_greedy_lru.c
 * description: FTL simulation engine for Hu's Greedy/LRU algorithm
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "ftlsim.h"
#include "runsim.h"

struct block {
    struct block *next;         /* standard 1,2-linked list pointers */
    struct block *prev;
    int *lba;               /* LBA mapped to each page */
    int i;                      /* next LBA to write */
    int n_valid;                /* stats, plus indicates greedy bin */
    int in_greedy;
};

/* the standard doubly-linked-list primitives
 */
static void list_add(struct block *b, struct block *bin)
{
    b->next = bin;
    b->prev = bin->prev;
    bin->prev->next = b;
    bin->prev = b;
}

static void list_rm(struct block *b)
{
    b->prev->next = b->next;
    b->next->prev = b->prev;
    b->next = b->prev = b;
}

static int list_empty(struct block *b)
{
    return b->next == b;
}

/* The reverse map, from logical page to physical block and page */
struct rmap {
    struct block *b;
    int           page;
};

struct greedylru_private {
    struct greedylru *parent;
    struct rmap *rmap;
    struct block *bins;
    int min_valid;              /* start searching bins here */
    struct block *frontier;
    struct block *free_list;
    struct block *blocks;
    struct {
        struct block *head;
        struct block *tail;
        int len;
    } lru;
    int nfree;
    int Np;
};

/* put a block back on the free list */
static void blk_free(struct greedylru_private *gp, struct block *b)
{
    b->next = gp->free_list;
    gp->free_list = b;
    gp->nfree++;
}

/* get a block from the free list and initialize it */
static struct block *blk_alloc(struct greedylru_private *gp)
{
    int i;
    struct block *b = gp->free_list;
    gp->free_list = b->next;
    gp->nfree--;
    for (i = 0; i < gp->Np; i++)
        b->lba[i] = -1;
    b->next = b->prev = b;
    b->n_valid = b->i = b->in_greedy = 0;
    return b;
}

/* greedy cleaning. note that this won't be called until the greedy
 * tail is non-empty */
static struct block *get_greedy_block(struct greedylru_private *gp)
{
    int i;
    for (i = gp->min_valid; i < gp->Np; i++)
        if (!list_empty(&gp->bins[i])) {
            gp->min_valid = i;
            struct block *b = gp->bins[i].next; /* don't remove it */
            return b;
        }
    assert(0);
    return NULL;
}

/* add a block to the LRU queue, move a block to the greedy tail if needed */
static void queue_block(struct greedylru_private *gp, struct block *b)
{
    if (gp->lru.tail == NULL)
        gp->lru.head = gp->lru.tail = b;
    else {
        gp->lru.head->next = b;
        gp->lru.head = b;
    }
    gp->lru.len++;

    while (gp->lru.len > gp->parent->lru_max) {
        b = gp->lru.tail;
        gp->lru.tail = b->next;
        gp->lru.len--;
        list_add(b, &gp->bins[b->n_valid]);
        if (b->n_valid < gp->min_valid)
            gp->min_valid = b->n_valid;
    }
}
    
/* any internal write to flash, whether cleaning-related or not */
static void int_write(struct greedylru_private *gp, int a)
{
    gp->parent->int_writes++;
    
    struct block *b = gp->rmap[a].b;
    if (b != NULL) {       /* invalidate the old page, if it exists */
        int p = gp->rmap[a].page;
        b->lba[p] = -1;
        b->n_valid--;
        if (b->in_greedy) { /* move between bins in the greedy tail */
            list_rm(b);
            list_add(b, &gp->bins[b->n_valid]);
            if (b->n_valid < gp->min_valid)
                gp->min_valid = b->n_valid;
        }
    }

    /* write the data */
    int i = gp->frontier->i++;
    gp->frontier->lba[i] = a;
    gp->rmap[a].b = gp->frontier;
    gp->rmap[a].page = i;
    gp->frontier->n_valid++;

    /* if the block is full, it goes on the LRU queue and we get another */
    if (gp->frontier->i == gp->Np) {
        queue_block(gp, b);
        gp->frontier = blk_alloc(gp);
    }
}

static void host_write(struct greedylru_private *gp, int a)
{
    int i;

    gp->parent->ext_writes++;
    int_write(gp, a);

    while (gp->nfree < gp->parent->target_free) {
        struct block *b = get_greedy_block(gp);
        for (i = 0; i < gp->Np; i++)
            if (b->lba[i] >= 0) 
                int_write(gp, b->lba[i]);
        list_rm(b);
        blk_free(gp, b);
    }
}

static void greedylru_init(struct greedylru *g)
{
    int i;
    
    struct greedylru_private *gp = calloc(sizeof(*gp), 1);
    gp->parent = g;
    gp->Np = g->Np;

    /* set up the bins for efficient greedy search */
    gp->bins = calloc((g->Np + 1) * sizeof(*gp->bins), 1);
    for (i = 0; i <= g->Np; i++)
        gp->bins[i].next = gp->bins[i].prev = &gp->bins[i];
    gp->min_valid = 0;       /* this is OK, since we search upwards */

    gp->blocks = calloc(g->T * sizeof(*gp->blocks), 1); /* alloc all at once */

    for (i = 0; i < g->T; i++) {
        struct block *b = &gp->blocks[i];
        b->lba = calloc(g->Np * sizeof(int), 1); /* LBA map for each block */
        blk_free(gp, b);        /* all blocks start on free list */
    }

    gp->rmap = calloc(g->U * gp->Np * sizeof(*gp->rmap), 1);
    gp->frontier = blk_alloc(gp);

    for (i = 0; i < g->Np * g->U; i++)  /* now write every address once */
        host_write(gp, i);

    g->private_data = gp;       /* and we're done */
}

static void greedylru_run(void *private_data, int steps)
{
    int i;
    struct greedylru *greedy = private_data;
    struct getaddr *gen = greedy->generator;
    
    for (i = 0; i < steps; i++) {
        int a = gen->getaddr(gen->private_data);
        host_write(greedy->private_data, a);
    }
}

struct greedylru *greedylru_new(int T, int U, int Np)
{
    struct greedylru *val = calloc(sizeof(*val), 1);
    val->handle.private_data = val;
    val->handle.runsim = greedylru_run;
    val->T = T; val->U = U; val->Np = Np;
    greedylru_init(val);
    return val;
}

void greedylru_del(struct greedylru *g)
{
    int i;
    struct greedylru_private *p = g->private_data;
    free(p->bins);
    for (i = 0; i < g->T; i++)
        free(p->blocks[i].lba);
    free(p->blocks);
    free(p->rmap);
    free(p);
    free(g);
}

