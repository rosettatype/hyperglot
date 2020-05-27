"""
A humble start is better than none
"""
from fontlang.languages import parse_chars


def test_parse_chars():
    # Verify composites get decomposed correctly
    assert({"j", "ĳ", "i"} == parse_chars("ĳ"))
    assert({"å", "̊", "a", "̂", "â"} == parse_chars("â å"))

    # Check basic splitting
    assert(5 == len(parse_chars("abcde")))
    assert(5 == len(parse_chars("a b c d e")))
