#
# file:        lru-high.py
# description: Example LRU cleaning simulation using high-speed routines
#
# Peter Desnoyers, Northeastern University, 2012
#
import getaddr
import ftlsim

# parameters
#
U = 23020
Np = 128
S_f = 0.1
alpha = 1 / (1-S_f)
minfree = Np
T = int(U * alpha) + minfree

# FTL with default parameters for single pool
#
ftl = ftlsim.ftl(T, Np)
ftl.minfree = minfree
ftl.get_input_pool = ftlsim.cvar.write_select_first
ftl.get_pool_to_clean = ftlsim.cvar.clean_select_first

# LRU-managed pool
#
lru = ftlsim.pool(ftl, "lru", Np)
lru.next_pool = lru

# allocate blocks and put them on FTL free list, except for
# 1 write frontier.
#
freelist = [ftlsim.segment(Np) for i in range(T)]
for b in freelist:
    b.thisown = False
lru.add_segment(freelist.pop())
for b in freelist:
    ftl.put_blk(b)

# use a sequential address source to write each page once
#
seq = getaddr.seq()
ftl.run(seq.handle, U*Np);

print "ready..."

# Now run with uniform random traffic for 10 units of 0.1 volume each.
#
src = getaddr.uniform(U*Np)
for i in range(10):
    ftl.run(src.handle, U*Np/10)
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0

