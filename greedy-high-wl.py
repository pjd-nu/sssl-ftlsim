#
# file:        greedy-high.py
# description: Example Greedy cleaning simulation using high-speed routines
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
U,Np,minfree = opts.U, opts.Np, opts.minfree

alpha = 1 / (1-opts.S_f)
T = int(U * alpha) + minfree + 1

# FTL with default parameters for single pool
#
ftl = ftlsim.ftl(T, Np)
ftl.minfree = minfree
ftl.get_input_pool = ftlsim.cvar.write_select_first
ftl.get_segment_to_clean = ftlsim.cvar.segment_select_python

# Greedy-managed pool
#
gdy = ftlsim.pool(ftl, "greedy", Np)
gdy.next_pool = gdy

# for wear leveling
#
max_erasures = opts.max
bins = ftlsim.bins(max_erasures+200)

# Allocate segments...
#
freelist = [ftlsim.segment(Np) for i in range(T)]
for b in freelist:
    b.thisown = False
    bins.insert(b, 0)

gdy.add_segment(freelist.pop())
while freelist:
    b = freelist.pop()
    ftl.put_blk(b)

# use a sequential address source to write each page once
#
T0 = T-minfree
ftl.ext_writes,ftl.int_writes = 0,0
fill = getaddr.fill(T0, U)
ftl.run(fill.handle, (T0*Np) - 1);
ftl.ext_writes,ftl.int_writes = 0,0

print "ready..."

# Now create the data source and run
#
if opts.has('tracefile'):
    src = getaddr.trace(opts.tracefile)
else:
    src = getaddr.uniform(U*Np)

def segments(pool):
    s = pool.next_segment(None)
    while s:
        yield s
        s = pool.next_segment(s)
done = False
total = 0

count = 0
wl_rate = opts.rate

def clean_select():
    global gdy, opts, count, done
    count += 1
    if count > wl_rate:
        count = 0
        seg = None
        for i in range(max_erasures+20):
            seg = bins.tail(i)
            while seg and not seg.in_pool:
                bins.remove(seg)
                seg = bins.tail(i)
            if seg:
                break
    else:
        seg = gdy.tail_segment()

    if not seg:
        assert seg
    bins.remove(seg)
    bins.insert(seg, seg.erasures+1)
    if seg.erasures >= max_erasures:
        done = True

    ftlsim.return_segment(seg)
    
ftl.get_segment_to_clean_arg = clean_select

while not done:
    ftl.run(src.handle, U*Np/10)
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes
    total += ftl.ext_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0
    if type(src) is getaddr.trace:
        src = getaddr.trace(opts.tracefile)
    for s in segments(gdy):
        if s.erasures > max_erasures:
            done = True

m = 0
for s in segments(gdy):
    m = max(m, s.erasures)

e = [0] * (m+1)
for s in segments(gdy):
    e[s.erasures] += 1

print 'erasures:'
for i in range(m+1):
    if e[i]:
        print i, e[i]

print 'total writes:', total
