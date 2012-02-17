#
# file:        3hc.py
# description: simulation of 3-part non-uniform traffic mixes
#

import getaddr
import runsim

# 256k * 64 * 4K = 64GB

U = 256000
Np = 64

splits = ((1/2.0, 1/4.0, 1/4.0),
          (2/3.0, 2/9.0, 1/9.0),
          (3/4.0, 3/16.0, 1/16.0))

def cumulative_sum(x):
    return reduce(lambda a,b: a + [a[-1]+b], x, [0])[0:-1]
    
maxes = 

1/3 1/3 1/3
1/4 1/4 1/2

for S_f in 0.07 0.10 0.13:
    alpha = 1 / (1-S_f)
    T = int(U * alpha) + Np

    # iterate across splits in traffic distribution
    for s in splits:
        maxes = [U * f for f in s]
        bases = cumulative_sum(maxes)
        
        # and across assignments
        for a in splits:
            tops = cumulative_sum(a)[1:] + [1]
            addr = getaddr.mixed()
            for b,m,t in zip(bases, maxes, tops):
                aa = getaddr.uniform(m)
                addr.add(aa, t, b)

        

