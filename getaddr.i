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

struct uniform {
    struct getaddr handle;
    int max;
};
%extend uniform {
    uniform(int max) {
        return uniform_new(max);
    }
    ~uniform() {
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

struct mixed {
    struct getaddr handle;
};
%extend mixed {
    mixed() {
        return mixed_new();
    }
    ~mixed() {
        mixed_del(self);
    }
    void add(struct getaddr *g, double p, int base) {
        mixed_do_add(self, g, p, base);
    }
}

struct trace {
    struct getaddr handle;
};
%extend trace {
    trace(char *file) {
        return trace_new(file);
    }
    ~trace() {
        trace_del(self);
    }
}
