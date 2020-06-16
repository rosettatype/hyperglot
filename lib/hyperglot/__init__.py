"""
Gather a few package wide constants
"""
from os import path
__version__ = "0.1.14"

DB = path.abspath(path.join(path.dirname(__file__), "hyperglot.yaml"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}

VALIDITY = ["todo", "weak", "done", "verified"]
