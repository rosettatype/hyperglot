import logging
import unicodedata2
from .parse import parse_chars, list_unique, parse_marks
from . import SUPPORTLEVELS, CHARACTER_ATTRIBUTES, MARK_BASE

log = logging.getLogger(__name__)


def is_mark(c):
    # Nothing is no mark
    if not c:
        return False

    # This might be a base + mark combination, but not a single mark
    if type(c) is str and len(c) > 1:
        return False

    try:
        return unicodedata2.category(c).startswith("M")
    except Exception as e:
        log.error("Cannot get unicode category of '%s': %s" % (c, str(e)))


class Language(dict):
    """
    A dict wrapper around a language data yaml entry with additional querying
    options for convenience

    TODO all the getter functions could be rewritten as object parameter
    getters
    """

    def __init__(self, data, iso, parse=True):
        """
        Init a single Language with the data from rosetta.yaml

        @param data dict: The raw data as found in the yaml
        @param iso str: Iso 3 letter iso code that is the key in the yaml. Keep
            this a private attribute, not dict items, so it does not get
            printed out when converting this Language back to yaml for output
        """

        self.iso = iso
        self.update(data)

        if parse:
            self.parse()

    def __repr__(self):
        return "Language object '%s'" % self.get_name()

    def parse(self):
        if "orthographies" in self:
            for o in self["orthographies"]:

                marks = []
                if "marks" in o:
                    marks = parse_chars(
                        o["marks"], decompose=True, retainDecomposed=True)

                # Parse all character lists
                for type in CHARACTER_ATTRIBUTES:
                    if type not in o:
                        continue

                    # Any marks encountered are moved to 'marks'
                    # Note that any base+mark precomposed will not return marks
                    # since we use decompose=False, so only marks that are part
                    # of unencoded combinations will be returned and added to
                    # 'marks'
                    o[type] = parse_chars(
                        o[type], decompose=False, retainDecomposed=True)

                    decomposed = parse_marks(o[type])
                    if marks:
                        marks.extend(decomposed)

                    # Prune those marks that are separately in a character list
                    o[type] = [c for c in o[type] if not is_mark(c)]

                # No duplicate marks
                o["marks"] = list_unique(marks)

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
            raise KeyError("No orthography found for script '%s' and status "
                           "'%s' in language '%s'." %
                           (script, status, self.iso))

        # If we multiple were found return the primary one; if none of the
        # matched is primary, leave unfiltered and return the first
        if status is not None:
            primary_matches = [m for m in matches
                               if "status" in m and m["status"] == "primary"]
            if (len(primary_matches)):
                matches = primary_matches

        # Note for multiple-orthography-primary languages (Serbian, Korean,
        # Japanese) this returns only one orthography!
        return matches[0]

    def get_required_marks(self, ort, level="base"):
        """
        Get those marks which are not simply combining marks of the passed in
        chars, but explicitly listed, meaning they cannot be derived from
        decomposition
        """

        marks = parse_marks(ort["marks"]) if "marks" in ort else ""

        chars = []
        if "base" in ort:
            chars = chars + ort["base"]

        if level == "base":
            # When checking the required marks for 'base' remove the
            # decomposable marks from 'auxiliary' from 'marks'
            if "auxiliary" in ort:
                decomposed_aux = parse_marks(ort["auxiliary"])
                marks = [m for m in marks if m not in decomposed_aux]

        if level == "aux" and "auxiliary" in ort:
            chars = chars + ort["auxiliary"]

        decomposed = parse_marks(chars)
        unencoded = parse_marks(chars, decompose=False)
        marks = [m for m in marks if m not in decomposed]

        return marks + unencoded

    def get_all_marks(self, ort, level="base"):
        """
        Get all combining marks from a level, and any explicitly listed marks.
        For 'base' this needs to subtract implicitly listed marks from only
        'auxiliary'.
        """
        marks = parse_marks(ort["marks"]) if "marks" in ort else []
        decom_base = parse_marks(ort["base"]) if "base" in ort else []
        decom_aux = parse_marks(ort["auxiliary"]) if "auxiliary" in ort else []

        if level == "base":
            only_aux = [m for m in decom_aux if m not in decom_base]
            marks = [m for m in marks + decom_base if m not in only_aux]
            return list_unique(marks)

        if level == "aux":
            if "auxiliary" in ort:
                return list_unique(marks + decom_base + decom_aux)
            else:
                return list_unique(marks + decom_base)

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
                              ignoreMerge=False, decomposed=False):
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

        combined = [c for c in combined if c != MARK_BASE]

        return set(parse_chars(combined, decompose=decomposed,
                               retainDecomposed=False))

    def supported(self,
                  chars,
                  level="base",
                  decomposed=False,
                  marks=False,
                  checkAllOrthographies=False,
                  pruneOrthographies=True):
        """
        Return a dict with language support based on the passed in chars

        @param chars set: Set of chars to check against.
        @param level str: Support level for which to check.
        @param decomposed bool: Flag to decompose the passed in chars.
        @param marks bool: Flag to require all marks.
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

            # Any support check needs 'base'
            base = self.get_orthography_chars(ort, "base",
                                              ignoreMerge=checkAllOrthographies,  # noqa
                                              decomposed=decomposed)

            if base:
                if marks:
                    required_marks_base = self.get_all_marks(ort, "base")
                else:
                    required_marks_base = self.get_required_marks(ort, "base")

                if required_marks_base != []:
                    log.debug("Required base marks for %s: %s" %
                              (self.iso, required_marks_base))
                base = set(list(base) + list(required_marks_base))

                script = ort["script"]
                supported = base.issubset(chars)

                if not supported:
                    log.debug("Missing from base language %s: %s" %
                              (self.iso, " ".join(base.difference(chars))))

                if supported:
                    # Only check aux if base is supported to begin with
                    # and level is "aux" and orthography has "auxiliary"
                    # defined - if orthography has no "auxiliary" we consider
                    # it supported on "auxiliary" level, too
                    aux = self.get_orthography_chars(ort, "auxiliary",
                                                     ignoreMerge=checkAllOrthographies,  # noqa
                                                     decomposed=decomposed)
                    if level == "aux" and aux:
                        if marks:
                            required_marks_aux = self.get_all_marks(
                                ort, "aux")
                        else:
                            required_marks_aux = self.get_required_marks(
                                ort, "aux")

                        if required_marks_aux != []:
                            log.debug("Required aux marks for %s: %s" %
                                      (self.iso, required_marks_aux))
                        aux = set(list(aux) + list(required_marks_aux))

                        supported = aux.issubset(chars)

                        if not supported:
                            log.debug("Missing aux language %s: %s" %
                                      (self.iso,
                                       " ".join(aux.difference(chars))))

            if supported:
                if script not in support:
                    support[script] = []
                support[script].append(self.iso)
                pruned.append(ort)

        if pruneOrthographies:
            self["orthographies"] = pruned

        return support
