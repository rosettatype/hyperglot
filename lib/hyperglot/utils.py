import logging
from typing import List


class ConvenientEnumMixin:
    """
    Just some convenience additions to a basic ENUM.
    """

    log = logging.getLogger("hyperglot.choiceenum")

    @classmethod
    def values(self) -> List:
        return [level.value for level in self]

    @classmethod
    def index(self, val: str) -> int:
        """
        Get the index of a given value, useful for comparing the validities in
        order.
        """
        return self.values().index(val)


class AllChoicesEnumMixin(ConvenientEnumMixin):
    """
    An Enum which forms the choices for an CLI option.
    - The default is the first option.
    - Must have an ALL options.

    Use parse() to take an arbitrary list of inputs and:
    - Reduce it to only valid values
    - Reduce it to only the default
    - Expand 'all' to all values
    '
    """

    log = logging.getLogger("hyperglot.choiceenum")

    @classmethod
    def all(self) -> List:
        """
        Get the individual values for ALL.
        """
        return [level.value for level in self if level != self.ALL]

    @classmethod
    def parse(self, input: List[str]) -> List[str]:
        # Allow single string input and convert to list
        if isinstance(input, str):
            input = [input.strip()]

        if not isinstance(input, List):
            raise ValueError("Supplied choices are not in list format.")

        if self.ALL.value in input:
            return self.all()

        pruned = [l.lower() for l in input if l.lower() in self.values()]
        not_allowed = set(input).difference(pruned)
        if len(not_allowed) > 0:
            self.log.error(
                f"Provided choices {input} contain invalid options: {not_allowed}"
            )

        if len(pruned) == 0:
            self.log.error(
                f"Provided choices {input} are not valid, defaulting to '{self.values()[0]}'"
            )
            return [self.values()[0]]

        return pruned
