/*
 * file:        runsim_greedy.c
 * description: FTL simulation engine for simple greedy cleaning
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

struct greedy_private {
    struct greedy *parent;
    struct rmap *rmap;
    struct block *bins;
    int min_valid;              /* start searching bins here */
    struct block *frontier;
    struct block *free_list;
    struct block *blocks;
    int nfree;
    int Np;
};

static void blk_free(struct greedy_private *gp, struct block *b)
{
    b->next = gp->free_list;
    gp->free_list = b;
    gp->nfree++;
}

static struct block *blk_alloc(struct greedy_private *gp)
{
    int i;
    struct block *b = gp->free_list;
    gp->free_list = b->next;
    gp->nfree--;
    for (i = 0; i < gp->Np; i++)
        b->lba[i] = -1;
    b->next = b->prev = b;
    b->n_valid = b->i = 0;
    return b;
}

static struct block *get_greedy_block(struct greedy_private *gp)
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

static void int_write(struct greedy_private *gp, int a)
{
    gp->parent->int_writes++;
    
    struct block *b = gp->rmap[a].b;
    if (b != NULL) {       /* invalidate the old page, if it exists */
        int p = gp->rmap[a].page;
        b->lba[p] = -1;
        b->n_valid--;

        if (b != gp->frontier) {
            list_rm(b);
            list_add(b, &gp->bins[b->n_valid]);
            if (b->n_valid < gp->min_valid)
                gp->min_valid = b->n_valid;
        }
    }

    int i = gp->frontier->i++;  /* write the data */
    gp->frontier->lba[i] = a;
    gp->rmap[a].b = gp->frontier;
    gp->rmap[a].page = i;
    gp->frontier->n_valid++;

    /* if the block is full, it goes into the pool and we get another */
    if (gp->frontier->i == gp->Np) {
        list_add(gp->frontier, &gp->bins[gp->frontier->n_valid]);
        gp->frontier = blk_alloc(gp);
    }
}

static void host_write(struct greedy_private *gp, int a)
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

static void greedy_init(struct greedy *g)
{
    int i;
    
    struct greedy_private *gp = calloc(sizeof(*gp), 1);
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

static void greedy_run(void *private_data, int steps)
{
    int i;
    struct greedy *greedy = private_data;
    struct getaddr *gen = greedy->generator;
    
    for (i = 0; i < steps; i++) {
        int a = gen->getaddr(gen->private_data);
        if (a == -1)
            break;
        host_write(greedy->private_data, a);
    }
}

struct greedy *greedy_new(int T, int U, int Np)
{
    struct greedy *val = calloc(sizeof(*val), 1);
    val->handle.private_data = val;
    val->handle.runsim = greedy_run;
    val->T = T; val->U = U; val->Np = Np;
    greedy_init(val);
    return val;
}

void greedy_del(struct greedy *g)
{
    int i;
    struct greedy_private *p = g->private_data;
    free(p->bins);
    for (i = 0; i < g->T; i++)
        free(p->blocks[i].lba);
    free(p->blocks);
    free(p->rmap);
    free(p);
    free(g);
}

