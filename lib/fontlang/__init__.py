"""
Gather a few package wide constants
"""
from os import path
__version__ = "0.1.12"

DB = path.abspath(path.join(path.dirname(__file__), "rosetta.yaml"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}
