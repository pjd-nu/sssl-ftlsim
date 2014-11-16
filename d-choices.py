#
# file:        low-level.py
# description: Example LRU cleaning using Python address generation
#              and low-level FTL routines. 
#
# Peter Desnoyers, Northeastern University, 2012
#
# Copyright 2012 Peter Desnoyers
# This file is part of ftlsim.
# ftlsim is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. 
#
# ftlsim is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details. 
# You should have received a copy of the GNU General Public License
# along with ftlsim. If not, see http://www.gnu.org/licenses/. 
#

import getaddr
import ftlsim
import numpy

# parameters
from optparse import OptionParser

usage = "%prog [options]"

parser = OptionParser(usage=usage)
parser.add_option("", "--Np", type='int')
parser.add_option("", "--U", type='int')
parser.add_option("", "--Sf", type='float')
parser.add_option("", "--minfree", type='int', default=3)
parser.add_option("", "--N", type='int', default=10)
parser.add_option("", "--tracefile")
parser.add_option("", "--r", type='float')
parser.add_option("", "--f", type='float')
parser.add_option("", "--stop", action='store_true', default=False)
parser.add_option("", "--d", type='int')

(opts, args) = parser.parse_args()
if len(args):
    parser.error("what?")
U, Np, S_f, d = opts.U, opts.Np, opts.Sf, opts.d

alpha = 1 / (1-S_f)
minfree = opts.minfree
T = int(U * alpha) + minfree

# moving parts
#
src = getaddr.uniform(U*Np)
if opts.tracefile:
    src = getaddr.trace(opts.tracefile)
rmap = ftlsim.ftl(T, Np)
pool = ftlsim.pool(rmap, "null", Np)

in_pool = numpy.zeros(T, numpy.int8)

# allocate segments, make sure to set .thisown = false
#
freelist = [ftlsim.segment(Np) for i in range(T)]
for b in freelist:
    b.thisown = False

# Start off with a write frontier
#
pool.frontier = freelist.pop()
pool.i = 0

intwrites = 0
extwrites = 0

# individual flash page write (internal copy or external write)
#
def int_write(lba):
    global pool, rmap
    global intwrites, extwrites

    intwrites += 1
    b = rmap.find_blk(lba)
    if b is not None:
        pg = rmap.find_page(lba)
        b.overwrite(pg, lba)
    f = pool.frontier
    f.write_ftl(rmap, pool.i, lba)
    pool.i += 1
    if pool.i >= Np:
        in_pool[f.blkno] = 1
        pool.frontier = freelist.pop()
        pool.i = 0
        
import random

def min_valid(a, b):
    return a.n_valid - b.n_valid

def get_segment():
    global pool, d
    ii = set([random.randint(0,T-1) for i in range(d)])
    segs = [ftlsim.get_segment(i) for i in ii]
    segs = filter(lambda x: in_pool[x.blkno], segs)
    return min(segs, key=lambda b: b.n_valid)
    
# external host write - write the LBA and then do on-demand cleaning
#
def host_write(lba):
    global pool, rmap
    global intwrites, extwrites
    extwrites += 1

    int_write(lba)
    
    while len(freelist) < minfree:
        b = get_segment()
        in_pool[b.blkno] = 0
        for i in range(Np):
            a = b.page(i)
            if a != -1:
                int_write(a)
        freelist.append(b)

# initialize
T0 = T-minfree
fill = getaddr.fill(T0, U)
for a in range(T0*Np):
    host_write(fill.handle.next())
extwrites,intwrites = 0,0

print "ready..."

# Now write a full volume's worth of random data.
#
for i in range(opts.N):
    for j in range(U*Np/10):
        a = src.handle.next()
        if a == -1:
            src = getaddr.trace(opts.tracefile)
            continue
        host_write(a)

    print extwrites, intwrites, (1.0*intwrites)/extwrites
    extwrites = 0
    intwrites = 0

        # e = [0] * T
        # for i in range(T):
        #     s = ftlsim.get_segment(i)
        #     if s is None:
        #         continue
        #     e[s.n_valid] += 1

        # for i in range(T):
        #     if e[i]:
        #          print i, e[i]
        # print '----'

