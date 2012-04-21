
       SSSL-ftlsim -- a fast Flash Translation Layer simulator

		   Peter Desnoyers pjd@ccs.neu.edu

SSSL-ftlsim is a set of Python extensions, implemented in C using the
SWIG interface generator, for generating traffic distributions
(getaddr) and running Flash Translation Layer simulations (runsim). 

These are stripped-down simulations which only handle single-page
writes, and which ignore all performance parameters other than write
amplification. High performance is achieved by implementing the
simulation engine and traffic generators in C -- e.g. page-mapped
greedy cleaning runs at over 10 million flash writes/sec on a 3.2GHz
Core i7. Implementing these different parts as Python extensions makes
it simple to configure the myriad simulation parameters, as well as
allowing e.g. composition of traffic generators.

A simulation consists of traffic generation, FTL simulation, and
statistics collection:

getaddr: flexible traffic generation.

This module supports the following traffic generator types, each of
which generate a stream of page addresses:

1. getaddr.uniform(max) 

This generates addresses uniformly distributed on [0..max-1]

2. m = getaddr.mixed()
This combines several generators probabilistically, e.g. to create
simple hot/cold traffic from two uniform generators. In particular:

  m.add(gen_i.handle, p_i, base_i)  for i = 1 .. n

will return (base_i + gen_i.next()) with probability (p_i - p_(i-1)),
where p_0 = 0. The user is responsible for maintaining resonable
invariants:
      base_1 = 0                      - addresses start at zero
      base_(i+1) - base_i = gen_i.max - ranges are independent
      p_n                             - total probability = 1

3. getaddr.trace(file)

File contains lines of the form '<addr> <len>'. For each pair 'A N'
the address generator will return N addresses: A, A+1,... A+N-1. 
Numbers can be decimal or hex in 0x... format.

4. m = getaddr.scramble(max)
   m.input = <generator>.handle

Applies a random permutation to addresses from <generator> to remove
any spatial locality.

genaddr.py - python version of traffic generator

lambertw - the Lambert W function, for calculating optimal cleaning

ftlsim - FTL simulator, with the following types:

segment: a physical flash block
  .n_valid - number of valid pages in block
  .lbas[].val - array [0..Np-1] of LBAs (-1 for invalid pages)
constructor: segment(Np)

rmap: 
