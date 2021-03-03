# Hyperglot – database and tool for detecting language support in fonts

**Warning: this work is still in progress and provided AS IS.**

Characters are represented using [Unicode](https://unicode.org) code points in digital texts, e.g. the Latin-script letter `a` has a code point `U+0061`. Digital OpenType fonts map these code points to glyphs, visual representations of characters. In order to find whether one can use a font for texts in a particular language, one needs to know which character code points are required for the language. This is what the Hyperglot database is for.

A few notes to illustrate why the question of language support is complicated:

1. a single language can be written using different orthographies in one or more scripts,
2. languages are not isolated, there are loan words, names etc. from other languages, thus finding what is an essential character set for a language is largerly a question of convention,
3. what one person considers a dialect, is a language for someone else,
4. different kinds of texts require different vocabulary and hence different characters.

We have decided to take a pragmatic approach and reduce the problem to finding standard character set of each language (typically an official alphabet or syllabary or its approximation) for each orthography it uses. We only occassionally provide a list of auxiliary characters used in reference literature (linguistics) or in very common loan words.

It is important to note that **there is more to language support in fonts than supporting a set of code points**. A font needs to include glyphs with acceptable/readable shapes of the characters for a particular language. Sometimes there are regional or language variations for the same code point which means that different languages pose different requirements on the shape of a character, but identical requirements on the code point of the character. Moreover, glyphs have to interact as expected by the convention of a particular script/orthography. For example, some languages/scripts require (or strongly expect) certain glyph combinations to form ligatures or some glyph combinations require additional spacing correction (kerning) to prevent clashes or gaps. Thus, the report produced by the hyperglot tool should be used only to detect whether a font can be used for a particular language.

## Database

The database is stored in the YAML file `lib/Hyperglot/hyperglot.yaml`.


### Languages

The highest level entries represent languages indexed using the ISO 639-3 code.

Each language entry can have these attributes which default to empty string or list unless stated otherwise:

- `name` (required): the English name of the language. This is also based on ISO 639-3. 
- `preferred_name` (optional): an override of the ISO 639-3 name. This is useful when the ISO 639-3 name  is pejorative or racist. We also use this to simplify very long names and where we have a preference (e.g. Sami over Saami). This can be turned off when using the database via the CLI tool or module to adhere strictly to ISO 639-3.
- `autonym` (optional): the name of the language in the language itself.
- `orthographies` (optional): a list of orthographies for this language. See below.
- `speakers` (optional) is a number of L1 speakers obtained from Wikipedia. Note that this is a number of speakers, thus one needs to account for literacy rate in particular language. This can an integer or a range.
- `speakers_date` (optional) is the publication date of the reference used for the speakers count on Wikipedia.
- `status` (required, defaults to `living`) the status of the language, may be one of `historical, constructed, living`.
- `source` (optional) is a list of source names used to define the orthographies, e.g. Wikipedia, Omniglot, Alvestrand. See below for the complete list.
- `validity` (required, defaults to `todo`): one of the following:
  - `todo` for unfinished entries which may be used to detect a potential language support with little certainty,
  - `weak` for entries that are complete but have not been checked, yet,
  - `done` for entries we have checked with at least two online sources,
  - `verified` for entries confirmed by a native speaker or a linguist.
- `note` (optional): a note of any kind.


### Orthographies

A language can refer to one or more orthographies. An orthography specifies the script and characters from this script used to represent the language. There can be multiple orthographies for the same language using the same or different scripts. Each orthographic entry can have these attributes which default to an empty string or list unless stated otherwise:

- `base` (required or use `inherit`): a string of space-separated characters or combinations of characters and combining marks that are required to represent the language in common texts. This typically maps to a standard alphabet or syllabary for the language or an approximation of thereof. In case the script used is bicameral, only lowercase versions of characters are provided with a few exceptions, e.g. the Turkish `İ`.
- `auxiliary` (optional): a string of space-separated characters or combinations of characters and combining marks that are not part of the standard alphabet, but appear in very common loan words or in reference literature. Deprecated characters can be included here too, e.g. `ş ţ` for Romanian.
- `autonym` (optional): the name of the language in the language itself using this orthography. If missing, the `autonym` defined in the parent language entry is used. It is expected that the `autonym` can be spelled with the orthography's `base`.
- `inherit` (required or use `base`): the code of a language to copy the `base` and `auxiliary` strings from. In case the language has multiple orthographies, the first one for the same script is used.
- `script` (required): English name of the main script used by the orthography, e.g. Latin, Arabic, Armenian, Cyrillic, Greek, Hebrew. When a language uses a combination of several scripts in conjunction each script forms its own orthography.
- `status` (required, defaults to `primary`): the status of the orthography, may be one of: `deprecated, secondary, local, primary`. The value `local` refers to an orthography which is used only in a specific region. Orthographies with `secondary` status are ignored during language support detection, but used when detecting `orthography` support. Orthographies with `deprecated` status are included only for the sake of completeness.
- `preferred_as_group` will combine all orthographies of this language. For a language to be listed as supported the font needs to support all those orthographies.
- `note` (optional): a note of any kind. We will add a note about other support requirements we know, e.g. OpenType features.


### Macrolanguages

[Macrolanguages](https://en.wikipedia.org/wiki/ISO_639_macrolanguage) are used in the ISO 639-3 standard to keep it compatible with ISO 639-2 in situations where one language entry in ISO 639-2 corresponds to a group of languages in ISO 639-3. Macrolanguages are typically not used by the Hyperglot’s main database. They are stored in a separate file in `other/hyperglot_macrolanguages.yaml` for convenience. However, in some situations, it is our preference to include some of the macrolanguages as if they were regular ISO 639-3 languages. This is done to simplify the listings or to deal with scarcity of information for its sub-languages. Besides the same attributes as language entries, macrolanguages can use the following:

- `includes` (required) contains a list of ISO 639-3 codes referring to sub-languages of the macrolanguage.
- `preferred_as_individual` (optional, defaults to `false`): set to `true` signifies that the macrolanguage us included in the main database as if it was a regular language.



### Example of individual language with one orthography

```
dan:
  orthographies:
  - base: a b c d e f g h i j k l m n o p q r s t u v w x y z å æ ø
    auxiliary: ǻ  # this character is used only in linguistic literature for Danish
    autonym: Dansk
    script: Latin
  name: Danish
  speakers: 6000000
  source: [Omniglot, Wikipedia, CLDR]
  todo_status: strong  # status of the database record
```

### A macrolanguage

```
fas:
  name: Persian
  includes: [pes, prs, tgk, aiq, bhh, haz, jpr, phv, deh, jdt, ttt]
  speakers: 70000000
  source: [Wikipedia]
```

## Detecting support

1. A list of codepoints is obtained from a font.
2. The database can be accessed in two modes:
	- By **default** combinations of a base character with marks are required as single code point where this exists (e.g. encoded `ä`), codepoints for base characters and combining mark characters (e.g. `a` and combining `¨`) from these combinations are also required.
	- Using the `decomposed` flag fonts are required to contain the base character and combining marks for a language (e.g. languages with `ä` will match for fonts that only have `a` and combining `¨` but not `ä` as  encoded glyph).
3. Specified `validity` level is used to filter out language entries according to a user’s preference.
4. If requested, `base` and `aux` (auxiliary) lists of codepoints are combined to achieve more strict criteria by using the `--support` option.
5. When detecting language support (default), code points from **all** primary orthographies for a given language are combined (need to be included to detect support of the language). Orthographies with `deprecated` and `secondary` status are ignored.
6. When detecting orthography support, use `--include-all-orthographies`, all orthographies for a given language are checked individually. Orthographies with `secondary` status are included. Orthographies with `deprecated` are ignored.
7. If the list of code points in the font includes all code points from the list of codepoints from points 5 or 6, the font is considered to support this language/orthography. In listings these are grouped by scripts.

The language-orthography combination means that a language that has multiple orthographies using different scripts (e.g., Serbian or Japanese) will be listed under all of these scripts.




## Command-line tool

A simple CLI tool is provided to output language support data for a passed in font file.

### Installation

You will need to have Python 3 installed. Install via repo and pip:

```
$ pip install git+https://github.com/rosettatype/hyperglot
```

### Usage

`$ hyperglot path/to/font.otf`

or to check several fonts at once, or their combined coverage (with `-m union`)

`$ hyperglot path/to/font.otf path/to/anotherfont.otf ...`

**Additional options**:

- `-s, --support`: Specify what level of support to check against (currently options are "base" (default if omitted) or "aux")
- `-d, --decomposed`: Flag to signal a font should be considered supporting a language as long as it has all base glyphs and marks to write a language - by default also encoded precomposed glyphs are required (default is False)
- `-a, --autonyms`: Output the language names in their native language and script
- `-u, --users`: Also output language user count (where available)
- `-o, --output`: Supply a file path to write the output to, in yaml format. For a single input font this will be a subset of the Hyperglot database with the languages and orthographies that the font supports. If several fonts are provided the yaml file will have a top level dict key for each file. If the `-m` option is provided the yaml file will contain the specific intersection or union result
- `-m, --mode`: How to process input if several files are provided (currently options are "individual", "union" and "intersection")
- `--include-all-orthographies`: Check all orthographies of a language, not just its primary one(s)
- `--validity`: Specifiy to filter by the level of certainty the database information has for languages (default is "done")
- `--include-historical`: Option to include languages and orthographies marked as historical (default is False)
- `--include-constructed`: Option to include languages and orthographies that are marked as constructed (default is False)
- `--strict-iso`: Display language names and macrolanguage data strictly according to ISO (default is False)
- `-v, --verbose`: More logging information (default is False)
- `-V, --version`: Print the version hyperglot version number (default is False)

### Validating and sorting the database yaml file

Simple validation and sorting script to verify the data integrity of `hyperglot.yaml` and point out possible formatting errors is included as `hyperglot-validate` (prints problems to terminal) and `hyperglot-save` (saves the `hyperglot.yaml` sorted alphabetically and pruned by iso keys)

### Development

To run the script during development without having to constantly reinstall the pip package, you can use:

```
$ git clone https://github.com/rosettatype/hyperglot.git && cd hyperglot
$ pip install --upgrade --user --editable .
```

To test the codebases after making changes run the `pytest` test suite:

```
pytest
```

## Sources

The main sources we used to build the database are:

- Alvestrand, Harald Tveit. Characters and character sets for various languages. 1995.
- [Ethnologue](http://ethnologue.org)
- [ISO 639-3 ](http://iso639-3.sil.org)
- [Omniglot](http://omniglot.com)
- [Unicode CLDR](http://unicode.org)
- [Wikipedia](http://wikipedia.org)

The autonyms were sourced from Ethnologue, Wikipedia, and Omniglot (in this order preferrably).
The speaker counts are from Wikipedia.

## Credits

- David Březina  
- Sérgio Martins  
- Johannes Neumeier
- Toshi Omagari

## Contributing

A few random notes:

- Languages that are not written should not be included. Obviously.
- Languages that have some speakers should not be marked as `extinct` even if ISO standard says so.
- When adding or editing language data use the CLI commands `hyperglot-validate` to check your new data is compatible and use `hyperglot-save` to actually "save" the database in a standardized way (clean up, sorting, etc).
- When contributing code make sure to install the `pytest` module and run `pytest` and make sure no errors are detected. Ideally, write tests for any code additions or changes you added.


## Other databases included in this repo

The following are YAML files distilled from the original data stored in subfolders with corresponding names.

- `other/alvestrand.yaml` – data (indexed by ISO 639-3 codes) scraped from Alvestrand (see Sources below).
- `other/cldr.yaml` - data (indexed by 4-letter script tags and ISO 639-3 language codes) from Unicode’s CLDR database.
- `other/iso-639-3.yaml` – data from IS0 639-3 (three-letter codes) with corresponding ISO 639-2 (older three-letter codes) and ISO 639-1 (two-letter codes) where available. Also includes language names and attributes from ISO 639-3.
- `other/iso-639-3_retirements.yaml` – language codes no longer available in ISO 639-3
- `other/iso-639-2_collections.yaml` – language collections from ISO 639-2 (no longer available in ISO 639-3)
- `other/opentype-language-tags.yaml` –OpenType language tags and names with their corresponding ISO 639-3 language codes

The following data was not used to built the Hyperglot database, but it used to build comparative previews:

- `other/extensis` – character sets compiled by Extensis/WebINK
- `other/iana` – from [IANA language subtag registry](https://www.iana.org/assignments/lang-subtags-templates/lang-subtags-templates.xhtml)
- `other/latin-plus` - data from a [Latin-only database compiled by Underware](https://underware.nl/latin_plus/)
