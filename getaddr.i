/*
 * file:        getaddr.i
 * description: SWIG interface file for address generators.
 *
 * For each of the getaddr classes:
 *  Each call to getaddr(self) returns a signed integer address or -1 if done.
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

%module getaddr

%{
#define SWIG_FILE_WITH_INIT
#include "getaddr.h"
%}

struct getaddr_uniform {
    struct getaddr handle;
    int max;
};
%extend getaddr_uniform {
    getaddr_uniform(int max) {
        return uniform(max);
    }
    ~getaddr_uniform() {
        free(self);
    }
}

struct getaddr {
};

%extend getaddr {
    int next(void) {
        return next(self);
    }
};

struct getaddr_mix {
    struct getaddr handle;
};
%extend getaddr_mix {
    getaddr_mix() {
        return mixed();
    }
    ~getaddr_mixed() {
        mixed_del(self);
    }
    void add(struct getaddr *g, double p, int base) {
        mixed_add(self, g, p, base);
    }
}

struct getaddr_trace {
    struct getaddr handle;
};
%extend getaddr_trace {
    getaddr_trace(char *file) {
        return trace(file);
    }
    ~getaddr_trace() {
        trace_del(self);
    }
}
