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

struct int_array {          /* kludge for indexed arrays */
    int val;
};

%extend int_array {
    struct int_array *__getitem__(int i) {
        return self + i;
    }
 }

struct runsim {
    PyObject *stats_exit;       /* blocks at cleaning time */
    PyObject *stats_enter;      /* blocks entering pool */
    PyObject *stats_write;      /* every write */
    PyObject *generator;
};
%extend runsim {
    %insert("python") %{
        def run(self, nsteps):
            for a in self.generator.next_n(nsteps):
                self.step(a)
    %}
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

struct flash_block {
    int  n_valid;
    struct int_array *lbas;
};

%extend flash_block {
    flash_block(int Np) {
        return flash_block_new(Np);
    }
    ~flash_block() {
        flash_block_del(self);
    }
    void write(int page, int lba) {
        assert(page < self->Np && page >= 0 && self->lba[page] == -1);
        self->lba[page] = lba;
        self->n_valid++;
    }
    void overwrite(int page, int lba) {
        assert(page < self->Np && page >= 0 && self->lba[page] == lba);
        self->lba[page] = -1;
        self->n_valid--;
    }
}
    
struct rmap {
    int int_writes, ext_writes;
};

%extend rmap {
    rmap(int T, int Np) {
        return rmap_new(T, Np);
    }
    struct flash_block *find_blk(int lba) {
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].block;
    }
    int find_page(int lba) {
        assert(lba >= 0 && lba < self->T * self->Np);
        return self->map[lba].page_num;
    }
    ~rmap() {
        rmap_del(self);
    }
}

struct lru_pool {
    struct runsim handle;
    struct flash_block *frontier;
    int i, pages_valid, pages_invalid;
};
%extend lru_pool {
    lru_pool(struct rmap *map, int Np) {
        return lru_pool_new(map, Np);
    }
    void add_block(struct flash_block *blk) {
        lru_pool_addseg(self, blk);
    }
    struct flash_block *remove_block(void) {
        return lru_pool_getseg(self);
    }
    ~lru_pool() {
        lru_pool_del(self);
    }
}

void srand(int seed);
int rand(void);
