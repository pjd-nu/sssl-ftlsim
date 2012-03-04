import getaddr
import runsim
import sys

S_f = 0.10
alpha = 1 / (1-S_f)
#U = 256*1024
U = 17000
T = int(U * alpha)
Np = 128

#lru = runsim.greedy(T+Np/2, U, Np)
#lru.target_free = Np/2
lru = runsim.lru(T, U, Np)


hist = dict()
def exit_stats(nv, blk):
    global hist
    if nv not in hist:
        hist[nv] = 0
    hist[nv] += 1

stat_functions = {'exit': exit_stats}

def stat_handler(_type, *args):
    if _type == 'exit':
        exit_stats(*args)

def do_print_stats():
    global hist
    print 'print_stats'
    for i in range(129):
        if i in hist:
            print i, hist[i]
            hist.pop(i)
        
lru.handle.stats = stat_handler

warmup = getaddr.uniform(U*Np)
lru.handle.generator = warmup.handle
lru.handle.run(T*Np*2)
lru.int_writes = 0
lru.ext_writes = 0

#rnge = [111, 1307, 697260, 1477320]
#base = [0, 111, 1418, 698678, 2175998]
#rate = [0.1713167, 0.3860835, 0.9810381, 1]

rnge = [83, 453, 671, 106189, 2068600]
base = [0,  83,  536,   1207,  107396]
rate = [0.1319, 0.3052, 0.4803, 0.6863, 1]

addr = getaddr.mixed()
for i in (0,1,2,3,4):
    a = getaddr.uniform(rnge[i])
    a.thisown = 0;
    addr.add(a.handle, rate[i], base[i])

print "T %d U %d" % (T, U)
lru.handle.generator = addr.handle

# a1 = getaddr.uniform(13107*Np)
# a1.thisown = 0
# addr.add(a1.handle, 0.05, 0)
# a2 = getaddr.uniform(249036*Np)
# a2.thisown = 0
# addr.add(a2.handle, 1, 13107*Np)
# addr.thisown = 0

#aaa = getaddr.log(addr.handle, "/tmp/foo1.trc");
#lru.generator = aaa.handle

#addr = getaddr.trace(sys.argv[1])
#addr.single = 1
#addr.thisown = 0
#a2 = getaddr.scramble(addr.handle, Np*U)

for i in range(100):
    lru.handle.run(U*Np/10)
    print "%d %d %f" % (lru.int_writes, lru.ext_writes,
                        1.0 * lru.int_writes / lru.ext_writes)
    lru.int_writes = 0
    lru.ext_writes = 0
    do_print_stats()
