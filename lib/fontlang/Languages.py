"""
Helper classes to work with the rosetta.yaml data in more pythonic way
"""
import yaml
import logging
from . import DB


class Language(dict):
    """
    A dict wrapper around a language data yaml entry with additional querying
    options for convenience
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
        return self.get_name()

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

    def has_support(self, chars, pruneOrthographies=True):
        """
        Return a dict with language support based on the passed in chars

        @param chars set: Set of chars to check against
        @param pruneOthographies bool: Flag to remove non-supported
            orthographies from this Language object
        @return dict: Dict sorted by 1) script 2) support level 3) list of isos
        """
        support = {}
        if "orthographies" not in self:
            return support

        pruned = []

        for ort in self["orthographies"]:
            supported = False
            if "script" not in ort:
                logging.warning("Skipping an orthography in language '%s',"
                                " because it has no 'script'" % self.iso)
                continue

            if "base" in ort:
                script = ort["script"]
                base = set(ort["base"])
                if base.issubset(chars):
                    if script not in support:
                        support[script] = {}
                    if "base" not in support[script]:
                        support[script]["base"] = []

                    support[script]["base"].append(self.iso)
                    supported = True

                    # Only check aux if base is supported also
                    if "auxiliary" in ort:
                        aux = set(ort["auxiliary"])
                        if aux.issubset(chars):
                            if "auxiliary" not in support[script]:
                                support[script]["auxiliary"] = []

                            support[script]["auxiliary"].append(self.iso)
                            supported = True
            if supported:
                pruned.append(ort)

        if pruneOrthographies:
            self["orthographies"] = pruned

        return support


class Languages(dict):
    """
    A dict wrapper around the language data yaml file with additional querying
    options for convenience
    """

    def __init__(self, strict=False):
        with open(DB) as f:
            data = yaml.load(f, Loader=yaml.Loader)
            self.update(data)

            self.inherit_orthographies_from_macrolanguage()
            self.inherit_orthographies()

            if not strict:
                self.lax_macrolanguages()

    def lax_macrolanguages(self):
        """
        Unless specifically choosing the ISO macrolanguage model, we will
        bundle some macrolanguages and show them as single language
        This means: Remove includes attributes, remove included languages
        """
        pruned = dict(self)
        for iso, lang in self.items():
            if "preferred_as_individual" in lang:
                if "orthographies" not in lang:
                    logging.warning("'%s' cannot be treated as individual, "
                                    "because it does not have orthographies"
                                    % iso)
                    continue

                if "includes" not in lang:
                    # This should not be the case, but let's not warn about it
                    # either; it just means there is no sub-languages to worry
                    # about
                    continue

                # Remove the included languages from the main dict altogether
                pruned = {key: data for key, data in pruned.items()
                          if key not in lang["includes"]}

        self = pruned

    def inherit_orthographies(self):
        """
        Check through all languages and if an orthography inherits from another
        language copy those orthographies
        """
        for iso, lang in self.items():
            if "orthographies" in lang:
                for o in lang["orthographies"]:
                    if "inherit" in o and "script" in o:
                        parent_iso = o["inherit"]
                        if len(parent_iso) != 3:
                            logging.warning("'%s' failed to inherit "
                                            "orthography — not a language iso "
                                            "code" % iso)
                            continue
                        if parent_iso not in self:
                            logging.warning("'%s' inherits an orthography from"
                                            " '%s', but no such language was "
                                            "found" % (iso, parent_iso))
                            continue
                        ref = Language(self[parent_iso], parent_iso)
                        ort = ref.get_orthography(o["script"])
                        if ort:
                            logging.debug("'%s' inheriting orthography from "
                                          "'%s'" % (iso, parent_iso))
                            # Copy all the attributes we want to inherit
                            for attr in ["base", "auxiliary", "combinations",
                                         "status"]:
                                if attr in ort:
                                    # Wrap in type constructor, to copy, not
                                    # reference
                                    ty = type(ort[attr])
                                    o[attr] = ty(ort[attr])

    def inherit_orthographies_from_macrolanguage(self):
        """
        Check through all languages and if a language has no orthographies see
        if this language is included in a macrolanguage that has orthographies.
        If so, apply the macrolanguage's orthographies to this language
        """

        macrolanguages = {iso: lang for iso,
                          lang in self.items() if "includes" in lang}

        for lang in self:
            if "orthographies" not in self:

                for iso, m in macrolanguages.items():
                    if lang in m["includes"] and "orthographies" in m:
                        logging.debug("Inheriting macrolanguage '%s' "
                                      "orthographies to language '%s'"
                                      % (iso, lang))
                        # Make an explicit copy to keep the two languages
                        # separate
                        self[lang]["orthographies"] = m["orthographies"].copy()

    def from_chars(self, chars,
                   includeHistorical=False,
                   includeConstructed=False,
                   pruneOrthographies=True):
        chars = set(chars)
        support = {}

        for lang in self:
            l = Language(self[lang], lang)  # noqa, let's keep l short

            if "todo_status" in l and "todo_status" == "todo":
                logging.info("Skipping language '%s' with 'todo' status" %
                             lang)
                continue

            if includeHistorical and l.is_historical():
                logging.info("Including historical language '%s'" %
                             l.get_name())
            elif includeHistorical is False and l.is_historical():
                logging.info("Skipping historical language '%s'" % lang)
                continue

            if includeConstructed and l.is_constructed():
                logging.info("Including constructed language '%s'" %
                             l.get_name())
            elif includeConstructed is False and l.is_constructed():
                logging.info("Skipping constructed language '%s'" % lang)
                continue

            # Do the support check on the Language level, and with the prune
            # flag the resulting Language object will have only those
            # orthographies that are supported with chars
            lang_sup = l.has_support(chars, pruneOrthographies)

            for script, levels in lang_sup.items():
                if script not in support.keys():
                    support[script] = {}

                for level, isos in levels.items():
                    if level not in support[script]:
                        support[script][level] = {}

                    for iso in isos:
                        support[script][level][iso] = l

        return support
