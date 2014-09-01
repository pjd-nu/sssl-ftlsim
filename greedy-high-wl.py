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
U,Np = int(opts['U']), int(opts['Np'])
S_f = float(opts['S_f'])
minfree = int(opts['minfree'])

alpha = 1 / (1-S_f)
T = int(U * alpha) + minfree + 1

# FTL with default parameters for single pool
#
ftl = ftlsim.ftl(T, Np)
ftl.minfree = minfree
ftl.get_input_pool = ftlsim.cvar.write_select_first
ftl.get_pool_to_clean = ftlsim.cvar.clean_select_first

# Greedy-managed pool
#
gdy = ftlsim.pool(ftl, "greedy", Np)
gdy.next_pool = gdy

# Allocate segments...
#
freelist = [ftlsim.segment(Np) for i in range(T)]
for b in freelist:
    b.thisown = False
gdy.add_segment(freelist.pop())
for b in freelist:
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
if 'tracefile' in opts:
    src = getaddr.trace(opts['tracefile'])
else:
    src = getaddr.uniform(U*Np)

max_erase = 500
def segments(pool):
    s = pool.next_segment(None)
    while s:
        yield s
        s = pool.next_segment(s)
done = False
total = 0

def get_min_segment(pool):
    seg,m = None,999999
    for s in segments(pool):
        if not s.in_pool:
            continue
        if s.erasures < m:
            seg,m = s,s.erasures
        if s.n_valid == 0:
            break
    return seg

skip = Np * 100
q = 0

while not done:
    for i in range(U/1000):
        ftl.run(src.handle, skip)
        s = get_min_segment(gdy)
        n = 0
        for j in range(Np):
            lba = s.page(j)
            if lba != -1:
                #print 'w'
                ftl.write(lba)
                n += 1
        ftl.ext_writes -= n
    print ftl.ext_writes, ftl.int_writes, (1.0*ftl.int_writes)/ftl.ext_writes
    total += ftl.ext_writes
    ftl.ext_writes = 0
    ftl.int_writes = 0
    if type(src) is getaddr.trace:
        src = getaddr.trace(opts['tracefile'])
    for s in segments(gdy):
        if s.erasures > max_erase:
            done = True
    q += 1
    if q > 20:
        break

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
