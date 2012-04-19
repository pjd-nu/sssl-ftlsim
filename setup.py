#!/usr/bin/env python
"""
setup.py file for simulator
"""

from distutils.core import setup, Extension


sim_module = Extension('_newsim', 
                           sources=['newsim.i', 'multi-pool.c'],
                           )

setup (name = 'newsim',
       version = '0.1',
       author      = "Peter Desnoyers",
       author_email = "pjd@ccs.neu.edu",
       description = """Modular high-speed FTL simulator""",
       ext_modules = [sim_module],
       py_modules = ["genaddr", "newsim"]
       )
