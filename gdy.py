import getaddr
import runsim


S_f = 0.08
#S_f = 0.13
alpha = 1 / (1-S_f)
U = 100000
T = int(U * alpha) + 32
Np = 64

print "T %d U %d" % (T, U)
addr = getaddr.uniform(U*Np)

gdy = runsim.greedy(T, U, Np)
gdy.handle.generator = addr.handle
gdy.target_free = 32

hist = dict()
def exit_stats(tmp, nv, blk):
    global hist
    print 'exit_stats'
    if nv not in hist:
        hist[nv] = 0
    hist[nv] += 1
    return hist

lowpgs = 0

def enter_stats(tmp, blk):
    global lowpgs
    for i in range(Np):
        addr = gdy.handle.get_phys_page(blk, i)
        if addr < 10 and addr >= 0:
            print blk, i, addr
            lowpgs += 1
    
def do_print_stats():
    global hist
    print 'print_stats', lowpgs
    for i in range(129):
        if i in hist:
            print i, hist[i]
            hist.pop(i)
        
gdy.handle.stats_exit = exit_stats
gdy.handle.stats_enter = enter_stats

n=0
for i in range(50):
    gdy.handle.run(U*Np/10)
    print "%d %d %f" % (gdy.int_writes, gdy.ext_writes, 1.0 * gdy.int_writes / gdy.ext_writes)
    n += gdy.int_writes
    gdy.int_writes = 0
    gdy.ext_writes = 0
    do_print_stats()

print n, "writes"
