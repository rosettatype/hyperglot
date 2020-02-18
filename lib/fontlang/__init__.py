"""
Gather a few package wide constants
"""
from os import path

__version__ = "0.1.7"

DB = path.join(path.abspath(path.dirname(__file__)),
               *path.split("../../data/rosetta.yaml"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}
