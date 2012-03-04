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
gdy.generator = addr.handle
gdy.target_free = 32

n=0
for i in range(50):
    gdy.handle.run(U*Np/10)
    print "%d %d %f" % (gdy.int_writes, gdy.ext_writes, 1.0 * gdy.int_writes / gdy.ext_writes)
    n += gdy.int_writes
    gdy.int_writes = 0
    gdy.ext_writes = 0
print n, "writes"
