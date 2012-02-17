
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
