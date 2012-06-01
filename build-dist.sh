#!/bin/sh
#

VERSION=0.2
DIR=ftlsim-$VERSION
rm -rf $DIR
mkdir -p $DIR

MISC='README.txt setup.py'
SRC='ftlsim.c ftlsim.i ftlsim.h getaddr.c getaddr.i getaddr.h 
     lambertw.c lambertw.i'
SCRIPTS='low-level.py greedy-high.py lru-high.py 2hc.py 3hc.py two-pool.py windowed-greedy.py'

cp $MISC $SRC $SCRIPTS $DIR/
tar cvfz $DIR.tar.gz $DIR
rm -rf $DIR

