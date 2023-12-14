from hyperglot.languages import Languages


def test_languages_validity():
    # These statuses may change in the database, update accordingly
    # aae is verified
    # aaq is preliminary
    # aat is draft

    verified_languages = Languages(validity="verified")
    assert "aae" in verified_languages
    assert "aaq" not in verified_languages
    assert "aat" not in verified_languages

    including_draft_languages = Languages(validity="draft")
    assert "aat" in including_draft_languages


def test_languages_inherit():
    Langs = Languages(inherit=True)

    # Algerian Arabic arq has one orthography that inherits from Tunisian
    # Arabic aeb, which in turn inherits from Standard Arabic arb
    arq = Langs["arq"]["orthographies"][0]
    aeb = Langs["aeb"]["orthographies"][0]
    arb = Langs["arb"]["orthographies"][0]

    assert arq["base"] == arb["base"]

    # Make sure the autonym did not get inherited
    assert arq["autonym"] == "دارجة جزائرية"

    # Make sure arq and arb have same amount of attributes, e.g. everything
    # that can be inherited did get inherited (arq will have the 'inherit'
    # attribute, so for testing equality, add it to the list of attributes that
    # arb has)
    arq_attr = set(sorted(arq.keys()))
    aeb_attr = set(sorted(list(aeb.keys()) + ["inherit"]))
    arb_attr = set(sorted(list(arb.keys()) + ["inherit"]))
    assert arq_attr == aeb_attr == arb_attr


def test_languages_parsed_from_escaped_filenames():
    Langs = Languages()
    assert hasattr(Langs, "con")
    assert "con" in Langs
