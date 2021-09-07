"""
Gather a few package wide constants
"""
from os import path
__version__ = "0.3.5"

DB = path.abspath(path.join(path.dirname(__file__), "hyperglot.yaml"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}

# Note that order matters, since these may be used like a logging level
VALIDITYLEVELS = [
    "todo",
    "draft",
    "preliminary",
    "verified",
]


# Note that "secondary" as status is also used, but on orthographies!
STATUSES = [
    "historical",
    "constructed",
    "ancient",
    "living",
    "extinct",
    "deprecated",
]


# Possible orthography statuses, in no meaningful order
ORTHOGRAPHY_STATUSES = [
    "primary",
    "local",
    "secondary",
    "deprecated",
    "historical",
    "transliteration",
]

# Those attributes of orthographies that contain non-mark characters
CHARACTER_ATTRIBUTES = [
    "base",
    "auxiliary",
    "numerals",
    "punctuation",
]

MARK_BASE = "◌"
