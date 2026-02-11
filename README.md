# Hyperglot – a database and tools for detecting language support in fonts

**Hyperglot** is an open research project dedicated to documenting how the world’s languages are written. By mapping orthographies and their requirements, it supports inclusive, multilingual type design and equitable access to high-quality typography for underserved communities. Hyperglot currently covers 783 languages, representing approximately 7.3 billion speakers, and is developed as open source by [Rosetta Type/Research](https://rosettatype.com) in collaboration with a global [community of contributors](CONTRIBUTORS.txt).

Hyperglot is available as:

- the [Hyperglot web app](https://hyperglot.rosettatype.com),
- the command-line tool: `hyperglot`,
- the python packagage: `import hyperglot` (see [examples](/examples) for basic usage).

📖 [Learn more about Hyperglot](https://hyperglot.rosettatype.com/about)

💰 [Sponsor via GitHub](https://github.com/sponsors/rosettatype) or directly via [Hyperglot sponsorship](https://hyperglot.rosettatype.com/sponsor). Any and all contributions are much appreciated! 🙏

## Data validity & contributing

Hyperglot is a work in progress and provided AS IS. The validity of language data varies and continues to improve. Each language includes a validity label (`todo, draft, preliminary, verified`) to help you assess the data.

Mapping all the world’s languages is a huge task—we need help from native speakers and language users! If you notice an error or see that a language is missing, please get in touch (via [email](https://rosettatype.com/contact) or [Issues](/issues)). We welcome contributions and will credit your input.

The data structure is documented in a [separate README file along with guidelines for contributing](README_database.md).

## Core concepts

The following concepts are essential to understanding how Hyperglot works.

A *language* can be written in one or more scripts. Each such writing system is represented in Hyperglot as an *orthography*. Most languages have a single primary orthography; however, some use multiple orthographies either independently (for example, in different regions) or concurrently (such as Serbian or Japanese).

In the database, an orthography contains the following character sets:

- `base` – the required, essential characters,
- `aux` – non-essential, recommended characters,
- `marks` – combining marks,
- `punctuation`,
- `numerals`, and
- `currency`.

A script, however, is more than a collection of characters. It also defines how characters interact when combined. This behavior is known as *shaping* and, in digital fonts, is implemented using OpenType features.

[Read the detailed description of the database structure](README_database.md)

## Language support detection process

To detect language support in a font, Hyperglot performs the following checks:

1. **Required characters are present.** Which characters are considered required is specified by filtering based on language/orthography status, data validity, and by selecting which character sets to check against.
2. **Precomposed character combinations are handled by the font.** For character combinations that have a unique code point in [Unicode](https://unicode.org), one of the following (depending on the setting):
   1. The encoded, precomposed character combinations are present.
   2. Base characters and mark characters from these combinations are present independently.
   3. Both of the above.
3. **Shaping behaviour is correctly handled by the font,** where applicable:
   1. Required mark-positioning instructions are present.
   2. Required alternates for joining behavior (for example, in Arabic) are present.
   3. Conjunct syllable construction in Brahmi-derived scripts is supported. (Currently supported only for Hindi/Devanagari.)

Additional design-related notes are provided for the user’s discretion when assessing design quality. Hyperglot does not assess the font design in any way.

## Command-line tools

### Installation

You will need to have Python 3 installed. Install via pip:

```shell
pip install hyperglot
```

Besides the main `hyperglot` command used for font inspection, the package also includes:

- `hyperglot-report` – report missing language support (see [below](#report-missing-language-support)).
- `hyperglot-data` – review language data stored in the database.
- `hyperglot-validate`, `hyperglot-save`, and `hyperglot-export` – manage and process data when contributing.

### Basic usage

Use:

```shell
hyperglot path/to/font.otf
```

to output a list of supported languages (and other data) for a font. Use:

```shell
hyperglot path/to/font.otf path/to/anotherfont.otf …
```

to check several fonts at once, or their combined coverage (with `-m union`).

### Advanced options

- `-c, --check`: Specify which character sets to check against. Options are 'base, auxiliary, punctuation, numerals, currency, all', or a comma-separated combination of these. (Default: 'base')
- `--validity`: Filter languages by data validity level. Options are 'todo, draft, preliminary, verified'. (Default: 'preliminary')
- `-s, --status`: Specify which languages to consider when checking support. Options are 'living, historical, constructed, all', or a comma-separated combination of these . (Default: 'living')
- `-o, --orthography`: Which orthographies to consider when checking support for a language. Options are 'primary, secondary, historical, transliteration, all', or a comma-separated combination of these. (Default: 'primary')
- `-d, --decomposed`: For precomposed character combinations, require only the individual component characters. By default, precomposed character combinations are also required when they have a unique code point in Unicode. (Default: False)
- `-m, --marks`: Require that a font include all combining marks used by a language’s orthography. By default, only marks that are not part of precomposed character combinations are required. (Default: False)
- `--sort`: Specify the sort order. Use "speakers" to sort by number of speakers. (Default: "alphabetic")
- `--sort-dir`: Specify the sort direction. Use "desc" for descending order. (Default: "asc" for ascending order)
- `-y, --output`: Specify a file path to write the output to, in YAML format. For a single input font, the output is a subset of the Hyperglot database containing the languages and orthographies supported by the font. When multiple fonts are provided, the YAML file contains a top-level key for each font. If the `-m` option is provided, the output includes the specific intersection or union result.
- `-t, --shaping-threshold`: Set the frequency threshold for complex-script shaping checks. A font passes when it renders correctly for combinations at or above this threshold. Frequencies range from 1.0 (most frequent combinations) to 0.0 (rares combinations). (Default: 0.01)
- `--no-shaping` Disable shaping checks (mark attachment, joining behavior, and conjunct shaping). (Default: shaping checks enabled)
- `-v, --verbose`: Enable verbose logging.
- `-V, --version`: Print the Hyperglot version number.

### Report missing language support

The `hyperglot-report` reports missing characters and shaping support. A common use case is identifying languages that could be supported with minimal additional work in a given font. The command accepts the same options as `hyperglot` and the following options:

- `--report-missing`: Report languages missing `n` or fewer characters. If `n` is 0, all languages with any number of missing characters are reported. (Default: 0)
- `--report-marks`: Report languages missing `n` or fewer mark-attachment sequences. If `n` is 0, all languages with any number of missing mark-attachment sequences are reported. (Default: 0)
- `--report-joining`: Report languages missing `n` or fewer joining sequences. If `n` is 0, all languages with any number of missing joining sequences are reported. (Default: 0)
- `--report-all`: Set or override all other `--report-*` options.

## Common pitfalls / FAQ

**Q: Why doesn’t Serbian appear in the list of Latin-script languages?**

**A:** Serbian is written in both, the Latin and Cyrillic scripts. Thus, Hyperglot requires support for both required orthographies. The same applies to Japanese, Ainu, Okinawan, Pontic Greek, Tlingit, and Xavánte.

**Q: Why doesn’t Japanese appear in the list of Latin-script languages, even though it can be written using the Latin script?**

**A:** Japanese written in the Latin script (rōmaji) is classified as a secondary orthography. Adjust the filter accordingly (for example, `--orthography=primary,secondary`) to include it.

**Q: Why is German not showing up in the list of supported languages even though my font supports it?**

**A:** Make sure to consider precomposed character combinations (using `--decomposed` and `--marks`) and the orthography you want to check. This guidance applies to any language, not just German.

**Q: My font includes Katakana. Why is Japanese not listed as a supported language?**

**A:** Hyperglot requires a font to include Hiragana, Katakana, and Kanji in order to consider Japanese fully supported.

**Q: My font includes Balinese script characters. Why is Balinese not listed as a supported language?**

**A:** The primary orthography for Balinese is actually Latin, as it is the most common way of writing the language today. To include checks for the secondary orthography that uses the Balinese script, set the flag to `--orthography=primary,secondary`.

**Q: Why is language data for XYZ missing while YZX is included?**

**A:** A language can be included if it meets two criteria:

1. It has an assigned [ISO 639-3 code](https://iso639-3.sil.org).
2. It has an established orthography that can be represented using [Unicode](https://unicode.org) characters.

If XYZ meets these requirements but is not yet in the database, please consider contributing or opening an issue](/issues).

The database uses ISO 639-3 language codes. If a language does not have an assigned ISO 639-3 code, we are currently unable to include it.

We recognize that opinions may differ on what constitutes a distinct language versus a dialect. However, to ensure consistency and interoperability, we adhere to the ISO 639-3 international standard.

## Roadmap

- [x] 🪶 Change licence to Apache 2
- [x] 💰 Invite sponsorship and funding[#174](https://github.com/rosettatype/hyperglot/issues/174)
- [x] 🤖 Basic analysis of shaping support provided by the font (GPOS and GSUB): check whether character combinations are affected by font OpenType features, enabling scalable support for complex combinations (e.g., Arabic, Hindi/Devanagari). [#176](https://github.com/rosettatype/hyperglot/issues/176)
- [ ] ➡️ Export in a format suitable for submission to Unicode CLDR
- [ ] 🌍 Web app: add links to other resources per language
- [ ] 📚 Improve language data, sources, and validity for languages with fewer authoritative references [#157](https://github.com/rosettatype/hyperglot/issues/157)
- [ ] 🌍 Add data for more African languages and scripts, e.g., N'Ko [#195](https://github.com/rosettatype/hyperglot/issues/195)
- [ ] 🇮🇳 Add more shaping checks for Brahmi-derived scripts [#176](https://github.com/rosettatype/hyperglot/issues/176)
- [ ] 🇧🇷 Add data for indigenous Brazilian languages (Rafael Dietzch and students)
- [ ] 🇺🇳 Secure funding to expand language coverage

## Other

[The comparison of Hyperglot and the Unicode CLDR](README_comparison.md) (this might be outdated atm.)
