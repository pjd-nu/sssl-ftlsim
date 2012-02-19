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
#include "ftlsim.h"
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
    %insert("python") %{
        def addrs(self):
            while True:
                a = self.next()
                if a == -1:
                    break;
                yield(a)
    %}
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
    int eof, single;
};
%extend trace {
    trace(char *file) {
        return trace_new(file);
    }
    ~trace() {
        trace_del(self);
    }
}

struct log {
    struct getaddr handle;
};
%extend log {
    log(struct getaddr *src, char *file) {
        return log_new(src, file);
    }
    ~log() {
        log_close(self);
    }
}
   
struct scramble {
    struct getaddr handle;
    int eof;
};
%extend scramble {
    scramble(struct getaddr *src, int max) {
        return scramble_new(src, max);
    }
    ~scramble() {
        scramble_del(self);
    }
}
