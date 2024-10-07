import re
import logging
from typing import List, Set, Tuple

from hyperglot import (
    OrthographyStatus,
    MARK_BASE,
    CHARACTER_ATTRIBUTES,
    RE_INHERITANCE_TAG,
)
from hyperglot.shaper import Shaper
from hyperglot.parse import (
    parse_chars,
    parse_marks,
    remove_mark_base,
    list_unique,
    character_list_from_string,
    get_joining_type,
    drop_inheritance_tags,
    is_mark,
    filter_chars,
)
from hyperglot.loader import load_scripts_data

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


def get_script_iso(name: str) -> str:
    scripts = load_scripts_data()
    if name not in scripts:
        raise NotImplementedError(f"Missing script name to ISO mapping for {name}")
    return scripts[name]["iso_15924"]


def find_all_inheritance_codes(value: str) -> List:
    """
    In an attribute value find all <iso ...> inheritance shortcodes.
    """
    if not value:
        return []

    inherit = RE_INHERITANCE_TAG.findall(value)

    if inherit is None or inherit == []:
        return []

    # Ignore any <g> or similar short markup from the data, e.g. inside notes
    # this might have been used to highlight a individual characters.
    inherit = [i for i in inherit if len(i.strip()) >= 3]

    # Return matches with their position and original length
    matches = []
    for i in inherit:
        matches = [(i, value.find(i), len(i))]

    return matches


def extract_inheritance_specifics(code: str, attr: str) -> Tuple:
    """
    For an inheritance code like <iso attribute Script status> extract all
    values, or return defaults.
    """

    parts = re.split(r"\s+", code.strip())

    lang = parts.pop(0)
    attribute = attr
    status = None
    script = None

    if len(lang) < 3 or len(lang) > 4 and lang != "default":
        raise KeyError(
            "Skipping inheritance for '<%s>' — not a valid iso code."
            "Could this be an accidental <...> sequence inside an "
            "attribute? Review the data." % str(code)
        )
    if len(parts) > 0:

        # Look at the other parts, see if any of them is a valid
        # orthography attribute, if so, overwrite attr to inherit to

        for p in list(parts):
            if p in Orthography.inheritable_defaults.keys():
                attribute = p
                parts.remove(p)

            if p in load_scripts_data().keys():
                script = p
                parts.remove(p)

            if p in OrthographyStatus.values():
                status = p
                parts.remove(p)

        if len(parts) > 0:
            raise ValueError(
                f"Orthography tries to inherit from '{code}'. Could "
                f"not resolve '{parts}' as an orthography "
                "script, attribute or status."
            )

        return lang, attribute, status, script
    return lang, attribute, status, script


def resolve_inherited_attributes(value: str, attr: str, script: str) -> str:
    """
    Recursively resolve any <iso...> inheritance shortcodes in the passed in
    @param value.
    @parm attr and @param script are used to determine the "best" match.
    """

    resolved = value

    # Late import to avoid circular import
    from hyperglot.language import Language

    # Recursively call this until none are found
    codes = find_all_inheritance_codes(value)

    if len(codes) == 0:
        return value

    # One by one replace any <iso> inheritance tags
    while len(codes) > 0:

        # Keep the position and length in the original string, to replace with
        # the resolved attribute
        code, beginning, length = codes.pop(0)

        if script == "":
            script = None

        iso, attribute, status, _script = extract_inheritance_specifics(code, attr)

        log.debug(
            f"Inheriting to orthography from: {iso} {_script} {attribute} {status}"
        )

        ort = None
        source = Language(iso, inherit=False)
        err = (
            f"Orthography cannot inherit '{attr}' from '{iso}' "
            f"with script '{script}'. Source language has no "
            f"orthography for script '{script}'"
        )

        if _script is None:
            # If no script was specified in the shortcode:
            # - try with same script as _parent_
            #   - for character attributes failure to match is an issue
            #   - for non-character attributes, also try with no script, only
            #     when absolutely none are found raise an issue
            try:
                ort = source.get_orthography(script=script, status=status)
            except KeyError:
                if attribute in ("base", "auxiliary", "marks"):
                    raise KeyError(err)
                try:
                    ort = source.get_orthography(script=None, status=status)
                except KeyError:
                    raise KeyError(err)
        else:
            # Script explicitly set in shortcode, failure to match is an issue
            try:
                script = _script
                ort = source.get_orthography(script=_script, status=status)
            except KeyError:
                raise KeyError(err)

        if attribute not in ort or ort[attribute] is None:
            raise KeyError(
                f"Orthography cannot inherit non-existing '{attribute}' from "
                f"'{iso}' (script {script}, status {status}), nothing inherited."
            )

        # Return the replaced value with the same type as the source one
        replacement = ort[attribute]

        if type(replacement) is str and "<" in replacement:
            # Recursive replacement
            replacement = resolve_inherited_attributes(replacement, attribute, script)

        # Insert the inherited characters in the place of the <iso> tag. We
        # don't worry about duplicate characters at this spot, later
        # parse_chars calls will take care of that when and as needed.
        resolved = (
            resolved[: beginning - 1]
            + str(replacement)
            + resolved[beginning + length + 1 :]
        )

        # Start anew, keep looping while codes are found
        codes = find_all_inheritance_codes(resolved)

    return resolved


class Orthography(dict):
    """
    A orthography dict from yaml data. Language level inheritance has already
    taken place, but attribute inheritance is handled on init.

    The dict retains its original entries, but we extend it with getters that
    use the _parsed_ character lists, which returns a lot of decomposition and
    mark magic to make those characters more reliable to work with!
    """

    defaults = {
        "status": None,
        "preferred_as_group": False,
        "script_iso": None,
        "autonym": "",
        "script": "",
        "status": OrthographyStatus.PRIMARY.value,
        "design_requirements": [],
        "design_alternates": [],
    }

    inheritable_defaults = {
        "base": "",
        "auxiliary": "",
        "marks": "",
        "punctuation": "",
        "numerals": "",
        "currency": "",
        "design_requirements": [],
        "design_alternates": [],
    }

    def __init__(self, data: dict, expand: bool = True):
        if expand:
            self.update(self.defaults)
            self.update(self.inheritable_defaults)

        self.update(data)

        if expand:
            for key in self.inheritable_defaults.keys():
                self._resolve_inherited_attributes(key)

    def _resolve_inherited_attributes(self, attr: str) -> None:
        """
        Resolve any <iso> code references in the orthography attributes to
        inherit them from the referenced language. The inherited characters
        are added in the position of the tag.

        Valid inheritance can be any iso tag plus a combination of script,
        attribute and orthography status:

        # get the primary orthography of same script
        <iso>

        # get very specific
        <iso Arabic auxiliary transliteration>

        # nest within other values
        a b c <iso> d e f
        or
        a b c d e f <iso>
        """

        replaced = None
        value = self[attr]

        if value == [] or value == "" or value is None:
            return

        try:
            if type(value) is list:
                replaced = []
                for listitem in value:
                    replaced.append(
                        resolve_inherited_attributes(listitem, attr, self.script)
                    )
                self[attr] = list(replaced)
            else:
                replaced = resolve_inherited_attributes(value, attr, self.script)
                self[attr] = replaced
        except KeyError as e:
            log.error(f"Failed to expand inheritance tag {value}")
            log.debug("Orthography data: {}".format(self))
            raise e

    def __getitem__(self, key):
        # Only provide script_iso value on actual access, as it requires a file
        # read (once).
        if key == "script_iso":
            return get_script_iso(self["script"])
        else:
            return super().__getitem__(key)

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
    def status(self) -> str:
        return (
            OrthographyStatus.PRIMARY.value
            if self["status"] is None
            else self["status"]
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
        return list_unique([filter_chars(c) for c in self._character_list("base")])

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
        return list_unique([filter_chars(c) for c in self._character_list("auxiliary")])

    @property
    def base_marks(self):
        return self._all_marks("base")

    @property
    def auxiliary_marks(self):
        return self._all_marks("aux")

    @property
    def required_base_marks(self):
        return self._required_marks("base")

    @property
    def required_auxiliary_marks(self):
        return self._required_marks("aux")

    @property
    def currency(self):
        return self._character_list("currency")

    @property
    def punctuation(self):
        return self._character_list("punctuation")

    @property
    def numerals(self):
        return self._character_list("numerals")

    @property
    def design_alternates(self):
        return [
            remove_mark_base(chars)
            for chars in self._character_list("design_alternates")
        ]

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

    def _get_raw(self) -> dict:
        """
        Return a raw dict with all the {iso} inheritance tags intact.
        """

        # Automate extracting and writing marks (in addition to any
        # that might have been defined manually)
        marks, marks_replace, marks_fill = [], "", []

        if "marks" in self:
            mk, marks_replace, marks_fill = drop_inheritance_tags(self["marks"])
            marks = parse_marks(mk)

        # "Derive" all marks possible
        for attr in CHARACTER_ATTRIBUTES:
            if attr in self:
                marks = marks + parse_marks(drop_inheritance_tags(self[attr])[0])

        # Prune marks from character lists, delete empty
        for attr in CHARACTER_ATTRIBUTES:
            if attr in self:
                _, replace, fill = drop_inheritance_tags(self[attr])
                replace_chars = [
                    c.strip()
                    for c in re.split(r"\s+", replace)
                    if not is_mark(c) and c != MARK_BASE
                ]

                if len(fill) > 0:
                    if replace_chars == ["%s"]:
                        self[attr] = fill[0]

        if len(marks) > 0 or len(marks_fill) > 0:
            decorated = []
            if len(marks_fill) > 0:
                _repl = list_unique(marks_replace.split(" "))
                for m in _repl:
                    if m == "%s":
                        decorated.append(marks_fill.pop(0))
                    else:
                        decorated.append(MARK_BASE + remove_mark_base(m))
            else:
                decorated = list_unique([MARK_BASE + m for m in marks])

            # Note: Let's store marks with a dotted circle and a
            # whitespace between them to make them more legible. When
            # parsing the attribute back in circles and all whitespaces
            # are removed
            self["marks"] = " ".join(decorated)

        # Save inheritance tags on non-character, list attributes
        for attr in ["design_requirements", "design_alternates"]:
            if attr in self and self[attr]:
                input_is_yaml_object = (
                    type(self[attr]) is dict and len(self[attr].keys()) == 1
                )
                if input_is_yaml_object:
                    tag = list(self[attr].keys())[0]
                    self[attr] = "<" + tag + ">"
                elif type(self[attr]):
                    pass
                else:
                    self[attr] = list(self[attr])

        return dict(self)
