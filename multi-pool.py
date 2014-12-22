#
#
import getaddr
import ftlsim
import math
import sys

from optparse import OptionParser

usage = "%prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("", "--Np", type='int', default=128)
parser.add_option("", "--T", type='int')
parser.add_option("", "--U", type='int', default=30000)
parser.add_option("", "--Sf", type='float')
parser.add_option("", "--r", type='float')
parser.add_option("", "--f", type='float')
parser.add_option("", "--alpha", type='float')
parser.add_option("", "--minfree", type='int', default=2)
parser.add_option("", "--N", type='int', default=30)
parser.add_option("", "--pools", type='int', default=3)
parser.add_option("", "--equal", action='store_true', default=False)
parser.add_option("", "--sizes")

(opts, args) = parser.parse_args()

Np = opts.Np
if opts.Sf:
    alpha = 1 / (1-opts.Sf)
elif opts.alpha:
    alpha = opts.alpha
else:
    print "specify either alpha or Sf"
    sys.exit()

U = opts.U
minfree = 3
T = int(U * alpha) 
r = opts.r
f = opts.f

print "U, T, total", U, T, T*Np

if opts.sizes:
    pool_sizes = map(float, opts.sizes.split(','))
    if len(pool_sizes) != opts.pools-1:
        print "sizes", opts.sizes, "doesn't match pools:", opts.pools
        sys.exit(1)
    pool_sizes.append(1-sum(pool_sizes))
        
# FTL with default parameters for single pool
#
ftl = ftlsim.ftl(T, Np)
ftl.minfree = minfree
ftl.maxfree = minfree
ftl.get_input_pool = ftlsim.cvar.write_select_first
#ftl.get_pool_to_clean = ftlsim.cvar.clean_select_first
ftl.get_pool_to_clean = ftlsim.cvar.clean_select_python

#
pools = [ftlsim.pool(ftl, "lru", Np) for i in range(opts.pools)]

prev = None
for pool in pools:
    pool.next_pool = pool
    pool.n = 0
    pool.sum = 0.0
    if prev:
        prev.next_pool = pool
    prev = pool


def clean_select_equal():
    global pools
    p = max(pools, key=lambda p: p.pages_invalid)
    p.n += 1
    p.sum += p.tail_util()
    ftlsim.return_pool(p)

def clean_select_sizes():
    global pools
    for p,pool in zip(pool_sizes,pools):
        if pool.length > (p*T - 1):
            pool.n += 1
            pool.sum += pool.tail_util()
            ftlsim.return_pool(pool)

if opts.sizes:
    ftl.get_pool_to_clean_arg = clean_select_sizes
else:
    ftl.get_pool_to_clean_arg = clean_select_equal

doprint = False

# Allocate segments...
#
freelist = [ftlsim.segment(Np) for i in range(T+minfree)]
for b in freelist:
    b.thisown = False

for pool in pools:
    pool.add_segment(freelist.pop())
for b in freelist:
    ftl.put_blk(b)

# prepare
#
fill = getaddr.fill(T, U)
ftl.run(fill.handle, U*Np);

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

sum_e = 0
sum_i = 0

ftl.ext_writes = 0
ftl.int_writes = 0

#doprint = True
for i in range(opts.N):
    ftl.run(src.handle, U*Np/10)
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes

    for p in pools:
        u0 = p.pages_invalid*1.0 / (T*Np)
        print "  p=%f %f" % (p.length * 1.0 / T, u0),
        if p.n > 0:
            x = p.sum / p.n
            p.sum,p.n = 0.0,0
            t0 = p.length * 1.0 / T
            if x == 0:
                print
            else:
                L = math.log(1/x)
                if L == 0:
                    print
                else:
                    u1 = t0 + t0 * (x-1) / L
                    print " %f %f %f" % (x, u1, u0/u1)

    sum_e += ftl.ext_writes
    sum_i += ftl.int_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0

print (1.0*sum_i)/sum_e

