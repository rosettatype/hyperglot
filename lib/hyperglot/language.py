import logging
import unicodedata2
from .parse import (parse_chars, parse_marks, remove_mark_base, list_unique,
                    character_list_from_string)
from . import SUPPORTLEVELS, CHARACTER_ATTRIBUTES

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
    options for convenience.
    """

    def __init__(self, data, iso):
        """
        Init a single Language with the data from rosetta.yaml

        @param data dict: The raw data as found in the yaml
        @param iso str: Iso 3 letter iso code that is the key in the yaml. Keep
            this a private attribute, not dict items, so it does not get
            printed out when converting this Language back to yaml for output
        """
        self.iso = iso

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
            [textwrap.indent(Orthography(o).presentation, "\t")
                for o in self["orthographies"]])

        return tpl.format(name=self.get_name(),
                          autonym=self.get_autonym(),
                          iso=self.iso,
                          orthographies=orths,
                          speakers="" if not "speakers" in self else self["speakers"],  # noqa
                          status="" if not "status" in self else self["status"],  # noqa
                          validity="" if not "validity" in self else self["validity"])  # noqa

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
        @param decomposed bool: Flag to decompose the passed in chars, meaning
            matching languages do not need to have the encoded characters as
            long as they have the base + mark combinations to shape those
            characters.
        @param marks bool: Flag to require all marks.
        @param checkAllOrthographies bool: Flag to check also non-primary
            orthographies from this Language object. 'transliteration' 
            orthographies are always ignored. False by default.
        @param pruneOthographies bool: Flag to remove non-supported
            orthographies from this Language object.
        @return dict: Dict sorted by 1) script 2) list of isos.
        """
        if type(chars) is not set and type(chars) is not list:
            raise ValueError("Languages.supported needs to be passed a "
                             "set/list of characters, got type '%s'"
                             % type(chars))
        # Make unique and filter whitespace
        chars = set([c for c in chars if c.strip() != ""])

        support = {}
        if "orthographies" not in self:
            return support

        if level not in SUPPORTLEVELS.keys():
            log.warning("Provided support level '%s' not valid, "
                        "defaulting to 'base'" % level)
            level = "base"

        pruned = []

        # Determine which orthographies should be checked
        if checkAllOrthographies:
            orthographies = [o for o in self["orthographies"]
                             if "status" not in o or
                             o["status"] != "transliteration"]
        else:
            orthographies = [o for o in self["orthographies"]
                             if "status" in o and o["status"] == "primary"]

        if not checkAllOrthographies:
            # Note the .copy() here since we manipulate the attribute
            # and do not want to alter the original
            as_group = [o.copy() for o in orthographies
                        if "preferred_as_group" in o]

            as_individual = [o.copy() for o in orthographies
                             if "preferred_as_group" not in o]

            orthographies = as_individual if as_individual else []

            # Combine orthographies that are "preferred_as_group"
            # We will retain separate orthographies, but all of
            # CHARACTER_ATTRIBUTES should be the same for all grouped
            # orthographies. While some grouped orthographies will get grouped
            # as the same script, there are cases where we still want to retain
            # each match under a different script (e.g. Serbian with Latin and
            # Cyrillic but both being required for support)
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

        for o in orthographies:
            supported = False
            ort = Orthography(o)

            if ort.base:
                if marks:
                    required_marks_base = ort.base_marks
                else:
                    required_marks_base = ort.required_base_marks

                if required_marks_base:
                    log.debug("Required base marks for %s: %s" %
                              (self.iso, required_marks_base))

                base = set(ort.base_chars + required_marks_base)

                if not decomposed:
                    supported = base.issubset(chars)
                else:
                    # If we accept that a set of characters matches for a
                    # language also when it has only base+mark encodings, we
                    # need to check support for each of the languages chars
                    for c in base:
                        decomposed = set(parse_chars(c))
                        if c in chars or decomposed.issubset(chars):
                            supported = True
                            continue
                        supported = False
                        break

                if not supported:
                    log.debug("Missing from base language %s: %s" %
                              (self.iso, " ".join(["%s (%s)" % (c, str(ord(c))) for c in base.difference(chars)])))

                if supported:
                    # Only check aux if base is supported to begin with
                    # and level is "aux" and orthography has "auxiliary"
                    # defined - if orthography has no "auxiliary" we consider
                    # it supported on "auxiliary" level, too
                    if level == "aux" and ort.auxiliary:
                        if marks:
                            required_marks_aux = ort.auxiliary_marks
                        else:
                            required_marks_aux = ort.required_auxiliary_marks

                        if required_marks_aux:
                            log.debug("Required aux marks for %s: %s" %
                                      (self.iso, required_marks_aux))
                        aux = set(ort.auxiliary_chars + required_marks_aux)

                        supported = aux.issubset(chars)

                        if not supported:
                            log.debug("Missing aux language %s: %s" %
                                      (self.iso,
                                       " ".join(aux.difference(chars))))

            if supported:
                if ort.script not in support:
                    support[ort.script] = []
                support[ort.script].append(self.iso)
                pruned.append(o)

        if pruneOrthographies:
            self["orthographies"] = pruned

        return support


class Orthography(dict):
    """
    A orthography dict from yaml data. Inheritance has already taken place.

    The dict retains its original entries, but we extend it with getters that
    use the _parsed_ character lists!
    """

    def __init__(self, data):
        self.update(data)

    @property
    def presentation(self):
        tpl = """autonym: {autonym}
base characters: {base_chars}
base marks: {base_marks}
auxiliary characters: {aux_chars}
auxiliary marks: {aux_marks}
script: {script}
status: {status}
note: {note}"""
        return tpl.format(autonym=self["autonym"] if "autonym" in self else "",
                          base_chars=" ".join(self.base_chars),
                          base_marks=" ".join(self.base_marks),
                          aux_chars=" ".join(self.auxiliary_chars),
                          aux_marks=" ".join(self.auxiliary_marks),
                          script="" if "script" not in self else self["script"],  # noqa
                          status="" if "status" not in self else self["status"],  # noqa
                          note="" if "note" not in self else self["note"])

    def diff(self, chars):
        """
        Output a presentation that highlights found and missing chars
        """
        tpl = """autonym: {autonym}
supported base characters: {base_chars}
supported base marks: {base_marks}
supported auxiliary characters: {aux_chars}
supported auxiliary marks: {aux_marks}
missing base characters: {base_chars_missing}
missing base marks: {base_marks_missing}
missing auxiliary characters: {aux_chars_missing}
missing auxiliary marks: {aux_marks_missing}
script: {script}
status: {status}
note: {note}
"""

        # base_chars_missing = " ".join([c for c in self.base_chars if c not in chars])
        # base_marks_missing = " ".join([c for c in self.base_marks if c not in chars])
        # aux_chars_missing = " ".join([c for c in self.auxiliary_chars if c not in chars])
        # aux_marks_missing = " ".join([c for c in self.auxiliary_marks if c not in chars])

        return tpl.format(autonym=self["autonym"] if "autonym" in self else "",
                          base_chars=" ".join([c for c in self.base_chars if c in chars]),
                          base_chars_missing=" ".join([ c for c in self.base_chars if c not in chars]),
                          base_marks=" ".join([c for c in self.base_marks if c in chars]),
                          base_marks_missing=" ".join([ c for c in self.base_marks if c not in chars]),
                          aux_chars=" ".join([c for c in self.auxiliary_chars if c in chars]),
                          aux_chars_missing=" ".join([ c for c in self.auxiliary_chars if c not in chars]),
                          aux_marks=" ".join([c for c in self.auxiliary_marks if c in chars]),
                          aux_marks_missing=" ".join([ c for c in self.auxiliary_marks if c not in chars]),
                          script="" if "script" not in self else self["script"],  # noqa
                          status="" if "status" not in self else self["status"],  # noqa
                          note="" if "note" not in self else self["note"])

    @property
    def script(self):
        return self["script"]

    @property
    def base(self):
        """
        A parsed base list, including unencoded base + mark combinations
        """
        return self._character_list("base")

    @property
    def base_chars(self):
        """
        A list of all encoded base characters (no marks)
        """
        base = []
        for b in self._character_list("base"):
            if len(b) > 1:
                for c in parse_chars(b):
                    if not is_mark(c):
                        base.append(c)
            else:
                base.append(b)
        return base

    @property
    def auxiliary(self):
        """
        A parsed auxiliary list, including unencoded base + mark combinations
        """
        return self._character_list("auxiliary")

    @property
    def auxiliary_chars(self):
        """
        A list of all encoded auxiliary characters (no marks)
        """
        aux = []
        for a in self._character_list("auxiliary"):
            if len(a) > 1:
                for c in parse_chars(a):
                    if not is_mark(c):
                        aux.append(c)
            else:
                aux.append(a)
        return aux

    @property
    def base_marks(self):
        return self._all_marks("base")

    @property
    def auxiliary_marks(self):
        return self._all_marks("aux")

    @property
    def required_base_marks(self):
        return self._required_marks("base")

    @property
    def required_auxiliary_marks(self):
        return self._required_marks("aux")

    @property
    def design_alternates(self):
        return [remove_mark_base(chars) for chars
                in self._character_list("design_alternates")]

    # "Private" methods

    def _character_list(self, attr):
        """
        Get a character list from an orthography.
        This also abstracts combining 'preferred_as_group' for special cases.
        @return set or bool
        """
        if attr not in self:
            return []

        return parse_chars(self[attr],
                           decompose=False,
                           retainDecomposed=False)

    def _required_marks(self, level="base"):
        """
        Get those marks which are not simply combining marks of the passed in
        chars, but explicitly listed, meaning they cannot be derived from
        decomposition. Further get those combining marks which are used in
        _unencoded_ base + mark combinations
        """

        # Such as those attributes exist:
        # - parse 'marks'
        # - parse decomposed marks from 'base'
        # - parse decomposed marks from 'aux'
        # - remove those 'marks' which are decomposed from 'base' or 'aux

        # Note how this accesses the original dict entries, not the parsed
        # character lists!
        marks = parse_marks(self["marks"]) if "marks" in self else []
        marks_base = parse_marks(self["base"]) if "base" in self else []
        marks_aux = parse_marks(
            self["auxiliary"]) if "auxiliary" in self else []

        non_decomposable = [
            m for m in marks if m not in marks_base and m not in marks_aux]

        marks_unencoded_combos = []
        if "base" in self:
            for c in character_list_from_string(self["base"]):
                if len(c) > 1:
                    marks_unencoded_combos.extend(parse_marks(c))

        if level == "aux" and "auxiliary" in self:
            for c in character_list_from_string(self["auxiliary"]):
                if len(c) > 1:
                    marks_unencoded_combos.extend(parse_marks(c))

        return list_unique(non_decomposable + marks_unencoded_combos)

    def _all_marks(self, level="base"):
        """
        Get all combining marks from a level, and any explicitly listed marks.
        For 'base' this needs to subtract implicitly listed marks from only
        'auxiliary'.
        """
        marks = parse_marks(self["marks"]) if "marks" in self else []
        decom_base = parse_marks(self["base"]) if "base" in self else []
        decom_aux = parse_marks(
            self["auxiliary"]) if "auxiliary" in self else []

        if level == "base":
            only_aux = [m for m in decom_aux if m not in decom_base]
            marks = [m for m in marks + decom_base if m not in only_aux]
            return list_unique(marks)

        if level == "aux":
            if "auxiliary" in self:
                return list_unique(marks + decom_base + decom_aux)
            else:
                return list_unique(marks + decom_base)
