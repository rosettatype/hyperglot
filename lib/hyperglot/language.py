"""
Helper classes to work with the lib/hyperglot/data in more pythonic way
"""
import logging
from hyperglot import ORTHOGRAPHY_STATUSES
from hyperglot.languages import get_languages
from hyperglot.orthography import Orthography

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

class Language(dict):
    """
    A dict wrapper around a language data yaml entry with additional querying
    options for convenience.
    """

    def __init__(self, iso, data=None):
        """
        Init a single Language with the data from lib/hyperglot/data yaml.

        @param iso str: Iso 3 letter iso code that is the key in the yaml. Keep
            this a private attribute, not dict items, so it does not get
            printed out when converting this Language back to yaml for output
        @param data dict: The raw data as found in the yaml or extended by
            hyperglot.languages.Languages() on load.
        """
        self.iso = iso

        if data is None:
            # Load languages from cache, return the data for this language
            languages = get_languages()
            data = languages[iso]

        # A default for unset speakers, to allow sorting
        self["speakers"] = 0

        self.update(data)

    def __repr__(self):
        return "Language object '%s'" % self.get_name()

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
"""
        import textwrap

        orths = "\n\n".join(
            [
                textwrap.indent(Orthography(o).presentation, "\t")
                for o in self["orthographies"]
            ]
        )

        return tpl.format(
            name=self.get_name(),
            autonym=self.get_autonym(),
            iso=self.iso,
            orthographies=orths,
            speakers="" if not "speakers" in self else self["speakers"],  # noqa
            status="" if not "status" in self else self["status"],  # noqa
            validity="" if not "validity" in self else self["validity"],
        )  # noqa

    def get_orthography(self, script=None, status=None):
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

            if "status" not in o and status is not None:
                continue

            if status is not None and o["status"] != status:
                continue

            matches.append(o)

        if not matches:
            raise KeyError(
                "No orthography found for script '%s' and status "
                "'%s' in language '%s'." % (script, status, self.iso)
            )

        # Sort by status index in the ORTHOGRAPHY_STATUSES
        matches = sorted(matches, key=lambda o: ORTHOGRAPHY_STATUSES.index(o["status"]))

        # Note for multiple-orthography-primary languages (Serbian, Korean,
        # Japanese) this returns only one orthography!
        return matches[0]

    def get_name(self, script=None, strict=False):
        if script is not None:
            ort = self.get_orthography(script)
            if "name" in ort:
                return ort["name"]
        # Without script fall back to main dict name, if one exists
        try:
            if not strict and "preferred_name" in self:
                return self["preferred_name"]
            return self["name"]
        except KeyError:
            # If neither are found
            return False

    def get_autonym(self, script=None):
        if script is not None:
            ort = self.get_orthography(script)
            if "autonym" in ort:
                return ort["autonym"]
        # Without script fall back to main dict autonym, if one exists
        try:
            return self["autonym"]
        except KeyError:
            return False

    def is_historical(self, orthography=None):
        """
        Check if a language or a specific orthography of a language is marked
        as historical

        If a language has a "historical" top level entry all orthographies are
        by implication historical.
        """
        if "status" in self and self["status"] == "historical":
            return True

        if (
            orthography is not None
            and "status" in orthography
            and orthography["status"] == "historical"
        ):
            return True

        return False

    def is_constructed(self, orthography=None):
        """
        Check if a language or a specific orthography of a language is marked
        as constructed

        If a language has a "constructed" top level entry all orthographies
        are by implication constructed.
        """
        if "status" in self and self["status"] == "constructed":
            return True

        if (
            orthography is not None
            and "status" in orthography
            and orthography["status"] == "constructed"
        ):
            return True

        return False

    def is_deprecated(self, orthography=None):
        """
        Check if a language or a specific orthography of a language is marked
        as deprecated

        If a language has a "deprecated" top level entry all orthographies
        are by implication deprecated.
        """
        if "status" in self and self["status"] == "deprecated":
            return True

        if (
            orthography is not None
            and "status" in orthography
            and orthography["status"] == "deprecated"
        ):
            return True

        return False

    def is_secondary(self, orthography=None):
        """
        Check if a language or a specific orthography of a language is marked
        as secondary

        If a language has a "secondary" top level entry all orthographies
        are by implication secondary.
        """
        if "status" in self and self["status"] == "secondary":
            return True

        if (
            orthography is not None
            and "status" in orthography
            and orthography["status"] == "secondary"
        ):
            return True

        return False


