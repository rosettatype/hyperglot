"""
Gather a few package wide constants
"""
import os
__version__ = "0.1.10"

DB = os.path.join(os.path.dirname(__file__), "rosetta.yaml")

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}
