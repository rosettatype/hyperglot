import logging
from .parse import parse_chars
from . import SUPPORTLEVELS

log = logging.getLogger(__name__)


class Language(dict):
    """
    A dict wrapper around a language data yaml entry with additional querying
    options for convenience

    TODO all the getter functions could be rewritten as object parameter
    getters
    """

    def __init__(self, data, iso):
        """
        Init a single Language with the data from rosetta.yaml
        @param data dict: The raw data as found in the yaml
        @param iso str: Iso 3 letter iso code that is the key in the yaml. Keep
            this a private attribute, not dict items, so it does not get
            printed out when converting this Language back to yaml for output
        """
        self.update(data)
        self.iso = iso

    def __repr__(self):
        return "Language object '%s'" % self.get_name()

    # TODO this should return all orthographies for a script, not the first it
    # hits
    # TODO include_historical check
    def get_orthography(self, script=None):
        if "orthographies" not in self:
            return False

        for o in self["orthographies"]:
            if script is not None and "script" in o and o["script"] == script:
                return o

        # No script provided or no orthography found for that script, return
        # first best
        return self["orthographies"][0]

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

        if orthography is not None and "status" in orthography and \
                orthography["status"] == "historical":
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

        if orthography is not None and "status" in orthography and \
                orthography["status"] == "constructed":
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

        if orthography is not None and "status" in orthography and \
                orthography["status"] == "deprecated":
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

        if orthography is not None and "status" in orthography and \
                orthography["status"] == "secondary":
            return True

        return False

    def get_orthography_chars(self, orthography, attr="base",
                              ignoreMerge=False):
        """
        Get a character list from an orthography.
        This also abstracts combining 'preferred_as_group' for special cases.
        @return set or bool
        """
        combined = []

        if "preferred_as_group" not in orthography or ignoreMerge:
            if attr in orthography:
                combined = orthography[attr]
        else:
            for o in self["orthographies"]:
                if attr not in o:
                    continue

                if "preferred_as_group" in o and attr in o:
                    combined = combined + list(o[attr])

        if combined == []:
            return False

        return set(parse_chars(combined))

    def has_support(self, chars, level="base", decomposed=False,
                    checkAllOrthographies=False,
                    pruneOrthographies=True):
        """
        Return a dict with language support based on the passed in chars

        @param chars set: Set of chars to check against.
        @param level str: Support level for which to check.
        @param decomposed bool: Flag to decompose the passed in chars.
        @param checkAllOrthographies bool: Flag to check also non-primary
            orthographies from this Language object. False by default.
        @param pruneOthographies bool: Flag to remove non-supported
            orthographies from this Language object.
        @return dict: Dict sorted by 1) script 2) list of isos.
        """
        support = {}
        if "orthographies" not in self:
            return support

        if level not in SUPPORTLEVELS.keys():
            log.warning("Provided support level '%s' not valid, "
                        "defaulting to 'base'" % level)
            level = "base"

        pruned = []

        chars = set(chars)
        if decomposed:
            chars = set(parse_chars(chars, decompose=True,
                                    retainDecomposed=False))

        # Determine which orthographies should be checked
        if checkAllOrthographies:
            orthographies = [o for o in self["orthographies"]
                             if "status" not in o or
                             o["status"] != "deprecated"]
        else:
            orthographies = [o for o in self["orthographies"]
                             if "status" in o and o["status"] == "primary"]

        for ort in orthographies:
            supported = False

            if self.is_secondary(ort) or self.is_deprecated(ort):
                log.info("Skipping orthography in '%s' because it is "
                         "deprecated or secondary" % self.iso)

            # Any support check needs 'base'
            base = self.get_orthography_chars(ort, "base",
                                              checkAllOrthographies)
            if base:
                script = ort["script"]
                supported = base.issubset(chars)

                if supported:
                    # Only check aux if base is supported to begin with
                    # and level is "aux" and orthography has "auxiliary"
                    # defined - if orthography has no "auxiliary" we consider
                    # it supported on "auxiliary" level, too
                    aux = self.get_orthography_chars(ort, "auxiliary",
                                                     checkAllOrthographies)
                    if level == "aux" and aux:
                        supported = aux.issubset(chars)

            if supported:
                if script not in support:
                    support[script] = []
                support[script].append(self.iso)
                pruned.append(ort)

        if pruneOrthographies:
            self["orthographies"] = pruned

        return support
