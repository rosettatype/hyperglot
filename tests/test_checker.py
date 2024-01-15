"""
Basic Language support checks
"""
import os
import logging
import pytest
import unicodedata as uni
from hyperglot.parse import character_list_from_string, parse_font_chars, parse_marks
from hyperglot.checker import CharsetChecker, FontChecker

# Just a most simple placeholder charset
ascii = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Some test font paths
plex_arabic = os.path.abspath(
    "tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf"
)  # noqa
plex_arabic_without_medi_fina = os.path.abspath(
    "tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular-without-medi-fina.otf"
)  # noqa
eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
testfont = os.path.abspath("tests/HyperglotTestFont-Regular.ttf")


def test_checker_classes():
    eng = ascii + "ÆŒæœ"
    fontchecker = FontChecker(eczar)

    assert "Latin" in fontchecker.get_supported_languages(shaping=True).keys()

    charsetchecker = CharsetChecker(eng)

    assert "Latin" in charsetchecker.get_supported_languages().keys()
    assert charsetchecker.supports_language("eng")

    # You cannot test shaping with CharsetChecker
    with pytest.raises(ValueError):
        charsetchecker.get_supported_languages(shaping=True)

    with pytest.raises(ValueError):
        charsetchecker.supports_language("eng", shaping=True)


def test_language_supported():
    # These "chars" represent a font with supposedly those codepoints in it
    fin_missing_a = character_list_from_string("bcdefghijklmnopqrstuvwxyzäöå")
    fin_base = character_list_from_string(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅabcdefghijklmnopqrstuvwxyzäöå"
    )
    fin_aux = character_list_from_string(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÅÆÕØÜŠŽabcdefghijklmnopqrstuvwxyzäöåæõøüšž"
    )
    # fin_chars_no_precomposed = character_list_from_string(
    #     "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    # )

    rus_base = character_list_from_string(
        "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЁабвгдежзийклмнопрстуфхцчшщъыьэюяё"
    )
    # rus_aux = "А́ Е́ И́ О́ У́ Ы́ Э́ ю́ я́ а́ е́ и́ о́ у́ ы́ э́ ю́ я́"
    # rus_marks = "◌̆ ◌̈ ◌́"

    # This is long
    matches = CharsetChecker(fin_base).get_supported_languages()
    assert "fin" in matches["Latin"].keys()

    # for this shorter direct check
    assert CharsetChecker(fin_base).supports_language("fin")

    # Just base chars input won't support aux
    assert (
        CharsetChecker(fin_base).supports_language("fin", supportlevel="aux") is False
    )

    # But aux chars input will
    assert CharsetChecker(fin_aux).supports_language("fin", supportlevel="aux")

    # A Font without 'a' won't support this language
    assert CharsetChecker(fin_missing_a).supports_language("fin") is False

    # Just basic other language check
    assert CharsetChecker(rus_base).supports_language("rus", supportlevel="base")


def test_language_supported_dict():
    checker = FontChecker(eczar)

    # Detected scripts
    assert "Latin" in checker.supports_language("deu", return_script_object=True).keys()
    assert (
        "Arabic"
        not in checker.supports_language("deu", return_script_object=True).keys()
    )

    # Detected arbitrary language
    assert "zul" in checker.supports_language("zul", return_script_object=True)["Latin"]


def test_language_supported_validity():
    aae_base = character_list_from_string(
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Ç Ë a b c d e f g h i j k l m n o p q r s t u v w x y z ç ë"
    )
    aaq_base = character_list_from_string(
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Ô a b c d e f g h i j k l m n o p q r s t u v w x y z ô"
    )
    aat_base = character_list_from_string(
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Á Ä Ç È É Ë Í Ï Ó Ö Ú Ü Ý a b c d e f g h i j k l m n o p q r s t u v w x y z á ä ç è é ë í ï ó ö ú ü ý"
    )

    # These statuses may change in the database, update accordingly
    # aae is verified (Latin)
    # aaq is preliminary (Latin)
    # aat is draft (has Latin also)
    assert CharsetChecker(aae_base).supports_language("aae", validity="verified")
    assert CharsetChecker(aae_base).supports_language("aae", validity="preliminary")
    assert CharsetChecker(aae_base).supports_language("aae", validity="draft")

    assert (
        CharsetChecker(aaq_base).supports_language("aaq", validity="verified") is False
    )
    assert CharsetChecker(aaq_base).supports_language("aaq", validity="preliminary")
    assert CharsetChecker(aaq_base).supports_language("aaq", validity="draft")

    assert (
        CharsetChecker(aat_base).supports_language("aat", validity="verified") is False
    )
    assert (
        CharsetChecker(aat_base).supports_language("aat", validity="preliminary")
        is False
    )
    assert CharsetChecker(aat_base).supports_language("aat", validity="draft")


def test_non_iso():
    # Nope for language names
    with pytest.raises(ValueError):
        assert CharsetChecker(ascii).supports_language("German")

    # Nope for non existing iso codes
    with pytest.raises(ValueError):
        assert CharsetChecker(ascii).supports_language("xxx")

    # Nope for misc other input
    with pytest.raises(ValueError):
        assert CharsetChecker(ascii).supports_language(True)
    with pytest.raises(ValueError):
        assert CharsetChecker(ascii).supports_language(123)


def test_supports_marks():
    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with no combining marks
    chars = [c for c in chars if not uni.category(c).startswith("M")]

    assert CharsetChecker(chars).supports_language("deu")

    # If all combining marks are required and the input has no combining marks
    # this should no longer match
    assert CharsetChecker(chars).supports_language("deu", marks=True) is False


def test_supports_decomposed_only_marks(caplog):
    caplog.set_level(logging.WARNING, logger="hyperglot.reporting.missing")

    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font's chars which has all precomposed chars removed which
    # can be combined from base + mark combinations
    _chars = []
    for c in chars:
        if (
            not uni.category(c).startswith("L")
            or len(uni.decomposition(c).split(" ")) < 2
        ):
            _chars.append(c)
            continue

    assert CharsetChecker(_chars).supports_language("deu", decomposed=True)


def test_supports_decomposed():
    eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
    chars = parse_font_chars(eczar)

    # Let's fake a font with no encoded german umlauts
    chars = [c for c in chars if c not in ["Ä", "Ö", "Ü", "ä", "ö", "ü"]]

    # Base + marks are not enough, we want composed chars, and they are missing
    assert CharsetChecker(chars).supports_language("deu", decomposed=False) is False

    # Let's fake a font which has neither umlauts nor marks (the last is a dieresis comb)
    chars = parse_font_chars(eczar)
    chars = [c for c in chars if c not in ["Ä", "Ö", "Ü", "ä", "ö", "ü", "̈"]]
    # It should not be supporting deu either
    assert CharsetChecker(chars).supports_language("deu", decomposed=True) is False

    # Let's fake a font which is missing some umlauts, but has needed
    # base + marks
    chars = parse_font_chars(eczar)
    chars = [c for c in chars if c not in ["Ö", "Ü", "ö", "ü"]]
    # It should be supporting deu, because the missing A/a umlauts can be
    # composed from base + marks
    assert CharsetChecker(chars).supports_language("deu", decomposed=True)


def test_supports_font():
    # Basic FontChecker sanity tests.
    assert FontChecker(eczar).supports_language("deu")
    assert FontChecker(eczar).supports_language("fin")


def test_language_all_orthographies():
    # This charset is missing e.g. 'ŋ' in order to support the primary orthography,
    # but it is supporting the historical orthography.
    smj_historical = character_list_from_string(
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Á Ä Å Ñ Ö Ń a b c d e f g h i j k l m n o p q r s t u v w x y z á ä å ñ ö ń"
    )

    # When checking primary orthographies this should not be supported.
    assert (
        CharsetChecker(smj_historical).supports_language(
            "smj", check_all_orthographies=False
        )
        is False
    )

    # When checking all it should be supported.
    assert CharsetChecker(smj_historical).supports_language(
        "smj", check_all_orthographies=True
    )

    # Even when checking all orthographies the 'transliteration' orthography
    # should not be included; byn has a primary and a transliteration
    # orthography only
    byn_base = character_list_from_string(
        "ሀ ሁ ሂ ሃ ሄ ህ ሆ ለ ሉ ሊ ላ ሌ ል ሎ ሐ ሑ ሒ ሓ ሔ ሕ ሖ መ ሙ ሚ ማ ሜ ም ሞ ረ ሩ ሪ ራ ሬ ር ሮ ሰ ሱ ሲ ሳ ሴ ስ ሶ ሸ ሹ ሺ ሻ ሼ ሽ ሾ ቀ ቁ ቂ ቃ ቄ ቅ ቆ ቈ ቊ ቋ ቌ ቍ ቐ ቑ ቒ ቓ ቔ ቕ ቖ ቘ ቚ ቛ ቜ ቝ በ ቡ ቢ ባ ቤ ብ ቦ ተ ቱ ቲ ታ ቴ ት ቶ ነ ኑ ኒ ና ኔ ን ኖ አ ኡ ኢ ኣ ኤ እ ኦ ከ ኩ ኪ ካ ኬ ክ ኮ ኰ ኲ ኳ ኴ ኵ ኸ ኹ ኺ ኻ ኼ ኽ ኾ ዀ ዂ ዃ ዄ ዅ ወ ዉ ዊ ዋ ዌ ው ዎ ዐ ዑ ዒ ዓ ዔ ዕ ዖ የ ዩ ዪ ያ ዬ ይ ዮ ደ ዱ ዲ ዳ ዴ ድ ዶ ጀ ጁ ጂ ጃ ጄ ጅ ጆ ገ ጉ ጊ ጋ ጌ ግ ጎ ጐ ጒ ጓ ጔ ጕ ጘ ጙ ጚ ጛ ጜ ጝ ጞ ⶓ ⶔ ጟ ⶕ ⶖ ጠ ጡ ጢ ጣ ጤ ጥ ጦ ጨ ጩ ጪ ጫ ጬ ጭ ጮ ፈ ፉ ፊ ፋ ፌ ፍ ፎ e u i a é o b c d f g h j k l m n p q r s t v w x y z ñ ñw th ch sh kh kw khw qw gw"
    )
    byn_trans = character_list_from_string(
        "e u i a é o b c d f g h j k l m n p q r s t v w x y z ñ ñw th ch sh kh kw khw qw gw"
    )
    assert CharsetChecker(byn_trans).supports_language("byn") is False
    assert (
        CharsetChecker(byn_trans).supports_language("byn", check_all_orthographies=True)
        is False
    )

    # rmn Balkan Romani has Latin (primary) and Cyrillic (secondary) orthographies

    # All the chars from both orthographies
    rmn_primary = character_list_from_string(
        "A Ä Á B C Ć Č D E Ê É F Ğ H I Î Í J K L M N O Ö Ó P Ṗ Q R Ř S Š T U V W X Y Z a ä á b c ć č d e ê é f ğ h i î í j k l m n o ö ó p ṗ q r ř s š t u v w x y z А Б В Г Д Е Ё Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Ы Ь Э Ю Я а б в г д е ё ж з и й к л м н о п р с т у ф х ц ч ш ы ь э ю я"
    )
    rmn_secondary = character_list_from_string(
        "А Б В Г Д Е Ё Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Ы Ь Э Ю Я а б в г д е ё ж з и й к л м н о п р с т у ф х ц ч ш ы ь э ю я"
    )

    # Match for primary orthography chars
    assert CharsetChecker(rmn_primary).supports_language("rmn")
    assert CharsetChecker(rmn_primary).supports_language(
        "rmn", check_all_orthographies=True
    )

    # Match for secondary orthography chars only if checking all orthographies
    assert CharsetChecker(rmn_secondary).supports_language("rmn") is False
    assert CharsetChecker(rmn_secondary).supports_language(
        "rmn", check_all_orthographies=True
    )


def test_language_multiple_primaries():
    # E.g. aat Arvanitika Albanian has exceptionally two `primary`
    # orthographies (but not prefer_as_group), so a font with support for
    # either should include the language
    aat_latin = character_list_from_string(
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Á Ä Ç È É Ë Í Ï Ó Ö Ú Ü Ý a b c d e f g h i j k l m n o p q r s t u v w x y z á ä ç è é ë í ï ó ö ú ü ý"
    )
    assert CharsetChecker(aat_latin).supports_language("aat")


def test_language_combined_orthographies():
    # E.g. Serbian or Japanese have multiple orthographies that should be
    # treated as a combination, e.g. require all for support

    srp_cyrillic = character_list_from_string(
        "А Б В Г Д Е Ж З И К Л М Н О П Р С Т У Ф Х Ц Ч Ш Ђ Ј Љ Њ Ћ Џ З́ С́ а б в г д е ж з и к л м н о п р с т у ф х ц ч ш ђ ј љ њ ћ џ з́ с́"
    ) + [
        "́"
    ]  # noqa
    srp_latin = character_list_from_string(
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z Ć Č Đ Ś Š Ź Ž a b c d e f g h i j k l m n o p q r s t u v w x y z ć č đ ś š ź ž"
    )  # noqa

    assert CharsetChecker(srp_latin).supports_language("srp") is False
    assert CharsetChecker(srp_cyrillic).supports_language("srp") is False
    assert CharsetChecker(srp_latin + srp_cyrillic).supports_language("srp")

    # Checking with --include-all-orthographies should return also a single
    # orthography
    assert CharsetChecker(srp_latin).supports_language(
        "srp", check_all_orthographies=True
    )


def test_language_supported_combining_chars():
    hau_base = character_list_from_string(
        "A B C D E F G H I J K L M N O R S T U W Y Z Ƙ Ƴ Ɓ Ɗ R̃ a b c d e f g h i j k l m n o r s t u w y z ƙ ƴ ɓ ɗ r̃ ʼ"
    )
    hau_marks = parse_marks("◌̃ ◌̀ ◌́ ◌̂")

    # Drop the unencoded R/r tilde chars with len > 1
    hau_base = [b for b in hau_base if len(b) == 1]

    # A "font charset" with all encoded Hausa chars
    hau_chars = hau_base + hau_marks

    assert CharsetChecker(hau_chars).supports_language("hau")


def test_language_mark_attachment():
    checker = FontChecker(eczar)

    # Basic Latin sanity check
    assert checker.supports_language("deu", shaping=True)

    # 'mah' has unencoded combination M + ogonekcomb — this is a good test case
    # to check if the mark gets attached as many fonts won't have the required
    # bottom anchor in M.
    # Eczar has both M and ogonekcomb (U+0328), but not the required anchor in
    # M and so it should not have support.
    assert checker.supports_language("mah", shaping=True) is False

    # Without the shaping check, however, it should pass
    assert checker.supports_language("mah", shaping=False)


def test_shaper_greek_marks():
    # Base for 'fin' but missing ÄÅ so we can check if decomposed=True will
    # actually compose and attach marks correctly
    fin_base_without_a_umlauts = character_list_from_string(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZÖabcdefghijklmnopqrstuvwxyzäöå"
    )
    fin_marks = parse_marks("◌̈ ◌̊ ◌̃ ◌̌")

    # The font needs to actually support the mark positioning, but we want to
    # test different types of "detected" characters to use for shaping
    missing_precomposed = FontChecker(eczar)
    missing_precomposed.characters = fin_base_without_a_umlauts + fin_marks
    assert missing_precomposed.supports_language("fin") is False
    assert missing_precomposed.supports_language("fin", decomposed=True)

    # Eczar does not support 'mah' with default decomposed=False either, but
    # just to confirm (and check debug logs for a language where decompose
    # would yield required marks for base)
    checker = FontChecker(eczar)
    assert checker.supports_language("mah", decomposed=True) is False


def test_checker_missing(caplog):
    caplog.set_level(logging.WARNING, logger="hyperglot.reporting.missing")

    checker = CharsetChecker(ascii)

    # Basic ascii should be missing 4 characters for English, so
    # this should log:
    checker.supports_language("eng", report_missing=4)
    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert "(eng) English missing characters for 'base'" in record.msg
    caplog.clear()

    # but this should not log:
    checker.supports_language("eng", report_missing=3)
    assert len(caplog.records) == 0


def test_checker_marks(caplog):
    caplog.set_level(logging.WARNING, logger="hyperglot.reporting.marks")

    checker = FontChecker(eczar)
    checker.supports_language("mah", report_marks=6)

    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert "(mah) Marshallese missing mark attachment for 'base'" in record.msg

    caplog.clear()

    # Checking for languages with at most 5 mark errors should not return mah
    # because it has 6 errors
    checker.supports_language("mah", report_marks=5)
    assert len(caplog.records) == 0


def test_checker_joining(caplog):
    caplog.set_level(logging.WARNING, logger="hyperglot.reporting.joining")

    checker = FontChecker(plex_arabic_without_medi_fina)
    checker.supports_language("acm", report_joining=99)

    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert "(acm) Iraqi Arabic missing joining forms" in record.msg

    caplog.clear()

    # Checking for languages with at most 1 joining error should not return
    # acm, because it is missing two dozen
    checker.supports_language("acm", report_joining=1)
    assert len(caplog.records) == 0
