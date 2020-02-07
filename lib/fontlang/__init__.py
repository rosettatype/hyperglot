"""
Gather a few package wide constants
"""
from os import path

__version__ = "0.1.6"

DB = path.join(path.abspath(path.dirname(__file__)),
               *path.split("../../data/rosetta.yaml"))

# Add full script names from data/other/iana/language-subtag-registry.txt as
# needed when new scripts are encountered in rosetta.yaml
SCRIPTNAMES = {
    "Latn": "Latin",
    "Cyrl": "Cyrillic",
    "Grek": "Greek",
    "Arab": "Arabic",
    "Hebr": "Hebrew"
}

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}
