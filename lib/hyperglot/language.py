import os
import yaml
import pickle
import logging
from typing import List, Union
from copy import deepcopy

from hyperglot import (
    LANGUAGE_CACHE_FILE,
    CHARACTER_ATTRIBUTES,
    LanguageStatus,
    LanguageValidity,
    OrthographyStatus,
)
from hyperglot.loader import load_language_data
from hyperglot.orthography import Orthography

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


MACRO_LANGUAGES_CACHE = None


def get_macro_languages():
    global MACRO_LANGUAGES_CACHE

    from hyperglot.languages import Languages

    if MACRO_LANGUAGES_CACHE is None:
        MACRO_LANGUAGES_CACHE = {
            iso: lang
            for iso, lang in Languages(inherit=False).items()
            if "includes" in lang
        }

    return MACRO_LANGUAGES_CACHE


# Use a pickled cache of all fully inherited language data to save on loading
# and parsing
LANGUAGE_CACHE = {}
try:
    if os.path.isfile(LANGUAGE_CACHE_FILE):
        with open(LANGUAGE_CACHE_FILE, "rb+") as f:
            LANGUAGE_CACHE = pickle.load(f)
            log.info("Loaded language cache with %d entries" % len(LANGUAGE_CACHE))
except:
    pass


class Language(dict):
    """
    A dict wrapper around a language data yaml entry with additional querying
    options for convenience.

    Use Language["attribute"] to access raw yaml data, and
    use Language.attribute to access parsed and defaulted values.
    """

    defaults = {
        "name": None,
        "autonym": None,
        "speakers": None,
        "validity": None,
        "status": None,
        "contributors": None,
        "reviewers": None,
    }

    def __init__(self, iso, data: dict = None, inherit: bool = True):
        """
        Init a single Language with the data from lib/hyperglot/data yaml.

        @param iso str: Iso 3 letter iso code that is the key in the yaml. Keep
            this a private attribute, not dict items, so it does not get
            printed out when converting this Language back to yaml for output
        @param data dict: The raw data as found in the yaml or extended by
            hyperglot.languages.Languages() on load.
        """
        self.iso = iso
        self.inherit = inherit

        if data is None:
            if inherit and iso in LANGUAGE_CACHE:
                data = LANGUAGE_CACHE[iso]
            else:
                data = self._parse_data()

        if inherit:
            for key, default in self.defaults.items():
                if key not in data:
                    data[key] = default

        self.update(data)

        if inherit and iso not in LANGUAGE_CACHE:
            try:
                LANGUAGE_CACHE[iso] = data
                with open(LANGUAGE_CACHE_FILE, "wb+") as f:
                    log.debug(f"Writing {iso} to language cache.")
                    pickle.dump(LANGUAGE_CACHE, f)
            except:
                pass

    def __repr__(self):
        return f"Language ({self.iso}) {self.get_name()}"

    @property
    def presentation(self):
        tpl = """name: {name}
autonym: {autonym}
iso: {iso}
orthographies:
{orthographies}
speakers: {speakers}
status: {status}
validity: {validity}
contributors: {contributors}
reviewers: {reviewers}
"""
        import textwrap

        orths = None
        if "orthographies" in self:
            orths = "\n\n".join(
                [
                    textwrap.indent(Orthography(o).presentation, "\t")
                    for o in self["orthographies"]
                ]
            )

        return tpl.format(
            name=self.name,
            autonym=self.autonym,
            iso=self.iso,
            orthographies="-" if orths is None else orths,
            speakers="no data" if self["speakers"] is None else self.speakers,  # noqa
            status=self.status,  # noqa
            validity=self.validity,
            contributors=(
                "no data"
                if self["contributors"] is None
                else "\n- " + ("\n- ".join(self["contributors"]))
            ),
            reviewers=(
                "no data"
                if self["reviewers"] is None
                else "\n- " + ("\n- ".join(self["reviewers"]))
            ),
        )  # noqa

    def _parse_data(self) -> Union[dict, bool]:
        """
        Get and parse the language data from the yaml file. Expand
        orthographies and resolve inheritance.
        """
        try:
            data = load_language_data(self.iso)

            if not isinstance(data, dict):
                raise ValueError(f"Malformed data in {self.iso}: Not a dictionary")

            if self.inherit:
                self._inherit_orthographies_from_macrolanguage(data)

            self._expand_orthographies(data)

            return data

        # Catch various formatting issues in the yaml files
        except ValueError as e:
            log.error(f"Malformed data in {self.iso}: {e}")

        except yaml.scanner.ScannerError as e:
            log.error(f"Malformed data in {self.iso}: {e}")

        except yaml.parser.ParserError as e:
            log.error(f"Malformed data in {self.iso}: {e}")

        return False

    def _expand_orthographies(self, data):
        """
        Init all orthographies and expand their <iso> references.
        """
        if "orthographies" not in data:
            return
        _orthographies = []
        for o in data["orthographies"]:
            try:
                _orthographies.append(Orthography(o, expand=self.inherit))
            except KeyError as e:
                log.error(f"Failed expanding Orthographies in Language {self.iso}")
                raise e
        data["orthographies"] = _orthographies

    def _inherit_orthographies_from_macrolanguage(data, target):
        """
        If a language has no orthographies see check through all languages and
        if this language is included in a macrolanguage that has orthographies.
        If so, apply the macrolanguage's orthographies to this language.
        """

        if "orthographies" in data:
            return

        macrolanguages = get_macro_languages()

        for source, mlang in macrolanguages.items():
            if target in mlang["includes"] and "orthographies" in mlang:
                log.debug(
                    "Inheriting macrolanguage '%s' "
                    "orthographies to language '%s'" % (source, target)
                )
                # Make an explicit copy to keep the two languages
                # separate
                data["orthographies"] = deepcopy(mlang["orthographies"])

    def get_orthography(
        self, script: str = None, status: str = None
    ) -> Union[Orthography, bool]:
        """
        Get the most appropriate raw orthography attribute value, or one
        specifically matching the parameters. If there are multiple
        orthographies for a script, the "primary" one will be returned. If
        filters are provided and no orthography is matched an KeyError is
        raised.

        @param script str: The script
        @param status str: The status of the orthography
        @raises KeyError
        @returns dict
        """

        if "orthographies" not in self:
            return False

        matches = []
        for o in self["orthographies"]:

            if script is not None and o["script"] != script:
                continue

            if status is not None and o["status"] != status:
                continue

            matches.append(o)

        if not matches:
            raise KeyError(
                "No orthography found for script '%s' and status "
                "'%s' in language '%s'." % (script, status, self.iso)
            )

        # Sort by status index in the OrthographyStatus'es
        matches = sorted(
            matches, key=lambda o: OrthographyStatus.values().index(o["status"])
        )

        # Note for multiple-orthography-primary languages (Serbian, Korean,
        # Japanese) this returns only one orthography!
        return matches[0]

    def get_check_orthographies(self, check_all_orthographies: bool = False) -> List:
        """
        Get the orthographies relevant for performing support checks.
        """
        if "orthographies" not in self:
            return []

        # Determine which orthographies should be checked.
        if check_all_orthographies:
            orthographies = [
                o
                for o in self["orthographies"]
                if "status" not in o or o["status"] != "transliteration"
            ]
        else:
            orthographies = [
                o
                for o in self["orthographies"]
                if "status" in o and o["status"] == "primary"
            ]

        if not check_all_orthographies:
            # Note the .copy() here since we manipulate the attribute
            # and do not want to alter the original.
            as_group = [deepcopy(o) for o in orthographies if o["preferred_as_group"]]

            as_individual = [
                deepcopy(o) for o in orthographies if not o["preferred_as_group"]
            ]

            orthographies = as_individual if as_individual else []

            # Combine orthographies that are "preferred_as_group".
            # We will retain separate orthographies, but all of
            # CHARACTER_ATTRIBUTES should be the same for all grouped
            # orthographies. While some grouped orthographies will get grouped
            # as the same script, there are cases where we still want to retain
            # each match under a different script (e.g. Serbian with Latin and
            # Cyrillic but both being required for support).
            if as_group:
                combined = {}
                for _ort in as_group:
                    for attr in CHARACTER_ATTRIBUTES:
                        if attr not in _ort:
                            continue
                        if attr not in combined:
                            combined[attr] = ""
                        combined[attr] = combined[attr] + " " + _ort[attr]

                for _ort in as_group:
                    for key, val in combined.items():
                        _ort[key] = val
                    orthographies.append(_ort)

        return [o for o in orthographies]

    def get_name(self, script: str = None, strict: bool = False) -> Union[str, bool]:
        if script is not None:
            ort = self.get_orthography(script)
            if "name" in ort:
                return ort["name"]
        # Without script fall back to main dict name, if one exists
        try:
            if not strict and "preferred_name" in self:
                return self["preferred_name"]
            return self["name"] if self["name"] is not None else ""
        except KeyError:
            # If neither are found
            return False

    @property
    def name(self) -> str:
        """
        Get the default name for this language.
        """
        name = self.get_name()
        return name if name else ""

    def get_autonym(self, script: str = None) -> str:
        try:
            ort = self.get_orthography(script)
            if ort and "autonym" in ort:
                return ort["autonym"]
        except KeyError:
            # Explicitly asked for an autonym for a script that the language
            # has no orthography for
            pass

        # Without orthography autonym fall back to language autonym, if one
        # exists
        try:
            return self["autonym"] if self["autonym"] is not None else ""
        except KeyError:
            return ""

    @property
    def autonym(self) -> str:
        """
        Get the default autonym for this language.
        """
        return self.get_autonym()

    @property
    def speakers(self) -> int:
        """
        Get a speaker count, or 0 for unknown number of speakers. To access
        raw speaker data with possibly unknown count used Language["speakers"].
        """
        if self["speakers"] is None:
            return 0

        return int(self["speakers"])

    @property
    def validity(self) -> str:
        """
        Get the validity for this language (describes the data validity).
        """
        if self["validity"] is None:
            return LanguageValidity.TODO.value

        return self["validity"]

    @property
    def status(self) -> str:
        """
        Get the status for this language (describes the language, not the
        database accuracy).
        """
        if self["status"] is None:
            return LanguageStatus.LIVING.value

        return self["status"]

    @property
    def is_historical(self) -> bool:
        """
        Check if a language or a specific orthography of a language is marked
        as historical.

        If a language has a "historical" top level entry all orthographies are
        by implication historical.
        """
        if "status" in self and self["status"] == "historical":
            return True

        orthography = self.get_orthography()

        if orthography is False:
            return False

        return orthography["status"] == "historical"

    @property
    def is_constructed(self) -> bool:
        """
        Check if a language or a specific orthography of a language is marked
        as constructed.

        If a language has a "constructed" top level entry all orthographies
        are by implication constructed.
        """
        if "status" in self and self["status"] == "constructed":
            return True

        orthography = self.get_orthography()

        if orthography is False:
            return False

        return orthography["status"] == "constructed"
