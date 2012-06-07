#!/bin/sh
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

