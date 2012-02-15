/*
 * file:        getaddr.c
 * * description: Address generation for fast FTL simulation.
 *
 * External C code uses the 'struct getaddr' handle to interface
 * directly - h->getaddr(h->private_data) returns the next address. 
 *
 * Peter Desanoyers, Northeastern University, 2012
 */

#include <stdio.h>
#include <stdlib.h>
#include "getaddr.h"

int next(struct getaddr *g)
{
    return g->getaddr(g->private_data);
}

int uniform_get(void *private_data)
{
    struct getaddr_uniform *u = private_data;
    double r1 = (double)rand() / RAND_MAX;
    return r1 * u->max;
}
    
struct getaddr_uniform *uniform(int max)
{
    struct getaddr_uniform *u = calloc(sizeof(*u), 1);
    u->max = max;
    u->handle.private_data = u;
    u->handle.getaddr = uniform_get;
    u->handle.del = (void*)free;
    return u;
}

struct mixed_private {
    int n;
    double p[5];
    int base[5];
    struct getaddr *gen[5];
};

int mixed_get(void *private_data)
{
    struct getaddr_mix *m = private_data;
    struct mixed_private *p = m->private_data;
    int i;
    double r = (double)rand() / RAND_MAX;
    for (i = 0; i < p->n; i++)
        if (r < p->p[i])
            return p->base[i] + next(p->gen[i]);
    return 0;
}

void mixed_del(struct getaddr_mix *self)
{
    int i;
    struct mixed_private *p = self->private_data;
    for (i = 0; i < p->n; i++)
        if (p->gen[i]->del)
            p->gen[i]->del(p->gen[i]->private_data);
    free(p);
    free(self);
}

struct getaddr_mix *mixed(void)
{
    struct getaddr_mix *m = calloc(sizeof(*m), 1);
    m->handle.private_data = m;
    m->handle.getaddr = mixed_get;
    m->private_data = calloc(sizeof(*m->private_data), 1);
    return m;
}

void mixed_add(struct getaddr_mix *self, struct getaddr *g, double p, int base)
{
    struct mixed_private *priv = self->private_data;
    int i = priv->n;            /* ignore overflow */
    priv->gen[i] = g;
    priv->p[i] = p;
    priv->base[i] = base;
    priv->n++;
}

/*
 * getaddr_trace(filename) - reads lines containing addr,len pairs.
 *  addresses and lengths beginning with '0x' will be parsed as hex
 *  addresses are in units of *PAGES*, not sectors or bytes
 */
struct trace_private {
    FILE *fp;
    int addr, count;
};

static int trace_get(void *private_data)
{
    struct getaddr_trace *t = private_data;
    struct trace_private *p = t->private_data;

    if (p->count > 0) {
        p->count--;
        return ++(p->addr);
    }

    char line[80], *tmp;
    if (fgets(line, sizeof(line), p->fp) == NULL)
        return -1;
    p->addr = strtol(line, &tmp, 0);
    p->count = strtol(tmp, NULL, 0) - 1;
    return p->addr;
}

void trace_del(struct getaddr_trace *t)
{
    fclose(t->private_data->fp);
    free(t->private_data);
    free(t);
}

struct getaddr_trace *trace(char *file)
{
    struct getaddr_trace *t = calloc(sizeof(*t), 1);
    t->handle.private_data = t;
    t->handle.getaddr = trace_get;
    t->handle.del = (void*)trace_del;
    
    struct trace_private *p = calloc(sizeof(*p), 1);
    p->fp = fopen(file, "r");
    t->private_data = p;
    
    return t;
}

