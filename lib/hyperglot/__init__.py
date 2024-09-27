"""
Gather a few package wide constants.
"""
import re
from os import path
from enum import Enum

from hyperglot.utils import AllChoicesEnumMixin, ConvenientEnumMixin

__version__ = "0.7.3"

DB = path.abspath(path.join(path.dirname(__file__), "data"))
DB_EXTRA = path.abspath(path.join(path.dirname(__file__), "extra_data"))
DB_CHECKS = path.abspath(path.join(path.dirname(__file__), "checks"))

LANGUAGE_CACHE_FILE = ".hyperglot-cache"

# ~~DONE Refactor these levels and status as Enum's~~
# TODO Eventaully remove deprecated "CONSTANTS"

class SupportLevel(AllChoicesEnumMixin, Enum):
    """
    Valid support levels for querying Hyperglot.
    """

    # Default as first!
    BASE = "base"
    AUX = "auxiliary"
    PUNCTUATION = "punctuation"
    NUMERALS = "numerals"
    CURRENCY = "currency"
    # Inlclude an ALL option
    ALL = "all"


class LanguageValidity(ConvenientEnumMixin, Enum):
    """
    Allowed hyperglot.Language["validity"] values.

    Order from least to most valid matters for comparison!
    """

    TODO = "todo"
    DRAFT = "draft"
    PRELIMINARY = "preliminary"
    VERIFIED = "verified"


# Deprecated: VALIDIRITLEVELS will be removed in the future, use LanguageValidity!
VALIDITYLEVELS = LanguageValidity.values()


# Note that "secondary" as status is also used, but on orthographies!
class LanguageStatus(AllChoicesEnumMixin, Enum):
    """
    Allowed hyperglot.Language["status"] values, with LIVING being the default.

    Deprecated values for 'status' previously used are: ancient, extinct and
    deprecated.
    """

    # Default as first option
    LIVING = "living"
    HISTORICAL = "historical"
    CONSTRUCTED = "constructed"
    # Include an all option
    ALL = "all"


class OrthographyStatus(AllChoicesEnumMixin, Enum):
    """
    Possible hyperglot.orthography.Orthography["status"] values.

    Note: Order matters for preference of first found orthography.

    Deprecated: "deprecated" orthography status removed in favour of "historical"
    """

    # Default as first option
    PRIMARY = "primary"
    LOCAL = "local"
    SECONDARY = "secondary"
    HISTORICAL = "historical"
    TRANSLITERATION = "transliteration"
    # Include an ALL option
    ALL = "all"


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
