#
#
import getaddr
import ftlsim
import sys

# parameters
#
U = 23020
Np = 128
#S_f = 0.1
#alpha = 1 / (1-S_f)
alpha = 1.1
alpha = 1.07
minfree = Np
minfree = 3
T = int(U * alpha) 

# FTL with default parameters for single pool
#
ftl = ftlsim.ftl(T, Np)
ftl.minfree = minfree
ftl.get_input_pool = ftlsim.cvar.write_select_first
#ftl.get_pool_to_clean = ftlsim.cvar.clean_select_first
ftl.get_pool_to_clean = ftlsim.cvar.clean_select_python

# Greedy-managed pool
#
pool1 = ftlsim.pool(ftl, "lru", Np)
pool2 = ftlsim.pool(ftl, "lru", Np)
pool2a = ftlsim.pool(ftl, "lru", Np)
pool2b = ftlsim.pool(ftl, "lru", Np)
pool2c = ftlsim.pool(ftl, "lru", Np)
pool2d = ftlsim.pool(ftl, "lru", Np)
pool3 = ftlsim.pool(ftl, "greedy", Np)


# Uu = dict()
# Nn = dict()
# for p in (pool1, pool2, pool2a, pool3):
#     Uu[p] = 0.0; Nn[p] = 0

#pools = ((0.0997,pool1), (0,pool3))
#pools = ((0.0935,pool1), (0.0683,pool2), (0,pool3))


# pools = ((0.0736,pool1), (0.0412,pool2), (0,pool3)) # for 0.9/0.05
# pools = ((0.1128,pool1), (0.0864,pool2), (0,pool3)) # 80/20
# pools = ((0.0877,pool1), (0.0615,pool2), (0.0520,pool2a), (0,pool3))
# pools = ((0.1100,pool1), (0.0840,pool2), (0.0670,pool2a), (0,pool3)) # 80/20

# #pools = ((0.0851, pool1), (0.0565, pool2), (0.0445, pool2a), (0.0467, pool2b), (0, pool3))

# #pools = ((0.0849,pool1), (0.0548,pool2), (0.0415,pool2a), (0.0408,pool2b), (0.0563,pool2c), (0,pool3))
# #pools = ((0.0850,pool1), (0.0546,pool2), (0.0415,pool2a), (0.0406,pool2b), (0.0559,pool2c), (0.0780,pool2d), (0,pool3))
# lens = (0.1090, 0.0802, 0.0620, 0.0512, 0.0464, 0.0468, 0)
lens = (0.0643, 0.0399, 0.0266, 0.0200, 0.0184, 0.0236, 0)
pools = zip(lens, (pool1, pool2, pool2a, pool2b, pool2c, pool2d, pool3))

# lens = (0.1089, 0.0811, 0.0634, 0.0533, 0.0494, 0)
# pools = zip(lens, (pool1, pool2, pool2a, pool2b, pool2c, pool3))
# lens = (0.1096, 0.0826, 0.0655, 0.0560, 0)
# pools = zip(lens, (pool1, pool2, pool2a, pool2b, pool3))
# lens = (0.1110, 0.0846, 0.0678, 0)
# pools = zip(lens, (pool1, pool2, pool2a, pool3))
# lens = (0.1128, 0.0864, 0)
# pools = zip(lens, (pool1, pool2, pool3))
# lens = (0.1144, 0)
# pools = zip(lens, (pool1, pool3))
# pools = ((0, pool3),)
# pool1.next_pool = pool2
# pool2.next_pool = pool2a
# pool2a.next_pool = pool2b
# pool2b.next_pool = pool3
# #pool2c.next_pool = pool3
# pool3.next_pool = pool3

#pools = ((0,pool3),)

prev = None
for p,pool in pools:
    if prev:
        prev.next_pool = pool
    prev = pool
pool3.next_pool = pool3

def clean_select():
    global pools
    for p,pool in pools:
        if pool.length > p*T:
            if doprint:
                print pool.name, pool.tail_util()
            #Uu[pool] += pool.tail_util()
            #Nn[pool] += 1
            ftlsim.return_pool(pool)
            return

def clean_select2():
    global pool1, pool2, pool3
    pools = filter(lambda x: x.pages_invalid >= 2*Np, (pool1, pool2, pool3))
    pool = max(pools, key=lambda x: x.length)
    ftlsim.return_pool(pool)

def printit(pool):
    global pool1, pool2, pool3
    n = 1 if pool == pool1 else 2 if pool == pool2 else 3
    hot,cold,inv = (0,0,0)
    seg = pool.tail_segment()
    for i in range(Np):
        lba = seg.lbas[i].val
        if lba == -1:
            inv += 1
        elif lba < U_h:
            hot += 1
        else:
            cold += 1
    print n, hot, cold

doprint = False

def clean_select3():
    global pool1, pool2, pool3, doprint
    for p in (pool1,pool2):
        if p.length > 0.06*T:
            if doprint:
                print p.name, p.tail_util()
            ftlsim.return_pool(p)
            return
    if doprint:
        print pool3.name, pool3.tail_util()
    ftlsim.return_pool(pool3)

ftl.get_pool_to_clean_arg = clean_select

# Allocate segments...
#
freelist = [ftlsim.segment(Np) for i in range(T+minfree)]
for b in freelist:
    b.thisown = False

    #for pool in (pool1, pool2, pool2a, pool2b, pool2c, pool3):
for p,pool in pools:
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
f = 0.2
r = 0.9
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

# rr = [0.64, 0.42, 0.04];
# ff = [0.04, 0.16, 0.8];
# u1 = int(ff[0]*U*Np)
# u2 = int(ff[1]*U*Np)
# u3 = U*Np - u1 - u2
# src_1 = getaddr.uniform(u1)
# src_1.thisown = False
# src.add(src_1.handle, rr[0], 0)
# src_2 = getaddr.uniform(u2)
# src_2.thisown = False
# src.add(src_2.handle, sum(rr[0:2]), u1)
# src_3 = getaddr.uniform(u3)
# src_3.thisown = False
# src.add(src_3.handle, sum(rr[0:3]), u1+u2)

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
            lba = seg.lbas[j].val
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
ftl.run(src.handle, U*Np*5/3)
ftl.ext_writes = 0
ftl.int_writes = 0

#doprint = True
for i in range(30):
    ftl.run(src.handle, U*Np/5)
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes
    #print " ", float(pool3.pages_valid + pool3.pages_invalid) / pool3.pages_valid #, pool2.pages_valid, pool2.pages_invalid
    #if Nn[pool3] > 0:
    #print Uu[pool3] / Nn[pool3]
    #Uu[pool3] = 0.0; Nn[pool3] = 0
    #poolutil(pool2)
    #h1,c1,i1 = poolinfo(pool1)
    #h2,c2,i2 = poolinfo(pool3)
    #h3 = U_h - h1 - h2
    #c3 = U_c - c1 - c2
    #i3 = Np*(T - U) - i1 - i2
    #for pair in ((h2,c2,i2),): #((h1,c1,i1), (h2,c2,i2)): #, 
    #h,c,ii = pair
    #print "%d %d %d %.3f" % (h, c, ii, float(h)/(1+h+c))

    sum_e += ftl.ext_writes
    sum_i += ftl.int_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0

print (1.0*sum_i)/sum_e

