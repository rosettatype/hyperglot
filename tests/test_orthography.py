import pytest
import logging

from hyperglot import OrthographyStatus
from hyperglot.languages import Languages
from hyperglot.language import Language
from hyperglot.orthography import Orthography, is_mark


@pytest.fixture
def langs():
    return Languages()


@pytest.fixture
def orthography_with_omitted_defaults():
    """
    Return a Orthography with omitted default values, to test defaults being
    set correctly. Currently there is only 'preferred_as_group' that is
    optional on Orthography.
    """

    return Orthography({})


def test_orthography_character_list(langs):
    deu = Language("deu")
    ort_default = Orthography(deu["orthographies"][0])

    deu_base_default = ort_default._character_list("base")

    assert "Ä" in deu_base_default
    assert "̈" not in deu_base_default


def test_orthography_base():
    # An orthography with unencoded base + marks should return only the base
    unencoded_base_chars = {"base": "R̃ r̃"}
    ort = Orthography(unencoded_base_chars)
    assert ort.base_chars == ["R", "r"]
    assert ort.base == ["R̃", "r̃"]

    # Make sure encoded base + marks are returned, and do not decompose
    encoded_base_chars = {"base": "Ä ä"}
    ort = Orthography(encoded_base_chars)
    assert ort.base_chars == ["Ä", "ä"]
    assert "A" not in ort.base_chars
    assert "a" not in ort.base_chars

    multiple_unencoded = {"base": "Ɔ̀ Ɔ̌ Ɔ̈"}  # from sbd.yaml
    ort = Orthography(multiple_unencoded)
    assert ort.base_chars == ["Ɔ"]
    assert len(ort.base_chars) == 1
    assert ort.base == ["Ɔ̀", "Ɔ̌", "Ɔ̈"]


def test_orthography_required_marks(langs):
    """
    autonym: Deutsch
    auxiliary: À É ẞ à é
    base: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Ä Ö Ü a b c d e f g h i j k l m n o p q r s t u v w x y z ß ä ö ü
    marks: ◌̈ ◌̀ ◌́
    note: Includes capital Eszett as an auxiliary character for capitalization of ß.
    script: Latin
    status: primary
    """
    deu = Language("deu")
    ort = Orthography(deu["orthographies"][0])

    # Neither base nor aux has marks which cannot be derived form precomposed
    # chars, so there should not be any required marks
    assert ort.required_base_marks == []
    assert ort.required_auxiliary_marks == []

    # Base only requires diesresis comb
    assert ort.base_marks == ["̈"]

    # Aux requires acute and grave comb, and also the base dieresis comb
    assert ort.auxiliary_marks == ["̈", "̀", "́"]

    """
    rus_base = "А Б В Г Д Е Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я Ё а б в г д е ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я ё"
    rus_aux = "А́ Е́ И́ О́ У́ Ы́ Э́ ю́ я́ а́ е́ и́ о́ у́ ы́ э́ ю́ я́"
    rus_marks = "◌̆ ◌̈ ◌́"
    """

    rus = Language("rus")
    ort = Orthography(rus["orthographies"][0])

    # No marks should be required since all are implicit from precomposed
    assert ort.required_base_marks == []
    assert ort.required_auxiliary_marks == ["́"]

    # Base should not need the acute
    assert ort.base_marks == ["̆", "̈"]

    # Aux should need all
    assert ort.auxiliary_marks == ["̆", "̈", "́"]

    """
    bulgarian:

    auxiliary: А̀ О̀ У̀ Ъ̀ Ю̀ Я̀ а̀ о̀ у̀ ъ̀ ю̀ я̀
    base: А Б В Г Д Е Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ъ Ь Ю Я Ѐ Ѝ а б в г д е ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ь ю я ѐ ѝ
    marks: ◌̀ ◌̆
    """
    bul = Language("bul")
    ort = Orthography(bul["orthographies"][0])

    assert ort.base_marks == ["̀", "̆"]
    assert ort.required_base_marks == []
    assert ort.required_auxiliary_marks == ["̀"]

    """
    hausa:

    base: A B C D E F G H I J K L M N O R S T U W Y Z Ƙ Ƴ Ɓ Ɗ R̃ a b c d e f g h i j k l m n o r s t u w y z ƙ ƴ ɓ ɗ r̃ ʼ
    """
    hau = Language("hau")
    ort = Orthography(hau["orthographies"][0])

    assert ort.required_base_marks == ["̃"]
    assert ort.required_auxiliary_marks == ["̃"]


def test_orthography_decomposed():
    o = Orthography({"base": "Ä"})
    assert o["base"] == "Ä"
    assert o.base == ["Ä"]


def test_orthography_design_alternates():
    o = Orthography({"design_alternates": "Ą Ę Į Ǫ ą ą́ ę ę́ į į́ ǫ ǫ́"})

    assert o.design_alternates == [
        "Ą",
        "Ę",
        "Į",
        "Ǫ",
        "ą",
        "ą́",
        "ę",
        "ę́",
        "į",
        "į́",
        "ǫ",
        "ǫ́",
    ]

    o = Orthography({"design_alternates": "◌̆"})
    assert o.design_alternates == ["̆"]


def test_is_mark():
    assert is_mark("Я̀") is False
    assert is_mark("A") is False
    assert is_mark("Ä") is False
    assert is_mark("◌̆") is False
    assert is_mark("◌") is False
    assert is_mark("") is False
    assert is_mark("ُ") is True
    assert is_mark("̃") is True


def test_yaml_escape_sequences(langs):
    # Test some particular cases where the yaml encoding has lead to confusion

    # Confirm the single auxiliary mark ' in Standard Malay is returned as such
    zsm = Language("zsm")
    assert zsm.get_orthography()["auxiliary"] == "'"


def test_orthography_defaults(orthography_with_omitted_defaults):
    assert orthography_with_omitted_defaults["preferred_as_group"] is False
    assert orthography_with_omitted_defaults["base"] == ""
    assert (
        orthography_with_omitted_defaults["status"] == OrthographyStatus.PRIMARY.value
    )


def test_orthography_script_iso(langs):
    # Something that relies on the mapping
    assert Orthography({"script": "Chinese"})["script_iso"] == "Hani"

    # Just sanity checks
    assert Orthography({"script": "Latin"})["script_iso"] == "Latn"
    assert Orthography({"script": "N'Ko"})["script_iso"] == "Nkoo"

    # An actual Orthography with data
    deu = Language("deu")
    assert Orthography(deu["orthographies"][0])["script_iso"] == "Latn"

    # An error for a script not in the hyperglot mapping
    with pytest.raises(NotImplementedError):
        Orthography({"script": "Foobar"})["script_iso"]

    assert Orthography({"script": "Geʽez"})["script_iso"] == "Ethi"


def test_inheritance(caplog):
    # Just basic inheritance test
    basic = Orthography({"base": "<eng> ß ∂ œ ø", "script": "Latin"})
    assert "A" in basic.base_chars

    # Multiple languages, and position test
    inherit_multiple = Orthography({"base": "ß <eng> ∂ œ < fin > ø", "script": "Latin"})
    assert "ß" in inherit_multiple.base_chars
    assert "ß" == inherit_multiple.base_chars[0]
    assert "ø" == inherit_multiple.base_chars[-1]
    assert "Å" in inherit_multiple.base_chars

    # Afar (aar) has no auxiliary or marks to inherit, this should trigger a
    # warning.
    with pytest.raises(KeyError):
        Orthography({"auxiliary": "<aar>", "script": "Latin"})
        assert "Orthography cannot inherit non-existing" in caplog.text

    with pytest.raises(KeyError):
        Orthography({"marks": "<aar>", "script": "Latin"})
        assert "Orthography cannot inherit non-existing" in caplog.text

    assert "»" in Orthography({"punctuation": "<eng> » « › ‹"})["punctuation"]

    # Sanity-test a few specific cases from the data

    assert "»" in Language("fra").get_orthography()["punctuation"]
    assert "0" in Language("fra").get_orthography()["numerals"]

    # The inherited value IS in the parsed Orthography
    assert "¤" in Language("fra").get_orthography()["currency"]
    assert "0" in Language("arb").get_orthography()["numerals"]

    # Confirm specifying a script works
    basic = Orthography({"base": "<eng Latin> ß ∂ œ ø", "script": "Latin"})
    assert "A" in basic.base_chars

    # Make sure all script names work
    nko = Orthography({"base": "<emk N'Ko>", "script": "N'Ko"})
    assert "ߐ" in nko.base

    # Fail with error for forcing inheriting from a script that does not exist
    with pytest.raises(KeyError):
        Orthography({"base": "<eng Arabic> ß ∂ œ ø", "script": "Latin"})

    # Fail when trying to inherit gibberish
    with pytest.raises(ValueError):
        Orthography({"base": "<eng Foobar> ß ∂ œ ø", "script": "Latin"})

    # Inherit from a different attribute
    different = Orthography({"base": "<eng auxiliary>", "script": "Latin"})
    assert "Ç" in different.base
    assert "<" not in different.base
    assert not different.auxiliary

    # Inherit from a non-primary orthography
    nonprimary = Orthography({"base": "<eng auxiliary historical>", "script": "Latin"})
    assert "ſ" in nonprimary.base

    # Fail for inheriting a non existing status
    with pytest.raises(KeyError):
        Orthography({"base": "<eng transliteration>", "script": "Latin"})

    # Just test the parser doesn't choke
    sloppy = Orthography({"base": "A B   <   eng  auxiliary   historical>C D"})
    assert "ſ" in sloppy.base
    assert "C" in sloppy.base

    # Test all attributes get inherited
    assert type(Language("aec").get_orthography()["design_requirements"]) is not dict


def test_inheritance_debug():
    # print(">>>>>arabic ", Language("arb").get_orthography()["numerals"])

    # Just test the parser doesn't choke
    sloppy = Orthography({"base": "A B   <   eng  auxiliary   historical>C D"})
    assert "ſ" in sloppy.base
    assert "C" in sloppy.base


# TBD not sure if this is strictly necessairy anywhere down the road. It's
# quite tricky to get lists and strings to merge sensibly.
# def test_inheritance_types():
#     # Test lists are inherited with the same type
#     src = Language("pes").get_orthography()
#     inh = Language("prs").get_orthography()
#     print("A src", type(src["design_requirements"]), src["design_requirements"])
#     print("B inh", type(inh["design_requirements"]), inh["design_requirements"])
#     assert type(src["design_requirements"]) == type(inh["design_requirements"])


def test_inherit_default():
    inherit_default = Orthography({"numerals": "<default>", "script": "Latin"})
    assert "0" in inherit_default.numerals

    inherit_default_script = Orthography({"numerals": "<default>", "script": "Arabic"})
    assert "٩" in inherit_default_script.numerals

    arb = Language("arb").get_orthography()
    assert "0" in arb.numerals
    assert "٩" in arb.numerals
