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

# This replicates a configuration of the MSR modifications to Disksim,
# with the following parameters:
#   Blocks per plane = 2048,
#   Planes per package = 8,
#   Flash chip elements = 8, 
#   Page size = 8,
#   Pages per block = 64,
#   Reserve pages percentage = 8
#   Minimum free blocks percentage = 1
#
# Yes, it's slow. It's probably even slower than the MSR simulator.

import getaddr
import ftlsim

# Total blocks and user-visible blocks, based on parameters above
#
T_plane = 2048
U_plane = 2048 - 163
minfree = 20                            # blocks per plane
minfree_elmt = 164

T = T_plane * 8 * 8
U = U_plane * 8 * 8

# The MSR simulator reserves one page per block for mapping
# information, so only N-1 can be used for user data.
#
Np = 63

# Simulating 8 flash packages (or maybe more properly channels) with 8
# planes each.
#
nelements = 8
nplanes = 8
npools = nelements * nplanes

ftl = ftlsim.ftl(T, Np)

elements = [ftlsim.pool(ftl, "greedy", Np) for i in range(nelements)]
for e in elements:
    e.msr = 1

# allocate segments, with one freelist per element
#
blks_per_plane = T/(nplanes*nelements)
blks_per_elmt = nplanes * blks_per_plane

freemap = [ [None] * blks_per_elmt for i in range(nelements) ]
next_free = [0] * nelements
blks_free = [0] * nelements

freelists = []
for i in range(nelements):
    list = [ftlsim.segment(Np) for j in range(blks_per_elmt)]
    for s,j in zip(list,range(blks_per_elmt)):
	s.thisown = False
	s.elem = i
	s.blkno = j
    freelists.append(list)

import copy
physblks = [ copy.copy(map) for map in freemap ]

def getblk(elmt):
    global freemap, next_free, blks_free
    assert blks_free[elmt] > 0
    _map = freemap[elmt]
    i = next_free[elmt] % blks_per_elmt
    #j = i
    while True:                 # fails for full map, but much faster
	if _map[i] is not None:  # than range()
	    tmp = _map[i]
	    _map[i] = None
	    blks_free[elmt] -= 1
	    next_free[elmt] = i
	    assert tmp.elem == elmt
	    return tmp
        i = (i+1) % blks_per_elmt
    return None

def putblk(elmt, blk):
    global freemap, blks_free
    assert blk.elem == elmt
    _map = freemap[elmt]
    idx = (blk.blkno % nplanes) * blks_per_plane + blk.blkno / nplanes
    assert _map[idx] is None
    _map[idx] = blk
    blks_free[elmt] += 1
    
for i in range(nelements):
    elements[i].add_segment(freelists[i].pop(0))

intwrites = 0
extwrites = 0

verbose = True

# MSR algorithm - write at active page in active block, then go to next free block.
# blocks numbered 0..N-1 in element, if full_stripe then (block mod N_elements) = plane
#
# individual flash page write (internal copy or external write)
#
def int_write(ftl, elem, lba):
    global intwrites, elements
    intwrites += 1
    b = ftl.find_blk(lba)
    if b is not None:
        pg = ftl.find_page(lba)
        b.overwrite(pg, lba)
    e = elements[elem]

    # lpn active_page active_plane elem_num
    if verbose:
        print "write: %d %d %d %d" % (lba/nelements,
                                     e.frontier.blkno * (Np+1) + e.i,
                                     e.frontier.blkno % nplanes, elem)
    e.frontier.write(e.i, lba)
    e.i += 1
    #print e.frontier.blkno*64 + e.i
    if e.i >= Np:
        e.add_segment(getblk(elem))

# external host write - write the LBA and then do on-demand cleaning
#
def host_write(lba):
    global ftl, elements, extwrites
    extwrites += 1

    # writes are striped by LBA between elements
    #
    elem = lba % nelements
    int_write(ftl, elem, lba)

    if blks_free[elem] < minfree_elmt:
	pool = elements[elem]
	while blks_free[elem] <= minfree_elmt:
	    b = pool.remove_segment()
	    for i in range(Np):
		a = b.page(i)
		if a != -1:
		    int_write(ftl, elem, a)
	    putblk(elem, b)

# initialize by writing every LBA once. inlined from int_write...
#
#print 'writing', U*Np
for lba in range(U*Np):
    elem = lba % nelements
    e = elements[elem]
    e.frontier.write(e.i, lba)
    e.i += 1
    if e.i >= Np:
        e.add_segment(freelists[elem].pop(0))

for e in range(nelements):
    for b in freelists[e]:
	putblk(e, b)

def printall():
    for i in range(nelements):
        print 'element', i
        print 'physical blocks:'
        _map = physblks[i]
        for j in range(blks_per_elmt):
            b = _map[j]
            print j,
            for k in range(Np):
                print b.page(k)/nelements, 
            print '-1 '
        print 'logical blocks:'
        lba = 0
        lba_max = U_plane * nplanes * Np
        pool = elements[i]
        while lba < lba_max:
            for k in range(63):
                b = ftl.find_blk(lba*nplanes + i)
                p = ftl.find_page(lba*nplanes + i)
                print b.blkno * (Np+1) + p,
                lba += 1
            print ''

    import sys
    sys.exit(0)

# for a in range(U*Np):
#     host_write(a)
#     if False and a % 100000 == 99999:
#         print a+1

import sys
file = sys.argv[1]
sum_e = 0
sum_i = 0
src = getaddr.trace(file)

# Now write a full volume's worth of random data.
#
i,j = 0,0
while not src.eof:
    extwrites,intwrites = 0,0
    i=0
    a = src.handle.next()
    while i < 100000 and a != -1 and not src.eof:
        host_write(a)
        a = src.handle.next()
        i += 1
    if extwrites > 0 and not verbose:
        print extwrites, intwrites, (1.0*intwrites)/extwrites
    sum_e += extwrites
    sum_i += intwrites

if not verbose:
    print (1.0*sum_i)/sum_e

#printall()
