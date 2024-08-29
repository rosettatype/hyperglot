"""
Basic Language support checks
"""
import pytest
from hyperglot import LanguageStatus, LanguageValidity
from hyperglot.languages import Languages
from hyperglot.language import Language
from hyperglot.orthography import Orthography


@pytest.fixture
def language_with_omitted_defaults():
    """
    Return a Language with omitted default values, to test defaults being set
    correctly. Currently there is only 'status' that is optional on Language.
    """

    return Language("tmp", {})

@pytest.fixture
def langs():
    return Languages()


def test_language_inherit():
    # aae inherits aln orthography
    aae = Language("aae")
    aln = Language("aln")
    print("AAE", aae.get_orthography()["base"])
    print("ALN", aln.get_orthography()["base"])
    assert aae.get_orthography()["base"] == aln.get_orthography()["base"]


def test_language_preferred_name(langs):
    bal = Language("bal")
    #   name: Baluchi
    #   preferred_name: Balochi
    assert bal.get_name() == "Balochi"
    assert bal.name == "Balochi"


def test_language_get_autonym(langs):
    bal = Language("bal")
    #   name: Baluchi
    #   - autonym: بلۏچی
    #     script: Arabic
    #   preferred_name: Balochi

    # For Arabic it should return the correct autonym, without script False
    assert bal.get_autonym(script="Arabic") == "بلۏچی"
    assert bal.get_autonym() == "بلۏچی"
    assert bal.autonym == "بلۏچی"

    # No autonym for this script, and none on the main language dict
    assert bal.get_autonym(script="Latin") == ""


def test_language_orthographies():

    assert len(Language("smj")["orthographies"]) == 2
    primary_orthography = Language("smj").get_orthography()
    assert primary_orthography["status"] == "primary"


def test_get_orthography(langs):

    deu = Language("deu")

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

    bos = Language("bos")

    # Return a script specific orthography, even if that is not the primary one
    bos_cyrillic = bos.get_orthography("Cyrillic")
    assert ("Д" in bos_cyrillic["base"]) is True

    # However if for a specific script and status no orthography exists raise
    # exceptions
    with pytest.raises(KeyError):
        bos.get_orthography("Cyrillic", "primary")


def test_language_defaults(language_with_omitted_defaults):
    assert language_with_omitted_defaults["status"] == None
    assert language_with_omitted_defaults.status == LanguageStatus.LIVING.value

    assert language_with_omitted_defaults["validity"] == None
    assert language_with_omitted_defaults.validity == LanguageValidity.TODO.value

    assert language_with_omitted_defaults["speakers"] is None
    assert language_with_omitted_defaults.speakers == 0

    assert language_with_omitted_defaults["name"] is None
    assert language_with_omitted_defaults.name == ""

    assert language_with_omitted_defaults["autonym"] is None
    assert language_with_omitted_defaults.autonym == ""


def test_language_presentation():
    deu = Language("deu")
    assert "speakers:" in deu.presentation
    assert "status: living" in deu.presentation
    assert "validity: verified" in deu.presentation

    # language without speakers
    tob = Language("tob")
    assert tob.speakers == 0
    assert tob["speakers"] is None


def test_language_orthography_access():
    eng = Language("eng")
    assert type(eng["orthographies"][0]) is Orthography
    assert type(eng.get_orthography()) is Orthography


def test_default_language():
    default = Language("default")
    assert "0" in default.get_orthography().numerals