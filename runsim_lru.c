/*
 * file:        runsim_lru.c
 * description: Simple, fast LRU FTL simulator
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "ftlsim.h"
#include "runsim.h"

struct lru_private {
    struct lru *lru;
    int i, j;
    int U, T;                   /* in pages, not blocks */
    int *p2l;                   /* phys to logical and vice versa */
    int *l2p;
    int head, tail;
};

/*
    VVVVVVVVVVVVVVVVVVVVVVV IIIIIIIIIII 
    ^......................^
    tail                   head
 */
static void lru_init(struct lru *lru)
{
    struct lru_private *p = calloc(sizeof(*p), 1);
    p->lru = lru;
    p->T = lru->T * lru->Np;
    p->U = lru->U * lru->Np;
    
    p->p2l = calloc(p->T * sizeof(int), 1);
    p->l2p = calloc(p->U * sizeof(int), 1);
    
    int i;
    for (i = 0; i < p->U; i++) 
        p->l2p[i] = p->p2l[i] = i;
    p->head = i;
    for (; i < p->T; i++) 
	p->p2l[i] = -1;
    p->tail = 0;
    lru->private_data = p;
}

/*
 * p2l is array[0..N_p*T-1] of addresses (or -1 if invalid)
 * l2p is array[0..N_p*U-1] of phys addresses (or -1 if invalid)
 * we do strict circular buffer LRU by page (not block), except that we clean
 * a block at a time. (which really only makes a trivial difference)
 */

static void int_write(struct lru *lru, int a)
{
    struct lru_private *p = lru->private_data;
    int phys = p->l2p[a];

    lru->int_writes++;

    runsim_stats_write(&p->lru->handle, a, p->head / p->lru->Np, p->head % p->lru->Np);
    
    if (phys != -1)             /* invalidate old mapping */
        p->p2l[phys] = -1;

    phys = p->head;             /* and install new mapping */
    p->p2l[phys] = a;
    p->l2p[a] = phys;

    /* if we just finished a full block, calculate the block number
       and report it to the stats handler. */
    if ((p->head % p->lru->Np) == p->lru->Np - 1) 
        runsim_stats_enter(&p->lru->handle, p->head / p->lru->Np);

    p->head = (p->head + 1) % p->T;

}

static void host_write(struct lru *lru, int a)
{
    struct lru_private *p = lru->private_data;

    assert(a < p->U);
    
    /* first make sure we have space, cleaning some integer number of
     * erase blocks if necessary
     */
    while ((p->tail + p->T - p->head) % p->T < 2 * lru->Np) {
        int i, nv;
        for (i = nv = 0; i < lru->Np; i++) 
            if (p->p2l[p->tail+i] != -1)
                nv++;
        runsim_stats_exit(&lru->handle, nv, p->tail / p->lru->Np);
        for (i = 0; i < lru->Np; i++) {
            int a2 = p->p2l[p->tail];
            if (a2 != -1) 
                int_write(lru, a2);
            p->tail = (p->tail + 1) % p->T;
        }
    }

    /* then write the user data
     */
    lru->ext_writes++;
    int_write(lru, a);
}
    
static void lru_step(void *private_data, int a)
{
    struct lru *lru = private_data;
    host_write(lru, a);
}

int lru_get_phys_page(void *private_data, int blk, int pg)
{
    struct lru *lru = private_data;
    if (blk < 0 || blk >= lru->T || pg < 0 || pg >= lru->Np)
        return -1;
    struct lru_private *p = lru->private_data;
    return p->p2l[lru->Np * blk + pg];
}
    
struct lru *lru_new(int T, int U, int Np)
{
    struct lru *val = calloc(sizeof(*val), 1);
    val->handle.private_data = val;
    val->handle.step = lru_step;
    val->handle.get_physpage = lru_get_phys_page;
    val->T = T; val->U = U; val->Np = Np;
    
    lru_init(val);

    int i;
    double sum = 0.0, incr = 1.0 * U / T;
    for (i = 0; i < U*Np; i++) {
        host_write(val, i);
        sum += incr;
        if (i - sum >= 1) {
            host_write(val, i);
            sum += incr;
        }
    }
    
    return val;
}

void lru_del(struct lru *lru)
{
    struct lru_private *p = lru->private_data;
    if (p && p->p2l)
        free(p->p2l);
    if (p && p->l2p)
        free(p->l2p);
    free(p);
    free(lru);
    printf("deleted %p\n", lru);
}
    
