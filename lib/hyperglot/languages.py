"""
Helper classes to work with the rosetta.yaml data in more pythonic way
"""
import yaml
import logging
from .parse import parse_chars
from .language import Language
from . import DB, VALIDITYLEVELS


class Languages(dict):
    """
    A dict wrapper around the language data yaml file with additional querying
    options for convenience
    """

    def __init__(self, strict=False, inherit=True, prune=True):
        with open(DB) as f:
            data = yaml.load(f, Loader=yaml.Loader)
            self.update(data)

            if inherit:
                self.inherit_orthographies_from_macrolanguage()
                self.inherit_orthographies()

            if not strict:
                self.lax_macrolanguages()

            if prune:
                # Transform all orthography character lists to pruned python
                # sets
                self.prune_chars()

    def prune_chars(self):
        for iso, lang in self.items():
            if "orthographies" in lang:
                for o in lang["orthographies"]:
                    for type in ["base", "auxiliary", "numerals"]:
                        if type in o:
                            o[type] = parse_chars(o[type], True)

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

                # Remove the macro language from the main dict altogether
                pruned = {key: data for key, data in pruned.items()
                          if key not in lang["includes"]}

        self.clear()
        self.update(pruned)

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
                                         "numerals", "status"]:
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

    def get_support_from_chars(self, chars, validity=VALIDITYLEVELS[1],
                               includeHistorical=False,
                               includeConstructed=False,
                               pruneOrthographies=True):
        chars = set(chars)
        support = {}

        for lang in self:
            l = Language(self[lang], lang)  # noqa, let's keep l short

            if "validity" not in l:
                logging.info("Skipping langauge '%s' which is missing "
                             "'validity'" % lang)
                continue

            # Skip languages below the currently selected validity level
            if VALIDITYLEVELS.index(l["validity"]) < \
                    VALIDITYLEVELS.index(validity):
                logging.info("Skipping language '%s' which has lower "
                             "'validity'" % lang)
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
            lang_sup = l.has_support(chars, "base", pruneOrthographies)
            # print("LANG_SUP", lang_sup)

            for script in lang_sup:
                if script not in support.keys():
                    support[script] = {}

                # print(script, lang_sup)
                for script, isos in lang_sup.items():
                    # print("ISOS", isos)
                    for iso in isos:
                        support[script][iso] = l

                # for level, isos in levels.items():
                #     if level not in support[script]:
                #         support[script][level] = {}

                #     for iso in isos:
                #         support[script][level][iso] = l

        return support
