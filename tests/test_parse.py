"""
Tests for basic parsing and decomposition methods
"""
import os
from hyperglot.parse import (parse_chars, parse_font_chars,
                             character_list_from_string,
                             sort_by_character_type,
                             list_unique)


def test_parse_chars():
    # Verify composites get decomposed correctly and their order is as expected

    # def parse_chars(characters, decompose=True, retainDecomposed=False):
    assert ["a", "̈"] == parse_chars("ä", decompose=True)
    assert ["ä", "a", "̈"] == parse_chars("ä", decompose=True,
                                          retainDecomposed=True)
    assert ["ä"] == parse_chars("ä", decompose=False)

    # This tests the decomposing will add first letter components, then mark
    # components (order!)
    assert ["â", "å", "a", "̂", "̊"] == parse_chars("â å",
                                                    retainDecomposed=True)
    assert ["a", "̂", "̊"] == parse_chars("â å", retainDecomposed=False)

    assert ["ĳ", "i", "j"] == parse_chars("ĳ", retainDecomposed=True)
    assert ["i", "j"] == parse_chars("ĳ", retainDecomposed=False)

    # Check basic splitting
    assert 5 == len(parse_chars("abcde"))
    assert 5 == len(parse_chars("a b c d e"))

    # Check whitespace separation
    assert ["a", "b", "c"] == parse_chars("abc")
    assert ["a", "b", "c"] == parse_chars("a   bc")

    # Check whitespaces get stripped
    # Non breaking, em space
    for uni in ["00A0", "2003"]:
        assert ["a", "b"] == parse_chars("a" + chr(int(uni, 16)) + "b")

    # Check "whitespace" control characters do not get stripped
    # joiners, directional overwrites
    for uni in ["200D", "200E", "200F"]:
        unichr = chr(int(uni, 16))
        assert ["a", unichr, "b"] == parse_chars("a" + unichr + "b")

    assert " " not in parse_chars("a   bc")
    assert " " not in parse_chars(
        "a ą b c d e ę g h i į j k l ł m n o ǫ s t w x y z ' ´")


def test_character_list_from_string():
    # Check list formation from (whitespace separated) input string with
    assert ["a", "b", "c"] == character_list_from_string("abc")
    assert ["a", "b", "c"] == character_list_from_string("a b c")
    assert ["a", "b", "c"] == character_list_from_string("a  b  c")
    assert ["a", "b", "c"] == character_list_from_string("a a b a c")
    assert ["ä"] == character_list_from_string("ä")


def test_list_unique():
    assert ["a", "b", "c"] == list_unique(["a", "a", "b", "c"])


def test_parse_font_chars():
    path = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(path)

    # Obviously this changes if the test file ever gets updated!
    assert len(chars) == 479

    # Just some basic sanity checks
    assert "Ä" in chars
    assert "अ" in chars


def test_sort_by_character_type():
    # Test sorting, Letters first, Marks second, rest after, and secondary sort
    # by ASC unicode
    expected = ["A", "Z", "a", "z", "̇", ".", "1"]
    assert sort_by_character_type(expected) == expected
