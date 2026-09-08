from pathlib import Path

import pytest
from click.testing import CliRunner
from fontTools.ttLib import TTFont

from hyperglot.checker import FontChecker
from hyperglot.cli import cli
from hyperglot.shaper import Shaper


@pytest.fixture(params=['woff', 'woff2'])
def webfont(request, tmp_path):
    source = Path('tests/Roboto/Roboto-Black.ttf').resolve()
    target = tmp_path / ('Roboto.' + request.param)
    with TTFont(source) as font:
        font.flavor = request.param
        font.save(target)
    return source, target


def test_webfont_shaping(webfont):
    source, target = webfont
    original = Shaper(str(source))
    compressed = Shaper(str(target))
    # Compression preserves characters and layout, including combining marks.
    for text in ['ABC', 'A\u0301', 'бгд']:
        expected = [(info.codepoint, pos.position)
                    for info, pos in original.get_glyph_data(text)]
        assert all(gid != 0 for gid, position in expected)
        assert [(info.codepoint, pos.position)
                for info, pos in compressed.get_glyph_data(text)] == expected


def test_webfont_language_support(webfont):
    source, target = webfont
    original = FontChecker(str(source))
    compressed = FontChecker(str(target))
    for iso in ['eng', 'rus', 'fin']:
        assert original.supports_language(iso)
        assert compressed.supports_language(iso)


def test_webfont_cli(webfont):
    source, target = webfont
    runner = CliRunner()
    original = runner.invoke(cli, ['--check=all', str(source)])
    compressed = runner.invoke(cli, ['--check=all', str(target)])
    assert original.exit_code == 0, original.output
    assert compressed.exit_code == 0, compressed.output

    def language_output(output):
        return [line for line in output.splitlines()
                if not line.endswith(' has support for:') and set(line) != {'='}]

    assert language_output(compressed.output) == language_output(original.output)
