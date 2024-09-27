"""
A few tests for conventience classes 
"""
from hyperglot import SupportLevel, OrthographyStatus


def test_parse_check_supportlevel():
    assert SupportLevel.parse("base") == ["base"]
    assert SupportLevel.parse(["base"]) == ["base"]
    assert SupportLevel.parse(["foo"]) == ["base"]
    assert SupportLevel.parse(["base", "foo"]) == ["base"]
    assert SupportLevel.parse(["all"]) == SupportLevel.all()
    assert SupportLevel.parse("all") == SupportLevel.all()
    assert SupportLevel.parse(["all"]) == [
        "base",
        "auxiliary",
        "punctuation",
        "numerals",
        "currency",
    ]


def test_parse_check_orthographystatus():
    assert OrthographyStatus.parse("primary") == ["primary"]
    assert OrthographyStatus.parse(["primary"]) == ["primary"]
    assert OrthographyStatus.parse(["foo"]) == ["primary"]
    assert OrthographyStatus.parse(["primary", "foo"]) == ["primary"]
    assert OrthographyStatus.parse(["all"]) == OrthographyStatus.all()
    assert OrthographyStatus.parse("all") == OrthographyStatus.all()
    assert OrthographyStatus.parse(["all"]) == [
        "primary",
        "local",
        "secondary",
        "historical",
        "transliteration",
    ]
