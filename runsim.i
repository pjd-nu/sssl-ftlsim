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

struct pyobj {
  PyObject *obj;
};
extern struct pyobj foo_obj;
%}

struct pyobj {
  PyObject *obj;
};
struct pyobj foo_obj;

struct runsim {
    struct getaddr *generator;
    PyObject *stats_exit;       /* blocks at cleaning time */
    PyObject *stats_enter;      /* blocks entering pool */
    PyObject *stats_write;      /* every write */
};

%extend runsim {
    void run(int steps) {
        struct getaddr *gen = self->generator;
        int i, a = gen->getaddr(gen->private_data);
        for (i = 0; i < steps && a != -1; i++) {
            self->step(self->private_data, a);
            a = gen->getaddr(gen->private_data);
        }
    }
    void step(int addr) {
        self->step(self->private_data, addr);
    }
    int get_phys_page(int blk, int pg) {
        if (self->get_physpage == NULL)
            return -1;
        else
            return self->get_physpage(self->private_data, blk, pg);
    }
}

struct lru {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
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
};
%extend greedy {
    greedy(int T, int U, int Np) {
        return greedy_new(T, U, Np);
    }
    ~greedy() {
        greedy_del(self);
    }
}

struct greedylru {
    struct runsim handle;
    int T, U, Np;
    int int_writes, ext_writes;
    int target_free, lru_max;
};
%extend greedylru {
    greedylru(int T, int U, int Np) {
        return greedylru_new(T, U, Np);
    }
    ~greedylru() {
        greedylru_del(self);
    }
}

void srand(int seed);
int rand(void);
