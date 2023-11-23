# Hyperglot – a database and tools for detecting language support in fonts

Hyperglot helps type designers answer a seemingly simple question of language support in fonts: When can I use font A to set texts in language B?  It takes a pragmatic answer by identifying a standard character set for each orthography used by a language. The database that currently contains information for over 640+ languages is a work in progress, designed to grow.

We record a basic and any auxiliary character sets for each orthography of a language. Note that only actively used orthographies (their status is set to `primary`) are used when detecting language support in a font. Other, secondary or historical, orthographies are displayed just for information purposes. 

Where relevant, we also provide a brief design note containing tips about shaping and positioning requirements that go beyond Unicode character code points. Hyperglot should only be used to detect whether a font can be considered for use with a particular language. It does not say anything about the quality of a font’s design.

Hyperglot is a work in progress provided AS IS, and the validity of its language data varies. To help you assess the validity of the results you view, each language in the database comes with a label indicating the quality of the data we have for it (e.g. some are considered `drafts`, some have been `verified`). We have checked the information against various online and offline sources and we are committed to continually improve it. However, we admit that mapping all the languages of the world in this way is beyond our capacity – we need help from users of each respective language! So, if you spot an issue or notice your favourite language is altogether missing from the database, get in touch. We will happily [incorporate your feedback and credit you](README_database.md#development-and-contributions).

[The comparison of Hyperglot and the Unicode CLDR](README_comparison.md)

## How to use

There are several ways how to use the database:

- Hyperglot web app at http://hyperglot.rosettatype.com
- command-line tool (`pip install hyperglot`, see usage notes below)
- python packagage (`pip install hyperglot`)
- access the YAML file with the database directly ([database README](README_database.md))

## It is complicated (disclaimer)

A few notes to illustrate why the question of language support is complicated:

1. a single language can be written using different orthographies in one or more scripts,
2. languages are not isolated, there are loan words, names etc. from other languages, thus finding what is an essential character set for a language is largerly a question of convention,
3. what one person considers a dialect, is a language for someone else,
4. different kinds of texts require different vocabulary and hence different characters.

It is important to note that **there is more to language support in fonts than supporting a set of code points**. A font needs to include glyphs with acceptable/readable shapes of the characters for a particular language. Sometimes there are regional or language variations for the same code point which means that different languages pose different requirements on the shape of a character, but identical requirements on the code point of the character. Moreover, glyphs have to interact as expected by the convention of a particular script/orthography. For example, some languages/scripts require (or strongly expect) certain glyph combinations to form ligatures or some glyph combinations require additional spacing correction (kerning) to prevent clashes or gaps. Thus, the report produced by the Hyperglot tools should only be used to detect whether a font can be considered for use with a particular language. It does not say anything about the quality of the design.

## Detecting support

Characters are represented using [Unicode](https://unicode.org) code points in digital texts, e.g. the Latin-script letter `a` has a code point `U+0061`. Digital OpenType fonts map these code points to glyphs, visual representations of characters. In order to find whether one can use a font for texts in a particular language, one needs to know which character code points are required for the language. This is what the Hyperglot database is for.

1. A list of codepoints is obtained from a font.
2. The database can be accessed in two modes:
  - By **default** combinations of a base character with marks are required as single code point where this exists (e.g. encoded `ä`), codepoints for base characters and combining mark characters (e.g. `a` and combining `¨`) from these combinations are also required.
  - Using the `decomposed` flag fonts are required to contain the base character and combining marks for a language (e.g. languages with `ä` will match for fonts that only have `a` and combining `¨` but not `ä` as encoded glyph).
3. Specified `validity` level is used to filter out language entries according to a user’s preference.
4. If requested, `base` and `aux` (auxiliary) lists of codepoints are combined to achieve more strict criteria by using the `--support` option. `marks` are always required, if set in the data.
5. When detecting language support (default), code points from **all** primary orthographies for a given language are combined (need to be included to detect support of the language). Orthographies with `historical` and `secondary` status are ignored.
6. When detecting orthography support, use `--include-all-orthographies`, all orthographies for a given language are checked individually. Orthographies with `secondary` status are included. Orthographies with `historical` status are ignored.
7. If the list of code points in the font includes all code points from the list of codepoints from points 5 or 6, the font is considered to support this language/orthography. In listings these are grouped by scripts.

The language-orthography combination means that a language that has multiple orthographies using different scripts (e.g., Serbian or Japanese) is listed under all of these scripts in the tools’ output.

## Command-line tool

A simple CLI tool is provided to output language support data for a passed in font file.

### Installation

You will need to have Python 3 installed. Install via pip:

```shell
pip install hyperglot
```

### Usage

```shell
hyperglot path/to/font.otf
```

or to check several fonts at once, or their combined coverage (with `-m union`)

```shell
hyperglot path/to/font.otf path/to/anotherfont.otf ...
```

**Additional options**:

- `-s, --support`: Specify what level of support to check against (currently options are "base" (default if omitted) or "aux")
- `-m, --marks`: Flag to signal a font should also include all combining marks used for a language - by default only those marks are required which are not part of preencoded characters (default is False)
- `-d, --decomposed`: Flag to signal a font should be considered supporting a language as long as it has all base glyphs and marks to write a language - by default also encoded precomposed glyphs are required (default is False)
- `-a, --autonyms`: Output the language names in their native language and script
- `--speakers`: Ouput how many speakers each language has (where available)
- `--sort`: Specify "speakers" to sort by speakers (default is "alphabetic")
- `--sort-dir`: Specify "desc" to sort in descending order (default is "asc" for ascending order)
- `-o, --output`: Supply a file path to write the output to, in yaml format. For a single input font this will be a subset of the Hyperglot database with the languages and orthographies that the font supports. If several fonts are provided the yaml file will have a top level dict key for each file. If the `-m` option is provided the yaml file will contain the specific intersection or union result
- `-c, --comparison`: How to process input if several files are provided (currently options are "individual", "union" and "intersection")
- `--include-all-orthographies`: Check all orthographies of a language, not just its primary one(s)
- `--validity`: Specify to filter by the level of validity of the language data (default is "preliminary")
- `--include-historical`: Option to include languages and orthographies marked as historical (default is False)
- `--include-constructed`: Option to include languages and orthographies that are marked as constructed (default is False)
- `--strict-iso`: Display language names and macrolanguage data strictly according to ISO (default is False)
- `-v, --verbose`: More logging information (default is False)
- `-V, --version`: Print the version hyperglot version number (default is False)

Installing the pip package also installed the `hyperglot-validate` and `hyperglot-save` commands, which allow checking and saving the yaml data in a structured and compatible way.

## Database and contributing

The data structure is described in a separate file together with guidelines for contributing.

Updates are comitted/merged to the `dev` branch with the `master` branch holding the latest released version.

[Database and contributing](README_database.md)

## Roadmap

- [] include records to track language and script specific punctuation and numerals
- [] include character combinations required by abugidas/syllabic scripts, e.g. list of conjuncts required by Hindi etc.
- [] comparison and export to Unicode CLDR format
- [] analysis of OpenType features in font to check if character combinations are supported

## Authors and contributors

The Hyperglot database and tools were originally developed by [Rosetta](http://rosettatype.com), world typography specialists, publishers, and makers of original fonts addressing the needs of global typography. Our goal is to enable people to read better in their native languages.

Main contributors, so far:

- David Březina <david@rosettatype.com> @MrBrezina (concept, database structure, and main language data set)
- Johannes Neumeier <hello@johannesneumeier.com> @kontur (tool and tests)
- Sérgio Martins @sergiolmartins (major expansion and review of the data, ca 250+ languages)
- Toshi Omagari  @toshe (basic language data for many Cyrillic-script languages)

[The full list of contributors](CONTRIBUTORS.txt)

## Similar projects and inspirations

- [Unicode CLDR](http://cldr.unicode.org)
- [Underware Latin Plus](https://underware.nl/latin_plus/)
- [Alphabet Type’ Charset Checker](https://www.alphabet-type.com/tools/charset-checker/) (uses Unicode CLDR AFAIK)
- [Typekit Speakeasy](https://github.com/typekit/speakeasy)
- [Adobe spreadsheets for Latin and Cyrillic](https://blog.typekit.com/2006/08/01/defining_an_ext/)
- [WebINK character sets](http://web.archive.org/web/20150222004543/http://blog.webink.com/custom-font-subsetting-for-faster-websites/) 
- [font-config languages definitions](https://cgit.freedesktop.org/fontconfig/tree/fc-lang)
- [Context of diacritics](https://www.setuptype.com/x/cod/)
