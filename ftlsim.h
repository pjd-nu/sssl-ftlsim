/* for statistics - add a visitor method? what else?
 */

#include <Python.h>

struct runsim {
    void (*step)(void *private_data, int addr);
    struct getaddr *generator;
    void *private_data;
    PyObject *stats;
};

struct getaddr {
    int (*getaddr)(void *self);
    void (*del)(void *self);
    void *private_data;
};

