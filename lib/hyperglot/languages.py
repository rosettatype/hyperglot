from functools import lru_cache
import os
import re
import logging

from hyperglot import DB, LanguageValidity
from hyperglot.language import Language

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

@lru_cache
def find_language(search):
    """
    Utility method to find a language by ISO code or language name
    """

    hg = Languages(validity=LanguageValidity.TODO.value)

    search = search.lower()

    # Search as 3-letter iso code, return if matched
    if search in hg.keys():
        return [Language(search)], f"Matched from iso code {search}:"

    # Search from language names and autonyms
    # If a single match is a full 1=1 match return that
    # If a single match is a partial match, return iso and prompt with info
    # If more than one are found, return a list of isos as prompt

    matches = {}
    for iso in hg.keys():
        lang = Language(iso)
        name = lang.name.lower()
        aut = lang.autonym
        autonyms = [] if not aut else [aut.lower()]
        if "orthographies" in lang:
            for o in lang["orthographies"]:
                if "autonym" in o:
                    autonyms.append(o["autonym"].lower())

        if search == name or search in autonyms:
            return [lang], f"Matched from name match for {search}:"

        # For now let's not do any fancy input proximity checks, just partials
        search_in_autonym = len([a for a in autonyms if search in a]) > 0
        if search in name or search_in_autonym:
            matches[iso] = lang

    if len(matches) > 0:
        return matches.values(), f"Matched for search string {search}"

    return False, ""

class Languages(dict):
    """
    A dict wrapper around the language data yaml file with additional querying
    options for convenience.
    """

    def __init__(
        self, 
        strict: bool = False, 
        validity: str = LanguageValidity.DRAFT.value,
        inherit: bool = True, 
    ):
        """
        @param strict (Boolean): Use Rosetta macrolanguage definitions (False)
            or ISO definitions (True). Defaults to False.
        @param validity (Hyperglot.LanguageValidity): Minimum level of validity
            which languages must have. One of "todo", "draft", "preliminary",
            "verified". Defaults to "draft" — all languages with basic
            information, but possibly unconfirmed.
        @param inherit (Boolean): Inherit orthographies. Defaults to True.
        """
        self.strict = strict
        self.inherit = inherit
        self.validity = validity

        # Keep track of loaded Language objects available on keys
        self._loaded = []

        # Load raw yaml data for all languages
        for file in os.listdir(DB):
            if file.startswith(".") or not file.endswith(".yaml"):
                log.debug(f"Skipping irrelevant data file '{file}'")
                continue

            # Remove possibly appended escape underscore to get iso from
            # filename (escaping some reserved file names, see #127)
            iso = re.sub(r"_", "", os.path.splitext(file)[0])

            # Index the iso keys, but load the data only on __getitem__ access
            self[iso] = None

        if not strict:
            self.lax_macrolanguages()

        self.filter_by_validity(validity)
        self.set_defaults()

    def __repr__(self):
        return "Languages DB dict with '%d' languages" % len(self.keys())
    
    def __getitem__(self, iso: str) -> Language:
        """
        On item access load the requested data. Raises a KeyError if no such
        iso exists.
        """
        if iso not in self._loaded:
            self[iso] = Language(iso, inherit=self.inherit)
        
        return super().__getitem__(iso)
    
    def __getattribute__(self, iso: str) -> Language:
        """
        Deprecated, but keep for backwards compatibility.
        """
        if iso in self:
            log.warning(
                "Accessing iso attributes on Language objects is deprecated, "
                "use key access like Languages()[iso] instead."
            )
            return self[iso]

        return super().__getattribute__(iso)

    def set_defaults(self):
        """
        There are some implicit defaults we set if they are not in the data
        """
        for iso, lang in self.items():
            if "orthographies" in lang:
                if len(lang["orthographies"]) == 1 \
                        and "status" not in lang["orthographies"][0]:
                    log.debug("Implicitly setting only orthography of '%s' to "
                              "'primary'." % iso)
                    lang["orthographies"][0]["status"] = "primary"

    def lax_macrolanguages(self):
        """
        Unless specifically choosing the ISO macrolanguage model, we will
        bundle some macrolanguages and show them as single language
        This means: Remove includes attributes, remove included languages
        """
        pruned = dict(self)
        for iso in self:
            lang = self[iso]
            if "preferred_as_individual" in lang:
                if "orthographies" not in lang:
                    log.warning("'%s' cannot be treated as individual, "
                                "because it does not have orthographies"
                                % iso)
                    continue

                if "includes" not in lang:
                    # This should not be the case, but let's not warn about it
                    # either; it just means there is no sub-languages to worry
                    # about
                    continue

                pruned = {key: data for key, data in pruned.items()
                          if key not in lang["includes"]}

        self.clear()
        self.update(pruned)

    def filter_by_validity(self, validity):
        if validity not in LanguageValidity.values():
            raise ValueError(
                "Validity level '%s' not valid, must be one of: %s" %
                (validity, ", ".join(LanguageValidity.values()))
            )

        allowed = LanguageValidity.index(validity)
        pruned = {}
        for iso in self:
            lang = self[iso]
            # print("LANG", lang, vars(lang))
            try:
                if LanguageValidity.index(lang["validity"]) >= allowed:
                    pruned[iso] = lang
            except KeyError as e:
                # Provide more context, but escalate
                raise KeyError("Language '%s' missing attribute %s" %
                               (iso, e))

        self.clear()
        self.update(pruned)
