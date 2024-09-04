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
        ),
    }
    requires_font = False
    priority = 10
    logger = logging.getLogger("hyperglot.reporting.missing")

    def check(self, ort: Orthography, checker: Checker, **kwargs) -> bool:

        supported = False

        if not ort.base:
            return False

        options = self._get_options(**kwargs)

        base = ort.get_chars("base", options["marks"])

        if not options["decomposed"]:
            supported = base.issubset(checker.characters)
        else:
            # If we accept that a set of characters matches for a
            # language also when it has only base+mark encodings, we
            # need to check support for each of the languages chars.
            supported = True
            for c in base:
                decomposed_char = set(parse_chars(c))
                if not decomposed_char.issubset(checker.characters):
                    supported = False

        if not supported:
            base_missing = base.difference(checker.characters)

            if len(base_missing) > 0:
                self.logs.append(
                    (
                        self.logger,
                        logging.WARNING,
                        len(base_missing),
                        "missing characters for 'base': %s" % ", ".join(base_missing),
                    )
                )

                # Validation
                supported = False

        # If an orthography has no "auxiliary" we consider it supported on
        # "auxiliary" level, too.
        if options["supportlevel"] == SupportLevel.AUX.value and ort.auxiliary:
            if options["marks"]:
                req_marks_aux = ort.auxiliary_marks
            else:
                req_marks_aux = ort.required_auxiliary_marks

            aux = set(ort.auxiliary_chars + req_marks_aux)
            aux_missing = aux.difference(checker.characters)

            if len(aux_missing) > 0:
                self.logs.append(
                    (
                        self.logger,
                        logging.WARNING,
                        len(aux_missing),
                        "missing characters for 'aux': %s" % ", ".join(aux_missing),
                    )
                )

                # Validation
                supported = False

        return supported
