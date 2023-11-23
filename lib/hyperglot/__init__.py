"""
Gather a few package wide constants
"""
from os import path
__version__ = "0.5.2"

DB = path.abspath(path.join(path.dirname(__file__), "data"))

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}

# TODO Refactor these levels and status as Enum's

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
# "deprecated" orthography status removed in favour of "historical"
ORTHOGRAPHY_STATUSES = [
    "primary",
    "local",
    "secondary",
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

SORTING = {
    "alphabetic": lambda lang: lang.get_name(),
    "speakers": lambda lang: lang["speakers"]
}

SORTING_DIRECTIONS = ["asc", "desc"]

MARK_BASE = "◌"
