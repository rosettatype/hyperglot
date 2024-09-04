import logging

from hyperglot import SupportLevel, LanguageValidity


class CheckBase:

    conditions = {
        "script": "Devanagari",
        "attributes": ("conjuncts",),
    }

    requires_font = False

    priority = 999

    logger = logging.getLogger("hyperglot.reporting.errors")

    def __init__(self):
        self.logs = []

    def check(self):
        raise NotImplementedError("Checks need to implement check method!")

    def _get_options(self, **kwargs):
        # Set defaults
        options = {
            "supportlevel": SupportLevel.BASE.value,
            "validity": LanguageValidity.DRAFT.value,
            "decomposed": False,
            "marks": False,
            
            "report_missing": -1,
            "report_marks": -1,
            "report_joining": -1,
            # check_all_orthographies: bool = False,
        }

        # Update from call arguments
        options.update(kwargs)

        return options
