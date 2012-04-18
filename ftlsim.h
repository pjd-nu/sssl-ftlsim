/* for statistics - add a visitor method? what else?
 */

#include <Python.h>

struct runsim {
    void (*step)(void *private_data, int addr);
    void *private_data;
    PyObject *stats_exit;       /* blocks at cleaning time */
    PyObject *stats_enter;      /* blocks entering pool */
    PyObject *stats_write;      /* every write */
    PyObject *generator;
    int (*get_physpage)(void *, int blk, int pg);
};

