import os
from click.testing import CliRunner
from hyperglot.main import cli

runner = CliRunner()

eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
plex_arabic = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf")  # noqa


def test_main_cli():
    res = runner.invoke(cli, [eczar])
    assert res.exit_code == 0
    assert "languages of Latin script" in res.output
    assert "7 languages of Devanagari script" in res.output
    assert "Czech" in res.output
    assert "Hindi" in res.output
    assert "Sanskrit" in res.output
    assert "Assyrian Neo-Aramaic" in res.output


def test_main_cli_support_aux():
    res = runner.invoke(cli, [eczar])
    assert res.exit_code == 0
    assert "Assyrian Neo-Aramaic" in res.output

    res = runner.invoke(cli, eczar + " --support aux")
    assert "Assyrian Neo-Aramaic" not in res.output

    res = runner.invoke(cli, plex_arabic)
    assert "languages of Latin script" in res.output
    assert "languages of Arabic script" in res.output
    assert "Standard Arabic" in res.output
    assert "Assyrian Neo-Aramaic" in res.output

    res = runner.invoke(cli, plex_arabic + " --support aux")
    assert "Standard Arabic" not in res.output
    assert "Assyrian Neo-Aramaic" not in res.output


def test_main_cli_decomposed():
    """
    Tests that when requiring only "composable components" the language
    coverage should be wider (as compared to requiring encoded characters by
    default)
    """
    res = runner.invoke(cli, plex_arabic)
    assert "Achuar-Shiwiar" not in res.output

    res = runner.invoke(cli, plex_arabic + " --decomposed")
    assert "Achuar-Shiwiar" in res.output


def test_main_cli_include_constructed():
    res = runner.invoke(cli, plex_arabic)
    assert "Interlingua" not in res.output

    res = runner.invoke(cli, plex_arabic + " --include-constructed")
    assert "Interlingua" in res.output
