import logging
from fontTools.ttLib import TTFont
import os
import sys
import importlib.util
from typing import List, Set
from collections.abc import Iterable

from hyperglot import DB_CHECKS
from hyperglot.checkbase import CheckBase
from hyperglot.shaper import Shaper
from hyperglot.languages import Languages
from hyperglot.language import Language
from hyperglot.orthography import Orthography
from hyperglot import SupportLevel, LanguageValidity

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


def format_missing_unicodes(codepoints: Set[str], reference) -> str:
    """
    List missing codepoints. For cases where all or most codepoints are missing
    output a wordy message, instead of e.g. 10k CJK glyphs
    """
    diff = codepoints.difference(reference)
    if len(diff) == len(codepoints):
        return "All required characters"
    elif len(diff) / len(codepoints) > 0.5:
        return "The majority of required characters"
    else:
        return (" ".join(["%s (%s)" % (c, str(ord(c))) for c in diff]),)


class Checker:
    """
    A base class for CharsetChecker and FontChecker encapsulating language
    support checks.
    """

    def __init__(self, fontpath: str = None, characters: List = None):
        self.fontpath = fontpath
        self.characters = characters
        self.font = None
        self.shaper = None

    def _get_checks_for_orthography(self, orthography: Orthography):
        """
        Parse lib/hyperglot/checks and return all Check classes where
        conditions are satisfied for this language.
        """
        checks = []

        check_files = [
            f for f in os.listdir(os.path.join(DB_CHECKS)) if f.endswith(".py")
        ]

        for f in check_files:
            module_file = os.path.join(DB_CHECKS, f)
            module_name = os.path.splitext(f)[0]

            try:
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                c = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = c
                spec.loader.exec_module(c)
                check = c.Check()
            except Exception as e:
                log.error(f"Failed to instantiate check {module_name}. Fix the below:")
                raise e

            if not isinstance(check, CheckBase):
                raise Exception(f"Check {module_name} needs to subclass CheckBase!")

            # Ignore checks that only run when checking with a font
            if check.requires_font and self.shaper is None:
                continue

            fulfills = True

            if "script" in check.conditions:
                if "script" in check.conditions:
                    if check.conditions["script"] != orthography["script"]:
                        fulfills = False
            if "attributes" in check.conditions["attributes"]:
                for a in check.conditions["attributes"]:
                    if a not in orthography:
                        fulfills = False

            if fulfills:
                checks.append((module_name, check.priority, c.Check()))

        checks = sorted(checks, key=lambda x: x[1])

        return checks

    def get_supported_languages(
        self,
        supportlevel: str = SupportLevel.BASE.value,
        validity: str = LanguageValidity.DRAFT.value,
        decomposed: bool = False,
        marks: bool = False,
        shaping: bool = False,
        shaping_threshold: float = 0.001,
        include_all_orthographies: bool = False,
        include_historical: bool = False,
        include_constructed: bool = False,
        report_missing: int = -1,
        report_marks: int = -1,
        report_joining: int = -1,
        report_conjuncts: int = -1,
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
        @param shaping_threshold: Number between 0.00 and 1.00 of shaping checks
            that muss pass.
        @param include_all_orthographies bool: Return all or just primary
            (default) orthographies of a language.
        @param include_historical bool: Flag to include historical languages.
        @param include_constructed bool: Flag to include constructed languages.
        @param report_missing int: Report languages with <= n issues. Report
            any number of issues when 0, andreport nothing when -1 (default).
        @param report_marks int: Report languages with <= n issues. Report
            any number of issues when 0, andreport nothing when -1 (default).
        @param report_joining int: Report languages with <= n issues. Report
            any number of issues when 0, andreport nothing when -1 (default).
        @return dict: Returns a dict with script-keys and values of dicts of
            iso-keyed language data.
        """

        languages = Languages()

        support = {}

        for iso in languages:
            lang = languages[iso]

            if "validity" not in lang:
                log.info("Skipping langauge '%s' which is missing " "'validity'" % iso)
                continue

            # Skip languages below the currently selected validity level.
            if LanguageValidity.index(lang["validity"]) < LanguageValidity.index(
                validity
            ):
                log.info("Skipping language '%s' which has lower " "'validity'" % iso)
                continue

            if include_historical and lang.is_historical:
                log.info("Including historical language '%s'" % lang.name)
            elif include_historical is False and lang.is_historical:
                log.info("Skipping historical language '%s'" % iso)
                continue

            if include_constructed and lang.is_constructed:
                log.info("Including constructed language '%s'" % lang.name)
            elif include_constructed is False and lang.is_constructed:
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
                shaping_threshold=shaping_threshold,
                check_all_orthographies=include_all_orthographies,  # noqa
                report_missing=report_missing,
                report_marks=report_marks,
                report_joining=report_joining,
                report_conjuncts=report_conjuncts,
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
                        support[script][iso] = lang

        return support

    def supports_language(
        self,
        iso: str,
        supportlevel: str = SupportLevel.BASE.value,
        validity: str = LanguageValidity.DRAFT.value,
        decomposed: bool = False,
        marks: bool = False,
        shaping: bool = False,
        shaping_threshold: float = 0.001,
        check_all_orthographies: bool = False,
        report_missing: int = -1,
        report_marks: int = -1,
        report_joining: int = -1,
        report_conjuncts: int = -1,
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
        @param shaping_threshold: Number between 0.00 and 1.00 of shaping checks
            that muss pass.
        @param check_all_orthographies bool: Flag to check also non-primary
            orthographies from this Language object. 'transliteration'
            orthographies are always ignored. False by default.
        @param report_missing int: Report languages with <= n issues. Report
            any number of issues when 0, and report nothing when -1 (default).
        @param report_marks int: Report languages with <= n issues. Report
            any number of issues when 0, and report nothing when -1 (default).
        @param report_joining int: Report languages with <= n issues. Report
            any number of issues when 0, and report nothing when -1 (default).
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
                f"Checker.supports_language expects a 3 letter iso code, got '{iso}'."
            )

        try:
            language = Language(iso)
        except KeyError:
            raise ValueError(
                f"Checker.supports_language got iso code '{iso}' not found in the database."
            )

        # Exit if validity is not met
        if "validity" not in language or (
            LanguageValidity.index(language["validity"])
            < LanguageValidity.index(validity)
        ):
            return False

        if supportlevel not in [s.value for s in SupportLevel]:
            log.error(
                "Provided support level '%s' not valid, "
                "defaulting to 'base'" % supportlevel
            )
            supportlevel = "base"

        support = {}
        orthographies = language.get_check_orthographies(check_all_orthographies)

        if orthographies == []:
            return {} if return_script_object else False

        self.shaper = None
        if shaping:
            # Setup a reusable shaper to run checks with
            self.shaper = Shaper(self.fontpath)

        for ort in orthographies:
            supported = True
            checks = self._get_checks_for_orthography(ort)

            # FIXME TBD Run all checks, even after one has failed, to get logging output
            for check_name, priority, c in checks:
                result = c.check(
                    ort,
                    self,
                    # Pass the support arguments
                    marks=marks,
                    supportlevel=supportlevel,
                    decomposed=decomposed,
                    validity=validity,
                    threshold=shaping_threshold,
                )

                log.debug(f"Running check {check_name} for {iso}: " + ("Satisfied" if result else "Failed"))

                if not result:
                    supported = False

                    # Reporting, by different loggers, levels and limits
                    # The checks themselves buffer their logs into self.logs
                    # so we can output them here based on their count.
                    for logger, severity, count, msg in c.logs:
                        if logger.name == "hyperglot.reporting.missing" and (
                            report_missing == 0 or report_missing >= count
                        ):
                            logger.log(severity, f"{iso}: {msg}")

                        if logger.name == "hyperglot.reporting.marks" and (
                            report_marks == 0 or report_marks >= count
                        ):
                            logger.log(severity, f"{iso}: {msg}")

                        if logger.name == "hyperglot.reporting.joining" and (
                            report_joining == 0 or report_joining >= count
                        ):
                            logger.log(severity, f"{iso}: {msg}")

                        if logger.name == "hyperglot.reporting.conjuncts" and (
                            report_conjuncts == 0 or report_conjuncts >= count
                        ):
                            logger.log(severity, f"{iso}: {msg}")

                    # Abort the remaining checks with lower priority
                    break

            # At this point, if not supported, skip.
            if not supported:
                continue

            if ort.script not in support:
                support[ort.script] = []
            support[ort.script].append(iso)

        return support if return_script_object else support != {}


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
