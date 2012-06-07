"""
NetworkX
========

    NetworkX (NX) is a Python package for the creation, manipulation, and
    study of the structure, dynamics, and functions of complex networks.

    https://networkx.lanl.gov/

Using
-----

    Just write in Python

    >>> import networkx as nx
    >>> G=nx.Graph()
    >>> G.add_edge(1,2)
    >>> G.add_node("spam")
    >>> print(G.nodes())
    [1, 2, 'spam']
    >>> print(G.edges())
    [(1, 2)]
"""
#    Copyright (C) 2004-2010 by
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
#
# Add platform dependent shared library path to sys.path
#

from __future__ import absolute_import

import sys
if sys.version_info[:2] < (2, 6):
    m = "Python version 2.6 or later is required for NetworkX (%d.%d detected)."
    raise ImportError(m % sys.version_info[:2])
del sys

#These are import orderwise
from networkx.exception import  *
from networkx import externalnx
from networkx import utils
# these packages work with Python >= 2.6

from networkx import classes
from networkx.classes import *


from networkx import convert
from networkx.convert import *

from networkx import relabel
from networkx.relabel import *

from networkx import generators
from networkx.generators import *

from networkx import readwrite
from networkx.readwrite import *

#Need to test with SciPy, when available
from networkx import algorithms
from networkx.algorithms import *
from networkx import linalg

from networkx.linalg import *

from networkx import drawing
from networkx.drawing import *

