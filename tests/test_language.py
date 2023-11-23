"""
Basic Language support checks
"""
import os
import pytest
import unicodedata2 as uni
from hyperglot.languages import Languages
from hyperglot.language import Language, Orthography, is_mark
from hyperglot.parse import (character_list_from_string,
                             parse_font_chars, parse_marks)


@pytest.fixture
def langs():
    return Languages()


def test_language_supported(langs):

    # A Language object with the 'fin' data
    fin = getattr(langs, "fin")

    # These "chars" represent a font with supposedly those codepoints in it
    fin_chars_missing_a = character_list_from_string(
        "bcdefghijklmnopqrstuvwxyzäöå")
    fin_chars_base = character_list_from_string("ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅabcdefghijklmnopqrstuvwxyzäöå")  # noqa
    fin_chars_aux = character_list_from_string("ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅÆÕØÜŠŽabcdefghijklmnopqrstuvwxyzäöåæõøüšž")  # noqa
    fin_chars_no_precomposed = character_list_from_string("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")  # noqa

    # This is what supported should look like if it determines 'fin' is
    # supported
    fin_matched = {"Latin": ["fin"]}

    # Note pruneOrthographies=False is used to re-use the same Language object
    # for these tests without having removed unsupported orthographies

    matches = fin.supported(fin_chars_base, pruneOrthographies=False)
    assert matches == fin_matched

    no_matches = fin.supported(fin_chars_base, level="aux",
                               pruneOrthographies=False)
    assert no_matches == {}

    matches = fin.supported(fin_chars_aux, level="aux",
                            pruneOrthographies=False)
    assert matches == fin_matched

    no_matches = fin.supported(fin_chars_base, level="aux",
                               pruneOrthographies=False)
    assert no_matches == {}

    no_matches = fin.supported(fin_chars_missing_a, pruneOrthographies=False)
    assert no_matches == {}

    rus = getattr(langs, "rus")

    rus_base = character_list_from_string("А Б В Г Д Е Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я Ё а б в г д е ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я ё")  # noqa
    # rus_aux = "А́ Е́ И́ О́ У́ Ы́ Э́ ю́ я́ а́ е́ и́ о́ у́ ы́ э́ ю́ я́"
    # rus_marks = "◌̆ ◌̈ ◌́"

    assert rus.supported(rus_base, level="base", pruneOrthographies=False)


def test_supported_marks(langs):
    deu = getattr(langs, "deu")

    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with not combining marks
    chars = [c for c in chars if not uni.category(c).startswith("M")]
    assert deu.supported(chars) != {}
    assert deu.supported(chars, marks=True) == {}


def test_supported_decomposed_no_marks(langs):
    deu = getattr(langs, "deu")

    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with not combining marks
    chars = [c for c in chars if not uni.category(c).startswith("M")]

    # The font which has no marks but all encoded characters should still match
    print(deu.supported(chars, decomposed=True))

    assert deu.supported(chars, decomposed=True) != {}


def test_supported_decomposed(langs):

    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with no encoded german umlauts
    chars = [c for c in chars if c not in ["Ä", "Ö", "Ü", "ä", "ö", "ü"]]

    deu = getattr(langs, "deu")
    assert deu.supported(chars, decomposed=False) == {}

    # Let's fake a font which has neither umlauts nor marks
    chars = parse_font_chars(eczar)
    chars = [c for c in chars if c not in ["Ä", "Ö", "Ü", "ä", "ö", "ü", "̈"]]
    deu = getattr(langs, "deu")
    # It should not be supporting deu
    assert deu.supported(chars, decomposed=True) == {}

    # Let's fake a font which is missing some umlauts, but has needed
    # base + marks
    chars = parse_font_chars(eczar)
    chars = [c for c in chars if c not in ["Ö", "Ü", "ö", "ü"]]
    deu = getattr(langs, "deu")
    # It should be supporting deu
    assert deu.supported(chars, decomposed=True) != {}


def test_language_inherit():
    langs = Languages(inherit=True)

    # aae inherits aln orthography
    aae = getattr(langs, "aae")
    aln = getattr(langs, "aln")
    assert aae.get_orthography()["base"] == aln.get_orthography()["base"]

    # without inheritance aae's only orthography should not have any base chars
    langs = Languages(inherit=False)
    aae = getattr(langs, "aae")
    assert "base" not in aae.get_orthography()


def test_language_preferred_name(langs):
    bal = getattr(langs, "bal")
    #   name: Baluchi
    #   preferred_name: Balochi
    assert bal.get_name() == "Balochi"


def test_language_get_autonym(langs):
    bal = getattr(langs, "bal")
    #   name: Baluchi
    #   - autonym: بلۏچی
    #     script: Arabic
    #   preferred_name: Balochi

    # For Arabic it should return the correct autonym, without script False
    assert bal.get_autonym(script="Arabic") == "بلۏچی"
    assert bal.get_autonym() is False


def test_language_all_orthographies(langs):
    # smj Lule Sami with one primary and one deprecated orthography should
    # always return only the primary
    # All the chars from both orthographies
    smj_base = character_list_from_string("A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Á Ä Å Ñ Ö Ń a b c d e f g h i j k l m n o p q r s t u v w x y z á ä å ñ ö ń A B D E F G H I J K L M N O P R S T U V Á Ä Å Ŋ a b d e f g h i j k l m n o p r s t u v á ä å ŋ a n o")  # noqa

    # When checking primary orthographies only one should be included
    smj = getattr(langs, "smj")
    support = smj.supported(smj_base)
    assert ("smj" in support["Latin"]) is True
    assert len(smj["orthographies"]) == 1

    # Even when checking all orthographies the 'transliteration' orthography 
    # should not be included; byn has a primary and a transliteration 
    # orthography only
    byn = getattr(langs, "byn")
    byn_base = character_list_from_string("ሀ ሁ ሂ ሃ ሄ ህ ሆ ለ ሉ ሊ ላ ሌ ል ሎ ሐ ሑ ሒ ሓ ሔ ሕ ሖ መ ሙ ሚ ማ ሜ ም ሞ ረ ሩ ሪ ራ ሬ ር ሮ ሰ ሱ ሲ ሳ ሴ ስ ሶ ሸ ሹ ሺ ሻ ሼ ሽ ሾ ቀ ቁ ቂ ቃ ቄ ቅ ቆ ቈ ቊ ቋ ቌ ቍ ቐ ቑ ቒ ቓ ቔ ቕ ቖ ቘ ቚ ቛ ቜ ቝ በ ቡ ቢ ባ ቤ ብ ቦ ተ ቱ ቲ ታ ቴ ት ቶ ነ ኑ ኒ ና ኔ ን ኖ አ ኡ ኢ ኣ ኤ እ ኦ ከ ኩ ኪ ካ ኬ ክ ኮ ኰ ኲ ኳ ኴ ኵ ኸ ኹ ኺ ኻ ኼ ኽ ኾ ዀ ዂ ዃ ዄ ዅ ወ ዉ ዊ ዋ ዌ ው ዎ ዐ ዑ ዒ ዓ ዔ ዕ ዖ የ ዩ ዪ ያ ዬ ይ ዮ ደ ዱ ዲ ዳ ዴ ድ ዶ ጀ ጁ ጂ ጃ ጄ ጅ ጆ ገ ጉ ጊ ጋ ጌ ግ ጎ ጐ ጒ ጓ ጔ ጕ ጘ ጙ ጚ ጛ ጜ ጝ ጞ ⶓ ⶔ ጟ ⶕ ⶖ ጠ ጡ ጢ ጣ ጤ ጥ ጦ ጨ ጩ ጪ ጫ ጬ ጭ ጮ ፈ ፉ ፊ ፋ ፌ ፍ ፎ e u i a é o b c d f g h j k l m n p q r s t v w x y z ñ ñw th ch sh kh kw khw qw gw")
    support = byn.supported(byn_base, checkAllOrthographies=True)
    assert len(byn["orthographies"]) == 1

    # rmn Balkan Romani has Latin (primary) and Cyrillic orthographies
    # It should return only Latin by default, but both when listing all

    # All the chars from both orthographies
    rmn_base = character_list_from_string("A Ä Á B C Ć Č D E Ê É F Ğ H I Î Í J K L M N O Ö Ó P Ṗ Q R Ř S Š T U V W X Y Z a ä á b c ć č d e ê é f ğ h i î í j k l m n o ö ó p ṗ q r ř s š t u v w x y z А Б В Г Д Е Ё Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Ы Ь Э Ю Я а б в г д е ё ж з и й к л м н о п р с т у ф х ц ч ш ы ь э ю я")  # noqa

    # When checking all orthographies, the Cyrillic non-primary should be
    # included
    rmn = getattr(langs, "rmn")
    support = rmn.supported(rmn_base, checkAllOrthographies=True)
    assert ("rmn" in support["Latin"]) is True
    assert ("Cyrillic" in support.keys()) is True
    assert len(rmn["orthographies"]) == 2

    # When checking only primary only Latin should be included
    rmn = getattr(langs, "rmn")
    support = rmn.supported(rmn_base, checkAllOrthographies=False)
    assert ("rmn" in support["Latin"]) is True
    assert ("Cyrillic" not in support.keys()) is True
    assert len(rmn["orthographies"]) == 1


def test_language_multiple_primaries(langs):

    # E.g. aat Arvanitika Albanian has exceptionally two `primary`
    # orthographies, a font with support for either should include the language
    aat_latin = character_list_from_string("A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Á Ä Ç È É Ë Í Ï Ó Ö Ú Ü Ý a b c d e f g h i j k l m n o p q r s t u v w x y z á ä ç è é ë í ï ó ö ú ü ý")  # noqa
    aat = getattr(langs, "aat")
    support = aat.supported(aat_latin)
    assert ("Latin" in support.keys()) is True
    assert ("Greek" not in support.keys()) is True
    assert len(aat["orthographies"]) == 1


def test_language_combined_orthographies():
    langs = Languages(inherit=False)

    # E.g. Serbian or Japanese have multiple orthographies that should be
    # treated as a combination, e.g. require all for support
    srp = getattr(langs, "srp")
    srp_cyrillic = character_list_from_string('А Б В Г Д Е Ж З И К Л М Н О П Р С Т У Ф Х Ц Ч Ш Ђ Ј Љ Њ Ћ Џ З́ С́ а б в г д е ж з и к л м н о п р с т у ф х ц ч ш ђ ј љ њ ћ џ з́ с́') + ["́"]  # noqa
    srp_latin = character_list_from_string('A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Ć Č Đ Ś Š Ź Ž a b c d e f g h i j k l m n o p q r s t u v w x y z ć č đ ś š ź ž')  # noqa

    # Checking support with just the one script will no list the language
    support = srp.supported(srp_latin)
    assert support == {}
    support = srp.supported(srp_cyrillic)
    assert support == {}

    # Checking with the combined chars this should now return both
    # orthographies
    srp = getattr(langs, "srp")
    combined = srp_cyrillic + srp_latin
    support = srp.supported(combined)
    assert ("Cyrillic" in support) is True
    assert ("Latin" in support) is True
    assert ("srp" in support["Cyrillic"]) is True
    assert ("srp" in support["Latin"]) is True

    # Checking with --include-all-orthographies should return also a single
    # orthography
    srp = getattr(langs, "srp")
    support = srp.supported(srp_latin, checkAllOrthographies=True)
    assert ("Latin" in support) is True


def test_language_supported_combining_chars():

    hau_base = character_list_from_string(
        "A B C D E F G H I J K L M N O R S T U W Y Z Ƙ Ƴ Ɓ Ɗ R̃ a b c d e f g h i j k l m n o r s t u w y z ƙ ƴ ɓ ɗ r̃ ʼ")
    hau_marks = parse_marks("◌̃ ◌̀ ◌́ ◌̂")

    # Drop the unencoded R/r tilde chars
    hau_base = [b for b in hau_base if len(b) == 1]

    # A "font charset" with all encoded Hausa chars
    hau_chars = hau_base + hau_marks

    langs = Languages()
    hau = getattr(langs, "hau")
    result = hau.supported(hau_chars)
    assert "hau" in result["Latin"]


def test_get_orthography(langs):

    deu = getattr(langs, "deu")

    # By default and with not parameters it should return the primary
    # orthography
    deu_primary = deu.get_orthography()
    assert ("ẞ" in deu_primary["auxiliary"]) is True

    # Return a specific orthography
    deu_historical = deu.get_orthography(status="historical")
    assert deu_historical != deu_primary
    assert ("ẞ" not in deu_historical["auxiliary"]) is True

    # Raise error when a script does not exist
    with pytest.raises(KeyError):
        deu.get_orthography(script="Foobar")

    # Raise error when a status does not exist
    with pytest.raises(KeyError):
        deu.get_orthography(status="constructed")

    bos = getattr(langs, "bos")

    # Return a script specific orthography, even if that is not the primary one
    bos_cyrillic = bos.get_orthography("Cyrillic")
    assert ("Д" in bos_cyrillic["base"]) is True

    # However if for a specific script and status no orthography exists raise
    # exceptions
    with pytest.raises(KeyError):
        bos.get_orthography("Cyrillic", "primary")


def test_orthography_character_list(langs):

    deu = getattr(langs, "deu")
    ort_default = Orthography(deu["orthographies"][0])

    deu_base_default = ort_default._character_list("base")

    assert "Ä" in deu_base_default
    assert '̈' not in deu_base_default


def test_orthography_base():

    # An orthography with unencoded base + marks should return only the base
    unencoded_base_chars = {
        "base": "R̃ r̃"
    }
    ort = Orthography(unencoded_base_chars)
    assert ort.base_chars == ["R", "r"]
    assert ort.base == ["R̃", "r̃"]

    # Make sure encoded base + marks are returned, and do not decompose
    encoded_base_chars = {
        "base": "Ä ä"
    }
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
    assert ort.base_marks == ['̈']

    # Aux requires acute and grave comb, and also the base dieresis comb
    assert ort.auxiliary_marks == ['̈', '̀', '́']

    """
    rus_base = "А Б В Г Д Е Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я Ё а б в г д е ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я ё"
    rus_aux = "А́ Е́ И́ О́ У́ Ы́ Э́ ю́ я́ а́ е́ и́ о́ у́ ы́ э́ ю́ я́"
    rus_marks = "◌̆ ◌̈ ◌́"
    """

    rus = getattr(langs, "rus")
    ort = Orthography(rus["orthographies"][0])

    # No marks should be required since all are implicit from precomposed
    assert ort.required_base_marks == []
    assert ort.required_auxiliary_marks == ['́']

    # Base should not need the acute
    assert ort.base_marks == ['̆', '̈']

    # Aux should need all
    assert ort.auxiliary_marks == ['̆', '̈', '́']

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
    o = Orthography({
        "base": "Ä"
    })
    assert o["base"] == "Ä"
    assert o.base == ["Ä"]


def test_orthography_design_alternates():
    o = Orthography({
        "design_alternates": "Ą Ę Į Ǫ ą ą́ ę ę́ į į́ ǫ ǫ́"
    })

    assert o.design_alternates == [
        "Ą", "Ę", "Į", "Ǫ", "ą", "ą́", "ę", "ę́", "į", "į́", "ǫ", "ǫ́"]

    o = Orthography({
        "design_alternates": "◌̆"
    })
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
