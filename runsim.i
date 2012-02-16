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
    lru(int T, int U, int Np) {
        return lru_new(T, U, Np);
    }
    ~lru() {
        lru_del(self);
    }
}

struct greedy {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    int target_free;
    struct getaddr *generator;
};
%extend greedy {
    greedy(int T, int U, int Np) {
        return greedy_new(T, U, Np);
    }
    ~greedy() {
        greedy_del(self);
    }
}

void srand(int seed);
int rand(void);
