"""
A humble start is better than none
"""
from hyperglot.parse import (parse_chars,
                             character_list_from_string,
                             list_unique)


def test_parse_chars():
    # Verify composites get decomposed correctly and their order is as expected
    assert(["ĳ", "i", "j"] == parse_chars("ĳ"))
    assert(["â", "a", "̂", "å", "̊"] == parse_chars("â å"))

    # Check basic splitting
    assert(5 == len(parse_chars("abcde")))
    assert(5 == len(parse_chars("a b c d e")))

    # Check whitespace separation
    assert(["a", "b", "c"] == parse_chars("abc"))
    assert(["a", "b", "c"] == parse_chars("a   bc"))

    # Check whitespaces get stripped
    # Non breaking, em space
    for uni in ["00A0", "2003"]:
        assert(["a", "b"] == parse_chars("a" + chr(int(uni, 16)) + "b"))

    # Check "whitespace" control characters do not get stripped
    # joiners, directional overwrites
    for uni in ["200D", "200E", "200F"]:
        unichr = chr(int(uni, 16))
        assert(["a", unichr, "b"] == parse_chars("a" + unichr + "b"))

    assert(len(parse_chars("а̄")) == 2)
    assert(parse_chars("ä") == ["ä", "a", "̈"])


def test_character_list_from_string():
    # Check list formation from (whitespace separated) input string with
    assert(["a", "b", "c"] == character_list_from_string("abc"))
    assert(["a", "b", "c"] == character_list_from_string("a b c"))
    assert(["a", "b", "c"] == character_list_from_string("a  b  c"))
    assert(["a", "b", "c"] == character_list_from_string("a a b a c"))


def test_list_unique():
    assert(["a", "b", "c"] == list_unique(["a", "a", "b", "c"]))
