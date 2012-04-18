#!/usr/bin/env python
"""
setup.py file for getaddr
"""

from distutils.core import setup, Extension


runsim_module = Extension('_runsim', 
                           sources=['runsim.i', 'runsim_lru.c', 'runsim_greedy.c',
                                    'runsim_greedy_lru.c', 'runsim.c'],
                           )

setup (name = 'ftlsim',
       version = '0.1',
       author      = "Peter Desnoyers",
       author_email = "pjd@ccs.neu.edu",
       description = """Modular high-speed FTL simulator""",
       ext_modules = [runsim_module],
       py_modules = ["genaddr", "runsim"],
       )
