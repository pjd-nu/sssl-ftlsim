/*
 * file:        runsim.c
 * description: shared simulation routines - mostly statistics
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <Python.h>

#include "ftlsim.h"
#include "runsim.h"

static void run_stats(PyObject *f, PyObject *args)
{
    PyObject *result = PyEval_CallObject(f, args);
    Py_DECREF(args);
    if (result) {
        Py_DECREF(result);
    }
}

/* simulator calls this whenever a block is selected for cleaning -
 * provides the number of valid pages remaining and the physical block
 * number in case the stats routine wants to query the individual
 * pages */
static int exit_depth;
void runsim_stats_exit(struct runsim *sim, int n_valid, int pblk)
{
    exit_depth++;
    assert(exit_depth<2);
    if (sim->stats_exit != NULL)
        run_stats(sim->stats_exit, Py_BuildValue("(s i i)", "exit", n_valid, pblk));
    exit_depth--;
}

static int enter_depth;
void runsim_stats_enter(struct runsim *sim, int pblk)
{
    enter_depth++;
    assert(enter_depth<2);
    if (sim->stats_enter != NULL)
        run_stats(sim->stats_enter, Py_BuildValue("(s i)", "enter", pblk));
    enter_depth--;
}

static int write_depth;
void runsim_stats_write(struct runsim *sim, int addr, int blk, int pg)
{
    write_depth++;
    assert(write_depth<2);
    if (sim->stats_write != NULL)
        run_stats(sim->stats_write, Py_BuildValue("(s i i i)", "write", addr, blk, pg));
    write_depth--;
}

struct pyobj {
  PyObject *obj;
};
struct pyobj foo_obj;
