import os
from click.testing import CliRunner
from hyperglot.main import cli

runner = CliRunner()

eczar = os.path.abspath("tests/Eczar-v1.004/otf/Eczar-Regular.otf")
plex_arabic = os.path.abspath("tests/plex-4.0.2/IBM-Plex-Sans-Arabic/fonts/complete/otf/IBMPlexSansArabic-Regular.otf")  # noqa


def test_main_cli():
    res = runner.invoke(cli, [eczar])
    assert res.exit_code == 0
    assert "271 languages of Latin script" in res.output
    assert "7 languages of Devanagari script" in res.output
    assert "278 languages supported in total" in res.output


def test_main_cli_support():
    res = runner.invoke(cli, plex_arabic)
    assert "267 languages supported in total" in res.output
    res = runner.invoke(cli, plex_arabic + " --support aux")
    assert "240 languages supported in total" in res.output


def test_main_cli_decomposed():
    res = runner.invoke(cli, plex_arabic)
    assert "267 languages supported in total" in res.output
    res = runner.invoke(cli, plex_arabic + " --decomposed")
    assert "329 languages supported in total" in res.output


def test_main_cli_include_constructed():
    res = runner.invoke(cli, plex_arabic)
    assert "267 languages supported in total" in res.output
    res = runner.invoke(cli, plex_arabic + " --include-constructed")
    assert "275 languages supported in total" in res.output
