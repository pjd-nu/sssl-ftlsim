#
#
import getaddr
import ftlsim

# parameters
#
U = 2302
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
#ftl.get_input_pool = ftlsim.cvar.write_select_first
ftl.get_pool_to_clean = ftlsim.cvar.clean_select_python

# Greedy-managed pool
#
pool1 = ftlsim.pool(ftl, "lru", Np)
pool2 = ftlsim.pool(ftl, "lru", Np)
pool3 = ftlsim.pool(ftl, "greedy", Np)
pool1.next_pool = pool2
pool2.next_pool = pool3
pool3.next_pool = pool3

x = True
def clean_select():
    global pool1, pool2, pool3
    pools = filter(lambda x: x.pages_invalid >= 2*Np, (pool1, pool2, pool3))
    pool = max(pools, key=lambda x:
                   float(x.pages_invalid)/(x.pages_valid+x.pages_invalid))
    ftlsim.return_pool(pool)

ftl.get_pool_to_clean_arg = clean_select

# Allocate segments...
#
freelist = [ftlsim.segment(Np) for i in range(T+Np)]
for b in freelist:
    b.thisown = False
for pool in (pool1, pool2, pool3):
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
r = 0.8
f = 0.1
U_h = int(f*U*Np)
U_c = U*Np - U_h

src_h = getaddr.uniform(U_h)
src_h.thisown = False
src_c = getaddr.uniform(U_c)
src_c.thisown = False
src = getaddr.mixed()
src.add(src_h.handle, r, 0) 
src.add(src_c.handle, 1.0, U_h)

def showpool(pool):
    hot = 0; cold = 0
    seg = pool.next_segment(None)
    while seg != None:
        for j in range(Np):
            lba = seg.lbas[j].val
            if lba > -1:
                if lba < U_h:
                    hot += 1
                else:
                    cold += 1
        seg = pool.next_segment(seg)
    print "%d %d %.3f" % (hot, cold, float(hot)/(hot+cold+1))

ftl.ext_writes = 0
ftl.int_writes = 0
sum_e = 0
sum_i = 0
for i in range(30):
    ftl.run(src.handle, U*Np/10)
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes
    for pool in (pool1, pool2, pool3):
        showpool(pool)
    sum_e += ftl.ext_writes
    sum_i += ftl.int_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0

print (1.0*sum_i)/sum_e

