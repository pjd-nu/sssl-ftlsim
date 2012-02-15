/*
 * file:        runsim.i
 * description: SWIG interface for multiple FTL simulation engines
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

%module runsim

%{
#define SWIG_FILE_WITH_INIT
#include "ftlsim.h"
#include "runsim.h"
%}

struct runsim {
    void (*runsim)(void *private_data, int steps);
};
%extend runsim {
    void run(int steps) {
        self->runsim(self->private_data, steps);
    }
}

struct lru {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    struct getaddr *generator;
};
%extend lru {
    lru() {
        return lru_new();
    }
    ~lru() {
        lru_del(self);
    }
}

void srand(int seed);
int rand(void);
