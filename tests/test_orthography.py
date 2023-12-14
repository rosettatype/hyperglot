import pytest
from hyperglot.orthography import Orthography, is_mark
from hyperglot.languages import Languages


@pytest.fixture
def langs():
    return Languages()


def test_orthography_character_list(langs):
    deu = getattr(langs, "deu")
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
    deu = getattr(langs, "deu")
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

    rus = getattr(langs, "rus")
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
    bul = getattr(langs, "bul")
    ort = Orthography(bul["orthographies"][0])

    assert ort.base_marks == ["̀", "̆"]
    assert ort.required_base_marks == []
    assert ort.required_auxiliary_marks == ["̀"]

    """
    hausa:

    base: A B C D E F G H I J K L M N O R S T U W Y Z Ƙ Ƴ Ɓ Ɗ R̃ a b c d e f g h i j k l m n o r s t u w y z ƙ ƴ ɓ ɗ r̃ ʼ
    """
    hau = getattr(langs, "hau")
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
    zsm = getattr(langs, "zsm")
    assert zsm.get_orthography()["auxiliary"] == "'"
