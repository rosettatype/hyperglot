"""
Helper classes to work with the rosetta.yaml data in more pythonic way
"""
from os import path
import yaml
import logging

# Add full script names from data/other/iana/language-subtag-registry.txt as
# needed when new scripts are encountered in rosetta.yaml
SCRIPTNAMES = {
    "Latn": "Latin",
    "Cyrl": "Cyrillic",
    "Grek": "Greek",
    "Arab": "Arabic",
    "Hebr": "Hebrew"
}

SUPPORTLEVELS = {
    "base": "base",
    "aux": "auxiliary"
}


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
    def get_orthography(self, script=None):
        if "orthographies" not in self:
            return False

        for o in self["orthographies"]:
            # TODO and check historical
            if script is not None and "script" in o and o["script"] == script:
                return o

        # No script provided or no orthography found for that script, return
        # first best
        return self["orthographies"][0]

    def get_name(self, script=None):
        if script is not None:
            ort = self.get_orthography(script)
            if "name" in ort:
                return ort["name"]
        # Without script fall back to main dict name, if one exists
        try:
            if "preferred_name" in self:
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
                # TODO Confirm this is also caught by validate.py
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

    source = "../../data/rosetta.yaml"

    def __init__(self):
        db_path = path.join(path.abspath(path.dirname(__file__)),
                            *path.split(self.source))

        with open(db_path) as f:
            data = yaml.load(f, Loader=yaml.Loader)
            self.update(data)

    def get_lang(self, tag):
        """
        Use a language tag to retieve that language’s data
        """
        if tag in self:
            return self[tag]
        return False

    def from_chars(self, chars, includeHistorical=False,
                   pruneOrthographies=True):
        chars = set(chars)
        support = {}

        for lang in self:
            l = Language(self[lang], lang)  # noqa, let's keep l short

            if "todo_status" in l and "todo_status" == "todo":
                logging.info("Skipping language '%s' with 'todo' status" %
                             lang)
                continue

            historical_lang = "status" in l and l["status"] == "historical"
            if historical_lang is True and includeHistorical is False:
                logging.info("Skipping language '%s' with 'historical' "
                             "status" % lang)
                continue

            if "orthographies" not in l:
                logging.info("Skipping language '%s' without orthography "
                             "entries" % lang)
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
