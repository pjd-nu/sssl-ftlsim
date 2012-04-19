/*
 * file:        lambert2.i
 * description: SWIG interface for lambert W function
 *
 * Peter Desnoyers, Northeastern University, 2012
 */

%module lambertw

%{
#define SWIG_FILE_WITH_INIT
double lambertw(double z)
%}
double lambertw(double z);
