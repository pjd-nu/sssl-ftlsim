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
T = 2048 * 8 * 8
U = T - T*8/100
T = T - T/100

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
minfree = 1

ftl = ftlsim.ftl(T, Np)

# Greedy-managed pools - one for each plane, organized by element
#
elements = []
for i in range(nelements):
    planes = [ftlsim.pool(ftl, "greedy", Np) for j in range(nplanes)]
    elements.append(planes)

# allocate segments, with one freelist per plane
#
freelist = []
for i in range(nelements):
    lists = []
    for j in range(nplanes):
        list = [ftlsim.segment(Np)
                for i in range(minfree + T/(nplanes*nelements))]
        for s in list:
            s.thisown = False
        lists.append(list)
    freelist.append(lists)

for i in range(nelements):
    for j in range(nplanes):
        elements[i][j].add_segment(freelist[i][j].pop())

intwrites = 0
extwrites = 0

verbose = False
# individual flash page write (internal copy or external write)
#
def int_write(ftl, elem, plane, lba):
    global intwrites, elements, freelist
    intwrites += 1
    b = ftl.find_blk(lba)
    if b is not None:
        pg = ftl.find_page(lba)
        b.overwrite(pg, lba)
    p = elements[elem][plane]

    if verbose:
        print "write %d %d %d %d" % (lba, p.frontier.blkno * Np + p.i,
                                     plane, elem)
    p.frontier.write(p.i, lba)
    p.i += 1
    if p.i >= Np:
        p.add_segment(freelist[elem][plane].pop())

# block allocation for new writes - pick the last plane used, unless
# it has fewer free blocks than another one.
#
plane_to_write = [0] * nplanes
def get_plane(elem):
    global elements, last_element, nelements, freelist
    i = plane_to_write[elem]
    n = len(freelist[elem][i])
    for j in range(nplanes):
        k = (i+j) % nplanes
        if len(freelist[elem][k]) > n:
            break
    plane_to_write[elem] = k
    return k

# external host write - write the LBA and then do on-demand cleaning
#
def host_write(lba):
    global ftl, elements, extwrites
    extwrites += 1

    # writes are striped by LBA between elements; plane selection
    # logic is in the function above
    #
    elem = lba % nelements
    plane = get_plane(elem)
    int_write(ftl, elem, plane, lba)
    
    while len(freelist[elem][plane]) < minfree:
        pool = min(elements[elem], key=lambda(p): p.tail_util())
        b = pool.remove_segment()
        for i in range(Np):
            a = b.page(i)
            if a != -1:
                plane2 = get_plane(elem)
                int_write(ftl, elem, plane2, a)
        freelist[elem][plane].append(b)

# initialize by writing every LBA once
#
print 'writing', U*Np
for a in range(U*Np):
    host_write(a)
    if a % 100000 == 99999:
        print a+1

print "ready..."
#verbose = True
import sys
file = sys.argv[1]
sum_e = 0
sum_i = 0
src = getaddr.trace(file)

# Now write a full volume's worth of random data.
#
i,j = 0,0
while not src.eof:
    ext_writes,int_writes = 0,0
    i=0
    a = src.handle.next()
    while i < 100000 and a != -1 and not src.eof:
        host_write(a)
        a = src.handle.next()
        i += 1
    if extwrites > 0:
        print extwrites, intwrites, (1.0*intwrites)/extwrites
    sum_e += ext_writes
    sum_i += int_writes

print (1.0*sum_i)/sum_e
