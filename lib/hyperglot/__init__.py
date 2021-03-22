"""
Gather a few package wide constants
"""
from os import path
__version__ = "0.2.4"

DB = path.abspath(path.join(path.dirname(__file__), "hyperglot.yaml"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}

# Note that order matters, since these may be used like a logging level
VALIDITYLEVELS = [
    "todo",
    "weak",
    "done",
    "verified"
]


# Note that "secondary" as status is also used, but on orthographies!
STATUSES = [
    "historical",
    "constructed",
    "ancient",
    "living",
    "extinct",
    "deprecated"
]
