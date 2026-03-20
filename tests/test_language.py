"""
Basic Language support checks
"""
import pickle
import pytest
from unittest.mock import patch
from hyperglot import LanguageStatus, LanguageValidity
from hyperglot.languages import Languages
from hyperglot.language import Language, _load_language_cache
from hyperglot.orthography import Orthography
import hyperglot.language as language_module


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


def test_language_speakers():
    # historic language without speakers
    aaq = Language("aaq")
    assert aaq.speakers == 0

    # mock language without speakers attribute, should still return 0 on
    # attribute, and none on dict access
    foo = Language("foo", {})
    assert foo.speakers == 0
    assert foo["speakers"] is None

    # language with 'unknown' speakers
    njo = Language("njo")
    assert njo.speakers == 0
    assert njo["speakers"] == "unknown"


def test_language_orthography_access():
    eng = Language("eng")
    assert type(eng["orthographies"][0]) is Orthography
    assert type(eng.get_orthography()) is Orthography


def test_default_language():
    default = Language("default")
    assert "0" in default.get_orthography().numerals


# ---------------------------------------------------------------------------
# _load_language_cache tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=False)
def reset_language_cache():
    """Reset global cache state before and after each cache test."""
    language_module.LANGUAGE_CACHE = {}
    import hyperglot
    hyperglot.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN = False
    language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN = False
    yield
    language_module.LANGUAGE_CACHE = {}
    hyperglot.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN = False
    language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN = False


def _make_cache(data):
    """Helper: pickle a dict for use as a cache file."""
    return pickle.dumps(data)


def test_load_cache_matching_version(tmp_path, reset_language_cache):
    """A cache whose _version matches __version__ should load successfully."""
    from hyperglot import __version__

    cache_data = {
        "_version": __version__,
        "deu": {"name": "German"},
        "eng": {"name": "English"},
    }
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert "deu" in language_module.LANGUAGE_CACHE
    assert "eng" in language_module.LANGUAGE_CACHE
    # _version key should be removed after loading
    assert "_version" not in language_module.LANGUAGE_CACHE


def test_load_cache_skips_when_already_loaded(tmp_path, reset_language_cache):
    """If the cache dict is already populated, _load_language_cache is a no-op."""
    language_module.LANGUAGE_CACHE = {"already": "loaded"}

    from hyperglot import __version__

    cache_data = {"_version": __version__, "new": "data"}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    # Should still have the old data, file was not read
    assert language_module.LANGUAGE_CACHE == {"already": "loaded"}


def test_load_cache_version_mismatch(tmp_path, reset_language_cache):
    """A cache with a different version should be discarded."""
    cache_data = {
        "_version": "0.0.1",
        "deu": {"name": "German"},
    }
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE == {}


def test_load_cache_version_mismatch_warning_once(tmp_path, reset_language_cache):
    """The version-mismatch warning should only fire once."""
    cache_data = {"_version": "0.0.1", "deu": {"name": "German"}}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    # First call sets the flag
    assert language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN is True

    # Reset cache to empty so second call actually reads the file again
    language_module.LANGUAGE_CACHE = {}
    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)), \
         patch.object(language_module.log, "info") as mock_info:
        _load_language_cache()
        # The info log for mismatch should NOT be called again
        for call in mock_info.call_args_list:
            assert "does not match" not in str(call)


def test_load_cache_unversioned_legacy(tmp_path, reset_language_cache):
    """A cache without _version (legacy) should be discarded."""
    cache_data = {"deu": {"name": "German"}}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE == {}
    assert language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN is True


def test_load_cache_unversioned_warning_once(tmp_path, reset_language_cache):
    """The unversioned-cache warning should only fire once."""
    cache_data = {"deu": {"name": "German"}}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    language_module.LANGUAGE_CACHE = {}
    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)), \
         patch.object(language_module.log, "info") as mock_info:
        _load_language_cache()
        for call in mock_info.call_args_list:
            assert "unversioned" not in str(call).lower()


def test_load_cache_no_file(tmp_path, reset_language_cache):
    """When no cache file exists, the cache stays empty."""
    missing = str(tmp_path / "nonexistent-cache")

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", missing):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE == {}


def test_load_cache_corrupt_file(tmp_path, reset_language_cache):
    """A file with invalid pickle data should be handled gracefully."""
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(b"not valid pickle data at all")

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE == {}
    assert language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN is True


def test_load_cache_corrupt_file_warning_once(tmp_path, reset_language_cache):
    """The corrupt-file warning should only fire once."""
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(b"bad data")

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN is True

    # Reset cache so second call tries to read again
    language_module.LANGUAGE_CACHE = {}
    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)), \
         patch.object(language_module.log, "warning") as mock_warn:
        _load_language_cache()
        mock_warn.assert_not_called()


def test_load_cache_unreadable_file(tmp_path, reset_language_cache):
    """A file with no read permissions should be handled gracefully."""
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(b"something")
    cache_file.chmod(0o000)

    try:
        with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
            _load_language_cache()

        assert language_module.LANGUAGE_CACHE == {}
        assert language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN is True
    finally:
        # Restore permissions so tmp_path cleanup works
        cache_file.chmod(0o644)


def test_load_cache_empty_pickle_file(tmp_path, reset_language_cache):
    """An empty file (0 bytes) should be handled gracefully as corrupt."""
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(b"")

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE == {}


def test_load_cache_upgrade_then_downgrade(tmp_path, reset_language_cache):
    """Switching from a newer cache version to an older one should discard."""
    from hyperglot import __version__
    from packaging.version import Version

    # Simulate a cache written by a "future" version
    future = str(Version(__version__).major + 1) + ".0.0"
    cache_data = {"_version": future, "deu": {"name": "German"}}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert language_module.LANGUAGE_CACHE == {}


def test_load_cache_downgrade_then_upgrade(tmp_path, reset_language_cache):
    """Switching from an older cache version to the current one loads OK."""
    from hyperglot import __version__

    # First: old version cache -> discarded
    cache_data_old = {"_version": "0.0.1", "deu": {"name": "German old"}}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data_old))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()
    assert language_module.LANGUAGE_CACHE == {}

    # Now write current-version cache and reload
    language_module.LANGUAGE_CACHE_MISMATCH_WARNING_SHOWN = False
    cache_data_new = {"_version": __version__, "deu": {"name": "German new"}}
    cache_file.write_bytes(_make_cache(cache_data_new))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()
    assert language_module.LANGUAGE_CACHE["deu"]["name"] == "German new"


def test_load_cache_version_key_removed(tmp_path, reset_language_cache):
    """After a successful load, _version must not remain in the dict."""
    from hyperglot import __version__

    cache_data = {"_version": __version__, "xyz": {"name": "Test"}}
    cache_file = tmp_path / ".hyperglot-cache"
    cache_file.write_bytes(_make_cache(cache_data))

    with patch.object(language_module, "LANGUAGE_CACHE_FILE", str(cache_file)):
        _load_language_cache()

    assert "_version" not in language_module.LANGUAGE_CACHE
    assert len(language_module.LANGUAGE_CACHE) == 1