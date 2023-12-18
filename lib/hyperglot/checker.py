import logging
from fontTools.ttLib import TTFont
from typing import List, Set
from collections.abc import Iterable

from hyperglot.shaper import Shaper
from hyperglot.languages import Languages
from hyperglot.language import Language
from hyperglot.orthography import Orthography
from hyperglot.parse import parse_chars
from hyperglot import SUPPORTLEVELS, VALIDITYLEVELS

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


def format_missing_unicodes(codepoints: Set[str], reference) -> str:
    diff = codepoints.difference(reference)

    if len(diff) == len(codepoints):
        return "All characters"
    else:
        return (" ".join(["%s (%s)" % (c, str(ord(c))) for c in diff]),)


class Checker:
    """
    A base class for CharsetChecker and FontChecker encapsulating language
    support checks.
    """

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
        supportlevel: str = "base",
        validity: str = VALIDITYLEVELS[1],
        decomposed: bool = False,
        marks: bool = False,
        shaping: bool = False,
        check_all_orthographies: bool = False,
        return_script_object: bool = False,
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
        @param shaping bool: Flag to require joining shapes and mark attachment.
        @param check_all_orthographies bool: Flag to check also non-primary
            orthographies from this Language object. 'transliteration'
            orthographies are always ignored. False by default.
        @param return_script_object bool: Flag to return a dict of languages
            sorted by scripts. The default (false) returns a boolean indicating
            the checked language's support. This is mostly used internally when
            aggregating all languages a font supports in
            get_supported_languages grouped by script.

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

        # Exit if validity is not met
        if "validity" not in language or (
            VALIDITYLEVELS.index(language["validity"]) < VALIDITYLEVELS.index(validity)
        ):
            return False

        if supportlevel not in SUPPORTLEVELS.keys():
            log.warning(
                "Provided support level '%s' not valid, "
                "defaulting to 'base'" % supportlevel
            )
            supportlevel = "base"

        support = {}
        orthographies = language.get_check_orthographies(check_all_orthographies)

        if orthographies == []:
            return {} if return_script_object else False

        if shaping:
            # Setup a reusable shaper
            self.shaper = Shaper(self.fontpath)

        for ort in orthographies:
            supported = False

            if not ort.base:
                continue

            base = ort.get_chars("base", marks)

            if not decomposed:
                supported = base.issubset(self.characters)
            else:
                # If we accept that a set of characters matches for a
                # language also when it has only base+mark encodings, we
                # need to check support for each of the languages chars.
                supported = True
                for c in base:
                    decomposed_char = set(parse_chars(c))
                    if not decomposed_char.issubset(self.characters):
                        supported = False

            if not supported:
                log.debug(
                    "Missing from language base for %s: %s"
                    % (iso, format_missing_unicodes(base, self.characters))
                )
                continue

            if shaping:
                if not self._check_shaping(ort, "base", marks, decomposed):
                    log.debug(f"Required shaping for {iso} base characters is missing.")
                    continue

            # Only check aux if base is supported to begin with
            # and level is "aux" and orthography has "auxiliary"
            # defined - if orthography has no "auxiliary" we consider
            # it supported on "auxiliary" level, too.
            if supportlevel == "aux" and ort.auxiliary:
                if marks:
                    req_marks_aux = ort.auxiliary_marks
                else:
                    req_marks_aux = ort.required_auxiliary_marks

                if req_marks_aux:
                    log.debug(f"Required aux marks for {iso}: {req_marks_aux}")

                aux = set(ort.auxiliary_chars + req_marks_aux)

                if not aux.issubset(self.characters):
                    log.debug(
                        "Missing aux language %s: %s"
                        % (iso, format_missing_unicodes(aux, self.characters))
                    )
                    continue

                if shaping:
                    if not self._check_shaping(ort, "aux", marks, decomposed):
                        log.debug(f"Required shaping for {iso} aux characters is missing.")
                        continue

            if ort.script not in support:
                support[ort.script] = []
            support[ort.script].append(iso)

        return support if return_script_object else support != {}

    def _check_shaping(
        self,
        orthography: Orthography,
        attr: str,
        all_marks: bool,
        decomposed: bool
    ) -> bool:
        """
        Check orthography shaping for given support level.
        """

        if not orthography.check_joining(
            orthography.get_chars(attr, all_marks), self.shaper
        ):
            log.debug("Missing joining shaping for {attr} characters.")
            return False

        check_attachment = []
        chars = getattr(orthography, attr)

        # Mark positioning needs to at least work for all unencoded
        # base + mark base characters.
        check_attachment.extend([c for c in chars if len(c) > 1])

        # If checking against decomposed characters also base + mark combinations
        # that do not exist precomposed in the characters need to be checked.
        if decomposed:
            check_attachment.extend([c for c in chars if c not in self.characters])

        if not orthography.check_mark_attachment(check_attachment, self.shaper):
            log.debug("Missing mark attachment for {attr} characters.")
            return False

        return True


class FontChecker(Checker):
    """
    A checker class working on a fontpath. Extracts characters from the font
    and can perform shaping checks.
    """

    def __init__(self, fontpath: str):
        super().__init__(fontpath=fontpath)

        self.font = TTFont(fontpath, lazy=True)
        self.shaper = Shaper(fontpath)
        self.characters = self._parse_font_chars()

    def get_supported_languages(self, **kwargs):
        if "shaping" not in kwargs:
            kwargs["shaping"] = True

        return super().get_supported_languages(**kwargs)

    def supports_language(self, iso, **kwargs):
        if "shaping" not in kwargs:
            kwargs["shaping"] = True

        return super().supports_language(iso, **kwargs)

    def _parse_font_chars(self) -> List:
        """
        Open the provided font path and extract the codepoints encoded in the font
        @return list of characters
        """
        cmap = self.font["cmap"].getBestCmap()

        # The cmap keys are int codepoints.
        return [chr(c) for c in cmap.keys()]


class CharsetChecker(Checker):
    """
    A basic checker class working with a set of characters.

    """

    def __init__(self, characters: Iterable):
        # Make unique and filter whitespace.
        characters = set([c for c in characters if c.strip() != ""])
        super().__init__(characters=characters)

    def get_supported_languages(self, **kwargs):
        if "shaping" in kwargs and kwargs["shaping"] is True:
            raise ValueError("CharsetChecker cannot check for shaping.")

        return super().get_supported_languages(**kwargs)

    def supports_language(self, iso, **kwargs):
        if "shaping" in kwargs and kwargs["shaping"] is True:
            raise ValueError("CharsetChecker cannot check for shaping.")

        return super().supports_language(iso, **kwargs)
