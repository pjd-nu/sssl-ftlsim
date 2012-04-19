import genaddr
import runsim
import sys

def doit(src):

    sim = runsim.greedy(T+Np/2, U, Np)
    sim.target_free = Np/2
    
    sim = runsim.lru(T, U, Np)
    for a in warmup.next_n(T*Np*2):
        sim.handle.step(a)
    sim.int_writes = 0
    sim.ext_writes = 0

    for i in range(100):
        for a in src.next_n(U*Np/10):
            sim.handle.step(a)
        print "%d %d %f" % (sim.int_writes, sim.ext_writes,
                            1.0 * sim.int_writes / sim.ext_writes)
        sim.int_writes = 0
        sim.ext_writes = 0
        if src.eof:
            break

U = 23020
Np = 128
warmup = genaddr.uniform(U*Np)
file = 'writes-4k-pg.dat'

for S_f in (0.07, 0.10):
    alpha = 1 / (1-S_f)
    T = int(U * alpha)

    print "T %d U %d" % (T, U)
    print "straight:"
    doit(genaddr.trace(file))

    print "space shuffled:"
    a = genaddr.trace(file)
    doit(genaddr.scramble(a, U*Np))

    for n in (10000, 100000, 1000000):
        print 'time shuffled 1/line', n
        fp = open('writes-4k-pg.dat', 'r')
        doit(genaddr.trace(genaddr.shuffle(fp, n)))
