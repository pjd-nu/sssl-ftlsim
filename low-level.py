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

import genaddr
import ftlsim

# parameters
#
U = 23020
Np = 64
S_f = 0.091
alpha = 1 / (1-S_f)
minfree = Np
T = int(U * alpha) + minfree

# moving parts
#
src = genaddr.uniform(U*Np)
rmap = ftlsim.ftl(T, Np)
lru = ftlsim.pool(rmap, "lru", Np)

# allocate segments, make sure to set .thisown = false
#
freelist = [ftlsim.segment(Np) for i in range(T)]
for b in freelist:
    b.thisown = False
    b.elem = 0
    
# Start off with a write frontier
#
lru.add_segment(freelist.pop())

intwrites = 0
extwrites = 0

t = 0
# individual flash page write (internal copy or external write)
#
def int_write(lba):
    global lru, rmap, t
    global intwrites, extwrites

    intwrites += 1
    b = rmap.find_blk(lba)
    if b is not None:
        pg = rmap.find_page(lba)
        b.overwrite(pg, lba)
    f = lru.frontier
    f.write(lru.i, lba)
    lru.i += 1
    if lru.i >= Np:
        f.elem = t
        t += 1
        lru.add_segment(freelist.pop())
        

# external host write - write the LBA and then do on-demand cleaning
#
def host_write(lba):
    global lru, rmap
    global intwrites, extwrites
    extwrites += 1

    int_write(lba)
    
    while len(freelist) < minfree:
        b = lru.get_segment()
        for i in range(Np):
            a = b.page(i)
            if a != -1:
                int_write(a)
        freelist.append(b)

# initialize by writing every LBA once
#
for a in range(U*Np):
    host_write(a)

print "ready..."

# Now write a full volume's worth of random data.
#
i,j = 0,0
for a in src.addrs():
    host_write(a)
    i += 1
    if i >= U*Np/10:
        i = 0
        print extwrites, intwrites, (1.0*intwrites)/extwrites
        extwrites = 0
        intwrites = 0
        j += 1
        if j > 15:
            break

        if j > 10:
            for i in range(T):
                s = ftlsim.get_segment(i)
                if s is None or not s.in_pool:
                    continue
                print t - s.elem, s.n_valid
            print '----'

