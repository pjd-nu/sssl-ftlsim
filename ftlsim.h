/* for statistics - add a visitor method? what else?
 */

struct runsim {
    void (*runsim)(void *private_data, int steps);
    void *private_data;
};

struct getaddr {
    int (*getaddr)(void *self);
    void (*del)(void *self);
    void *private_data;
};

