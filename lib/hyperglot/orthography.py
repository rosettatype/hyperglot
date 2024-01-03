from typing import List, Set
import unicodedata2
import logging

from hyperglot.shaper import Shaper
from hyperglot.parse import (
    parse_chars,
    parse_marks,
    remove_mark_base,
    list_unique,
    character_list_from_string,
    get_joining_type,
)

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


def is_mark(c):
    # Nothing is no mark
    if not c:
        return False

    # This might be a base + mark combination, but not a single mark
    if type(c) is str and len(c) > 1:
        return False

    try:
        return unicodedata2.category(c).startswith("M")
    except Exception as e:
        log.error("Cannot get unicode category of '%s': %s" % (c, str(e)))


class Orthography(dict):
    """
    A orthography dict from yaml data. Inheritance has already taken place.

    The dict retains its original entries, but we extend it with getters that
    use the _parsed_ character lists!
    """

    def __init__(self, data):
        self.update(data)

    @property
    def presentation(self):
        tpl = """autonym: {autonym}
base characters: {base_chars}
base marks: {base_marks}
auxiliary characters: {aux_chars}
auxiliary marks: {aux_marks}
script: {script}
status: {status}
note: {note}"""
        return tpl.format(
            autonym=self["autonym"] if "autonym" in self else "",
            base_chars=" ".join(self.base_chars),
            base_marks=" ".join(self.base_marks),
            aux_chars=" ".join(self.auxiliary_chars),
            aux_marks=" ".join(self.auxiliary_marks),
            script="" if "script" not in self else self["script"],  # noqa
            status="" if "status" not in self else self["status"],  # noqa
            note="" if "note" not in self else self["note"],
        )

    def diff(self, chars):
        """
        Output a presentation that highlights found and missing chars
        """
        tpl = """autonym: {autonym}
supported base characters: {base_chars}
supported base marks: {base_marks}
supported auxiliary characters: {aux_chars}
supported auxiliary marks: {aux_marks}
missing base characters: {base_chars_missing}
missing base marks: {base_marks_missing}
missing auxiliary characters: {aux_chars_missing}
missing auxiliary marks: {aux_marks_missing}
script: {script}
status: {status}
note: {note}
"""

        return tpl.format(
            autonym=self["autonym"] if "autonym" in self else "",
            base_chars=" ".join([c for c in self.base_chars if c in chars]),
            base_chars_missing=" ".join([c for c in self.base_chars if c not in chars]),
            base_marks=" ".join([c for c in self.base_marks if c in chars]),
            base_marks_missing=" ".join([c for c in self.base_marks if c not in chars]),
            aux_chars=" ".join([c for c in self.auxiliary_chars if c in chars]),
            aux_chars_missing=" ".join(
                [c for c in self.auxiliary_chars if c not in chars]
            ),
            aux_marks=" ".join([c for c in self.auxiliary_marks if c in chars]),
            aux_marks_missing=" ".join(
                [c for c in self.auxiliary_marks if c not in chars]
            ),
            script="" if "script" not in self else self["script"],  # noqa
            status="" if "status" not in self else self["status"],  # noqa
            note="" if "note" not in self else self["note"],
        )

    @property
    def script(self):
        return self["script"]

    @property
    def base(self):
        """
        A parsed base list, including unencoded base + mark combinations
        """
        return self._character_list("base")

    @property
    def base_chars(self):
        """
        A list of all encoded base characters (no marks)
        """
        base = []
        for b in self._character_list("base"):
            if len(b) > 1:
                for c in parse_chars(b):
                    if not is_mark(c):
                        base.append(c)
            else:
                base.append(b)
        return base

    @property
    def auxiliary(self):
        """
        A parsed auxiliary list, including unencoded base + mark combinations
        """
        return self._character_list("auxiliary")

    @property
    def auxiliary_chars(self):
        """
        A list of all encoded auxiliary characters (no marks)
        """
        aux = []
        for a in self._character_list("auxiliary"):
            if len(a) > 1:
                for c in parse_chars(a):
                    if not is_mark(c):
                        aux.append(c)
            else:
                aux.append(a)
        return aux

    @property
    def base_marks(self):
        return self._all_marks("base")

    @property
    def auxiliary_marks(self):
        return self._all_marks("aux")

    @property
    def required_base_marks(self):
        return self._required_marks("base")

    def get_chars(self, attr: str = "base", all_marks=False) -> Set:
        """
        Get the orthography base/aux + marks with required or all marks
        """
        if attr == "aux":
            return set(
                self.auxiliary_chars
                + (self.auxiliary_marks if all_marks else self.required_auxiliary_marks)
            )

        return set(
            self.base_chars
            + (self.base_marks if all_marks else self.required_base_marks)
        )

    @property
    def required_auxiliary_marks(self):
        return self._required_marks("aux")

    @property
    def design_alternates(self):
        return [
            remove_mark_base(chars)
            for chars in self._character_list("design_alternates")
        ]

    def check_joining(self, chars: List[str], shaper: Shaper) -> List:
        """
        Check the joining behaviour for the passed in characters.

        TODO: instead of passing chars pass the relevant attributes to check?
        """
        require_shaping = [
            c for c in chars if get_joining_type(c) in ["D", "R", "L", "T"]
        ]
        if require_shaping == []:
            return []

        missing_shaping = []
        for char in require_shaping:
            if shaper.check_joining(ord(char)) is False:
                missing_shaping.append(char)

        if missing_shaping != []:
            log.debug(f"Missing required joining forms for: {missing_shaping}")
            return missing_shaping

        return []

    def check_mark_attachment(self, chars: List[str], shaper: Shaper) -> List:
        """
        Check the mark attachment for the passed in characters.

        TODO: instead of passing chars pass the relevant attributes to check?
        """
        missing_positioning = []
        for c in chars:
            if shaper.check_mark_attachment(c) is False:
                missing_positioning.append(c)

        if missing_positioning != []:
            log.debug(f"Missing required mark positioning for: {missing_positioning}")
            return missing_positioning

        return []

    # "Private" methods

    def _character_list(self, attr):
        """
        Get a character list from an orthography.

        @return set or bool
        """
        if attr not in self:
            return []

        return parse_chars(self[attr], decompose=False, retain_decomposed=False)

    def _required_marks(self, level="base"):
        """
        Get those marks which are not simply combining marks of the passed in
        chars, but explicitly listed, meaning they cannot be derived from
        decomposition. Further get those combining marks which are used in
        _unencoded_ base + mark combinations
        """

        # Such as those attributes exist:
        # - parse 'marks'
        # - parse decomposed marks from 'base'
        # - parse decomposed marks from 'aux'
        # - remove those 'marks' which are decomposed from 'base' or 'aux

        # Note how this accesses the original dict entries, not the parsed
        # character lists!
        marks = parse_marks(self["marks"]) if "marks" in self else []
        marks_base = parse_marks(self["base"]) if "base" in self else []
        marks_aux = parse_marks(self["auxiliary"]) if "auxiliary" in self else []

        non_decomposable = [
            m for m in marks if m not in marks_base and m not in marks_aux
        ]

        marks_unencoded_combos = []
        if "base" in self:
            for c in character_list_from_string(self["base"]):
                if len(c) > 1:
                    marks_unencoded_combos.extend(parse_marks(c))

        if level == "aux" and "auxiliary" in self:
            for c in character_list_from_string(self["auxiliary"]):
                if len(c) > 1:
                    marks_unencoded_combos.extend(parse_marks(c))

        return list_unique(non_decomposable + marks_unencoded_combos)

    def _all_marks(self, level="base"):
        """
        Get all combining marks from a level, and any explicitly listed marks.
        For 'base' this needs to subtract implicitly listed marks from only
        'auxiliary'.
        """
        marks = parse_marks(self["marks"]) if "marks" in self else []
        decom_base = parse_marks(self["base"]) if "base" in self else []
        decom_aux = parse_marks(self["auxiliary"]) if "auxiliary" in self else []

        if level == "base":
            only_aux = [m for m in decom_aux if m not in decom_base]
            marks = [m for m in marks + decom_base if m not in only_aux]
            return list_unique(marks)

        if level == "aux":
            if "auxiliary" in self:
                return list_unique(marks + decom_base + decom_aux)
            else:
                return list_unique(marks + decom_base)
