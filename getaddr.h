/*
 * file:        getaddr.h
 * see getaddr.i for details
 * Peter Desnoyers, Northeastern University, 2012
 */

struct uniform {
    struct getaddr handle;
    int max;
};

struct uniform *uniform_new(int max);

struct mixed {
    struct getaddr handle;
    struct mixed_private *private_data;
};

struct mixed *mixed_new(void);
void mixed_do_add(struct mixed *self, struct getaddr *g, double p, int base);
void mixed_del(struct mixed *self);

struct trace {
    struct getaddr handle;
    struct trace_private *private_data;
};

struct trace *trace_new(char *file);
void trace_del(struct trace *t);

struct log {
    struct getaddr handle;
    struct log_private *private_data;
};

struct log *log_new(struct getaddr *src, char *file);
void log_close(struct log *l);

int next(struct getaddr *);
