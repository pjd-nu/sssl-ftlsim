#
#
import getaddr
import ftlsim
import sys

# parameters
#
U = 230200/2
Np = 64
alpha = 1.1
minfree = 3
T = int(U * alpha) 
r = 0.9
f = 0.1

# FTL with default parameters for single pool
#
ftl = ftlsim.ftl(T, Np)
ftl.minfree = minfree
ftl.get_input_pool = ftlsim.cvar.write_select_first
#ftl.get_pool_to_clean = ftlsim.cvar.clean_select_first
ftl.get_pool_to_clean = ftlsim.cvar.clean_select_python

pools = [ftlsim.pool(ftl, "lru", Np) for i in range(6)]
#pools = [ftlsim.pool(ftl, "lru", Np) for i in range(5)]
#pools.append(ftlsim.pool(ftl, "greedy", Np))

lens = (0.0873, 0.0452, 0.0275, 0.0229, 0.0327, 0)
pools_n_lens = zip(lens, pools)
prev = None
for p,pool in pools_n_lens:
    if prev:
        prev.next_pool = pool
    prev = pool
pools[-1].next_pool = pools[-1]

util_sum = dict()
util_n = dict()
for pool in pools:
    util_sum[pool] = 0.0
    util_n[pool] = 0

def clean_select():
    global pools
    for p,pool in pools_n_lens:
        if pool.length > p*T:
            if doprint:
                print pool.name, pool.tail_util()
            util_sum[pool] += pool.tail_util()
            util_n[pool] += 1
            ftlsim.return_pool(pool)
            return

def printit(pool):
    global pool1, pool2, pool3
    n = 1 if pool == pool1 else 2 if pool == pool2 else 3
    hot,cold,inv = (0,0,0)
    seg = pool.tail_segment()
    for i in range(Np):
        lba = seg.page(i)
        if lba == -1:
            inv += 1
        elif lba < U_h:
            hot += 1
        else:
            cold += 1
    print n, hot, cold

doprint = False

ftl.get_pool_to_clean_arg = clean_select

# Allocate segments...
#
freelist = [ftlsim.segment(Np) for i in range(T+minfree)]
for b in freelist:
    b.thisown = False

    #for pool in (pool1, pool2, pool2a, pool2b, pool2c, pool3):
for pool in pools:
    pool.add_segment(freelist.pop())
for b in freelist:
    ftl.put_blk(b)

# use a sequential address source to write each page once
#
seq = getaddr.seq()
ftl.run(seq.handle, U*Np);

print "ready..."

# Now run with uniform random traffic for 10 units of 0.1 volume each.
#
U_h = int(f*U*Np)
U_c = U*Np - U_h

src_h = getaddr.uniform(U_h)
src_h.thisown = False
src_c = getaddr.uniform(U_c)
src_c.thisown = False
src = getaddr.mixed()
src.add(src_h.handle, r, 0)
src.add(src_c.handle, 1.0, U_h)

src_u = getaddr.uniform(U*Np)

def poolutil(pool):
    ns = [0 for i in range(Np+1)]
    seg = pool.next_segment(None)
    while seg != None:
        ns[seg.n_valid] += 1
        seg = pool.next_segment(seg)
    for i in range(Np+1):
        if ns[i] > 0:
            print i, ns[i]

def poolinfo(pool):
    seg = pool.next_segment(None)
    hot,cold,inv = (0,0,0)
    while seg != None:
        for j in range(Np):
            lba = seg.page(j)
            if lba == -1:
                inv += 1
            elif lba < U_h:
                hot += 1
            else:
                cold += 1
        seg = pool.next_segment(seg)
    return (hot,cold,inv)

ftl.ext_writes = 0
ftl.int_writes = 0
sum_e = 0
sum_i = 0
ftl.run(src.handle, 2*U*Np)
ftl.ext_writes = 0
ftl.int_writes = 0
print "r2"

for pool in pools:
    print pool.invalidations
    pool.invalidations = 0


#doprint = True
for i in range(30):
    ftl.run(src.handle, U*Np/10)
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes
    for pool in []: #pools:
        u = 0.0
        if util_n[pool]:
            u = util_sum[pool] / util_n[pool]
        util_sum[pool] = 0.0
        util_n[pool] = 0
        print u,
        #print

    sum_e += ftl.ext_writes
    sum_i += ftl.int_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0

print (1.0*sum_i)/sum_e

for i in range(len(pools)):
    (h,c,inv) = poolinfo(pools[i])
    print i, h, c, inv, pools[i].invalidations

