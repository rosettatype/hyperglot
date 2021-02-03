"""
Gather a few package wide constants
"""
from os import path
__version__ = "0.2.1"

DB = path.abspath(path.join(path.dirname(__file__), "hyperglot.yaml"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}

VALIDITYLEVELS = [
    "todo",
    "weak",
    "done",
    "verified"
]


# note that "secondary" as status is also used, but on orthographies!
STATUSES = [
    "historical",
    "constructed",
    "ancient",
    "living",
    "extinct",
    "deprecated"
]
