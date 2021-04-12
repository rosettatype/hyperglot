"""
Tests verifying the CLI output is as expected. This uses the runner.invoke
helper to call the main cli handler with various arguments.
"""
import os
import re
import yaml
from collections import OrderedDict
from click.testing import CliRunner
from hyperglot.main import (cli, intersect_results,
                            union_results, sorted_script_languages)

runner = CliRunner()

eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
eczar_no_marks = os.path.abspath(
    "tests/Eczar-v1.004/otf/Eczar-Regular-nomarks-nofeatures.otf")
plex_arabic = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf")  # noqa


def test_main_cli():
    res = runner.invoke(cli, [eczar])
    assert res.exit_code == 0
    assert "languages of Latin script" in res.output
    assert "10 languages of Devanagari script" in res.output
    assert "Czech" in res.output
    assert "Hindi" in res.output
    assert "Sanskrit" in res.output


def test_main_cli_support_aux():
    res = runner.invoke(cli, [eczar])
    assert res.exit_code == 0
    assert ", German," in res.output

    res = runner.invoke(cli, eczar + " --support aux")
    # No cap ß, thus missing from aux level support, note "Swiss German" alas
    # the commas
    assert ", German," not in res.output

    res = runner.invoke(cli, plex_arabic)
    assert "languages of Latin script" in res.output
    assert "languages of Arabic script" in res.output
    assert "Standard Arabic" in res.output

    res = runner.invoke(cli, plex_arabic + " --support aux")
    assert "Standard Arabic" not in res.output


def test_main_cli_decomposed():
    """
    Tests that when requiring only "composable components" the language
    coverage should be wider (as compared to requiring encoded characters by
    default)
    """
    total = re.compile(r"(\d+) languages supported in total.")

    # With Plex Arabic
    res = runner.invoke(cli, plex_arabic)
    total_default = int(total.search(res.output).group(1))
    # acu / Achuar-Shiwiar should not be in default
    assert "Achuar-Shiwiar" not in res.output

    res = runner.invoke(cli, plex_arabic + " --decomposed")
    total_decomposed = int(total.search(res.output).group(1))
    # acu / Achuar-Shiwiar should be in decomposed
    assert "Achuar-Shiwiar" in res.output

    # Decomposed should always support more than default
    assert total_default <= total_decomposed

    # With Eczar
    res = runner.invoke(cli, eczar)
    total_default = int(total.search(res.output).group(1))
    # acu / Achuar-Shiwiar should not be in default, because Utilde is missing
    # but U + tildecomb are available
    assert "Achuar-Shiwiar" not in res.output

    res = runner.invoke(cli, eczar + " --decomposed")
    total_decomposed = int(total.search(res.output).group(1))
    # acu / Achuar-Shiwiar should be in decomposed, because Utilde is missing
    # but U + tildecomb are available
    assert "Achuar-Shiwiar" in res.output

    # Decomposed should always support more than default
    assert total_default <= total_decomposed


def test_main_cli_marks():
    total = re.compile(r"(\d+) languages supported in total.")

    # With Eczar which has all marks crudely removed
    # This should support _almost_ as many as the full version, mostly
    # non-latin missing
    res = runner.invoke(cli, eczar_no_marks)
    total_no_marks = int(total.search(res.output).group(1))

    # With Eczar which has all marks crudely removed
    # This will be drastically less supported, because the marks are missing,
    # so only languages which require no marks and of which all characters are
    # encoded are supported
    res = runner.invoke(cli, eczar_no_marks + " --marks")
    total_no_marks_flag = int(total.search(res.output).group(1))

    # With Eczar which has all marks
    res = runner.invoke(cli, eczar)
    total = int(total.search(res.output).group(1))

    assert total > total_no_marks
    assert total_no_marks > total_no_marks_flag


def test_main_cli_include_constructed():
    res = runner.invoke(cli, plex_arabic)
    assert "Interlingua" not in res.output

    res = runner.invoke(cli, plex_arabic + " --include-constructed")
    assert "Interlingua" in res.output


def test_main_cli_include_all_orthographies():
    res = runner.invoke(cli, plex_arabic)
    # Has Cyrillic primary, but Latin secondaries

    # primary Latin not supported, but secondary is
    assert "Chickasaw" not in res.output

    # Has Syriac primary, but Latin secondary
    assert "Assyrian Neo-Aramaic" not in res.output

    res = runner.invoke(cli, plex_arabic + " --include-all-orthographies")
    print(res.output)
    assert "Chickasaw" in res.output
    assert "Assyrian Neo-Aramaic" in res.output


def test_main_cli_output(yaml_output):
    res = runner.invoke(cli, eczar + " -o %s" % yaml_output)

    # CLI without errors
    assert res.exit_code == 0

    # Has content
    assert os.path.isfile(yaml_output) is True
    assert os.path.getsize(yaml_output) > 0

    with open(yaml_output, "r") as f:
        # Is yaml that can be parsed
        data = yaml.load(f, Loader=yaml.Loader)
        assert "aae" in data.keys()
        assert "fin" in data.keys()


def test_main_cli_output_union(yaml_output):
    res = runner.invoke(cli, "%s %s -o %s -c union" %
                        (eczar, plex_arabic, yaml_output))

    # CLI without errors
    assert res.exit_code == 0

    # Has content
    assert os.path.isfile(yaml_output) is True
    assert os.path.getsize(yaml_output) > 0

    with open(yaml_output, "r") as f:
        # Is yaml that can be parsed
        data = yaml.load(f, Loader=yaml.Loader)

        assert "aae" in data.keys()
        assert "fin" in data.keys()

        # Supported by plex but not eczar, thus union
        assert "abv" in data.keys()
        assert "azb" in data.keys()


def test_main_cli_output_intersection(yaml_output):
    res = runner.invoke(cli, "%s %s -o %s -c intersection" %
                        (eczar, plex_arabic, yaml_output))

    # CLI without errors
    assert res.exit_code == 0

    # Has content
    assert os.path.isfile(yaml_output) is True
    assert os.path.getsize(yaml_output) > 0

    with open(yaml_output, "r") as f:
        # Is yaml that can be parsed
        data = yaml.load(f, Loader=yaml.Loader)

        assert "aae" in data.keys()
        assert "fin" in data.keys()

        # Supported by plex but not eczar, thus intersection
        assert "abv" not in data.keys()
        assert "azb" not in data.keys()


def test_main_cli_output_multiple(yaml_output):
    res = runner.invoke(cli, "%s %s -o %s" %
                        (eczar, plex_arabic, yaml_output))

    # CLI without errors
    assert res.exit_code == 0

    # CLI will list both file names in output
    assert os.path.basename(eczar) in res.output
    assert os.path.basename(plex_arabic) in res.output

    # Has content
    assert os.path.isfile(yaml_output) is True
    assert os.path.getsize(yaml_output) > 0

    with open(yaml_output, "r") as f:
        # Is yaml that can be parsed
        data = yaml.load(f, Loader=yaml.Loader)

        # File names are top level dict keys
        assert os.path.basename(eczar) in data.keys()
        assert os.path.basename(plex_arabic) in data.keys()


def test_intersect_results():
    A = {
        "Latin": {
            "eng": {},
            "deu": {},
            "ces": {},
        },
        "Arabic": {
            "bar": {},
            "foo": {},
        },
        "Cyrillic": {
            "foo": {}
        },
    }

    B = {
        "Arabic": {
            "bar": {}
        },
        "Latin": {
            "fin": {},
            "deu": {},
            "eng": {},
        },
    }

    # Combined and both levels sorted alphabetically by key
    expected = {
        "Arabic": {
            "bar": {},
        },
        "Latin": {
            "deu": {},
            "eng": {},
        }
    }

    # Only the script + iso in both results should be returned
    assert intersect_results(A, B) == expected

    # If either is empty, the result should be empty
    assert intersect_results(A, {}) == {}
    assert intersect_results({}, B) == {}

    # Single should return itself
    assert intersect_results(A) == A

    # Empty should return empty
    assert intersect_results() == {}


def test_union_results():
    A = {
        "Latin": {
            "deu": {},
            "ces": {}
        },
        "Cyrillic": {
            "foo": {}
        }
    }

    B = {
        "Latin": {
            "deu": {},
            "eng": {}
        },
        "Arabic": {
            "bar": {}
        }
    }

    # Combined and both levels sorted alphabetically by key
    expected = OrderedDict({
        "Arabic": {
            "bar": {}
        },
        "Cyrillic": {
            "foo": {}
        },
        "Latin": {
            "ces": {},
            "deu": {},
            "eng": {}
        }
    })

    # Only the script + iso in both results should be returned
    assert union_results(A, B) == expected

    # If either is empty, the result should be the non empty one
    assert union_results(A, {}) == A
    assert union_results({}, B) == B


def test_sorted_script_languages():
    expected = OrderedDict({
        "Arabic": {
            "bar": {}
        },
        "Cyrillic": {
            "foo": {}
        },
        "Latin": {
            "ces": {},
            "deu": {},
            "eng": {}
        }
    })

    unsorted = OrderedDict({
        "Cyrillic": {
            "foo": {}
        },
        "Arabic": {
            "bar": {}
        },
        "Latin": {
            "eng": {},
            "deu": {},
            "ces": {},
        }
    })

    assert sorted_script_languages(unsorted) == expected
