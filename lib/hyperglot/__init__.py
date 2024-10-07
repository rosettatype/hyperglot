"""
Gather a few package wide constants
"""
import re
from os import path
from enum import Enum
from typing import List

__version__ = "0.7.1"

DB = path.abspath(path.join(path.dirname(__file__), "data"))
DB_EXTRA = path.abspath(path.join(path.dirname(__file__), "extra_data"))

LANGUAGE_CACHE_FILE = ".hyperglot-cache"

# ~~DONE Refactor these levels and status as Enum's~~
# TODO Eventaully remove deprecated "CONSTANTS"


class SupportLevel(Enum):
    """
    Valid support levels for querying Hyperglot.
    """

    BASE = "base"
    AUX = "auxiliary"


# Deprecated: SUPPORTLEVELS will be removed in the future, use SupportLevel!
SUPPORTLEVELS = {"base": "base", "aux": "auxiliary"}


class LanguageValidity(Enum):
    """
    Allowed hyperglot.Language["validity"] values.

    Order from least to most valid matters for comparison!
    """

    TODO = "todo"
    DRAFT = "draft"
    PRELIMINARY = "preliminary"
    VERIFIED = "verified"

    @classmethod
    def values(self) -> List:
        return [v.value for v in self]

    @classmethod
    def index(self, val: str) -> int:
        """
        Get the index of a given value, useful for comparing the validities in
        order.
        """
        return self.values().index(val)


# Deprecated: VALIDIRITLEVELS will be removed in the future, use LanguageValidity!
VALIDITYLEVELS = LanguageValidity.values()


# Note that "secondary" as status is also used, but on orthographies!
class LanguageStatus(Enum):
    """
    Allowed hyperglot.Language["status"] values, with LIVING being the default.

    Deprecated values for 'status' previously used are: ancient, extinct and
    deprecated.
    """

    LIVING = "living"
    HISTORICAL = "historical"
    CONSTRUCTED = "constructed"

    @classmethod
    def values(self) -> List:
        return [s.value for s in self]


# Deprecated: STATUSES will be removed in the future, use LanguageStatus!
STATUSES = LanguageStatus.values()


class OrthographyStatus(Enum):
    """
    Possible hyperglot.orthography.Orthography["status"] values.

    Note: Order matters for preference of first found orthography.

    Deprecated: "deprecated" orthography status removed in favour of "historical"
    """

    PRIMARY = "primary"
    LOCAL = "local"
    SECONDARY = "secondary"
    HISTORICAL = "historical"
    TRANSLITERATION = "transliteration"

    @classmethod
    def values(self) -> List:
        return [s.value for s in self]


# Deprecated: ORTHOGRAPHY_STATUSES will be removed in the futute, use
# OrthographyStatus!
ORTHOGRAPHY_STATUSES = OrthographyStatus.values()


# Those character attributes of orthographies that contain non-mark characters
CHARACTER_ATTRIBUTES = [
    "base",
    "auxiliary",
    "numerals",
    "punctuation",
    "currency",
]

SORTING = {
    "alphabetic": lambda lang: lang.name,
    "speakers": lambda lang: lang.speakers,
}

SORTING_DIRECTIONS = ["asc", "desc"]

MARK_BASE = "◌"

# Anything like <eng> or <eng Latin historical> or <   eng >
# Note the group needs to encompase valid iso codes and Script names, 
# e.g. A-z but also "Geʽez", "N'ko", ...
RE_INHERITANCE_TAG = re.compile(r"<([A-z'ʽ ]*)>")
# Anything between < and >
RE_INHERITANCE_TAG_PLUS = re.compile(r"<\s*([^>]*)>")
RE_MULTIPLE_SPACES = re.compile(r"\s{2,}")

# Define module level convenience imports

from hyperglot.languages import Languages
from hyperglot.language import Language
from hyperglot.orthography import Orthography

__all__ = [
    Languages,
    Language,
    Orthography,
    SupportLevel,
    LanguageValidity,
    LanguageStatus,
    OrthographyStatus,
]
