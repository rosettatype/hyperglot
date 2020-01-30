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

    def __init__(self, data):
        self.update(data)

    def __repr__(self):
        return self.get_name()

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
            # Save the iso as entry in the lang's dict so we can access is
            # later when returning the lang
            # for script, langs in self.items():
            #     for iso in langs.keys():
            #         self[script][iso]["iso"] = iso

    def get_lang(self, tag):
        """
        Use a language tag to retieve that language’s glyph data
        """
        # for script in self:
        #     for lang in self[script]:
        #         if lang == tag:
        #             return self[script][lang]
        if tag in self:
            return self[tag]
        return False

    def from_chars(self, chars, includeHistorical=False):
        chars = set(chars)
        # base_support = {}
        # aux_support = {}

        support = {}
        # script: {}
        #   level: {}
        #       iso: {}

        # for script in self:
        for lang in self:
            l = self[lang]  # noqa
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

            for ort in l["orthographies"]:
                historical_orth = "status" in ort and \
                    ort["status"] == "historical"
                if historical_orth is True and includeHistorical is False:
                    logging.info("Skipping orthography ('%s') for language "
                                 "'%s' with 'historical' status" %
                                 (ort["autonym"] if "autonym" in ort else "",
                                  lang))
                    continue

                if "script" not in ort:
                    logging.warning("Cannot add language '%s' orthography "
                                    "without script" % lang)
                    continue

                if "base" in ort:
                    script = ort["script"]
                    base = set(ort["base"])
                    if base.issubset(chars):
                        if script not in support:
                            support[script] = {}
                        if "base" not in support[script]:
                            support[script]["base"] = {}

                        support[script]["base"][lang] = l

                        # Only check aux is base is supported also
                        if "auxiliary" in ort:
                            aux = set(ort["auxiliary"])
                            if aux.issubset(chars):
                                if "auxiliary" not in support[script]:
                                    support[script]["auxiliary"] = {}

                                support[script]["auxiliary"][lang] = l

        return support
