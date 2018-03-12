import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from overload import setup_dirs
from overload.connectors.sierra_z3950 import z3950_query
from overload.utils import *
from overload.bibs import bibs
