import logging
from fontTools.ttLib import TTFont
from typing import List

from hyperglot.shaper import Shaper
from hyperglot.languages import Languages
from hyperglot.language import Language, Orthography
from hyperglot.parse import parse_chars
from hyperglot import SUPPORTLEVELS, VALIDITYLEVELS, CHARACTER_ATTRIBUTES


log = logging.getLogger(__name__)


class Checker:
    def __init__(self, fontpath=None, characters=None):
        self.fontpath = fontpath
        self.characters = characters
        self.font = None
        self.shaper = None

    def get_supported_languages(
        self,
        supportlevel=list(SUPPORTLEVELS.keys())[0],
        validity=VALIDITYLEVELS[1],
        decomposed=False,
        marks=False,
        shaping=False,
        include_all_orthographies=False,
        include_historical=False,
        include_constructed=False,
        prune_orthographies=True,
    ) -> dict:
        """
        Get all languages supported based on the passed in characters.

        @param supportlevel str: Check for 'base' (default) or 'aux' support.
        @param validatiy str: Filter by certainty of the database data.
            Defaults to 'weak', which ignores all but 'todo'. More stringent
            options are 'done' and 'verified'.
        @param decomposed bool: Flag to decompose the passed in chars, meaning
            matching languages do not need to have the encoded characters as
            long as they have the base + mark combinations to shape those
            characters.
        @param marks bool: Flag to require all marks.
        @param shaping bool: Flag to require joining shapes.
        @param include_all_orthographies bool: Return all or just primary
            (default) orthographies of a language.
        @param include_historical bool: Flag to include historical languages.
        @param include_constructed bool: Flag to include constructed languages.
        @param prune_orthographies bool: Flag to remove non-supported
            orthographies from the returned language. This does not affect
            detection, but the returned dict. Default is true.
        @return dict: Returns a dict with script-keys and values of dicts of
            iso-keyed language data.
        """

        languages = Languages()

        support = {}

        for iso in languages:
            l = getattr(languages, iso)  # noqa, let's keep l short

            if "validity" not in l:
                log.info("Skipping langauge '%s' which is missing " "'validity'" % iso)
                continue

            # Skip languages below the currently selected validity level.
            if VALIDITYLEVELS.index(l["validity"]) < VALIDITYLEVELS.index(validity):
                log.info("Skipping language '%s' which has lower " "'validity'" % iso)
                continue

            if include_historical and l.is_historical():
                log.info("Including historical language '%s'" % l.get_name())
            elif include_historical is False and l.is_historical():
                log.info("Skipping historical language '%s'" % iso)
                continue

            if include_constructed and l.is_constructed():
                log.info("Including constructed language '%s'" % l.get_name())
            elif include_constructed is False and l.is_constructed():
                log.info("Skipping constructed language '%s'" % iso)
                continue

            # Do the support check on the Language level, and with the prune
            # flag the resulting Language object will have only those
            # orthographies that are supported with chars.
            lang_sup = self.supports_language(
                iso,
                supportlevel=supportlevel,
                validity=validity,
                decomposed=decomposed,
                marks=marks,
                shaping=shaping,
                check_all_orthographies=include_all_orthographies,  # noqa
                prune_orthographies=prune_orthographies,
                # We want to explicitly get what scripts of a language are
                # supported.
                return_script_object=True,
            )

            for script in lang_sup:
                for script, isos in lang_sup.items():
                    if script not in support.keys():
                        support[script] = {}
                    for iso in isos:
                        # Note we are adding the pruned language object that
                        # has_support has updated.
                        support[script][iso] = l

        return support

    def supports_language(
        self,
        iso: str,
        supportlevel="base",
        validity=VALIDITYLEVELS[1],
        decomposed=False,
        marks=False,
        shaping=False,
        check_all_orthographies=False,
        prune_orthographies=True,
        return_script_object=False,
    ) -> bool:
        """
        Return boolean indicating support for language with given iso based on
        the Checker's characters.

        @param supportlevel str: Support level for which to check.
        @param decomposed bool: Flag to decompose the passed in chars, meaning
            matching languages do not need to have the encoded characters as
            long as they have the base + mark combinations to shape those
            characters.
        @param marks bool: Flag to require all marks.
        @param shaping bool: Flag to require joining shapes.
        @param check_all_orthographies bool: Flag to check also non-primary
            orthographies from this Language object. 'transliteration'
            orthographies are always ignored. False by default.
        @param pruneOthographies bool: Flag to remove non-supported
            orthographies from this Language object.
        @param return_script_object bool: Flag to return a dict of languages
            sorted by scripts. The default (false) returns a boolean indicating
            the checked language's support. This is mostly used internally when
            aggregating all languages a font supports in
            get_supported_languages.

        @return bool or dict: Dict sorted by 1) script 2) list of isos.
        """

        # Note we have "linb" iso code with 4 letters :/
        if not isinstance(iso, str) or len(iso) < 3 or len(iso) > 4:
            raise ValueError(
                "Checker.supports_language expects a 3 letter iso code, got '{iso}'."
            )

        try:
            language = Language(iso)
        except KeyError:
            raise ValueError(
                "Checker.supports_language got iso code '{iso}' not found in the database."
            )

        support = {}

        # Exit if there is no data.
        if "orthographies" not in language:
            return support if return_script_object else False
        
        # Exit if validity is not met
        if "validity" not in language or (VALIDITYLEVELS.index(language["validity"]) < VALIDITYLEVELS.index(validity)):
            return False

        if supportlevel not in SUPPORTLEVELS.keys():
            log.warning(
                "Provided support level '%s' not valid, "
                "defaulting to 'base'" % supportlevel
            )
            supportlevel = "base"

        pruned = []

        # Determine which orthographies should be checked.
        if check_all_orthographies:
            orthographies = [
                o for o in language["orthographies"]
                if "status" not in o or o["status"] != "transliteration"
            ]
        else:
            orthographies = [
                o for o in language["orthographies"]
                if "status" in o and o["status"] == "primary"
            ]

        if not check_all_orthographies:
            # Note the .copy() here since we manipulate the attribute
            # and do not want to alter the original.
            as_group = [o.copy() for o in orthographies if "preferred_as_group" in o]

            as_individual = [
                o.copy() for o in orthographies if "preferred_as_group" not in o
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

        for o in orthographies:
            supported = False
            ort = Orthography(o)

            if not ort.base:
                continue

            if marks:
                required_marks_base = ort.base_marks
            else:
                required_marks_base = ort.required_base_marks

            if required_marks_base:
                log.debug("Required base marks for %s: %s" % (iso, required_marks_base))

            base = set(ort.base_chars + required_marks_base)

            if not decomposed:
                supported = base.issubset(self.characters)
            else:
                # If we accept that a set of characters matches for a
                # language also when it has only base+mark encodings, we
                # need to check support for each of the languages chars.
                for c in base:
                    decomposed = set(parse_chars(c))
                    if c in self.characters or decomposed.issubset(self.characters):
                        supported = True
                        continue
                    supported = False
                    break

            if not supported:
                log.debug(
                    "Missing from language base for %s: %s"
                    % (
                        iso,
                        " ".join(
                            [
                                "%s (%s)" % (c, str(ord(c)))
                                for c in base.difference(self.characters)
                            ]
                        ),
                    )
                )

            if supported and shaping:
                font_shaper = Shaper(self.fontpath)
                supported = ort.check_joining(base, font_shaper)
                if not supported:
                    log.debug("Missing shaping for language base for %s" % iso)

            if supported:
                # Only check aux if base is supported to begin with
                # and level is "aux" and orthography has "auxiliary"
                # defined - if orthography has no "auxiliary" we consider
                # it supported on "auxiliary" level, too.
                if supportlevel == "aux" and ort.auxiliary:
                    if marks:
                        required_marks_aux = ort.auxiliary_marks
                    else:
                        required_marks_aux = ort.required_auxiliary_marks

                    if required_marks_aux:
                        log.debug(
                            "Required aux marks for %s: %s" % (iso, required_marks_aux)
                        )
                    aux = set(ort.auxiliary_chars + required_marks_aux)

                    supported = aux.issubset(self.characters)

                    if not supported:
                        log.debug(
                            "Missing aux language %s: %s"
                            % (iso, " ".join(aux.difference(self.characters)))
                        )

            if supported:
                # TBD do we want to retain this per script listing.
                if ort.script not in support:
                    support[ort.script] = []
                support[ort.script].append(iso)
                pruned.append(o)

        if prune_orthographies:
            language["orthographies"] = pruned

        return support if return_script_object else support != {}


class FontChecker(Checker):
    def __init__(self, fontpath: str):
        super().__init__(fontpath=fontpath)

        self.font = TTFont(fontpath, lazy=True)
        self.shaper = Shaper(fontpath)
        self.characters = self.parse_font_chars()

    def parse_font_chars(self) -> List:
        """
        Open the provided font path and extract the codepoints encoded in the font
        @return list of characters
        """
        cmap = self.font["cmap"].getBestCmap()

        # The cmap keys are int codepoints.
        return [chr(c) for c in cmap.keys()]


class CharsetChecker(Checker):
    def __init__(self, characters: set):
        # Make unique and filter whitespace.
        characters = set([c for c in characters if c.strip() != ""])
        super().__init__(characters=characters)
