import unicodedata2 as uni
import logging
import re
from fontTools.ttLib import TTFont
from . import MARK_BASE

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def list_unique(li):
    """
    Return unique list items while maintaining order
    """
    if type(li) is not list:
        raise ValueError("list_unique expected list, but got '%s' of type '%s'"
                         % (li, type(li)))
    seen = set()
    seen_add = seen.add
    return [x for x in li if not (x in seen or seen_add(x))]


def character_list_from_string(string, normalize=True):
    """
    Return a list of characters without space separators from an input string
    """
    # Make sure we are in fact dealing with a string, not a list
    if isinstance(string, list) or isinstance(string, set):
        string = " ".join(string)

    if not isinstance(string, str):
        import traceback
        traceback.print_stack()
        raise ValueError("Invalid type '%s' for character_list_from_string "
                         "with value '%s' received" %
                         (type(string), str(string)))

    # Since Unicode allows writing the same string either precomposed or as
    # combining characters, we want to transform all those strings that are
    # written as combining characters to precomposed, if possible. In our
    # data a combining char (be it encoded as precomposed or with
    # combining marks) means we want to explicitly check
    # a) the combining marks, and
    # b) with flag we want to check the precomposed unicode is present - and
    # for this we need to make sure our data input with combing marks is
    # actually interpreted (and re-saved) as precomposed!

    # Before splitting a string into a list of each character (and removing
    # spaces) make sure any composable characters written with combining marks
    # are in fact transformed to precomposed characters; otherwise the
    # "listifying" will split base and mark(s) into several list items (chars)
    if normalize:

        # N_ormal F_orm C_omposed
        # See more https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize # noqa
        string = uni.normalize("NFC", string)

    # We need to split by _letter_, so (also assuming unencoded base + mark):
    # - 'abc' gets split
    # - 'ábc' get split
    # - 'a b c' gets split
    # - 'á b c' gets split
    # li = [s.strip() for s in re.split(r"\s", string)]
    string = re.sub(r"\s+", "", string)
    li = []
    while len(string) > 0:
        for i, s in enumerate(string):

            if i == len(string) or len(string) == 1:
                li.append(string)
                string = ""
                break

            if len(string) > i + 1:
                cat = uni.category(string[i + 1])
                next_is_mark = cat.startswith("M")
                if next_is_mark:
                    continue

            li.append(string[0: i + 1])
            string = string[i + 1:]
            break

    li = list_unique([c for c in li if c.strip() != ""])

    return li


def sort_key_character_category(c):
    """
    Sorting comparator to sort unicode characters by their unicode type, first
    Letters (Uppercase, then lowercase, if applicable), then Marks, then
    anything else, secondary sort by unicode ASC
    """
    order = ["Lu", "Lt", "Ll", "LC", "L", "Lo", "Mn", "Me", "M", "Mc"]

    # Get the first letter of the category
    cat = uni.category(c)[:2]

    # Get the index of that letter in the order, or higher if not found
    order = order.index(cat) if cat in order else len(order)

    # Concat the primary order with the unicode int, so as secondary sort we
    # get unicode ASC
    order = "%s-%s" % (str(order).zfill(2), str(ord(c)).zfill(8))
    return order


def sort_by_character_type(chars):
    """
    Just a utility wrapper around sorted for this specific case
    """
    return sorted(chars, key=sort_key_character_category)


def parse_chars(characters, decompose=True, retainDecomposed=False):
    """
    From a string of characters get a set of unique unicode codepoints needed
    Note this will "decompose" combining characters/marks and remove any
    standard whitespace characters (space, line break) but treat special
    whitespace characters as part of the charset (e.g. non breaking, enspace,
    etc.)
    Use this on all orthography base/auxiliary data
    """
    unique_chars = []
    try:
        if not decompose:
            # If we want to just get the string of characters as a list without
            # doing any decomposition return a list of unique, space separated,
            # strings
            return character_list_from_string(characters, False)

        unique_strings = " ".join(character_list_from_string(characters))
        additional = []

        for c in unique_strings:

            # decomposition is either "" or a space separated string of
            # zero-filled unicode hex values like "0075 0308"
            decomposition = uni.decomposition(c)

            # This glyph should be part of the list if either it cannot be
            # decomposed or if we want to keep also decomposable ones (e.g.
            # when pruning and saving the DB)
            if decomposition == "" or retainDecomposed:
                unique_chars.append(c)

            # Not _entirely_ sure why the following can be parts of the
            # decomposition but let's ignore them when encountered. Some glyphs
            # decompose to these kind of parts instead of uni hex, presumambly
            # as layout hints based on the glyph context
            # Match and ignore them for now
            # e.g. <isolated> <compat> <super> <vertical> <final> <medial>
            # <initial> <sub> <fraction> <font> <wide> <narrow>
            inbrackets = re.compile(r"^<\w+\>$")

            if decomposition != "":
                for unihexstr in decomposition.split(" "):
                    if inbrackets.match(unihexstr):
                        continue
                    try:
                        additional.append(chr(int(unihexstr, 16)))
                    except Exception as e:
                        log.error("Error getting glyph from decomposition "
                                  "part '%s' of '%s' (decomposition '%s'):"
                                  " %s" % (unihexstr, c, decomposition, e))

        # Append additional chars retrieved from decomposition to the end, but
        # sort those so that we have letters, then marks, then anything else
        additional = sort_by_character_type(additional)

        unique_chars = list_unique(unique_chars + additional)
    except Exception as e:
        log.error("Error parsing characters '%s': %s" % (characters, e))

    return list_unique([u for u in unique_chars
                        if not re.match(r"\s", u) and len(u) != 0])


def parse_font_chars(path):
    """
    Open the provided font path and extract the codepoints encoded in the font
    @return list of characters
    """
    font = TTFont(path, lazy=True)
    cmap = font["cmap"].getBestCmap()
    font.close()

    # The cmap keys are int codepoints
    return [chr(c) for c in cmap.keys()]


def parse_marks(input, decompose=True):
    """
    Get the marks from a space separated string or list. This will also remove
    any occurance of ◌ used for placing the marks in a string.

    Note that input can be a string/list of marks to "clean up" or a
    string/list of characters from which to decompose marks.

    @return list of marks
    """
    if not input:
        return []

    if isinstance(input, list) or isinstance(input, set):
        input = " ".join(input)

    input = remove_mark_base(input)
    chars = parse_chars(input, decompose=decompose)
    return [c.strip() for c in chars if uni.category(c).startswith("M")]


def remove_mark_base(input, replace=""):
    return re.sub(MARK_BASE, replace, input)
