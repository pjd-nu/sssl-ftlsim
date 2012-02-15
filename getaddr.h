/*
 * file:        getaddr.h
 * see getaddr.i for details
 * Peter Desnoyers, Northeastern University, 2012
 */

struct getaddr {
    int (*getaddr)(void *self);
    void (*del)(void *self);
    void *private_data;
};

struct getaddr_uniform {
    struct getaddr handle;
    int max;
};

struct getaddr_mix {
    struct getaddr handle;
    struct mixed_private *private_data;
};

struct getaddr_trace {
    struct getaddr handle;
    struct trace_private *private_data;
};

struct getaddr_uniform *uniform(int max);

struct getaddr_trace *trace(char *file);
void trace_del(struct getaddr_trace *t);

struct getaddr_mix *mixed(void);
void mixed_add(struct getaddr_mix *self, struct getaddr *g, double p, int base);
void mixed_del(struct getaddr_mix *self);

int next(struct getaddr *);

