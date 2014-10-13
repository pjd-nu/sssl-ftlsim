#
# file:        hybrid-log.py
# description: Example Hybrid Log Block (BAST) FTL
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

# parameters
import opt, sys
opts = opt.parse(sys.argv[1])
U,Np = opts.U, opts.Np
log_blks = opts.log_blks

minfree = opts.minfree
T = U + log_blks + minfree

# moving parts
#
src = genaddr.uniform(U*Np)
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

# this is the look-aside array holding active log blocks
#
logs = [None] * U
log_list = []

# allocate free list segments
#
freelist = [ftlsim.segment(Np) for i in range(T-U)]
for b in freelist:
    b.thisown = False
    b.i = 0                             # index to write at
    b.sequential = True                 # only needs to live until we merge
    pool.add_segment(b)


# Standard statistics...
#
intwrites = 0
extwrites = 0
erasures = 0

def verify():
    for b in logs:
        if b is not None:
            assert b in log_list

# Standard hybrid log block merge. Note that we have to remove blocks
# from both the log map and the log round-robin list
#
def hlb_merge(b):
    global data, log, freelist, log_list, intwrites, erasures
    blkno = b.blkno
    tmp = data[b.blkno]
    if b.sequential:
        if b.i == Np:
            pass                        # switch merge
        else:                           # partial merge
            for i in range(b.i, Np):
                lba = blkno*Np + i
                assert tmp.page(i) == lba
                assert b.page(i) == -1
                b.write(i, lba)
                intwrites += 1
        data[blkno] = b
        logs[blkno] = None
        log_list.remove(b)
        tmp.erase()
        freelist.append(tmp)
        erasures += 1
    else:                               # full merge
        b2 = hlb_get_free_blk(0)
        for i in range(Np):            # we don't bother looking up
            lba = blkno*Np + i         # to see which block it's in...
            assert b2.page(i) == -1
            b2.write(i, lba)
            intwrites += 1
        tmp.erase()
        freelist.append(tmp)
        data[blkno] = b2
        logs[blkno] = None
        log_list.remove(b)
        b.erase()
        freelist.append(b)
        erasures += 2

# get a block, evicting and merging if necessary
#
def hlb_get_free_blk(nfree):
    global data, logs, freelist, log_list
    while len(freelist) < nfree:
        b = log_list[0]
        hlb_merge(b)
    return freelist.pop(0)

# get log block for an address, allocating if necessary
#
def hlb_log_block(lba):
    global data, logs, freelist, log_list
    blk = lba / Np
    if logs[blk] is None:
        b = hlb_get_free_blk(2)
        b.blkno = blk
        b.i = 0
        b.sequential = True
        logs[blk] = b
        log_list.append(b)
    return logs[blk]

# the write function itself. all the work is done above
#
def hlb_write(lba):
    global extwrites
    extwrites += 1
    b = hlb_log_block(lba)
    offset = lba % Np
    if b.i != offset:
        b.sequential = False
    b.write(b.i, lba)
    b.i += 1
    if b.i == Np:
        hlb_merge(b)

print "ready..."

# Now write a full volume's worth of random data.
#
i,j = 0,0
for a in src.addrs():
    hlb_write(a)
    verify()
    i += 1
    if i >= U*Np/10:
        i = 0
        print extwrites, intwrites, (1.0*intwrites)/extwrites
        extwrites = 0
        intwrites = 0
        j += 1
        if j > 10:
            break

