import logging

from hyperglot.checkbase import CheckBase
from hyperglot.orthography import Orthography
from hyperglot.checker import Checker
from hyperglot import SupportLevel
from hyperglot.parse import parse_chars

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


class Check(CheckBase):
    """
    A check determining if an orthography is covered by the given list of
    characters.
    """

    conditions = {
        "attributes": (
            "base",
            "auxiliary",
            "numerals",
            "punctuation",
            "currency",
        ),
    }
    requires_font = False
    priority = 10
    logger = logging.getLogger("hyperglot.reporting.missing")

    def check(self, ort: Orthography, checker: Checker, **kwargs) -> bool:

        support = True
        supported = {}

        options = self._get_options(**kwargs)

        # The coverage checks require a bit fine tuning for each attribute
        # - all attributes require basic characters to be present
        # - base/aux need to consider the required marks of unencoded combinations

        for attr in options["check"]:
            chars = set()
            supported[attr] = False

            if attr in (SupportLevel.PUNCTUATION.value, SupportLevel.NUMERALS.value, SupportLevel.CURRENCY.value):
                # For these attributes, if there is no data the orthography passes!
                chars = set(getattr(ort, attr, None))
                if not chars:
                    supported[attr] = True
                else:
                    supported[attr] = chars.issubset(checker.characters)

            if attr == SupportLevel.BASE.value:
                # Get the attribute chars, with all or only required marks
                chars = ort.get_chars(attr, options["marks"])

                if not chars:
                    supported[attr] = False

                # Check for coverage, but consider decomposed option:
                if not options["decomposed"]:
                    supported[attr] = chars.issubset(checker.characters)
                else:
                    # If we accept that a set of characters matches for a
                    # language also when it has only base+mark encodings, we
                    # need to check support for each of the languages chars.
                    supported[attr] = True
                    for c in chars:
                        decomposed_char = set(parse_chars(c))
                        if not decomposed_char.issubset(checker.characters):
                            supported[attr] = False
            
            if attr == SupportLevel.AUX.value:
                # Get the attribute chars, with all or only required marks
                chars = ort.get_chars(attr, options["marks"])
                if options["marks"]:
                    req_marks_aux = ort.auxiliary_marks
                else:
                    # If not including _all_ marks, we still require support
                    # for any unencoded char + mark combination marks
                    req_marks_aux = ort.required_auxiliary_marks

                chars = set(ort.auxiliary_chars + req_marks_aux)
                supported[attr] = chars.issubset(checker.characters)

            # Logging and set overall support
            if not supported[attr]:
                missing = sorted(chars.difference(checker.characters))

                if len(missing) > 0:
                    self.logs.append(
                        (
                            self.logger,
                            logging.WARNING,
                            len(missing),
                            f"missing characters for '{attr}': %s" % ", ".join(missing),
                        )
                    )

                support = False
            
        return support
