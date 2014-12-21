#
# file:        fast.py
# description: Fully Associative Sector Translation (FAST) FTL
#
# Peter Desnoyers, Northeastern University, 2014
#
# Copyright 2014 Peter Desnoyers
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

from optparse import OptionParser

usage = "%prog [options] tracefile"

parser = OptionParser(usage=usage)
parser.add_option("", "--Np", type='int')
parser.add_option("", "--T", type='int')
parser.add_option("", "--U", type='int')
parser.add_option("", "--Sf", type='float')
parser.add_option("", "--minfree", type='int', default=2)
parser.add_option("", "--maxfree", type='int')
parser.add_option("", "--tracefile")
(opts, args) = parser.parse_args()

U, Np, S_f = opts.U, opts.Np, opts.Sf
alpha = 1 / (1-S_f)
minfree = opts.minfree
maxfree = max(opts.maxfree, minfree)
T = int(U * alpha) + minfree

src = getaddr.uniform(U*Np)
rmap = ftlsim.ftl(T, Np)
pool = ftlsim.pool(rmap, "null", Np)

# allocate and initialize data blocks. Note that we need a pool to
# connect segments to the FTL rmap, but it doesn't do anything.
#
data = [ftlsim.segment(Np) for i in range(U)]
for i in range(U):
    b = data[i]
    b.thisown = False
    b.blkno = i
    pool.add_segment(b)
    for j in range(Np):
        b.write_ftl(rmap, j, i*Np+j)

lru_queue = []
L = T - U - minfree

# allocate free list segments
#
freelist = [ftlsim.segment(Np) for i in range(T - U)]
for b in freelist:
    b.thisown = False
    b.i = 0                             # index to write at
    b.sequential = True                 # only needs to live until we merge


# Standard statistics...
#
intwrites = 0
extwrites = 0
def l_blknum(lba):
    return lba / Np

def seq_merge(b, n):
    global freelist, data, intwrites
    blkno = l_blknum(b.page(0))
    tmp = data[blkno]
    for i in range(n, Np):
        lba = blkno*Np + i
        assert tmp.page(i) == lba
        assert b.page(i) == -1
        b.write_ftl(rmap, i, lba)
        intwrites += 1
    data[blkno] = b
    tmp.erase()
    freelist.append(tmp)
    
# FAST log block merge. 
#
def full_merge(b):
    global data, freelist, intwrites

    blknos = set([l_blknum(b.page(i))
                  for i in range(Np)])
    for blkno in blknos:
        tmp = data[blkno]
        b2 = freelist.pop(0)
        for i in range(Np):            # we don't bother looking up
            lba = blkno*Np + i         # to see which block it's in...
            assert b2.page(i) == -1
            b2.write_ftl(rmap, i, lba)
            intwrites += 1
        tmp.erase()
        freelist.append(tmp)
        data[blkno] = b2
    b.erase()
    freelist.append(b)

seq_lba, seq = -1, freelist.pop(0)
index, frontier = 0, freelist.pop(0)

# the write function itself. all the work is done above
#
def fast_write(lba):
    global extwrites, seq_lba, seq, frontier, index, lru_queue
    extwrites += 1

    if lba == seq_lba or (lba % Np == 0 and seq_lba == -1):
        seq.write_ftl(rmap, lba % Np, lba)
        seq_lba = lba + 1
        if seq_lba % Np == 0:
            seq_merge(seq, Np)
            seq, seq_lba = freelist.pop(0), -1
        return

    if seq_lba != -1:
        seq_merge(seq, seq_lba % Np);
        seq,seq_lba = freelist.pop(0), -1

    frontier.write_ftl(rmap, index, lba)
    index += 1
    if index == Np:
        lru_queue.append(frontier)
        frontier,index = freelist.pop(0), 0

    while len(freelist) < minfree:
        b = lru_queue.pop(0)
        full_merge(b)

print "ready..."

# Now write a full volume's worth of random data.
#
i,j = 0,0
for a in src.handle.addrs():
    fast_write(a)
    i += 1
    if i >= U*Np/10:
        i = 0
        print extwrites, intwrites, (1.0*intwrites)/extwrites
        extwrites = 0
        intwrites = 0
        j += 1
        if j > 10:
            break

