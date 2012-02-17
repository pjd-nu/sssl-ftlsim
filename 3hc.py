#
# file:        3hc.py
# description: simulation of 3-part non-uniform traffic mixes
#

import getaddr
import runsim

# 256k * 64 * 4K = 64GB

U = 256*1024
Np = 64

splits = ((1/2.0, 1/4.0, 1/4.0),
          (2/3.0, 2/9.0, 1/9.0),
          (3/4.0, 3/16.0, 1/16.0))

def cumulative_sum(x):
    return reduce(lambda a,b: a + [a[-1]+b], x, [0])[0:-1]
    
warmup = getaddr.uniform(U*Np)

for S_f in (0.07, 0.10, 0.13):
    alpha = 1 / (1-S_f)
    T = int(U * alpha) + Np

    # iterate across splits in traffic distribution
    for s in splits:
        maxes = [int(U * f) for f in s]
        bases = cumulative_sum(maxes)
        
        # and across assignments
        for a in splits:
            rates = a[-1::-1]
            tops = cumulative_sum(rates)[1:] + [1]
            addr = getaddr.mixed()
            for b,m,t in zip(bases, maxes, tops):
                aa = getaddr.uniform(m)
                aa.thisown = 0
                addr.add(aa.handle, t, b)

            sim = runsim.lru(T, U, Np);
            sim.generator = warmup.handle
            sim.handle.run(T*Np*2)
            sim.int_writes = 0
            sim.ext_writes = 0
            
            sim.generator = addr.handle

            print "S_f %.3f" % S_f
            print "f   %.2f %.2f %.2f" % s
            print "r   %.2f %.2f %.2f" % rates
            for i in range(100):
                sim.handle.run(U*Np/10)
                print "%d %d %f" % (sim.int_writes, sim.ext_writes,
                                    1.0 * sim.int_writes / sim.ext_writes)
                sim.int_writes = 0
                sim.ext_writes = 0
