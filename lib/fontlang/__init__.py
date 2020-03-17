"""
Gather a few package wide constants
"""
from os import path

__version__ = "0.1.9"

# DB = path.join(path.abspath(path.dirname(__file__)),
#                *path.split("../../data/rosetta.yaml"))
DB = "data/rosetta.yaml"

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}
