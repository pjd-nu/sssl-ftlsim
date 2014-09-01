import genaddr
import ftlsim
import sys

U = 2302
Np = 64

src = genaddr.uniform(U*Np)

S_f = 0.2
alpha = 1 / (1-S_f)
minfree = Np
T = int(U * alpha) + minfree

rmap = ftlsim.ftl(T, Np)
lru = ftlsim.pool(rmap, "lru", Np)
freelist = [ftlsim.segment(Np) for i in range(T)]
for b in freelist:
    b.thisown = False

lru.add_segment(freelist.pop())

intwrites = 0
extwrites = 0

def int_write(lba):
    global lru, rmap
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
        lru.add_segment(freelist.pop())
        
    
def host_write(lba):
    global lru, rmap
    global intwrites, extwrites
    extwrites += 1

    int_write(lba)
    
    while len(freelist) < minfree:
        b = lru.get_segment()
        for i in range(Np):
            a = b.lbas[i].val
            if a != -1:
                int_write(a)
                b.overwrite(i, a)
        freelist.append(b)

for a in range(U*Np):
    host_write(a)

print "ready..."

i = 0
j = 0
for a in src.addrs():
    host_write(a)
    i += 1
    if i >= U*Np/10:
        i = 0
        print extwrites, intwrites, (1.0*intwrites)/extwrites
        extwrites = 0
        intwrites = 0
        j += 1
        if j > 10:
            break

